from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatMessage, ChatReaction, ChatAttachment, ActivityFeedItem, UserPresence

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')


class ChatReactionSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    userId = serializers.UUIDField(source='user_id', read_only=True)

    class Meta:
        model = ChatReaction
        fields = ('id', 'emoji', 'user', 'userId', 'created_at')


class ChatAttachmentSerializer(serializers.ModelSerializer):
    uploadedBy = UserBriefSerializer(source='uploaded_by', read_only=True)
    fileName = serializers.CharField(source='file_name', read_only=True)
    fileUrl = serializers.URLField(source='file_url', read_only=True)
    fileSize = serializers.IntegerField(source='file_size', read_only=True)
    mimeType = serializers.CharField(source='mime_type', read_only=True)

    class Meta:
        model = ChatAttachment
        fields = ('id', 'fileName', 'fileUrl', 'fileSize', 'mimeType', 'uploadedBy', 'created_at')


class ChatMessageSerializer(serializers.ModelSerializer):
    author = UserBriefSerializer(read_only=True)
    reactions = ChatReactionSerializer(many=True, read_only=True)
    attachments = ChatAttachmentSerializer(many=True, read_only=True)
    replyToId = serializers.UUIDField(source='reply_to_id', allow_null=True, required=False)
    mentionIds = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(),
        source='mentions', required=False,
    )
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            'id', 'content', 'author', 'reactions', 'attachments',
            'replyToId', 'mentionIds', 'createdAt',
        )


class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=5000)
    replyToId = serializers.UUIDField(required=False, allow_null=True)
    mentionIds = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class ActivityFeedItemSerializer(serializers.ModelSerializer):
    actor = UserBriefSerializer(read_only=True)
    activityType = serializers.CharField(source='activity_type', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ActivityFeedItem
        fields = ('id', 'actor', 'activityType', 'description', 'metadata', 'createdAt')


class UserPresenceSerializer(serializers.ModelSerializer):
    userId = serializers.UUIDField(source='user_id', read_only=True)
    isOnline = serializers.BooleanField(source='is_online', read_only=True)
    lastSeen = serializers.DateTimeField(source='last_seen', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserPresence
        fields = ('userId', 'username', 'isOnline', 'lastSeen')