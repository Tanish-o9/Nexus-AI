import uuid
from django.db import models
from django.conf import settings


class GitHubRepository(models.Model):
    """Connected GitHub repository for a project."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='github_repos'
    )
    owner = models.CharField(max_length=128, help_text='Repository owner (user or org)')
    name = models.CharField(max_length=128, help_text='Repository name')
    full_name = models.CharField(max_length=256, unique=True, help_text='owner/name')
    installation_id = models.BigIntegerField(null=True, blank=True, help_text='GitHub App installation ID')
    webhook_secret = models.CharField(max_length=128, blank=True, default='')
    is_active = models.BooleanField(default=True)
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_repository'
        unique_together = ('project', 'full_name')
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name


class GitHubWebhookEvent(models.Model):
    """Incoming webhook events from GitHub."""
    class EventType(models.TextChoices):
        PUSH = 'push', 'Push'
        PULL_REQUEST = 'pull_request', 'Pull Request'
        ISSUES = 'issues', 'Issues'
        BRANCH = 'create', 'Branch Create'
        BRANCH_DELETE = 'delete', 'Branch Delete'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        GitHubRepository, on_delete=models.CASCADE, related_name='webhook_events'
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    github_event_id = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'github_webhook_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['repository', '-created_at']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.repository.full_name}'


class GitHubCommit(models.Model):
    """Commits tracked for commit→task mapping and timeline."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        GitHubRepository, on_delete=models.CASCADE, related_name='commits'
    )
    sha = models.CharField(max_length=64)
    message = models.TextField()
    author_name = models.CharField(max_length=255, blank=True)
    author_email = models.CharField(max_length=255, blank=True)
    branch = models.CharField(max_length=255, blank=True, default='main')
    url = models.URLField(max_length=512, blank=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'github_commit'
        unique_together = ('repository', 'sha')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['repository', 'branch']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f'{self.sha[:8]} @ {self.repository.full_name}'


class CommitTaskMapping(models.Model):
    """Maps commits to Nexus tasks via commit message references."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commit = models.ForeignKey(GitHubCommit, on_delete=models.CASCADE, related_name='task_mappings')
    task = models.ForeignKey('projects.Task', on_delete=models.CASCADE, related_name='commit_mappings')
    reference_type = models.CharField(
        max_length=16,
        choices=[('manual', 'Manual'), ('auto', 'Auto-detected')],
        default='auto',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'github_commit_task_mapping'
        unique_together = ('commit', 'task')

    def __str__(self):
        return f'{self.commit.sha[:8]} → {self.task.title}'


class GitHubPR(models.Model):
    """Pull request tracking for PR status and timeline."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        GitHubRepository, on_delete=models.CASCADE, related_name='pull_requests'
    )
    pr_number = models.IntegerField()
    title = models.CharField(max_length=512)
    body = models.TextField(blank=True)
    state = models.CharField(max_length=16, choices=[('open', 'Open'), ('closed', 'Closed'), ('merged', 'Merged')])
    author = models.CharField(max_length=128, blank=True)
    head_branch = models.CharField(max_length=255)
    base_branch = models.CharField(max_length=255)
    url = models.URLField(max_length=512, blank=True)
    is_draft = models.BooleanField(default=False)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    merged_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'github_pull_request'
        unique_together = ('repository', 'pr_number')
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.pr_number} {self.title}'


class GitHubBranch(models.Model):
    """Tracked branches and their status."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(
        GitHubRepository, on_delete=models.CASCADE, related_name='branches'
    )
    name = models.CharField(max_length=255)
    latest_sha = models.CharField(max_length=64, blank=True)
    is_protected = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    last_commit_message = models.TextField(blank=True)
    last_commit_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'github_branch'
        unique_together = ('repository', 'name')
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.repository.full_name}:{self.name}'