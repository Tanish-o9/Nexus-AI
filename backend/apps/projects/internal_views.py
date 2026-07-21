"""Narrow service-to-service read endpoints used by the AI tool layer."""

import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Project
from .serializers import ProjectSerializer, TaskSerializer


class InternalProjectOverviewView(APIView):
    """Return only a requesting user's visible project and task data."""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request, pk):
        supplied_secret = request.headers.get("X-Internal-Secret", "")
        if not secrets.compare_digest(supplied_secret, settings.INTERNAL_SERVICE_SECRET):
            raise AuthenticationFailed("Invalid internal service credential.")

        user_id = request.headers.get("X-Nexus-User-Id")
        if not user_id:
            raise AuthenticationFailed("Missing user context.")
        user = get_object_or_404(get_user_model(), pk=user_id)
        project = get_object_or_404(
            Project.objects.select_related("organization").prefetch_related("tasks"), pk=pk
        )
        if not user.memberships.filter(organization=project.organization, is_active=True).exists():
            raise PermissionDenied("Project is not available to this user.")

        requested_org_id = request.headers.get("X-Nexus-Organization-Id")
        if requested_org_id and str(project.organization_id) != requested_org_id:
            raise PermissionDenied("Project is outside the selected organization.")

        return Response({
            "project": ProjectSerializer(project).data,
            "tasks": TaskSerializer(project.tasks.select_related("assignee"), many=True).data,
        })
