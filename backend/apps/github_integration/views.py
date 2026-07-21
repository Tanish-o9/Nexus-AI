"""
GitHub Integration Views
========================
API endpoints for GitHub integration features.
All endpoints use existing JWT authentication.
"""

import json
import uuid

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project, Task
from apps.projects.views import _get_project_for_user
from .models import GitHubRepository, GitHubCommit, CommitTaskMapping, GitHubPR, GitHubBranch
from .serializers import (
    GitHubRepositorySerializer, GitHubRepositoryConnectSerializer,
    GitHubCommitSerializer, CommitTaskMappingSerializer,
    GitHubPRSerializer, GitHubBranchSerializer, GitHubWebhookEventSerializer,
)
from .services import (
    connect_repository, disconnect_repository,
    process_webhook_event, verify_webhook_signature,
    get_activity_timeline, get_commit_timeline,
    get_pr_status, get_branch_status, sync_repository,
)


# ── Repository Connect ─────────────────────────────────────────────────────────

class GitHubRepositoryListConnectView(APIView):
    """List connected repos and connect new ones."""

    def get(self, request):
        repos = GitHubRepository.objects.filter(
            project__organization__memberships__user=request.user,
            project__organization__memberships__is_active=True,
            is_active=True,
        ).select_related('project')
        return Response(GitHubRepositorySerializer(repos, many=True).data)

    def post(self, request):
        serializer = GitHubRepositoryConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = get_object_or_404(
            Project,
            pk=serializer.validated_data['projectId'],
            organization__memberships__user=request.user,
            organization__memberships__is_active=True,
        )

        repo = connect_repository(
            project=project,
            owner=serializer.validated_data['owner'],
            name=serializer.validated_data['name'],
            connected_by=request.user,
            installation_id=serializer.validated_data.get('installationId'),
        )
        return Response(GitHubRepositorySerializer(repo).data, status=status.HTTP_201_CREATED)


class GitHubRepositoryDetailView(APIView):
    """Disconnect or get details for a specific repo."""

    def get(self, request, pk):
        repo = get_object_or_404(GitHubRepository, pk=pk, is_active=True)
        return Response(GitHubRepositorySerializer(repo).data)

    def delete(self, request, pk):
        repo = get_object_or_404(GitHubRepository, pk=pk, is_active=True)
        disconnect_repository(repo)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Project-scoped GitHub endpoints ────────────────────────────────────────────

class GitHubProjectReposView(APIView):
    """List repos connected to a specific project."""

    def get(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        repos = project.github_repos.filter(is_active=True)
        return Response(GitHubRepositorySerializer(repos, many=True).data)

    def post(self, request, project_pk):
        project = _get_project_for_user(request.user, project_pk)
        payload = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        payload['projectId'] = str(project.id)
        serializer = GitHubRepositoryConnectSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        repo = connect_repository(
            project=project,
            owner=serializer.validated_data['owner'],
            name=serializer.validated_data['name'],
            connected_by=request.user,
            installation_id=serializer.validated_data.get('installationId'),
        )
        return Response(GitHubRepositorySerializer(repo).data, status=status.HTTP_201_CREATED)


class GitHubProjectRepoDashboardView(APIView):
    """Get repo dashboard data (commits, PRs, branches summary)."""

    def get(self, request, project_pk, repo_pk):
        project = _get_project_for_user(request.user, project_pk)
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, project=project, is_active=True)

        recent_commits = repo.commits.order_by('-timestamp')[:10]
        open_prs = repo.pull_requests.filter(state='open')[:10]
        branches = repo.branches.all()[:10]
        mappings = CommitTaskMapping.objects.filter(commit__repository=repo).select_related('commit', 'task')[:10]

        return Response({
            'repo': GitHubRepositorySerializer(repo).data,
            'commits': GitHubCommitSerializer(recent_commits, many=True).data,
            'pullRequests': GitHubPRSerializer(open_prs, many=True).data,
            'branches': GitHubBranchSerializer(branches, many=True).data,
            'taskMappings': CommitTaskMappingSerializer(mappings, many=True).data,
        })


# ── Webhook ────────────────────────────────────────────────────────────────────

class GitHubWebhookView(APIView):
    """
    Receive GitHub webhook events.
    No JWT auth — uses HMAC signature verification.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)

        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        if repo.webhook_secret and not verify_webhook_signature(
            request.body, signature, repo.webhook_secret
        ):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        event_type = request.headers.get('X-GitHub-Event', 'push')
        event = process_webhook_event(repo, event_type, request.data)
        return Response({'status': 'ok', 'event_id': str(event.id)})


# ── Commit Timeline ────────────────────────────────────────────────────────────

class GitHubCommitTimelineView(APIView):
    """Get commit history for a repository."""

    def get(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        branch = request.query_params.get('branch')
        timeline = get_commit_timeline(repo, branch=branch)
        return Response(timeline)


# ── PR Status ──────────────────────────────────────────────────────────────────

class GitHubPRStatusView(APIView):
    """Get PR status for a repository."""

    def get(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        pr_number = request.query_params.get('pr_number')
        if pr_number:
            pr_number = int(pr_number)
        prs = get_pr_status(repo, pr_number=pr_number)
        return Response(prs)


# ── Branch Status ──────────────────────────────────────────────────────────────

class GitHubBranchStatusView(APIView):
    """Get branch status for a repository."""

    def get(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        branches = get_branch_status(repo)
        return Response(branches)


# ── Activity Timeline ──────────────────────────────────────────────────────────

class GitHubActivityTimelineView(APIView):
    """Get combined activity timeline (commits + PRs)."""

    def get(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        timeline = get_activity_timeline(repo)
        return Response(timeline)


# ── Commit → Task Mapping ──────────────────────────────────────────────────────

class GitHubCommitTaskMappingsView(APIView):
    """Get commit→task mappings for a repository."""

    def get(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        mappings = CommitTaskMapping.objects.filter(
            commit__repository=repo,
        ).select_related('commit', 'task')[:50]
        return Response(CommitTaskMappingSerializer(mappings, many=True).data)


class GitHubManualTaskMappingView(APIView):
    """Manually map a commit to a task."""

    def post(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        commit_sha = request.data.get('commitSha', '')
        task_id = request.data.get('taskId', '')

        commit = get_object_or_404(GitHubCommit, repository=repo, sha=commit_sha)
        task = get_object_or_404(Task, pk=task_id, project__github_repos=repo)

        mapping, created = CommitTaskMapping.objects.get_or_create(
            commit=commit, task=task,
            defaults={'reference_type': 'manual'},
        )
        return Response(CommitTaskMappingSerializer(mapping).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# ── Sync ───────────────────────────────────────────────────────────────────────

class GitHubSyncView(APIView):
    """Sync repository data from GitHub API."""

    def post(self, request, repo_pk):
        repo = get_object_or_404(GitHubRepository, pk=repo_pk, is_active=True)
        import asyncio
        result = asyncio.run(sync_repository(repo))
        return Response(result)


# ── OAuth ──────────────────────────────────────────────────────────────────────

class GitHubOAuthInitView(APIView):
    """Start GitHub OAuth flow — redirect user to GitHub."""

    def get(self, request):
        client_id = getattr(settings, 'GITHUB_CLIENT_ID', '')
        if not client_id:
            return Response({'error': 'GitHub OAuth not configured'}, status=status.HTTP_501_NOT_IMPLEMENTED)

        state = uuid.uuid4().hex
        request.session['github_oauth_state'] = state

        redirect_uri = request.build_absolute_uri(reverse('github-oauth-callback'))
        url = (
            f'https://github.com/login/oauth/authorize'
            f'?client_id={client_id}'
            f'&redirect_uri={redirect_uri}'
            f'&state={state}'
            f'&scope=repo,admin:repo_hook'
        )
        return Response({'authorization_url': url, 'state': state})


class GitHubOAuthCallbackView(APIView):
    """Handle GitHub OAuth callback."""
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        stored_state = request.session.get('github_oauth_state')

        if state and stored_state and state != stored_state:
            return Response({'error': 'State mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        if not code:
            error = request.query_params.get('error', 'No code provided')
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        import httpx
        client_id = getattr(settings, 'GITHUB_CLIENT_ID', '')
        client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', '')

        try:
            resp = httpx.post(
                'https://github.com/login/oauth/access_token',
                data={
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'code': code,
                },
                headers={'Accept': 'application/json'},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            access_token = data.get('access_token', '')

            if not access_token:
                return Response({'error': 'Failed to get access token', 'details': data}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'access_token': access_token,
                'token_type': data.get('token_type', 'bearer'),
                'scope': data.get('scope', ''),
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimulateGitHubPushView(APIView):
    """
    Simulate a GitHub commit push for a task:
    - Automatically sets task status to 'done'
    - Populates github_commit_info with author, commit message, and files changed
    - Logs activity in the project
    """
    def post(self, request, project_pk, taskId):
        project = _get_project_for_user(request.user, project_pk)
        task = get_object_or_404(Task, pk=taskId, project=project)

        commit_msg = request.data.get('message', f'feat: completed {task.title}')
        files = request.data.get('files', ['backend/views.py', 'frontend/components/task.tsx'])
        author = request.data.get('pushedBy', request.user.username)

        commit_info = {
            'commitSha': uuid.uuid4().hex[:7],
            'message': commit_msg,
            'pushedBy': author,
            'filesChanged': files,
        }

        task.status = Task.Status.IN_REVIEW
        task.github_commit_info = commit_info
        task.save(update_fields=['status', 'github_commit_info', 'updated_at'])

        from apps.projects.models import ActivityLog
        from apps.projects.services import log_activity
        log_activity(
            project, request.user, ActivityLog.Action.UPDATED,
            task=task, field_name='status', old_value='in_progress', new_value='in_review',
            description=f'GitHub code pushed by {author} (Submitted for Owner Review): {commit_msg} ({len(files)} files)'
        )

        from apps.projects.serializers import TaskSerializer
        return Response(TaskSerializer(task).data)