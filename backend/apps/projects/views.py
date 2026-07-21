from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from apps.accounts.models import User

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import (
    Project, Task, Label, KanbanColumn, ChecklistItem,
    TaskDependency, TaskAttachment, TaskComment, TimeEntry,
    ProjectMembership, ActivityLog, Milestone
)
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectUpdateSerializer,
    TaskSerializer, TaskCreateSerializer, LabelSerializer, KanbanColumnSerializer,
    ChecklistItemSerializer, TaskAttachmentSerializer, TaskCommentSerializer,
    TimeEntrySerializer, TaskDependencySerializer,
    ProjectMembershipSerializer, ProjectMembershipUpdateSerializer,
    ActivityLogSerializer, MilestoneSerializer
)
from .services import (
    create_project, update_project, create_task, update_task, rate_task_performance,
    add_project_member, remove_project_member, update_project_member_role,
    log_activity
)
from .filters import ProjectFilter, TaskFilter
from common.pagination import StandardPagination
from common.permissions import get_user_role_in_org


# ── Helpers ───────────────────────────────────────────────────────────────────

def _user_projects_qs(user):
    """N+1-safe queryset of projects visible to the user."""
    org_ids = user.memberships.filter(
        is_active=True
    ).values_list('organization_id', flat=True)
    return (
        Project.objects
        .filter(organization_id__in=org_ids)
        .select_related('organization')
        .prefetch_related('organization__memberships', 'tasks', 'memberships')
    )


def _get_project_for_user(user, pk):
    project = get_object_or_404(
        Project.objects
        .select_related('organization')
        .prefetch_related('organization__memberships', 'tasks', 'memberships'),
        pk=pk,
    )
    if not user.memberships.filter(
        organization=project.organization, is_active=True
    ).exists():
        raise PermissionDenied()
    return project


def _assert_min_role(user, org_id, min_role, message):
    role = get_user_role_in_org(user, org_id)
    from common.permissions import ROLE_HIERARCHY, _role_rank
    if _role_rank(role or '') < _role_rank(min_role):
        raise PermissionDenied(message)


def _assert_project_min_role(user, project, min_role, message):
    """Check project-level role."""
    if not ProjectMembership.has_min_role(user, project, min_role):
        # Fallback to org-level check
        _assert_min_role(user, project.organization_id, min_role, message)


# ── Project views ─────────────────────────────────────────────────────────────

class ProjectListCreateView(APIView):
    def get(self, request):
        qs = _user_projects_qs(request.user)

        # Apply FilterSet
        f = ProjectFilter(request.query_params, queryset=qs)
        qs = f.qs

        # Ordering
        ordering = request.query_params.get('ordering', '-updated_at')
        allowed = {'name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at'}
        if ordering in allowed:
            qs = qs.order_by(ordering)

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(ProjectSerializer(page, many=True).data)

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = create_project(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            organization_id=str(serializer.validated_data['organizationId']),
            created_by=request.user,
            template_id=serializer.validated_data.get('templateId'),
            is_template=serializer.validated_data.get('is_template', False),
        )
        return Response(
            ProjectSerializer(project).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    def get(self, request, pk):
        project = _get_project_for_user(request.user, pk)
        return Response(ProjectSerializer(project).data)

    def patch(self, request, pk):
        project = _get_project_for_user(request.user, pk)
        # Members+ can update; only admin+ can archive
        new_status = request.data.get('status')
        if new_status in ('archived', 'completed'):
            _assert_min_role(request.user, project.organization_id, 'admin',
                             'Admin access required to archive or complete projects.')

        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        project = update_project(project, serializer.validated_data, updated_by=request.user)
        return Response(ProjectSerializer(project).data)

    def delete(self, request, pk):
        project = _get_project_for_user(request.user, pk)
        if project.created_by_id != request.user.id:
            _assert_min_role(request.user, project.organization_id, 'member',
                             'Member access required to delete projects.')
        project._deleted_by = request.user
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Task views ────────────────────────────────────────────────────────────────

class TaskListCreateView(APIView):
    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        qs = project.tasks.select_related('assignee')
        f = TaskFilter(request.query_params, queryset=qs)

        ordering = request.query_params.get('ordering', '-created_at')
        allowed = {
            'created_at', '-created_at', 'due_date', '-due_date',
            'priority', '-priority', 'status', '-status',
        }
        if ordering in allowed:
            qs = f.qs.order_by(ordering)
        else:
            qs = f.qs

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(TaskSerializer(page, many=True).data)

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_task(project, serializer.validated_data, created_by=request.user)
        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TaskDetailView(APIView):
    def get(self, request, project_pk, pk):
        task = self._get_task(request.user, project_pk, pk)
        return Response(TaskSerializer(task).data)

    def patch(self, request, project_pk, pk):
        task = self._get_task(request.user, project_pk, pk)
        serializer = TaskCreateSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        task = update_task(task, serializer.validated_data, updated_by=request.user)
        return Response(TaskSerializer(task).data)

    def delete(self, request, project_pk, pk):
        task = self._get_task(request.user, project_pk, pk)
        _assert_min_role(request.user, task.project.organization_id, 'member',
                         'Member access required to delete tasks.')
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_task(self, user, project_pk, pk):
        project = _get_project_for_user(user, project_pk)
        return get_object_or_404(
            Task.objects.select_related('project__organization'),
            pk=pk, project=project,
        )


class TaskRateView(APIView):
    def post(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required to rate tasks.')
        rating = request.data.get('rating')
        if rating and rating not in ['good', 'very_good', 'excellent', 'needs_work']:
            return Response({'error': 'Invalid rating'}, status=status.HTTP_400_BAD_REQUEST)
        task = rate_task_performance(task, rating, request.user)
        return Response(TaskSerializer(task).data)


class LabelListCreateView(APIView):
    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        labels = project.labels.all()
        return Response(LabelSerializer(labels, many=True).data)

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = LabelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        label = serializer.save(project=project)
        return Response(LabelSerializer(label).data, status=status.HTTP_201_CREATED)


class KanbanColumnListCreateView(APIView):
    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        columns = project.kanban_columns.all()
        return Response(KanbanColumnSerializer(columns, many=True).data)

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = KanbanColumnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pos = project.kanban_columns.count()
        col = serializer.save(project=project, position=pos)
        return Response(KanbanColumnSerializer(col).data, status=status.HTTP_201_CREATED)


class KanbanColumnDetailView(APIView):
    def delete(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        col = get_object_or_404(KanbanColumn, pk=pk, project=project)
        col.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChecklistItemListCreateView(APIView):
    def post(self, request, project_pk, task_pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = ChecklistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save(task=task)
        return Response(ChecklistItemSerializer(item).data, status=status.HTTP_201_CREATED)


class ChecklistItemDetailView(APIView):
    def patch(self, request, project_pk, task_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        item = get_object_or_404(ChecklistItem, pk=pk, task=task)
        serializer = ChecklistItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(ChecklistItemSerializer(item).data)

    def delete(self, request, project_pk, task_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        item = get_object_or_404(ChecklistItem, pk=pk, task=task)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCommentListCreateView(APIView):
    def post(self, request, project_pk, task_pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, author=request.user)
        log_activity(
            project, request.user, ActivityLog.Action.COMMENTED,
            task=task, description=f'{request.user.username} commented on task'
        )
        return Response(TaskCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class TaskAttachmentListCreateView(APIView):
    def post(self, request, project_pk, task_pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = TaskAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(task=task, uploaded_by=request.user)
        log_activity(
            project, request.user, ActivityLog.Action.ATTACHMENT_ADDED,
            task=task, description=f'{request.user.username} added attachment "{attachment.file_name}"'
        )
        return Response(TaskAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class TimeEntryListCreateView(APIView):
    def post(self, request, project_pk, task_pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = TimeEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = serializer.save(task=task, user=request.user)
        return Response(TimeEntrySerializer(entry).data, status=status.HTTP_201_CREATED)


class TaskDependencyListCreateView(APIView):
    def post(self, request, project_pk, task_pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        dep_task_id = request.data.get('dependsOnId')
        dep_task = get_object_or_404(Task, pk=dep_task_id, project=project)
        dep, created = TaskDependency.objects.get_or_create(task=task, depends_on=dep_task)
        return Response(TaskDependencySerializer(dep).data, status=status.HTTP_201_CREATED)

    def delete(self, request, project_pk, task_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=task_pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        dep = get_object_or_404(TaskDependency, task=task, depends_on_id=pk)
        dep.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Project Member Management Views ───────────────────────────────────────────

class ProjectMemberListView(APIView):
    """List all active members of a project."""

    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        members = project.memberships.filter(is_active=True).select_related('user', 'invited_by')
        serializer = ProjectMembershipSerializer(members, many=True)
        return Response(serializer.data)


class ProjectMemberInviteView(APIView):
    """Invite a user to a project by user ID, email, or username. Auto-creates user if not registered."""

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        if project.created_by_id != request.user.id:
            _assert_min_role(request.user, project.organization_id, 'member',
                             'Member access required to invite team members.')

        user_id = request.data.get('userId') or request.data.get('user')
        raw_email = request.data.get('email', '').strip()
        role = request.data.get('role', ProjectMembership.Role.DEVELOPER)

        user = None
        if user_id:
            user = User.objects.filter(pk=user_id).first()
        if not user and raw_email:
            from django.db.models import Q
            user = User.objects.filter(Q(email__iexact=raw_email) | Q(username__iexact=raw_email)).first()

        # If user does not exist yet, auto-create user record so invitation always succeeds!
        if not user and raw_email:
            import re
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '', raw_email.split('@')[0]) or 'member'
            username = clean_name
            count = 1
            while User.objects.filter(username=username).exists():
                username = f"{clean_name}{count}"
                count += 1

            email = raw_email if '@' in raw_email else f"{username}@nexus.local"
            user = User.objects.create_user(
                username=username,
                email=email,
                password=User.objects.make_random_password()
            )

        if not user:
            return Response(
                {'error': 'Please select a registered user or enter a valid email or username.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Auto-add user to Organization if not already an active member
        from apps.organizations.models import Membership
        org_membership, _ = Membership.objects.get_or_create(
            user=user,
            organization=project.organization,
            defaults={'role': 'member', 'is_active': True}
        )
        if not org_membership.is_active:
            org_membership.is_active = True
            org_membership.save(update_fields=['is_active'])

        membership = add_project_member(project, user, role, invited_by=request.user)
        return Response(ProjectMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class ProjectMemberDetailView(APIView):
    """Update or remove a project member."""

    def patch(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_project_min_role(request.user, project, 'manager',
                                 'Manager access required to update members.')

        membership = get_object_or_404(ProjectMembership, pk=pk, project=project, is_active=True)

        # Prevent changing owner role
        if membership.role == ProjectMembership.Role.OWNER:
            return Response(
                {'error': 'Cannot change the owner role.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ProjectMembershipUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if 'role' in serializer.validated_data:
            update_project_member_role(membership, serializer.validated_data['role'], updated_by=request.user)

        if 'is_active' in serializer.validated_data and not serializer.validated_data['is_active']:
            remove_project_member(membership, removed_by=request.user)

        membership.refresh_from_db()
        return Response(ProjectMembershipSerializer(membership).data)

    def delete(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_project_min_role(request.user, project, 'manager',
                                 'Manager access required to remove members.')

        membership = get_object_or_404(ProjectMembership, pk=pk, project=project, is_active=True)

        if membership.role == ProjectMembership.Role.OWNER:
            return Response(
                {'error': 'Cannot remove the owner.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        remove_project_member(membership, removed_by=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Activity Log Views ────────────────────────────────────────────────────────

class ActivityLogListView(APIView):
    """List activity logs for a project."""

    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)

        limit = int(request.query_params.get('limit', 50))
        logs = ActivityLog.objects.filter(project=project).select_related('actor', 'task')[:limit]

        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)


# ── Milestone Views ────────────────────────────────────────────────────────────

class MilestoneListCreateView(APIView):
    """List and create milestones for a project."""

    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        milestones = project.milestones.all()
        return Response(MilestoneSerializer(milestones, many=True).data)

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = MilestoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save(project=project, created_by=request.user)
        return Response(MilestoneSerializer(milestone).data, status=status.HTTP_201_CREATED)


class MilestoneDetailView(APIView):
    """Update or delete a milestone."""

    def patch(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        milestone = get_object_or_404(Milestone, pk=pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        serializer = MilestoneSerializer(milestone, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        milestone = serializer.save()
        return Response(MilestoneSerializer(milestone).data)

    def delete(self, request, project_pk, pk):
        project = _get_project_for_user(request.user, project_pk)
        milestone = get_object_or_404(Milestone, pk=pk, project=project)
        _assert_min_role(request.user, project.organization_id, 'member', 'Member access required.')
        milestone.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GlobalAnalyticsView(APIView):
    """Real time global portfolio health and workload analytics for user's organization."""

    def get(self, request):
        user = request.user
        org_ids = user.memberships.filter(is_active=True).values_list('organization_id', flat=True)
        projects = list(Project.objects.filter(organization_id__in=org_ids))

        # 1. Real Project Status Breakdown
        status_counts = {
            'Active': 0,
            'On Hold': 0,
            'Completed': 0,
            'Archived': 0,
        }
        for p in projects:
            s = str(p.status).lower()
            if 'hold' in s:
                status_counts['On Hold'] += 1
            elif 'complete' in s or 'done' in s:
                status_counts['Completed'] += 1
            elif 'archive' in s:
                status_counts['Archived'] += 1
            else:
                status_counts['Active'] += 1

        project_status_data = [
            {'name': 'Active', 'value': status_counts['Active'], 'color': '#6366f1'},
            {'name': 'On Hold', 'value': status_counts['On Hold'], 'color': '#f59e0b'},
            {'name': 'Completed', 'value': status_counts['Completed'], 'color': '#10b981'},
            {'name': 'Archived', 'value': status_counts['Archived'], 'color': '#475569'},
        ]

        # 2. Real Team Workload (real members & assigned tasks)
        tasks = list(Task.objects.filter(project__in=projects).select_related('assignee'))
        member_counts = {}
        for t in tasks:
            name = t.assignee.username if t.assignee else "Unassigned"
            member_counts[name] = member_counts.get(name, 0) + 1

        if not member_counts:
            from apps.organizations.models import OrganizationMembership
            memberships = OrganizationMembership.objects.filter(organization_id__in=org_ids, is_active=True).select_related('user')
            for m in memberships:
                member_counts[m.user.username] = 0

        workload_data = [
            {'member': name, 'tasks': count}
            for name, count in member_counts.items()
        ]

        # 3. Real Task Velocity (past 8 weeks task completions)
        from django.utils import timezone
        import datetime
        now = timezone.now()
        velocity_data = []
        for i in range(7, -1, -1):
            week_start = now - datetime.timedelta(days=(i+1)*7)
            week_end = now - datetime.timedelta(days=i*7)
            cnt = Task.objects.filter(
                project__in=projects,
                status=Task.Status.DONE,
                updated_at__gte=week_start,
                updated_at__lt=week_end
            ).count()
            velocity_data.append({'week': f'W{8-i}', 'completed': cnt})

        return Response({
            'project_status': project_status_data,
            'workload': workload_data,
            'velocity': velocity_data,
        })
