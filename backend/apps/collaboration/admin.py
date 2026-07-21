from django.contrib import admin
from .models import ChatMessage, ChatReaction, ChatAttachment, ActivityFeedItem, UserPresence


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'content_preview', 'project', 'created_at')
    list_filter = ('project',)

    def content_preview(self, obj):
        return obj.content[:60]


@admin.register(ChatReaction)
class ChatReactionAdmin(admin.ModelAdmin):
    list_display = ('emoji', 'user', 'message', 'created_at')


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'message', 'uploaded_by', 'created_at')


@admin.register(ActivityFeedItem)
class ActivityFeedItemAdmin(admin.ModelAdmin):
    list_display = ('activity_type', 'actor', 'description', 'project', 'created_at')
    list_filter = ('activity_type',)


@admin.register(UserPresence)
class UserPresenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'is_online', 'last_seen')
    list_filter = ('is_online',)