"""
Collaboration services for activity feed, mentions, and presence.
"""

from .models import ActivityFeedItem, UserPresence
from apps.notifications.services import send_notification


def log_activity(project, actor, activity_type: str, description: str, metadata: dict = None):
    """Create an activity feed entry."""
    return ActivityFeedItem.objects.create(
        project=project,
        actor=actor,
        activity_type=activity_type,
        description=description,
        metadata=metadata or {},
    )


def notify_mentions(actor, mentioned_users, project_name: str, content_preview: str):
    """Send mention notifications to users."""
    for user in mentioned_users:
        send_notification(
            user=user,
            type='mention',
            title=f'{actor.username} mentioned you',
            body=f'In {project_name}: {content_preview}',
        )


def get_online_users(project_id: str) -> list[dict]:
    """Get all online users for a project."""
    return list(
        UserPresence.objects.filter(
            project_id=project_id, is_online=True
        ).select_related('user').values(
            'user_id', 'user__username', 'is_online', 'last_seen'
        )
    )