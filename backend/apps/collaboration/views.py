"""
Collaboration REST API views.
All use existing JWT auth from rest_framework_simplejwt.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project
from .models import ChatMessage, ChatReaction, ChatAttachment, ActivityFeedItem, UserPresence
from .serializers import (
    ChatMessageSerializer, ChatMessageCreateSerializer,
    ChatReactionSerializer, ChatAttachmentSerializer,
    ActivityFeedItemSerializer, UserPresenceSerializer,
)
from .services import log_activity


# ── Team Chat ──────────────────────────────────────────────────────────────────

class ChatMessageListView(APIView):
    """List chat messages for a project."""

    def get(self, request, project_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        messages = ChatMessage.objects.filter(
            project=project
        ).select_related('author').prefetch_related(
            'reactions__user', 'attachments'
        )[:50]
        return Response(ChatMessageSerializer(messages, many=True).data)


class ChatMessageCreateView(APIView):
    """Create a chat message (REST fallback, primary is WebSocket)."""

    def post(self, request, project_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = ChatMessage.objects.create(
            project=project,
            author=request.user,
            content=serializer.validated_data['content'],
            reply_to_id=serializer.validated_data.get('replyToId'),
        )

        mention_ids = serializer.validated_data.get('mentionIds', [])
        if mention_ids:
            from apps.accounts.models import User
            mentioned = User.objects.filter(id__in=mention_ids)
            msg.mentions.set(mentioned)
            from .services import notify_mentions
            notify_mentions(
                request.user, mentioned, project.name,
                serializer.validated_data['content'][:100],
            )

        log_activity(
            project=project, actor=request.user,
            activity_type='chat_message',
            description=f'{request.user.username} sent a message',
            metadata={'message_id': str(msg.id)},
        )

        return Response(
            ChatMessageSerializer(msg).data,
            status=status.HTTP_201_CREATED,
        )


# ── Emoji Reactions ────────────────────────────────────────────────────────────

class ChatReactionToggleView(APIView):
    """Toggle an emoji reaction on a message."""

    def post(self, request, project_pk, msg_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        msg = get_object_or_404(ChatMessage, pk=msg_pk, project=project)
        emoji = request.data.get('emoji', '').strip()
        if not emoji:
            return Response({'error': 'emoji required'}, status=status.HTTP_400_BAD_REQUEST)

        reaction, created = ChatReaction.objects.get_or_create(
            message=msg, user=request.user, emoji=emoji,
        )
        if not created:
            reaction.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(ChatReactionSerializer(reaction).data, status=status.HTTP_201_CREATED)


# ── File Upload ────────────────────────────────────────────────────────────────

class ChatAttachmentCreateView(APIView):
    """Upload a file attachment to a chat message."""

    def post(self, request, project_pk, msg_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        msg = get_object_or_404(ChatMessage, pk=msg_pk, project=project)

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'file required'}, status=status.HTTP_400_BAD_REQUEST)

        # Store file URL (in production, upload to S3/CDN and store URL)
        # For now, store as a placeholder — frontend handles actual upload
        attachment = ChatAttachment.objects.create(
            message=msg,
            file_name=file.name,
            file_url=f'/uploads/{file.name}',  # Replace with actual CDN URL
            file_size=file.size,
            mime_type=file.content_type or '',
            uploaded_by=request.user,
        )
        return Response(ChatAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


# ── Activity Feed ──────────────────────────────────────────────────────────────

class ActivityFeedListView(APIView):
    """Get activity feed for a project."""

    def get(self, request, project_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        feed = ActivityFeedItem.objects.filter(
            project=project
        ).select_related('actor')[:50]
        return Response(ActivityFeedItemSerializer(feed, many=True).data)


# ── Presence ───────────────────────────────────────────────────────────────────

class PresenceListView(APIView):
    """Get online/offline status for all project members."""

    def get(self, request, project_pk):
        project = get_object_or_404(
            Project, pk=project_pk,
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )
        presence = UserPresence.objects.filter(
            project=project
        ).select_related('user')
        return Response(UserPresenceSerializer(presence, many=True).data)