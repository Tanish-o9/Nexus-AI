from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


def send_notification(user, type: str, title: str, body: str) -> Notification:
    """
    Persist a notification and push it to the user's WebSocket group.
    Called by signal receivers and views — never by the AI service directly.
    """
    notif = Notification.objects.create(user=user, type=type, title=title, body=body)
    _push_to_ws(user.id, notif)
    return notif


def notify_agent_completed(user_id: str, task_summary: str) -> None:
    """
    Called by the AI service via POST /api/notifications/agent-completed/.
    Decoupled: AI service knows nothing about Channels or Django signals.
    """
    from apps.accounts.models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    send_notification(
        user=user,
        type='agent_completed',
        title='EMAOS agent completed a task',
        body=task_summary,
    )


def _push_to_ws(user_id, notif: Notification) -> None:
    payload = {
        'id': str(notif.id),
        'type': notif.type,
        'title': notif.title,
        'body': notif.body,
        'read': notif.read,
        'createdAt': notif.created_at.isoformat(),
    }
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {'type': 'notification', 'payload': payload},
        )
    except Exception:
        # WS push failure must never break the main request
        pass
