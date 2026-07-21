from django.urls import path
from .views import (
    WikiPageListCreateView, WikiPageDetailView,
    WikiTreeView,
    WikiPageVersionListView, WikiPageVersionDetailView, WikiPageRestoreView,
    WikiAttachmentListCreateView, WikiAttachmentDeleteView,
    WikiRAGIndexView,
)

urlpatterns = [
    # Wiki pages
    path('<uuid:project_pk>/pages/', WikiPageListCreateView.as_view(), name='wiki-page-list-create'),
    path('<uuid:project_pk>/pages', WikiPageListCreateView.as_view()),
    path('<uuid:project_pk>/pages/<uuid:pk>/', WikiPageDetailView.as_view(), name='wiki-page-detail'),
    path('<uuid:project_pk>/pages/<uuid:pk>', WikiPageDetailView.as_view()),

    # Wiki tree / sidebar
    path('<uuid:project_pk>/tree/', WikiTreeView.as_view(), name='wiki-tree'),
    path('<uuid:project_pk>/tree', WikiTreeView.as_view()),

    # Version history
    path('<uuid:project_pk>/pages/<uuid:pk>/versions/', WikiPageVersionListView.as_view(), name='wiki-page-versions'),
    path('<uuid:project_pk>/pages/<uuid:pk>/versions', WikiPageVersionListView.as_view()),
    path('<uuid:project_pk>/pages/<uuid:pk>/versions/<uuid:version_pk>/', WikiPageVersionDetailView.as_view(), name='wiki-page-version-detail'),
    path('<uuid:project_pk>/pages/<uuid:pk>/versions/<uuid:version_pk>', WikiPageVersionDetailView.as_view()),
    path('<uuid:project_pk>/pages/<uuid:pk>/versions/<uuid:version_pk>/restore/', WikiPageRestoreView.as_view(), name='wiki-page-restore'),
    path('<uuid:project_pk>/pages/<uuid:pk>/versions/<uuid:version_pk>/restore', WikiPageRestoreView.as_view()),

    # Attachments
    path('<uuid:project_pk>/pages/<uuid:pk>/attachments/', WikiAttachmentListCreateView.as_view(), name='wiki-attachment-list-create'),
    path('<uuid:project_pk>/pages/<uuid:pk>/attachments', WikiAttachmentListCreateView.as_view()),
    path('<uuid:project_pk>/pages/<uuid:pk>/attachments/<uuid:attachment_pk>/', WikiAttachmentDeleteView.as_view(), name='wiki-attachment-delete'),
    path('<uuid:project_pk>/pages/<uuid:pk>/attachments/<uuid:attachment_pk>', WikiAttachmentDeleteView.as_view()),

    # RAG indexing
    path('<uuid:project_pk>/pages/<uuid:pk>/rag-index/', WikiRAGIndexView.as_view(), name='wiki-rag-index'),
    path('<uuid:project_pk>/pages/<uuid:pk>/rag-index', WikiRAGIndexView.as_view()),
]