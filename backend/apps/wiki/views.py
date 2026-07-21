from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.projects.models import Project
from apps.audit.services import log_action
from common.pagination import StandardPagination

from .models import WikiPage, WikiPageVersion, WikiAttachment
from .serializers import (
    WikiPageSerializer, WikiPageCreateSerializer, WikiPageUpdateSerializer,
    WikiPageVersionSerializer, WikiPageTreeSerializer, WikiAttachmentSerializer,
)


def _get_project(request, pk):
    return get_object_or_404(
        Project, pk=pk,
        organization__memberships__user=request.user,
        organization__memberships__is_active=True,
    )


def _get_client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _log_wiki(action: str, user, page, request, metadata=None):
    log_action(
        actor=user,
        action=action,
        resource_type='WikiPage',
        resource_id=str(page.id),
        metadata=metadata or {},
        ip_address=_get_client_ip(request),
    )


# ── Wiki Page CRUD ─────────────────────────────────────────────────────────────

class WikiPageListCreateView(APIView):
    """List and create wiki pages for a project."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        qs = WikiPage.objects.filter(project=project).select_related(
            'created_by', 'updated_by'
        ).prefetch_related('attachments', 'children')

        # Search support
        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                models.Q(title__icontains=search) | models.Q(content__icontains=search)
            )

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request)
        return paginator.get_paginated_response(WikiPageSerializer(page, many=True).data)

    def post(self, request, project_pk):
        project = _get_project(request, project_pk)
        serializer = WikiPageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        page = WikiPage.objects.create(
            title=serializer.validated_data['title'],
            slug=serializer.validated_data['slug'],
            content=serializer.validated_data.get('content', ''),
            project=project,
            parent=serializer.validated_data.get('parent'),
            is_published=serializer.validated_data.get('is_published', True),
            created_by=request.user,
            updated_by=request.user,
        )
        _log_wiki('wiki.create', request.user, page, request)
        return Response(WikiPageSerializer(page).data, status=status.HTTP_201_CREATED)


class WikiPageDetailView(APIView):
    """Retrieve, update, or delete a wiki page."""

    def get(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(
            WikiPage.objects.select_related('created_by', 'updated_by')
            .prefetch_related('attachments', 'children'),
            pk=pk, project=project
        )
        return Response(WikiPageSerializer(page).data)

    def patch(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        serializer = WikiPageUpdateSerializer(page, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Save version history before updating
        WikiPageVersion.objects.create(
            page=page,
            version=page.version,
            title=page.title,
            content=page.content,
            edited_by=request.user,
            summary=request.data.get('summary', ''),
        )

        # Update the page
        for attr, value in serializer.validated_data.items():
            setattr(page, attr, value)
        page.version += 1
        page.updated_by = request.user
        page.save()

        _log_wiki('wiki.update', request.user, page, request, {'version': page.version})
        return Response(WikiPageSerializer(page).data)

    def delete(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        _log_wiki('wiki.delete', request.user, page, request)
        page.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Wiki Tree / Sidebar ────────────────────────────────────────────────────────

class WikiTreeView(APIView):
    """Get the wiki page tree for the sidebar."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        root_pages = WikiPage.objects.filter(
            project=project, parent__isnull=True, is_published=True
        )
        return Response(WikiPageTreeSerializer(root_pages, many=True).data)


# ── Version History ─────────────────────────────────────────────────────────────

class WikiPageVersionListView(APIView):
    """List version history for a wiki page."""

    def get(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        versions = WikiPageVersion.objects.filter(page=page).select_related('edited_by')
        return Response(WikiPageVersionSerializer(versions, many=True).data)


class WikiPageVersionDetailView(APIView):
    """Get a specific version of a wiki page."""

    def get(self, request, project_pk, pk, version_pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        version = get_object_or_404(WikiPageVersion, pk=version_pk, page=page)
        return Response(WikiPageVersionSerializer(version).data)


class WikiPageRestoreView(APIView):
    """Restore a wiki page to a previous version."""

    def post(self, request, project_pk, pk, version_pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        version = get_object_or_404(WikiPageVersion, pk=version_pk, page=page)

        # Save current as version before restoring
        WikiPageVersion.objects.create(
            page=page,
            version=page.version,
            title=page.title,
            content=page.content,
            edited_by=request.user,
            summary=f'Restored from version {version.version}',
        )

        page.title = version.title
        page.content = version.content
        page.version += 1
        page.updated_by = request.user
        page.save()

        _log_wiki('wiki.restore', request.user, page, request, {
            'restored_version': version.version,
            'new_version': page.version,
        })
        return Response(WikiPageSerializer(page).data)


# ── Attachments ─────────────────────────────────────────────────────────────────

class WikiAttachmentListCreateView(APIView):
    """List and create attachments for a wiki page."""

    def get(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        attachments = page.attachments.all()
        return Response(WikiAttachmentSerializer(attachments, many=True).data)

    def post(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        serializer = WikiAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attachment = serializer.save(page=page, uploaded_by=request.user)
        return Response(WikiAttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)


class WikiAttachmentDeleteView(APIView):
    """Delete an attachment."""

    def delete(self, request, project_pk, pk, attachment_pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)
        attachment = get_object_or_404(WikiAttachment, pk=attachment_pk, page=page)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── RAG Indexing ───────────────────────────────────────────────────────────────

class WikiRAGIndexView(APIView):
    """Send wiki page content to the AI service for RAG indexing."""

    def post(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        page = get_object_or_404(WikiPage, pk=pk, project=project)

        if not page.content.strip():
            return Response({'error': 'Page has no content to index'}, status=status.HTTP_400_BAD_REQUEST)

        from django.conf import settings
        import requests

        try:
            resp = requests.post(
                f'{settings.AI_SERVICE_URL}/api/documents/ingest',
                json={
                    'filename': f'wiki-{page.slug}.md',
                    'mime_type': 'text/markdown',
                    'content': page.content,
                    'org_id': str(project.organization_id),
                    'project_id': str(project.id),
                    'user_id': str(request.user.id),
                },
                headers={'Authorization': f'Bearer {settings.INTERNAL_SERVICE_SECRET}'},
                timeout=30,
            )
            resp.raise_for_status()
            _log_wiki('wiki.rag_index', request.user, page, request, {'status': 'indexed'})
            return Response({'status': 'indexed', 'detail': resp.json()})
        except requests.RequestException as e:
            return Response({'error': f'Indexing failed: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)