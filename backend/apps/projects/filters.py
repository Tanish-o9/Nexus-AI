import django_filters
from .models import Project, Task


class ProjectFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Project.Status.choices)
    organization_id = django_filters.UUIDFilter(field_name='organization_id')
    search = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Project
        fields = ['status', 'organization_id', 'search']


class TaskFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.ChoiceFilter(choices=Task.Priority.choices)
    assignee = django_filters.UUIDFilter(field_name='assignee_id')
    due_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_after = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    search = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Task
        fields = ['status', 'priority', 'assignee', 'due_before', 'due_after', 'search']
