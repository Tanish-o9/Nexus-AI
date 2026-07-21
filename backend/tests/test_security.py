import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import pyotp

from apps.accounts.models import UserSession
from apps.audit.models import AuditLog


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(client):
    res = client.post(reverse('auth-register'), {
        'username': 'testuser',
        'email': 'test@nexus.io',
        'password': 'Str0ng!Pass',
    }, format='json')
    assert res.status_code == 201
    return res.data


@pytest.mark.django_db(transaction=True)
class TestSessionManagement:
    def test_login_creates_session(self, client, registered_user):
        assert UserSession.objects.filter(user__email='test@nexus.io').exists()
        assert 'sessionId' in registered_user

    def test_list_sessions(self, client, registered_user):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered_user['token']}")
        res = client.get(reverse('auth-sessions'), {'current': registered_user['sessionId']})
        assert res.status_code == 200
        assert len(res.data) >= 1
        assert any(s['isCurrent'] for s in res.data)

    def test_logout_revokes_session(self, client, registered_user):
        session_id = registered_user['sessionId']
        res = client.post(reverse('auth-logout'), {
            'refreshToken': registered_user['refreshToken'],
        }, format='json')
        assert res.status_code == 204
        session = UserSession.objects.get(pk=session_id)
        assert session.is_revoked


@pytest.mark.django_db(transaction=True)
class TestTwoFactorAuth:
    def _enable_2fa(self, client, user_data):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_data['token']}")
        setup = client.post(reverse('auth-2fa-setup'), format='json')
        assert setup.status_code == 200
        secret = setup.data['secret']
        code = pyotp.TOTP(secret).now()
        confirm = client.post(reverse('auth-2fa-confirm'), {'code': code}, format='json')
        assert confirm.status_code == 200
        return secret

    def test_login_requires_2fa_when_enabled(self, client, registered_user):
        self._enable_2fa(client, registered_user)
        client.credentials()

        res = client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        assert res.status_code == 200
        assert res.data['requires2FA'] is True
        assert 'tempToken' in res.data
        assert 'token' not in res.data

    def test_2fa_verify_issues_tokens(self, client, registered_user):
        secret = self._enable_2fa(client, registered_user)
        client.credentials()

        login = client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        code = pyotp.TOTP(secret).now()
        res = client.post(reverse('auth-2fa-verify'), {
            'tempToken': login.data['tempToken'],
            'code': code,
        }, format='json')
        assert res.status_code == 200
        assert 'token' in res.data
        assert 'sessionId' in res.data


@pytest.mark.django_db(transaction=True)
class TestAuthAuditLogging:
    def test_login_creates_audit_log_with_actor(self, client, registered_user):
        assert AuditLog.objects.filter(
            action='auth.register', actor__email='test@nexus.io'
        ).exists()

        client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        assert AuditLog.objects.filter(
            action='auth.login', actor__email='test@nexus.io'
        ).exists()

    def test_failed_login_audited(self, client, registered_user):
        client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'wrong',
        }, format='json')
        assert AuditLog.objects.filter(action='auth.login_failed').exists()


@pytest.mark.django_db(transaction=True)
class TestUserActivity:
    def test_user_can_view_own_activity(self, client, registered_user):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered_user['token']}")
        res = client.get(reverse('auth-activity'))
        assert res.status_code == 200
        assert res.data['count'] >= 1
