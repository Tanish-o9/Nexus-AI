import pytest
from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.organizations.services import create_organization
from apps.organizations.models import Membership
from apps.projects.services import create_project
from apps.projects.models import Task
from apps.notifications.models import Notification


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_user(email, username):
    return User.objects.create_user(email=email, username=username, password='Str0ng!Pass')


from apps.accounts.models import UserSession


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    UserSession.objects.get_or_create(user=user, jti=str(access['jti']))
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return client


@pytest.fixture
def owner():
    return make_user('owner@n.io', 'owner')


@pytest.fixture
def org(owner):
    return create_organization('Notify Org', created_by=owner)


@pytest.fixture
def project(owner, org):
    return create_project('Notify Project', '', str(org.id), owner)


# ── Signal: task assigned ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTaskAssignedSignal:
    def test_notification_created_on_assignment(self, owner, org, project):
        assignee = make_user('dev@n.io', 'dev')
        Membership.objects.create(user=assignee, organization=org, role='member', is_active=True)

        # Patch WS push so test doesn't need a real channel layer
        with patch('apps.notifications.services._push_to_ws'):
            task = Task.objects.create(
                title='Fix bug',
                project=project,
                assignee=assignee,
                created_by=owner,
            )

        notif = Notification.objects.filter(user=assignee, type='task_assigned').first()
        assert notif is not None
        assert 'Fix bug' in notif.body

    def test_no_notification_when_no_assignee(self, owner, project):
        with patch('apps.notifications.services._push_to_ws'):
            Task.objects.create(title='Unassigned', project=project, created_by=owner)

        assert Notification.objects.filter(type='task_assigned').count() == 0


# ── Signal: membership created ────────────────────────────────────────────────

@pytest.mark.django_db
class TestMembershipSignal:
    def test_notification_on_invite(self, org):
        new_member = make_user('nm@n.io', 'nm')
        with patch('apps.notifications.services._push_to_ws'):
            Membership.objects.create(
                user=new_member, organization=org, role='member', is_active=True
            )

        notif = Notification.objects.filter(user=new_member, type='project_update').first()
        assert notif is not None
        assert 'Notify Org' in notif.title


# ── Signal: project status changed ───────────────────────────────────────────

@pytest.mark.django_db
class TestProjectStatusSignal:
    def test_notification_on_status_change(self, owner, org, project):
        with patch('apps.notifications.services._push_to_ws'):
            project.status = 'on_hold'
            project.save()

        notif = Notification.objects.filter(
            user=owner, type='project_update'
        ).order_by('-created_at').first()
        assert notif is not None
        assert 'on_hold' in notif.body


# ── REST: mark read ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMarkRead:
    def test_mark_single_read(self, owner):
        with patch('apps.notifications.services._push_to_ws'):
            notif = Notification.objects.create(
                user=owner, type='mention', title='Hey', body='You were mentioned'
            )
        client = auth_client(owner)
        res = client.patch(reverse('notification-mark-read', kwargs={'pk': notif.id}))
        assert res.status_code == 200
        assert res.data['read'] is True

    def test_mark_all_read(self, owner):
        with patch('apps.notifications.services._push_to_ws'):
            Notification.objects.create(user=owner, type='mention', title='A', body='b')
            Notification.objects.create(user=owner, type='mention', title='C', body='d')

        client = auth_client(owner)
        res = client.post(reverse('notification-mark-all-read'))
        assert res.status_code == 200
        assert res.data['updated'] == 2
        assert Notification.objects.filter(user=owner, read=False).count() == 0

    def test_cannot_mark_other_users_notification(self, owner):
        other = make_user('other@n.io', 'other')
        with patch('apps.notifications.services._push_to_ws'):
            notif = Notification.objects.create(
                user=other, type='mention', title='X', body='y'
            )
        client = auth_client(owner)
        res = client.patch(reverse('notification-mark-read', kwargs={'pk': notif.id}))
        assert res.status_code == 404


# ── Internal: agent-completed ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestAgentCompleted:
    def test_valid_secret_delivers_notification(self, owner):
        client = APIClient()
        with patch('apps.notifications.services._push_to_ws'):
            res = client.post(
                reverse('notification-agent-completed'),
                {'userId': str(owner.id), 'summary': 'Agent finished planning.'},
                format='json',
                HTTP_X_INTERNAL_SECRET='change-me-in-prod',
            )
        assert res.status_code == 200
        assert Notification.objects.filter(user=owner, type='agent_completed').exists()

    def test_wrong_secret_rejected(self, owner):
        client = APIClient()
        res = client.post(
            reverse('notification-agent-completed'),
            {'userId': str(owner.id), 'summary': 'test'},
            format='json',
            HTTP_X_INTERNAL_SECRET='wrong-secret',
        )
        assert res.status_code == 403
