from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Project, Task, Label, KanbanColumn, ChecklistItem,
    TaskDependency, TaskAttachment, TaskComment, TimeEntry,
    ProjectMembership, ActivityLog, Milestone
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'name', 'color', 'project')


class KanbanColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanColumn
        fields = ('id', 'name', 'position', 'project')


class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = ('id', 'title', 'is_completed', 'task')


class TaskDependencySerializer(serializers.ModelSerializer):
    dependsOnId = serializers.UUIDField(source='depends_on_id')
    dependsOnTitle = serializers.CharField(source='depends_on.title', read_only=True)

    class Meta:
        model = TaskDependency
        fields = ('id', 'dependsOnId', 'dependsOnTitle')


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploadedBy = UserSerializer(source='uploaded_by', read_only=True)

    class Meta:
        model = TaskAttachment
        fields = ('id', 'file_name', 'file_url', 'uploadedBy', 'created_at')


class TaskCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ('id', 'author', 'content', 'created_at')


class TimeEntrySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TimeEntry
        fields = ('id', 'user', 'hours', 'date', 'description')


class TaskSerializer(serializers.ModelSerializer):
    assigneeId = serializers.UUIDField(source='assignee_id', allow_null=True, required=False)
    projectId = serializers.UUIDField(source='project_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    dueDate = serializers.DateField(source='due_date', allow_null=True, required=False)

    assignees = UserSerializer(many=True, read_only=True)
    assigneeIds = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(), source='assignees', required=False
    )
    watchers = UserSerializer(many=True, read_only=True)
    watcherIds = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(), source='watchers', required=False
    )
    labels = LabelSerializer(many=True, read_only=True)
    labelIds = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Label.objects.all(), source='labels', required=False
    )
    checklistItems = ChecklistItemSerializer(source='checklist_items', many=True, read_only=True)
    dependencies = TaskDependencySerializer(many=True, read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    timeEntries = TimeEntrySerializer(source='time_entries', many=True, read_only=True)
    kanbanColumnId = serializers.UUIDField(source='kanban_column_id', allow_null=True, required=False)
    performanceRating = serializers.CharField(source='performance_rating', allow_null=True, required=False)
    githubCommitInfo = serializers.JSONField(source='github_commit_info', required=False)

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'description', 'status', 'priority',
            'projectId', 'assigneeId', 'assignees', 'assigneeIds',
            'watchers', 'watcherIds', 'labels', 'labelIds',
            'checklistItems', 'dependencies', 'comments', 'timeEntries',
            'kanbanColumnId', 'performanceRating', 'githubCommitInfo', 'dueDate', 'createdAt', 'updatedAt',
        )
        read_only_fields = ('id', 'projectId', 'createdAt', 'updatedAt')


class TaskCreateSerializer(serializers.ModelSerializer):
    assigneeId = serializers.UUIDField(source='assignee_id', allow_null=True, required=False)
    assigneeIds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), source='assignees', required=False
    )
    watcherIds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), source='watchers', required=False
    )
    labelIds = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Label.objects.all(), source='labels', required=False
    )
    kanbanColumnId = serializers.UUIDField(source='kanban_column_id', allow_null=True, required=False)
    performanceRating = serializers.CharField(source='performance_rating', allow_null=True, required=False)
    githubCommitInfo = serializers.JSONField(source='github_commit_info', required=False)
    dueDate = serializers.DateField(source='due_date', allow_null=True, required=False)

    class Meta:
        model = Task
        fields = (
            'title', 'description', 'priority', 'status',
            'assigneeId', 'assigneeIds', 'watcherIds', 'labelIds', 'kanbanColumnId',
            'performanceRating', 'githubCommitInfo', 'dueDate'
        )

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError('Title must be at least 3 characters.')
        return value.strip()


class ProjectSerializer(serializers.ModelSerializer):
    organizationId = serializers.UUIDField(source='organization_id', read_only=True)
    isTemplate = serializers.BooleanField(source='is_template', read_only=True)
    memberCount = serializers.SerializerMethodField()
    taskCount = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = (
            'id', 'name', 'description', 'status',
            'organizationId', 'memberCount', 'taskCount',
            'createdAt', 'updatedAt', 'isTemplate', 'health', 'progress',
        )

    def get_memberCount(self, obj):
        return obj.memberships.filter(is_active=True).count()

    def get_taskCount(self, obj):
        return obj.tasks.count()

    def get_progress(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return 0.0
        completed = obj.tasks.filter(status='done').count()
        return round((completed / total) * 100, 2)


class ProjectCreateSerializer(serializers.ModelSerializer):
    organizationId = serializers.UUIDField(write_only=True)
    templateId = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Project
        fields = ('name', 'description', 'organizationId', 'templateId', 'is_template', 'health')

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters.')
        return value.strip()


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('name', 'description', 'status', 'is_template', 'health')
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'status': {'required': False},
        }

    def validate_name(self, value):
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters.')
        return value.strip()

    def validate_status(self, new_status):
        current_status = self.instance.status if self.instance else None
        if current_status and new_status != current_status:
            allowed = Project.ALLOWED_TRANSITIONS.get(current_status, set())
            if new_status not in allowed:
                raise serializers.ValidationError(
                    f"Cannot transition from '{current_status}' to '{new_status}'."
                )
        return new_status


# ── Project Membership Serializers ─────────────────────────────────────────────

class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    userId = serializers.UUIDField(write_only=True)
    role = serializers.ChoiceField(choices=ProjectMembership.Role.choices)
    invitedBy = UserSerializer(source='invited_by', read_only=True)
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ('id', 'user', 'userId', 'role', 'invitedBy', 'is_active', 'joinedAt')
        read_only_fields = ('id', 'user', 'invitedBy', 'is_active', 'joinedAt')

    def validate_userId(self, value):
        try:
            return User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError('User not found.')

    def create(self, validated_data):
        user = validated_data.pop('userId')
        return ProjectMembership.objects.create(user=user, **validated_data)


class ProjectMembershipUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=ProjectMembership.Role.choices, required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = ProjectMembership
        fields = ('role', 'is_active')


# ── Milestone Serializer ───────────────────────────────────────────────────────

class MilestoneSerializer(serializers.ModelSerializer):
    dueDate = serializers.DateField(source='due_date')
    isCompleted = serializers.BooleanField(source='is_completed', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Milestone
        fields = ('id', 'name', 'description', 'dueDate', 'isCompleted', 'createdAt', 'project')
        read_only_fields = ('id', 'isCompleted', 'createdAt', 'project')


# ── Activity Log Serializer ────────────────────────────────────────────────────

class ActivityLogSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ActivityLog
        fields = (
            'id', 'project', 'task', 'actor', 'action',
            'field_name', 'old_value', 'new_value', 'description', 'createdAt',
        )
        read_only_fields = fields