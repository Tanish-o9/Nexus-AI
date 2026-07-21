import uuid
from django.db import models
from django.conf import settings


class Project(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        ON_HOLD = 'on_hold', 'On Hold'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    # Valid forward transitions — prevents arbitrary status jumps
    ALLOWED_TRANSITIONS = {
        'active':    {'on_hold', 'completed', 'archived'},
        'on_hold':   {'active', 'archived'},
        'completed': {'archived'},
        'archived':  set(),
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='projects'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_projects'
    )
    is_template = models.BooleanField(default=False)
    health = models.CharField(
        max_length=16,
        choices=[('on_track', 'On Track'), ('at_risk', 'At Risk'), ('critical', 'Critical')],
        default='on_track'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_project'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return self.name


class ProjectMembership(models.Model):
    """Project-level roles for fine-grained RBAC."""

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        MANAGER = 'manager', 'Manager'
        DEVELOPER = 'developer', 'Developer'
        FRONTEND = 'frontend', 'Frontend Engineer'
        BACKEND = 'backend', 'Backend Engineer'
        DEVOPS = 'devops', 'DevOps / SRE'
        QA = 'qa', 'QA'
        DESIGNER = 'designer', 'Designer'
        DATA = 'data', 'Data Engineer'
        SECURITY = 'security', 'Security Engineer'
        WRITER = 'writer', 'Technical Writer'
        VIEWER = 'viewer', 'Viewer'

    # Hierarchy: higher index = more privilege
    ROLE_HIERARCHY = ['viewer', 'writer', 'designer', 'qa', 'data', 'frontend', 'backend', 'devops', 'developer', 'manager', 'owner']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships'
    )
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.DEVELOPER)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='invited_memberships'
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_projectmembership'
        unique_together = ('project', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f'{self.user.email} @ {self.project.name} ({self.role})'

    @classmethod
    def role_rank(cls, role: str) -> int:
        try:
            return cls.ROLE_HIERARCHY.index(role)
        except ValueError:
            return -1

    @classmethod
    def has_min_role(cls, user, project, min_role: str) -> bool:
        try:
            membership = cls.objects.get(project=project, user=user, is_active=True)
            return cls.role_rank(membership.role) >= cls.role_rank(min_role)
        except cls.DoesNotExist:
            return False


class ActivityLog(models.Model):
    """Tracks changes to projects and tasks for the activity timeline."""

    class Action(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        DELETED = 'deleted', 'Deleted'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
        ASSIGNED = 'assigned', 'Assigned'
        UNASSIGNED = 'unassigned', 'Unassigned'
        COMMENTED = 'commented', 'Commented'
        ATTACHMENT_ADDED = 'attachment_added', 'Attachment Added'
        MEMBER_ADDED = 'member_added', 'Member Added'
        MEMBER_REMOVED = 'member_removed', 'Member Removed'
        MEMBER_ROLE_CHANGED = 'member_role_changed', 'Member Role Changed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activity_logs')
    task = models.ForeignKey(
        'Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=32, choices=Action.choices)
    field_name = models.CharField(max_length=64, blank=True, default='')
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_activitylog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['task', '-created_at']),
        ]

    def __str__(self):
        return f'{self.actor} {self.action} on {self.project.name}'


class Milestone(models.Model):
    """Key project milestones with dates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_milestone'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['project', 'due_date']),
        ]

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class KanbanColumn(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='kanban_columns')
    name = models.CharField(max_length=64)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'projects_kanbancolumn'
        ordering = ['position']
        unique_together = ('project', 'name')

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class Label(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=7, default='#6366f1')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='labels')

    class Meta:
        db_table = 'projects_label'
        unique_together = ('name', 'project')

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        DONE = 'done', 'Done'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class PerformanceRating(models.TextChoices):
        GOOD = 'good', 'Good'
        VERY_GOOD = 'very_good', 'Very Good'
        EXCELLENT = 'excellent', 'Excellent'
        NEEDS_WORK = 'needs_work', 'Needs Work'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    performance_rating = models.CharField(
        max_length=16, choices=PerformanceRating.choices, null=True, blank=True, default=None
    )
    github_commit_info = models.JSONField(default=dict, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    
    # Single assignee kept for backward compatibility/quick fallback
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tasks'
    )
    
    # Enterprise multi-assignee and watchers
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='assigned_tasks_m2m', blank=True
    )
    watchers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='watched_tasks', blank=True
    )
    
    labels = models.ManyToManyField(Label, related_name='tasks', blank=True)
    kanban_column = models.ForeignKey(
        KanbanColumn, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks'
    )
    
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects_task'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assignee', 'status']),
        ]

    def __str__(self):
        return self.title


class ChecklistItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_checklistitem'
        ordering = ['created_at']

    def __str__(self):
        return self.title


class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='blocked_tasks')

    class Meta:
        db_table = 'projects_taskdependency'
        unique_together = ('task', 'depends_on')


class TaskAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_taskattachment'


class TaskComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_taskcomment'
        ordering = ['created_at']


class TimeEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects_timeentry'
        ordering = ['-date', '-created_at']