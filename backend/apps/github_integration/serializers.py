from rest_framework import serializers
from .models import (
    GitHubRepository, GitHubWebhookEvent, GitHubCommit,
    CommitTaskMapping, GitHubPR, GitHubBranch
)


class GitHubRepositorySerializer(serializers.ModelSerializer):
    projectId = serializers.UUIDField(source='project_id')
    fullName = serializers.CharField(source='full_name', read_only=True)
    installationId = serializers.IntegerField(source='installation_id', allow_null=True, required=False)
    webhookSecret = serializers.CharField(source='webhook_secret', read_only=True)
    isActive = serializers.BooleanField(source='is_active', read_only=True)
    connectedBy = serializers.CharField(source='connected_by_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = GitHubRepository
        fields = (
            'id', 'projectId', 'owner', 'name', 'fullName',
            'installationId', 'webhookSecret', 'isActive',
            'connectedBy', 'createdAt',
        )


class GitHubRepositoryConnectSerializer(serializers.Serializer):
    projectId = serializers.UUIDField()
    owner = serializers.CharField(max_length=128)
    name = serializers.CharField(max_length=128)
    installationId = serializers.IntegerField(required=False, allow_null=True)


class GitHubWebhookEventSerializer(serializers.ModelSerializer):
    eventType = serializers.CharField(source='event_type', read_only=True)
    githubEventId = serializers.CharField(source='github_event_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = GitHubWebhookEvent
        fields = ('id', 'eventType', 'githubEventId', 'payload', 'processed', 'createdAt')


class GitHubCommitSerializer(serializers.ModelSerializer):
    authorName = serializers.CharField(source='author_name', read_only=True)
    authorEmail = serializers.CharField(source='author_email', read_only=True)
    repositoryName = serializers.CharField(source='repository.full_name', read_only=True)

    class Meta:
        model = GitHubCommit
        fields = (
            'id', 'sha', 'message', 'authorName', 'authorEmail',
            'branch', 'url', 'timestamp', 'repositoryName',
        )


class CommitTaskMappingSerializer(serializers.ModelSerializer):
    commitSha = serializers.CharField(source='commit.sha', read_only=True)
    commitMessage = serializers.CharField(source='commit.message', read_only=True)
    taskTitle = serializers.CharField(source='task.title', read_only=True)
    referenceType = serializers.CharField(source='reference_type', read_only=True)

    class Meta:
        model = CommitTaskMapping
        fields = ('id', 'commitSha', 'commitMessage', 'taskTitle', 'referenceType', 'created_at')


class GitHubPRSerializer(serializers.ModelSerializer):
    prNumber = serializers.IntegerField(source='pr_number', read_only=True)
    headBranch = serializers.CharField(source='head_branch', read_only=True)
    baseBranch = serializers.CharField(source='base_branch', read_only=True)
    isDraft = serializers.BooleanField(source='is_draft', read_only=True)
    mergedAt = serializers.DateTimeField(source='merged_at', read_only=True)
    closedAt = serializers.DateTimeField(source='closed_at', read_only=True)
    repositoryName = serializers.CharField(source='repository.full_name', read_only=True)

    class Meta:
        model = GitHubPR
        fields = (
            'id', 'prNumber', 'title', 'body', 'state', 'author',
            'headBranch', 'baseBranch', 'url', 'isDraft',
            'created_at', 'updated_at', 'mergedAt', 'closedAt', 'repositoryName',
        )


class GitHubBranchSerializer(serializers.ModelSerializer):
    latestSha = serializers.CharField(source='latest_sha', read_only=True)
    isProtected = serializers.BooleanField(source='is_protected', read_only=True)
    isDefault = serializers.BooleanField(source='is_default', read_only=True)
    lastCommitMessage = serializers.CharField(source='last_commit_message', read_only=True)
    lastCommitTimestamp = serializers.DateTimeField(source='last_commit_timestamp', read_only=True)

    class Meta:
        model = GitHubBranch
        fields = (
            'id', 'name', 'latestSha', 'isProtected', 'isDefault',
            'lastCommitMessage', 'lastCommitTimestamp',
        )