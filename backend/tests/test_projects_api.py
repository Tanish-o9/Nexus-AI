import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.organizations.services import create_organization
from apps.organizations.models import Membership
from apps.projects.models import Project, Task
from apps.projects.services import create_project


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_user(email, username='user'):
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
    return make_user('owner@t.io', 'owner')


@pytest.fixture
def org(owner):
    return create_organization('Acme', created_by=owner)


@pytest.fixture
def project(owner, org):
    return create_project('Alpha', 'desc', str(org.id), owner)


@pytest.fixture
def client(owner):
    return auth_client(owner)


# ── Project CRUD ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProjectList:
    def test_returns_only_user_projects(self, client, project):
        res = client.get(reverse('project-list-create'))
        assert res.status_code == 200
        assert res.data['count'] == 1

    def test_outsider_sees_no_projects(self, project):
        outsider = make_user('out@t.io', 'out')
        c = auth_client(outsider)
        res = c.get(reverse('project-list-create'))
        assert res.status_code == 200
        assert res.data['count'] == 0

    def test_filter_by_status(self, client, project):
        res = client.get(reverse('project-list-create'), {'status': 'active'})
        assert res.status_code == 200
        assert res.data['count'] == 1

        res = client.get(reverse('project-list-create'), {'status': 'archived'})
        assert res.data['count'] == 0

    def test_search_by_name(self, client, project):
        res = client.get(reverse('project-list-create'), {'search': 'Alph'})
        assert res.data['count'] == 1

        res = client.get(reverse('project-list-create'), {'search': 'zzz'})
        assert res.data['count'] == 0


@pytest.mark.django_db
class TestProjectCreate:
    def test_success(self, client, org):
        res = client.post(reverse('project-list-create'), {
            'name': 'Beta',
            'description': 'New project',
            'organizationId': str(org.id),
        }, format='json')
        assert res.status_code == 201
        assert res.data['name'] == 'Beta'

    def test_short_name_rejected(self, client, org):
        res = client.post(reverse('project-list-create'), {
            'name': 'X',
            'organizationId': str(org.id),
        }, format='json')
        assert res.status_code == 400

    def test_non_member_cannot_create(self, org):
        outsider = make_user('x@t.io', 'x')
        c = auth_client(outsider)
        res = c.post(reverse('project-list-create'), {
            'name': 'Hack',
            'organizationId': str(org.id),
        }, format='json')
        assert res.status_code == 403


@pytest.mark.django_db
class TestProjectUpdate:
    def test_patch_name(self, client, project):
        res = client.patch(
            reverse('project-detail', kwargs={'pk': project.id}),
            {'name': 'Alpha Updated'},
            format='json',
        )
        assert res.status_code == 200
        assert res.data['name'] == 'Alpha Updated'

    def test_valid_status_transition(self, client, project):
        res = client.patch(
            reverse('project-detail', kwargs={'pk': project.id}),
            {'status': 'on_hold'},
            format='json',
        )
        assert res.status_code == 200
        assert res.data['status'] == 'on_hold'

    def test_invalid_status_transition(self, client, project):
        # active → completed is valid, but completed → active is not
        project.status = 'completed'
        project.save()
        res = client.patch(
            reverse('project-detail', kwargs={'pk': project.id}),
            {'status': 'active'},
            format='json',
        )
        assert res.status_code == 400

    def test_archived_project_cannot_transition(self, client, project):
        project.status = 'archived'
        project.save()
        res = client.patch(
            reverse('project-detail', kwargs={'pk': project.id}),
            {'status': 'active'},
            format='json',
        )
        assert res.status_code == 400


@pytest.mark.django_db
class TestProjectDelete:
    def test_admin_can_delete(self, client, project):
        res = client.delete(reverse('project-detail', kwargs={'pk': project.id}))
        assert res.status_code == 204

    def test_viewer_cannot_delete(self, org, project):
        viewer = make_user('v@t.io', 'v')
        Membership.objects.create(user=viewer, organization=org, role='viewer', is_active=True)
        c = auth_client(viewer)
        res = c.delete(reverse('project-detail', kwargs={'pk': project.id}))
        assert res.status_code == 403


# ── Task CRUD ─────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTaskCRUD:
    def test_create_task(self, client, project):
        res = client.post(
            reverse('task-list-create', kwargs={'project_pk': project.id}),
            {'title': 'Fix the bug', 'priority': 'high'},
            format='json',
        )
        assert res.status_code == 201
        assert res.data['title'] == 'Fix the bug'

    def test_short_title_rejected(self, client, project):
        res = client.post(
            reverse('task-list-create', kwargs={'project_pk': project.id}),
            {'title': 'AB'},
            format='json',
        )
        assert res.status_code == 400

    def test_list_tasks(self, client, project, owner):
        Task.objects.create(title='Task 1', project=project, created_by=owner)
        Task.objects.create(title='Task 2', project=project, created_by=owner)
        res = client.get(reverse('task-list-create', kwargs={'project_pk': project.id}))
        assert res.status_code == 200
        assert res.data['count'] == 2

    def test_filter_tasks_by_status(self, client, project, owner):
        Task.objects.create(title='Todo task', project=project, created_by=owner, status='todo')
        Task.objects.create(title='Done task', project=project, created_by=owner, status='done')
        res = client.get(
            reverse('task-list-create', kwargs={'project_pk': project.id}),
            {'status': 'done'},
        )
        assert res.data['count'] == 1

    def test_patch_task(self, client, project, owner):
        task = Task.objects.create(title='Old title', project=project, created_by=owner)
        res = client.patch(
            reverse('task-detail', kwargs={'project_pk': project.id, 'pk': task.id}),
            {'title': 'New title'},
            format='json',
        )
        assert res.status_code == 200
        assert res.data['title'] == 'New title'

    def test_delete_task(self, client, project, owner):
        task = Task.objects.create(title='Delete me', project=project, created_by=owner)
        res = client.delete(
            reverse('task-detail', kwargs={'project_pk': project.id, 'pk': task.id})
        )
        assert res.status_code == 204
        assert not Task.objects.filter(pk=task.id).exists()
