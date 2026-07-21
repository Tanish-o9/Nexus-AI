import uuid
from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    """Team chat messages with mentions and reactions support."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='chat_messages'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages'
    )
    content = models.TextField()
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='mentioned_in_messages'
    )
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collab_chat_message'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
        ]

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'


class ChatReaction(models.Model):
    """Emoji reactions on chat messages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reactions'
    )
    emoji = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collab_chat_reaction'
        unique_together = ('message', 'user', 'emoji')

    def __str__(self):
        return f'{self.emoji} by {self.user.username}'


class ChatAttachment(models.Model):
    """File attachments on chat messages."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        ChatMessage, on_delete=models.CASCADE, related_name='attachments'
    )
    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=512)
    file_size = models.IntegerField(default=0)
    mime_type = models.CharField(max_length=100, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collab_chat_attachment'

    def __str__(self):
        return self.file_name


class ActivityFeedItem(models.Model):
    """Unified activity feed for project events."""
    class ActivityType(models.TextChoices):
        TASK_CREATED = 'task_created', 'Task Created'
        TASK_UPDATED = 'task_updated', 'Task Updated'
        TASK_COMPLETED = 'task_completed', 'Task Completed'
        COMMENT_ADDED = 'comment_added', 'Comment Added'
        MEMBER_JOINED = 'member_joined', 'Member Joined'
        PROJECT_UPDATED = 'project_updated', 'Project Updated'
        CHAT_MESSAGE = 'chat_message', 'Chat Message'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='activity_feed'
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='activities'
    )
    activity_type = models.CharField(max_length=32, choices=ActivityType.choices)
    description = models.CharField(max_length=512)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collab_activity_feed_item'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['activity_type']),
        ]

    def __str__(self):
        return f'{self.activity_type}: {self.description[:50]}'


class UserPresence(models.Model):
    """Track user online/offline status per project."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='presence'
    )
    project = models.ForeignKey(
        'projects.Project', on_delete=models.CASCADE, related_name='user_presence'
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'collab_user_presence'
        unique_together = ('user', 'project')

    def __str__(self):
        return f'{self.user.username} {"online" if self.is_online else "offline"} @ {self.project.name}'