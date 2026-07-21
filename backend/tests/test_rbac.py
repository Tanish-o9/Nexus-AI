import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.organizations.models import Organization, Membership


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api():
    return APIClient()


def make_user(email, username):
    return User.objects.create_user(
        email=email, username=username, password='Str0ng!Pass'
    )


def auth_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    from apps.accounts.models import UserSession
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    UserSession.objects.get_or_create(user=user, jti=str(access['jti']))
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    return client


def make_org_with_owner(owner):
    from apps.organizations.services import create_organization
    return create_organization(name='Test Org', created_by=owner)


def add_member(user, org, role):
    return Membership.objects.create(user=user, organization=org, role=role, is_active=True)


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMemberList:
    def test_member_can_list(self):
        owner = make_user('owner@x.io', 'owner')
        org = make_org_with_owner(owner)
        client = auth_client(owner)
        res = client.get(reverse('org-members', kwargs={'org_id': org.id}))
        assert res.status_code == 200

    def test_non_member_cannot_list(self):
        owner = make_user('owner2@x.io', 'owner2')
        outsider = make_user('out@x.io', 'outsider')
        org = make_org_with_owner(owner)
        client = auth_client(outsider)
        res = client.get(reverse('org-members', kwargs={'org_id': org.id}))
        assert res.status_code == 403


@pytest.mark.django_db
class TestMemberInvite:
    def test_admin_can_invite(self):
        owner = make_user('o@x.io', 'o')
        admin = make_user('a@x.io', 'a')
        invitee = make_user('i@x.io', 'i')
        org = make_org_with_owner(owner)
        add_member(admin, org, 'admin')
        client = auth_client(admin)
        res = client.post(
            reverse('org-invite', kwargs={'org_id': org.id}),
            {'email': 'i@x.io', 'role': 'member'},
            format='json',
        )
        assert res.status_code == 201

    def test_member_cannot_invite(self):
        owner = make_user('o2@x.io', 'o2')
        member = make_user('m@x.io', 'm')
        invitee = make_user('i2@x.io', 'i2')
        org = make_org_with_owner(owner)
        add_member(member, org, 'member')
        client = auth_client(member)
        res = client.post(
            reverse('org-invite', kwargs={'org_id': org.id}),
            {'email': 'i2@x.io', 'role': 'member'},
            format='json',
        )
        assert res.status_code == 403

    def test_admin_cannot_assign_owner_role(self):
        owner = make_user('o3@x.io', 'o3')
        admin = make_user('a3@x.io', 'a3')
        invitee = make_user('i3@x.io', 'i3')
        org = make_org_with_owner(owner)
        add_member(admin, org, 'admin')
        client = auth_client(admin)
        res = client.post(
            reverse('org-invite', kwargs={'org_id': org.id}),
            {'email': 'i3@x.io', 'role': 'owner'},
            format='json',
        )
        assert res.status_code == 403


@pytest.mark.django_db
class TestLastOwnerGuard:
    def test_cannot_remove_last_owner(self):
        owner = make_user('solo@x.io', 'solo')
        org = make_org_with_owner(owner)
        membership = Membership.objects.get(user=owner, organization=org)
        client = auth_client(owner)
        res = client.delete(
            reverse('org-member-remove', kwargs={
                'org_id': org.id,
                'membership_id': membership.id,
            })
        )
        assert res.status_code == 400

    def test_cannot_demote_last_owner(self):
        owner = make_user('solo2@x.io', 'solo2')
        org = make_org_with_owner(owner)
        membership = Membership.objects.get(user=owner, organization=org)
        client = auth_client(owner)
        res = client.patch(
            reverse('org-member-role', kwargs={
                'org_id': org.id,
                'membership_id': membership.id,
            }),
            {'role': 'admin'},
            format='json',
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestProjectRBAC:
    def test_viewer_cannot_delete_project(self):
        from apps.organizations.services import create_organization
        from apps.projects.services import create_project

        owner = make_user('po@x.io', 'po')
        viewer = make_user('pv@x.io', 'pv')
        org = make_org_with_owner(owner)
        add_member(viewer, org, 'viewer')

        project = create_project(
            name='Test', description='', organization_id=str(org.id), created_by=owner
        )
        client = auth_client(viewer)
        res = client.delete(reverse('project-detail', kwargs={'pk': project.id}))
        assert res.status_code == 403

    def test_admin_can_delete_project(self):
        from apps.organizations.services import create_organization
        from apps.projects.services import create_project

        owner = make_user('pa@x.io', 'pa')
        admin = make_user('pad@x.io', 'pad')
        org = make_org_with_owner(owner)
        add_member(admin, org, 'admin')

        project = create_project(
            name='Test2', description='', organization_id=str(org.id), created_by=owner
        )
        client = auth_client(admin)
        res = client.delete(reverse('project-detail', kwargs={'pk': project.id}))
        assert res.status_code == 204
