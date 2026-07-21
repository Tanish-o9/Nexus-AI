from django.urls import path
from .views import (
    ChatMessageListView, ChatMessageCreateView,
    ChatReactionToggleView, ChatAttachmentCreateView,
    ActivityFeedListView, PresenceListView,
)

urlpatterns = [
    # Team chat
    path('<uuid:project_pk>/chat/', ChatMessageListView.as_view(), name='chat-list'),
    path('<uuid:project_pk>/chat', ChatMessageListView.as_view()),
    path('<uuid:project_pk>/chat/send/', ChatMessageCreateView.as_view(), name='chat-send'),
    path('<uuid:project_pk>/chat/send', ChatMessageCreateView.as_view()),

    # Emoji reactions
    path('<uuid:project_pk>/chat/<uuid:msg_pk>/react/', ChatReactionToggleView.as_view(), name='chat-react'),
    path('<uuid:project_pk>/chat/<uuid:msg_pk>/react', ChatReactionToggleView.as_view()),

    # File upload
    path('<uuid:project_pk>/chat/<uuid:msg_pk>/attach/', ChatAttachmentCreateView.as_view(), name='chat-attach'),
    path('<uuid:project_pk>/chat/<uuid:msg_pk>/attach', ChatAttachmentCreateView.as_view()),

    # Activity feed
    path('<uuid:project_pk>/activity/', ActivityFeedListView.as_view(), name='activity-feed'),
    path('<uuid:project_pk>/activity', ActivityFeedListView.as_view()),

    # Presence
    path('<uuid:project_pk>/presence/', PresenceListView.as_view(), name='presence-list'),
    path('<uuid:project_pk>/presence', PresenceListView.as_view()),
]