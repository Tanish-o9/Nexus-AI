import pytest
from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase, RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.organizations.services import create_organization
from apps.organizations.models import Membership
from apps.projects.services import create_project
from apps.projects.models import Task
from apps.audit.models import AuditLog
from apps.audit.services import log_action


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_user(email, username, is_staff=False):
    u = User.objects.create_user(email=email, username=username, password='Str0ng!Pass')
    if is_staff:
        u.is_staff = True
        u.save()
    return u


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
    return make_user('owner@a.io', 'owner')


@pytest.fixture
def org(owner):
    return create_organization('Audit Org', created_by=owner)


@pytest.fixture
def project(owner, org):
    return create_project('Audit Project', '', str(org.id), owner)


# ── log_action service ────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestLogAction:
    def test_creates_audit_log(self, owner):
        log_action(
            actor=owner,
            action='test.action',
            resource_type='Test',
            resource_id='abc-123',
            metadata={'key': 'value'},
            ip_address='127.0.0.1',
        )
        log = AuditLog.objects.get(action='test.action')
        assert log.actor == owner
        assert log.resource_id == 'abc-123'
        assert log.metadata == {'key': 'value'}
        assert log.ip_address == '127.0.0.1'

    def test_actor_can_be_none(self):
        log_action(
            actor=None,
            action='anon.action',
            resource_type='User',
            resource_id='unknown',
        )
        assert AuditLog.objects.filter(action='anon.action', actor=None).exists()


# ── Signal: project deleted ───────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestProjectDeleteSignal:
    def test_audit_log_on_project_delete(self, owner, project):
        project._deleted_by = owner
        project.delete()
        assert AuditLog.objects.filter(
            action='project.delete', resource_type='Project'
        ).exists()


# ── Signal: membership role change ───────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestMembershipRoleChangeSignal:
    def test_audit_log_on_role_change(self, owner, org):
        member = make_user('m@a.io', 'm')
        membership = Membership.objects.create(
            user=member, organization=org, role='member', is_active=True
        )
        # Change role
        membership.role = 'admin'
        membership._changed_by = owner
        membership.save()

        assert AuditLog.objects.filter(
            action='membership.role_change',
            resource_type='Membership',
        ).exists()
        log = AuditLog.objects.get(action='membership.role_change')
        assert log.metadata['old_role'] == 'member'
        assert log.metadata['new_role'] == 'admin'


# ── Audit log API ─────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestAuditLogAPI:
    def test_staff_can_list(self, owner):
        staff = make_user('staff@a.io', 'staff', is_staff=True)
        log_action(actor=owner, action='test.view', resource_type='X', resource_id='1')
        client = auth_client(staff)
        res = client.get(reverse('audit-log-list'))
        assert res.status_code == 200
        assert res.data['count'] >= 1

    def test_non_staff_forbidden(self, owner):
        log_action(actor=owner, action='test.view2', resource_type='X', resource_id='2')
        client = auth_client(owner)
        res = client.get(reverse('audit-log-list'))
        assert res.status_code == 403

    def test_filter_by_action(self, owner):
        staff = make_user('staff2@a.io', 'staff2', is_staff=True)
        log_action(actor=owner, action='filter.test', resource_type='Y', resource_id='3')
        client = auth_client(staff)
        res = client.get(reverse('audit-log-list'), {'action': 'filter.test'})
        assert res.status_code == 200
        assert all(r['action'] == 'filter.test' for r in res.data['results'])

    def test_logs_are_read_only(self, owner):
        staff = make_user('staff3@a.io', 'staff3', is_staff=True)
        client = auth_client(staff)
        # POST to list endpoint should 405
        res = client.post(reverse('audit-log-list'), {}, format='json')
        assert res.status_code == 405
