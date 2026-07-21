import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(client):
    """Register a user and return the response payload."""
    res = client.post(reverse('auth-register'), {
        'username': 'testuser',
        'email': 'test@nexus.io',
        'password': 'Str0ng!Pass',
    }, format='json')
    assert res.status_code == 201
    return res.data


@pytest.mark.django_db
class TestRegister:
    def test_success(self, client):
        res = client.post(reverse('auth-register'), {
            'username': 'alice',
            'email': 'alice@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        assert res.status_code == 201
        assert 'token' in res.data
        assert 'refreshToken' in res.data
        assert res.data['user']['email'] == 'alice@nexus.io'

    def test_duplicate_email(self, client, registered_user):
        res = client.post(reverse('auth-register'), {
            'username': 'other',
            'email': 'test@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        assert res.status_code == 400

    def test_weak_password_rejected(self, client):
        res = client.post(reverse('auth-register'), {
            'username': 'bob',
            'email': 'bob@nexus.io',
            'password': '123',
        }, format='json')
        assert res.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_success(self, client, registered_user):
        res = client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'Str0ng!Pass',
        }, format='json')
        assert res.status_code == 200
        assert 'token' in res.data

    def test_wrong_password(self, client, registered_user):
        res = client.post(reverse('auth-login'), {
            'email': 'test@nexus.io',
            'password': 'wrongpassword',
        }, format='json')
        assert res.status_code == 401

    def test_nonexistent_user(self, client):
        res = client.post(reverse('auth-login'), {
            'email': 'ghost@nexus.io',
            'password': 'anything',
        }, format='json')
        assert res.status_code == 401


@pytest.mark.django_db
class TestLogoutAndRefresh:
    def test_logout_blacklists_refresh_token(self, client, registered_user):
        refresh_token = registered_user['refreshToken']

        # Logout
        res = client.post(reverse('auth-logout'), {
            'refreshToken': refresh_token,
        }, format='json')
        assert res.status_code == 204

        # Attempt to use the blacklisted refresh token
        res = client.post(reverse('auth-token-refresh'), {
            'refresh': refresh_token,
        }, format='json')
        assert res.status_code == 401

    def test_token_refresh_returns_new_access(self, client, registered_user):
        res = client.post(reverse('auth-token-refresh'), {
            'refresh': registered_user['refreshToken'],
        }, format='json')
        assert res.status_code == 200
        assert 'access' in res.data


@pytest.mark.django_db
class TestForgotPassword:
    def test_always_returns_200(self, client):
        # Should not reveal whether email exists
        res = client.post(reverse('auth-forgot-password'), {
            'email': 'doesnotexist@nexus.io',
        }, format='json')
        assert res.status_code == 200
        assert 'message' in res.data

    def test_valid_email_also_returns_200(self, client, registered_user):
        res = client.post(reverse('auth-forgot-password'), {
            'email': 'test@nexus.io',
        }, format='json')
        assert res.status_code == 200


@pytest.mark.django_db
class TestMeEndpoint:
    def test_requires_auth(self, client):
        res = client.get(reverse('auth-me'))
        assert res.status_code == 401

    def test_returns_profile(self, client, registered_user):
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {registered_user['token']}")
        res = client.get(reverse('auth-me'))
        assert res.status_code == 200
        assert res.data['email'] == 'test@nexus.io'
