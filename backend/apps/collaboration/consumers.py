"""
WebSocket consumers for real-time collaboration:
- Team chat (send/receive messages)
- Presence (online/offline tracking)
- Activity feed (live updates)
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for project team chat."""

    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.group_name = f'chat_{self.project_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Mark user online
        await self._set_presence(True)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'presence_update',
                'userId': str(self.user.id),
                'username': self.user.username,
                'isOnline': True,
            },
        )

    async def disconnect(self, code):
        if hasattr(self, 'group_name'):
            await self._set_presence(False)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'presence_update',
                    'userId': str(self.user.id),
                    'username': self.user.username,
                    'isOnline': False,
                },
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', '')

        if msg_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
        elif msg_type == 'message':
            await self._handle_chat_message(data)
        elif msg_type == 'typing':
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'typing_indicator',
                    'userId': str(self.user.id),
                    'username': self.user.username,
                    'isTyping': data.get('isTyping', False),
                },
            )

    async def _handle_chat_message(self, data):
        """Save and broadcast a chat message."""
        from .models import ChatMessage
        from apps.projects.models import Project

        project = await database_sync_to_async(Project.objects.get)(pk=self.project_id)
        content = data.get('content', '').strip()
        if not content:
            return

        msg = await database_sync_to_async(ChatMessage.objects.create)(
            project=project,
            author=self.user,
            content=content,
        )

        # Parse @mentions
        mention_ids = data.get('mentionIds', [])
        if mention_ids:
            from apps.accounts.models import User
            mentioned_users = await database_sync_to_async(
                lambda: list(User.objects.filter(id__in=mention_ids))
            )()
            await database_sync_to_async(msg.mentions.set)(mentioned_users)

            # Send notifications to mentioned users
            from apps.notifications.services import send_notification
            for mentioned in mentioned_users:
                await database_sync_to_async(send_notification)(
                    user=mentioned,
                    type='mention',
                    title=f'{self.user.username} mentioned you',
                    body=f'In {project.name}: {content[:100]}',
                )

        # Broadcast to group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_broadcast',
                'id': str(msg.id),
                'authorId': str(self.user.id),
                'authorUsername': self.user.username,
                'authorEmail': self.user.email,
                'content': content,
                'mentionIds': [str(uid) for uid in mention_ids],
                'createdAt': msg.created_at.isoformat(),
            },
        )

        # Log activity
        from .services import log_activity
        await database_sync_to_async(log_activity)(
            project=project,
            actor=self.user,
            activity_type='chat_message',
            description=f'{self.user.username} sent a message',
            metadata={'message_id': str(msg.id), 'preview': content[:100]},
        )

    async def chat_broadcast(self, event):
        """Broadcast chat message to all group members."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'id': event['id'],
            'authorId': event['authorId'],
            'authorUsername': event['authorUsername'],
            'authorEmail': event['authorEmail'],
            'content': event['content'],
            'mentionIds': event['mentionIds'],
            'createdAt': event['createdAt'],
        }))

    async def typing_indicator(self, event):
        """Broadcast typing indicator."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'userId': event['userId'],
            'username': event['username'],
            'isTyping': event['isTyping'],
        }))

    async def presence_update(self, event):
        """Broadcast presence update."""
        await self.send(text_data=json.dumps({
            'type': 'presence',
            'userId': event['userId'],
            'username': event['username'],
            'isOnline': event['isOnline'],
        }))

    @database_sync_to_async
    def _set_presence(self, is_online: bool):
        from .models import UserPresence
        UserPresence.objects.update_or_create(
            user=self.user,
            project_id=self.project_id,
            defaults={'is_online': is_online, 'last_seen': timezone.now()},
        )