from rest_framework import serializers
from .models import Sprint, SprintBacklogItem, SprintReport


class SprintSerializer(serializers.ModelSerializer):
    projectId = serializers.UUIDField(source='project_id', read_only=True)
    startDate = serializers.DateField(source='start_date')
    endDate = serializers.DateField(source='end_date')
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    isCompleted = serializers.BooleanField(source='is_completed', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    taskCount = serializers.SerializerMethodField()
    totalPoints = serializers.SerializerMethodField()
    completedPoints = serializers.SerializerMethodField()

    class Meta:
        model = Sprint
        fields = (
            'id', 'projectId', 'name', 'goal', 'startDate', 'endDate',
            'isActive', 'isCompleted', 'taskCount', 'totalPoints',
            'completedPoints', 'createdAt',
        )

    def get_taskCount(self, obj):
        return obj.backlog_items.count()

    def get_totalPoints(self, obj):
        return sum(obj.backlog_items.values_list('story_points', flat=True))

    def get_completedPoints(self, obj):
        return sum(
            item.story_points for item in obj.backlog_items.select_related('task').all()
            if item.task.status == 'done'
        )


class SprintCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=128)
    goal = serializers.CharField(required=False, allow_blank=True)
    startDate = serializers.DateField()
    endDate = serializers.DateField()


class SprintBacklogItemSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source='sprint_id', read_only=True)
    taskId = serializers.UUIDField(source='task_id')
    taskTitle = serializers.CharField(source='task.title', read_only=True)
    taskStatus = serializers.CharField(source='task.status', read_only=True)
    taskAssignee = serializers.CharField(source='task.assignee.username', read_only=True, default='')
    storyPoints = serializers.FloatField(source='story_points')

    class Meta:
        model = SprintBacklogItem
        fields = (
            'id', 'sprintId', 'taskId', 'taskTitle', 'taskStatus',
            'taskAssignee', 'storyPoints', 'added_at',
        )


class SprintBacklogAddSerializer(serializers.Serializer):
    taskId = serializers.UUIDField()
    storyPoints = serializers.FloatField(default=1.0, min_value=0.1)


class SprintReportSerializer(serializers.ModelSerializer):
    sprintId = serializers.UUIDField(source='sprint_id', read_only=True)
    reportType = serializers.CharField(source='report_type', read_only=True)
    pdfUrl = serializers.URLField(source='pdf_url', read_only=True)
    excelUrl = serializers.URLField(source='excel_url', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = SprintReport
        fields = ('id', 'sprintId', 'reportType', 'data', 'pdfUrl', 'excelUrl', 'createdAt')