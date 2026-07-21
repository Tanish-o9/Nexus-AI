from django.urls import path
from .views import (
    GitHubRepositoryListConnectView,
    GitHubRepositoryDetailView,
    GitHubWebhookView,
    GitHubCommitTimelineView,
    GitHubPRStatusView,
    GitHubBranchStatusView,
    GitHubActivityTimelineView,
    GitHubCommitTaskMappingsView,
    GitHubManualTaskMappingView,
    GitHubSyncView,
    GitHubProjectReposView,
    GitHubProjectRepoDashboardView,
    GitHubOAuthInitView,
    GitHubOAuthCallbackView,
    SimulateGitHubPushView,
)

urlpatterns = [
    # Repository connection
    path('repos/', GitHubRepositoryListConnectView.as_view(), name='github-repo-list'),
    path('repos', GitHubRepositoryListConnectView.as_view()),
    path('repos/<uuid:pk>/', GitHubRepositoryDetailView.as_view(), name='github-repo-detail'),
    path('repos/<uuid:pk>', GitHubRepositoryDetailView.as_view()),

    # Webhook receiver (no auth, uses HMAC)
    path('webhook/<uuid:repo_pk>/', GitHubWebhookView.as_view(), name='github-webhook'),
    path('webhook/<uuid:repo_pk>', GitHubWebhookView.as_view()),

    # Commit timeline
    path('repos/<uuid:repo_pk>/commits/', GitHubCommitTimelineView.as_view(), name='github-commits'),
    path('repos/<uuid:repo_pk>/commits', GitHubCommitTimelineView.as_view()),

    # PR status
    path('repos/<uuid:repo_pk>/prs/', GitHubPRStatusView.as_view(), name='github-prs'),
    path('repos/<uuid:repo_pk>/prs', GitHubPRStatusView.as_view()),

    # Branch status
    path('repos/<uuid:repo_pk>/branches/', GitHubBranchStatusView.as_view(), name='github-branches'),
    path('repos/<uuid:repo_pk>/branches', GitHubBranchStatusView.as_view()),

    # Activity timeline
    path('repos/<uuid:repo_pk>/activity/', GitHubActivityTimelineView.as_view(), name='github-activity'),
    path('repos/<uuid:repo_pk>/activity', GitHubActivityTimelineView.as_view()),

    # Commit→Task mappings
    path('repos/<uuid:repo_pk>/mappings/', GitHubCommitTaskMappingsView.as_view(), name='github-mappings'),
    path('repos/<uuid:repo_pk>/mappings', GitHubCommitTaskMappingsView.as_view()),
    path('repos/<uuid:repo_pk>/mappings/manual/', GitHubManualTaskMappingView.as_view(), name='github-mapping-manual'),
    path('repos/<uuid:repo_pk>/mappings/manual', GitHubManualTaskMappingView.as_view()),

    # Sync from GitHub API
    path('repos/<uuid:repo_pk>/sync/', GitHubSyncView.as_view(), name='github-sync'),
    path('repos/<uuid:repo_pk>/sync', GitHubSyncView.as_view()),

    # Project-scoped repos
    path('projects/<uuid:project_pk>/repos/', GitHubProjectReposView.as_view(), name='github-project-repos'),
    path('projects/<uuid:project_pk>/repos', GitHubProjectReposView.as_view()),
    path('projects/<uuid:project_pk>/repos/<uuid:repo_pk>/dashboard/', GitHubProjectRepoDashboardView.as_view(), name='github-project-repo-dashboard'),
    path('projects/<uuid:project_pk>/repos/<uuid:repo_pk>/dashboard', GitHubProjectRepoDashboardView.as_view()),

    # OAuth
    path('oauth/init/', GitHubOAuthInitView.as_view(), name='github-oauth-init'),
    path('oauth/init', GitHubOAuthInitView.as_view()),
    path('oauth/callback/', GitHubOAuthCallbackView.as_view(), name='github-oauth-callback'),
    path('oauth/callback', GitHubOAuthCallbackView.as_view()),

    # Simulate GitHub Push
    path('projects/<uuid:project_pk>/tasks/<uuid:taskId>/simulate-push/', SimulateGitHubPushView.as_view(), name='github-simulate-push'),
    path('projects/<uuid:project_pk>/tasks/<uuid:taskId>/simulate-push', SimulateGitHubPushView.as_view()),
]