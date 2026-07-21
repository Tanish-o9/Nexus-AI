from django.contrib import admin
from .models import GitHubRepository, GitHubWebhookEvent, GitHubCommit, CommitTaskMapping, GitHubPR, GitHubBranch


@admin.register(GitHubRepository)
class GitHubRepositoryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'project', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('full_name',)


@admin.register(GitHubWebhookEvent)
class GitHubWebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'repository', 'processed', 'created_at')
    list_filter = ('event_type', 'processed')


@admin.register(GitHubCommit)
class GitHubCommitAdmin(admin.ModelAdmin):
    list_display = ('sha', 'repository', 'branch', 'author_name', 'timestamp')
    list_filter = ('branch',)


@admin.register(CommitTaskMapping)
class CommitTaskMappingAdmin(admin.ModelAdmin):
    list_display = ('commit', 'task', 'reference_type')


@admin.register(GitHubPR)
class GitHubPRAdmin(admin.ModelAdmin):
    list_display = ('pr_number', 'title', 'state', 'repository')
    list_filter = ('state',)


@admin.register(GitHubBranch)
class GitHubBranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'is_default', 'latest_sha')