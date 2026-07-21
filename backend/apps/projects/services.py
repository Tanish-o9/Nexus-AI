from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.organizations.models import Organization
from .models import Project, Task, ChecklistItem, ProjectMembership, ActivityLog


# ── Activity Logging ───────────────────────────────────────────────────────────

def log_activity(project, actor, action, task=None, field_name='', old_value='', new_value='', description=''):
    """Create an activity log entry."""
    return ActivityLog.objects.create(
        project=project,
        task=task,
        actor=actor,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value else '',
        new_value=str(new_value) if new_value else '',
        description=description,
    )


# ── Project services ──────────────────────────────────────────────────────────

def create_project(name: str, description: str, organization_id: str, created_by, template_id: str = None, is_template: bool = False) -> Project:
    try:
        org = Organization.objects.get(pk=organization_id)
    except Organization.DoesNotExist:
        raise ValidationError({'organizationId': 'Organization not found.'})

    if not created_by.memberships.filter(organization=org, is_active=True).exists():
        raise PermissionDenied('You are not a member of this organization.')

    project = Project.objects.create(
        name=name,
        description=description,
        organization=org,
        created_by=created_by,
        is_template=is_template,
    )

    # Auto-create owner membership for the creator
    ProjectMembership.objects.create(
        project=project,
        user=created_by,
        role=ProjectMembership.Role.OWNER,
        invited_by=created_by,
    )

    log_activity(project, created_by, ActivityLog.Action.CREATED, description=f'Project "{name}" created')

    if template_id:
        try:
            template = Project.objects.get(pk=template_id, is_template=True)
            for task in template.tasks.all():
                new_task = Task.objects.create(
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    project=project,
                    created_by=created_by,
                    due_date=task.due_date,
                )
                # Copy checklist items
                for item in task.checklist_items.all():
                    ChecklistItem.objects.create(
                        title=item.title,
                        is_completed=item.is_completed,
                        task=new_task,
                    )
        except Project.DoesNotExist:
            pass

    return project


def update_project(project: Project, data: dict, updated_by=None) -> Project:
    for field, value in data.items():
        old_val = getattr(project, field, '')
        setattr(project, field, value)
        if updated_by and old_val != value:
            log_activity(
                project, updated_by, ActivityLog.Action.UPDATED,
                field_name=field, old_value=old_val, new_value=value,
                description=f'Updated {field}'
            )
    project.save(update_fields=list(data.keys()) + ['updated_at'])
    return project


# ── Task services ─────────────────────────────────────────────────────────────

def create_task(project: Project, data: dict, created_by) -> Task:
    # Validate assignee is a member of the project's org
    assignee_id = data.get('assignee_id')
    if assignee_id:
        _assert_org_member(assignee_id, project.organization_id)

    assignees = data.pop('assignees', None)
    watchers = data.pop('watchers', None)
    labels = data.pop('labels', None)

    task = Task.objects.create(
        project=project,
        created_by=created_by,
        **data,
    )

    if assignees:
        task.assignees.set(assignees)
    if watchers:
        task.watchers.set(watchers)
    if labels:
        task.labels.set(labels)

    log_activity(
        project, created_by, ActivityLog.Action.CREATED,
        task=task, description=f'Task "{task.title}" created'
    )

    return task


def update_task(task: Task, data: dict, updated_by=None) -> Task:
    assignee_id = data.get('assignee_id')
    if assignee_id:
        _assert_org_member(assignee_id, task.project.organization_id)

    assignees = data.pop('assignees', None)
    watchers = data.pop('watchers', None)
    labels = data.pop('labels', None)

    for field, value in data.items():
        old_val = getattr(task, field, '')
        setattr(task, field, value)
        if updated_by and old_val != value:
            action = ActivityLog.Action.UPDATED
            if field == 'status':
                action = ActivityLog.Action.STATUS_CHANGED
            elif field == 'assignee_id':
                action = ActivityLog.Action.ASSIGNED if value else ActivityLog.Action.UNASSIGNED
            log_activity(
                task.project, updated_by, action,
                task=task, field_name=field, old_value=old_val, new_value=value,
                description=f'Updated {field}'
            )

    if data:
        task.save(update_fields=list(data.keys()) + ['updated_at'])

    if assignees is not None:
        task.assignees.set(assignees)
    if watchers is not None:
        task.watchers.set(watchers)
    if labels is not None:
        task.labels.set(labels)

    return task


def rate_task_performance(task: Task, rating: str, rated_by) -> Task:
    task.performance_rating = rating
    old_status = task.status
    task.status = Task.Status.DONE
    task.save(update_fields=['performance_rating', 'status', 'updated_at'])
    log_activity(
        task.project, rated_by, ActivityLog.Action.UPDATED,
        task=task, field_name='performance_rating', old_value=old_status, new_value='done',
        description=f'Owner rated task as {rating} (Moved to Done)'
    )
    return task


# ── Project Membership services ────────────────────────────────────────────────

def add_project_member(project, user, role, invited_by):
    """Add a member to a project. Creates membership if not exists, else reactivates."""
    membership, created = ProjectMembership.objects.get_or_create(
        project=project,
        user=user,
        defaults={'role': role, 'invited_by': invited_by, 'is_active': True},
    )
    if not created:
        membership.is_active = True
        membership.role = role
        membership.save(update_fields=['is_active', 'role'])

    log_activity(
        project, invited_by, ActivityLog.Action.MEMBER_ADDED,
        description=f'{user.email} added as {role}'
    )
    return membership


def remove_project_member(membership, removed_by):
    """Soft-remove a member from a project."""
    user_email = membership.user.email
    membership.is_active = False
    membership.save(update_fields=['is_active'])

    log_activity(
        membership.project, removed_by, ActivityLog.Action.MEMBER_REMOVED,
        description=f'{user_email} removed from project'
    )


def update_project_member_role(membership, new_role, updated_by):
    """Update a member's role in a project."""
    old_role = membership.role
    membership.role = new_role
    membership.save(update_fields=['role'])

    log_activity(
        membership.project, updated_by, ActivityLog.Action.MEMBER_ROLE_CHANGED,
        field_name='role', old_value=old_role, new_value=new_role,
        description=f'{membership.user.email} role changed from {old_role} to {new_role}'
    )


def _assert_org_member(user_id, org_id):
    from apps.accounts.models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        raise ValidationError({'assigneeId': 'Assignee not found.'})
    if not user.memberships.filter(organization_id=org_id, is_active=True).exists():
        raise ValidationError({'assigneeId': 'Assignee must be a member of this organization.'})