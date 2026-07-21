"""
GitHub Integration Services
===========================
Handles GitHub API calls, webhook processing, commit→task mapping,
and activity timeline generation.
"""

import hashlib
import hmac
import re
import uuid
from datetime import datetime

import httpx
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_action
from apps.notifications.services import send_notification
from .models import (
    GitHubRepository, GitHubWebhookEvent, GitHubCommit,
    CommitTaskMapping, GitHubPR, GitHubBranch,
)

# Pattern to detect task references in commit messages: "TASK-123" or "fixes #123"
TASK_REF_PATTERN = re.compile(r'(?:TASK[-\s]?|fixes?\s+#|closes?\s+#|refs?\s+#)([A-Za-z0-9-]+)', re.IGNORECASE)


# ── GitHub API helpers ─────────────────────────────────────────────────────────

def _github_headers():
    token = getattr(settings, 'GITHUB_TOKEN', '')
    if not token:
        return {}
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }


async def _github_get(path: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f'https://api.github.com{path}',
            headers=_github_headers(),
        )
        resp.raise_for_status()
        return resp.json()


# ── Repository connection ──────────────────────────────────────────────────────

def connect_repository(project, owner: str, name: str, connected_by, installation_id: int = None) -> GitHubRepository:
    """Connect a GitHub repository to a Nexus project."""
    full_name = f'{owner}/{name}'
    repo, created = GitHubRepository.objects.get_or_create(
        project=project,
        full_name=full_name,
        defaults={
            'owner': owner,
            'name': name,
            'installation_id': installation_id,
            'connected_by': connected_by,
            'webhook_secret': uuid.uuid4().hex,
        },
    )
    if not created:
        repo.is_active = True
        repo.save(update_fields=['is_active'])

    log_action(
        actor=connected_by,
        action='github.repo.connect',
        resource_type='GitHubRepository',
        resource_id=str(repo.id),
        metadata={'full_name': full_name, 'project_id': str(project.id)},
    )
    return repo


def disconnect_repository(repo: GitHubRepository) -> None:
    """Disconnect a GitHub repository."""
    repo.is_active = False
    repo.save(update_fields=['is_active'])


# ── Webhook handling ───────────────────────────────────────────────────────────

def verify_webhook_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature."""
    if not signature_header:
        return False
    expected = 'sha256=' + hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@transaction.atomic
def process_webhook_event(repo: GitHubRepository, event_type: str, payload: dict) -> GitHubWebhookEvent:
    """Process an incoming GitHub webhook event."""
    github_event_id = str(payload.get('head_commit', {}).get('id', '') or payload.get('pull_request', {}).get('id', '') or '')

    event = GitHubWebhookEvent.objects.create(
        repository=repo,
        event_type=event_type,
        github_event_id=github_event_id,
        payload=payload,
    )

    if event_type == 'push':
        _process_push_event(repo, payload, event)
    elif event_type == 'pull_request':
        _process_pr_event(repo, payload, event)
    elif event_type in ('create', 'delete'):
        _process_branch_event(repo, event_type, payload, event)

    event.processed = True
    event.save(update_fields=['processed'])
    return event


def _process_push_event(repo, payload, event):
    """Process a push event: record commits, update branches, map to tasks."""
    ref = payload.get('ref', '')
    branch = ref.replace('refs/heads/', '') if ref.startswith('refs/heads/') else ''

    # Update branch
    GitHubBranch.objects.update_or_create(
        repository=repo,
        name=branch or 'main',
        defaults={
            'latest_sha': payload.get('head_commit', {}).get('id', ''),
            'last_commit_message': payload.get('head_commit', {}).get('message', ''),
            'last_commit_timestamp': timezone.now(),
        },
    )

    # Record commits
    for commit_data in payload.get('commits', []):
        sha = commit_data.get('id', '')
        if not sha:
            continue

        commit, created = GitHubCommit.objects.get_or_create(
            repository=repo,
            sha=sha,
            defaults={
                'message': commit_data.get('message', ''),
                'author_name': commit_data.get('author', {}).get('name', ''),
                'author_email': commit_data.get('author', {}).get('email', ''),
                'branch': branch,
                'url': commit_data.get('url', ''),
                'timestamp': commit_data.get('timestamp', timezone.now()),
            },
        )

        if created:
            _map_commit_to_tasks(commit)

    # Auto-update tasks if commit messages reference them
    _auto_update_tasks_from_push(repo, payload)


def _process_pr_event(repo, payload, event):
    """Process a pull request event."""
    pr_data = payload.get('pull_request', {})
    action = payload.get('action', '')
    pr_number = pr_data.get('number')

    if not pr_number:
        return

    state = 'open'
    if action == 'closed':
        state = 'merged' if pr_data.get('merged') else 'closed'

    GitHubPR.objects.update_or_create(
        repository=repo,
        pr_number=pr_number,
        defaults={
            'title': pr_data.get('title', ''),
            'body': pr_data.get('body', ''),
            'state': state,
            'author': pr_data.get('user', {}).get('login', ''),
            'head_branch': pr_data.get('head', {}).get('ref', ''),
            'base_branch': pr_data.get('base', {}).get('ref', ''),
            'url': pr_data.get('html_url', ''),
            'is_draft': pr_data.get('draft', False),
            'created_at': pr_data.get('created_at', timezone.now()),
            'updated_at': pr_data.get('updated_at', timezone.now()),
            'merged_at': pr_data.get('merged_at'),
            'closed_at': pr_data.get('closed_at'),
        },
    )


def _process_branch_event(repo, event_type, payload, event):
    """Process branch create/delete events."""
    ref = payload.get('ref', '')
    ref_type = payload.get('ref_type', '')
    if ref_type != 'branch':
        return

    if event_type == 'create':
        GitHubBranch.objects.update_or_create(
            repository=repo,
            name=ref,
            defaults={'latest_sha': payload.get('master_branch', '')},
        )
    elif event_type == 'delete':
        GitHubBranch.objects.filter(repository=repo, name=ref).delete()


# ── Commit → Task mapping ──────────────────────────────────────────────────────

def _map_commit_to_tasks(commit: GitHubCommit) -> list[CommitTaskMapping]:
    """Parse commit message for task references and create mappings."""
    mappings = []
    matches = TASK_REF_PATTERN.findall(commit.message)
    for ref in matches:
        try:
            task_uuid = uuid.UUID(ref) if len(ref) == 36 else None
        except ValueError:
            task_uuid = None

        if task_uuid:
            from apps.projects.models import Task
            try:
                task = Task.objects.get(pk=task_uuid, project__github_repos=commit.repository)
                mapping, _ = CommitTaskMapping.objects.get_or_create(
                    commit=commit, task=task,
                    defaults={'reference_type': 'auto'},
                )
                mappings.append(mapping)
            except Task.DoesNotExist:
                pass
    return mappings


def _auto_update_tasks_from_push(repo, payload):
    """Auto-update task status when commits reference them with keywords."""
    from apps.projects.models import Task
    for commit_data in payload.get('commits', []):
        message = commit_data.get('message', '')
        # Detect "closes TASK-xxx" or "fixes TASK-xxx"
        for match in re.finditer(r'(?:closes?\s+|fixes?\s+)([A-Za-z0-9-]+)', message, re.IGNORECASE):
            ref = match.group(1)
            try:
                task_uuid = uuid.UUID(ref) if len(ref) == 36 else None
            except ValueError:
                continue
            if task_uuid:
                Task.objects.filter(pk=task_uuid, project__github_repos=repo).update(status='done')


# ── Activity timeline ──────────────────────────────────────────────────────────

def get_activity_timeline(repo: GitHubRepository, limit: int = 30) -> list[dict]:
    """Build a combined activity timeline from commits, PRs, and webhook events."""
    events = []

    for commit in repo.commits.all()[:limit]:
        events.append({
            'type': 'commit',
            'id': str(commit.id),
            'sha': commit.sha[:8],
            'message': commit.message.split('\n')[0],
            'author': commit.author_name,
            'branch': commit.branch,
            'timestamp': commit.timestamp.isoformat() if commit.timestamp else '',
        })

    for pr in repo.pull_requests.all()[:limit]:
        events.append({
            'type': 'pull_request',
            'id': str(pr.id),
            'number': pr.pr_number,
            'title': pr.title,
            'state': pr.state,
            'author': pr.author,
            'timestamp': pr.updated_at.isoformat() if pr.updated_at else '',
        })

    events.sort(key=lambda e: e.get('timestamp', ''), reverse=True)
    return events[:limit]


# ── Commit timeline ────────────────────────────────────────────────────────────

def get_commit_timeline(repo: GitHubRepository, branch: str = None, limit: int = 30) -> list[dict]:
    """Get commit history for a repository, optionally filtered by branch."""
    qs = repo.commits.all()
    if branch:
        qs = qs.filter(branch=branch)
    qs = qs[:limit]

    return [
        {
            'sha': c.sha[:8],
            'message': c.message.split('\n')[0],
            'author': c.author_name,
            'branch': c.branch,
            'timestamp': c.timestamp.isoformat() if c.timestamp else '',
            'url': c.url,
            'taskMappings': [
                {'taskId': str(m.task_id), 'taskTitle': m.task.title}
                for m in c.task_mappings.select_related('task').all()
            ],
        }
        for c in qs
    ]


# ── PR status ──────────────────────────────────────────────────────────────────

def get_pr_status(repo: GitHubRepository, pr_number: int = None) -> list[dict]:
    """Get PR status, optionally for a specific PR number."""
    qs = repo.pull_requests.all()
    if pr_number:
        qs = qs.filter(pr_number=pr_number)
    return list(qs.values()[:20])


# ── Branch status ──────────────────────────────────────────────────────────────

def get_branch_status(repo: GitHubRepository) -> list[dict]:
    """Get all tracked branches with their latest status."""
    return list(repo.branches.all().values())


# ── Sync from GitHub API ───────────────────────────────────────────────────────

async def sync_repository(repo: GitHubRepository) -> dict:
    """Sync commits, PRs, and branches from GitHub API."""
    result = {'commits': 0, 'prs': 0, 'branches': 0}

    try:
        # Sync branches
        branches_data = await _github_get(f'/repos/{repo.full_name}/branches')
        for b in branches_data:
            GitHubBranch.objects.update_or_create(
                repository=repo,
                name=b['name'],
                defaults={
                    'latest_sha': b['commit']['sha'],
                    'is_protected': b.get('protected', False),
                    'is_default': b.get('name') == 'main',
                },
            )
        result['branches'] = len(branches_data)

        # Sync recent commits
        commits_data = await _github_get(f'/repos/{repo.full_name}/commits?per_page=30')
        for c in commits_data:
            sha = c['sha']
            commit_detail = c['commit']
            _, created = GitHubCommit.objects.get_or_create(
                repository=repo,
                sha=sha,
                defaults={
                    'message': commit_detail['message'],
                    'author_name': commit_detail.get('author', {}).get('name', ''),
                    'author_email': commit_detail.get('author', {}).get('email', ''),
                    'branch': 'main',
                    'url': c.get('html_url', ''),
                    'timestamp': commit_detail.get('author', {}).get('date', timezone.now()),
                },
            )
            if created:
                result['commits'] += 1

        # Sync open PRs
        prs_data = await _github_get(f'/repos/{repo.full_name}/pulls?state=all&per_page=20')
        for pr in prs_data:
            state = 'merged' if pr.get('merged_at') else pr['state']
            GitHubPR.objects.update_or_create(
                repository=repo,
                pr_number=pr['number'],
                defaults={
                    'title': pr['title'],
                    'body': pr.get('body', ''),
                    'state': state,
                    'author': pr['user']['login'],
                    'head_branch': pr['head']['ref'],
                    'base_branch': pr['base']['ref'],
                    'url': pr.get('html_url', ''),
                    'is_draft': pr.get('draft', False),
                    'created_at': pr['created_at'],
                    'updated_at': pr['updated_at'],
                    'merged_at': pr.get('merged_at'),
                    'closed_at': pr.get('closed_at'),
                },
            )
            result['prs'] += 1

    except httpx.HTTPError:
        pass

    return result