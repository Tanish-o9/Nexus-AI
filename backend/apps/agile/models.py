import uuid
from django.db import models
from django.conf import settings


class Sprint(models.Model):
    """A time-boxed iteration for a project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='sprints'
    )
    name = models.CharField(max_length=128)
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agile_sprint'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['project', '-start_date']),
            models.Index(fields=['is_active', 'is_completed']),
        ]

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class SprintBacklogItem(models.Model):
    """Task assignment to a sprint."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.ForeignKey(
        Sprint, on_delete=models.CASCADE, related_name='backlog_items'
    )
    task = models.ForeignKey(
        'projects.Task', on_delete=models.CASCADE, related_name='sprint_assignments'
    )
    story_points = models.FloatField(default=1.0, help_text='Estimated story points')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agile_sprint_backlog_item'
        unique_together = ('sprint', 'task')
        ordering = ['added_at']

    def __str__(self):
        return f'{self.sprint.name} → {self.task.title}'


class SprintReport(models.Model):
    """Generated sprint reports."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sprint = models.ForeignKey(
        Sprint, on_delete=models.CASCADE, related_name='reports'
    )
    report_type = models.CharField(
        max_length=16,
        choices=[('weekly', 'Weekly'), ('monthly', 'Monthly'), ('sprint', 'Sprint Review')],
        default='sprint',
    )
    data = models.JSONField(default=dict)
    pdf_url = models.URLField(max_length=512, blank=True)
    excel_url = models.URLField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agile_sprint_report'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.report_type} report for {self.sprint.name}'