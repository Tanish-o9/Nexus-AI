"""
Agile module views: sprints, backlog, analytics, reports, exports.
All use existing JWT auth.
"""

from datetime import date

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.models import Project, Task
from .models import Sprint, SprintBacklogItem, SprintReport
from .serializers import (
    SprintSerializer, SprintCreateSerializer,
    SprintBacklogItemSerializer, SprintBacklogAddSerializer,
    SprintReportSerializer,
)
from .services import (
    get_project_analytics, get_velocity, get_burndown,
    get_workload, get_deadline_risk,
    generate_sprint_report, export_report_csv, export_report_excel,
)


def _get_project(request, pk):
    return get_object_or_404(
        Project, pk=pk,
        organization__memberships__user=request.user,
        organization__memberships__is_active=True,
    )


# ── Sprint Planning ────────────────────────────────────────────────────────────

class SprintListCreateView(APIView):
    """List and create sprints for a project."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        sprints = Sprint.objects.filter(project=project)[:20]
        return Response(SprintSerializer(sprints, many=True).data)

    def post(self, request, project_pk):
        project = _get_project(request, project_pk)
        serializer = SprintCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sprint = Sprint.objects.create(
            project=project,
            name=serializer.validated_data['name'],
            goal=serializer.validated_data.get('goal', ''),
            start_date=serializer.validated_data['startDate'],
            end_date=serializer.validated_data['endDate'],
            created_by=request.user,
        )
        return Response(SprintSerializer(sprint).data, status=status.HTTP_201_CREATED)


class SprintDetailView(APIView):
    """Activate, complete, or delete a sprint."""

    def patch(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        sprint = get_object_or_404(Sprint, pk=pk, project=project)
        action = request.data.get('action', '')

        if action == 'activate':
            # Deactivate all other sprints
            Sprint.objects.filter(project=project, is_active=True).update(is_active=False)
            sprint.is_active = True
            sprint.save(update_fields=['is_active'])
        elif action == 'complete':
            sprint.is_active = False
            sprint.is_completed = True
            sprint.save(update_fields=['is_active', 'is_completed'])

        return Response(SprintSerializer(sprint).data)

    def delete(self, request, project_pk, pk):
        project = _get_project(request, project_pk)
        sprint = get_object_or_404(Sprint, pk=pk, project=project)
        sprint.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Sprint Backlog ─────────────────────────────────────────────────────────────

class SprintBacklogListView(APIView):
    """List backlog items for a sprint."""

    def get(self, request, project_pk, sprint_pk):
        project = _get_project(request, project_pk)
        sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
        items = sprint.backlog_items.select_related('task__assignee').all()
        return Response(SprintBacklogItemSerializer(items, many=True).data)


class SprintBacklogAddView(APIView):
    """Add a task to a sprint backlog."""

    def post(self, request, project_pk, sprint_pk):
        project = _get_project(request, project_pk)
        sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
        serializer = SprintBacklogAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = get_object_or_404(Task, pk=serializer.validated_data['taskId'], project=project)
        item, created = SprintBacklogItem.objects.get_or_create(
            sprint=sprint,
            task=task,
            defaults={'story_points': serializer.validated_data['storyPoints']},
        )
        if not created:
            item.story_points = serializer.validated_data['storyPoints']
            item.save(update_fields=['story_points'])

        return Response(SprintBacklogItemSerializer(item).data, status=status.HTTP_201_CREATED)


class SprintBacklogRemoveView(APIView):
    """Remove a task from a sprint backlog."""

    def delete(self, request, project_pk, sprint_pk, task_pk):
        project = _get_project(request, project_pk)
        sprint = get_object_or_404(Sprint, pk=sprint_pk, project=project)
        item = get_object_or_404(SprintBacklogItem, sprint=sprint, task_id=task_pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Velocity ───────────────────────────────────────────────────────────────────

class VelocityView(APIView):
    """Get team velocity from completed sprints."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        velocity = get_velocity(str(project.id))
        return Response(velocity)


# ── Burndown ───────────────────────────────────────────────────────────────────

class BurndownView(APIView):
    """Get burndown chart data for a sprint."""

    def get(self, request, project_pk, sprint_pk):
        project = _get_project(request, project_pk)
        get_object_or_404(Sprint, pk=sprint_pk, project=project)
        burndown = get_burndown(str(sprint_pk))
        return Response(burndown)


# ── Project Analytics ──────────────────────────────────────────────────────────

class ProjectAnalyticsView(APIView):
    """Get aggregated project analytics."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        analytics = get_project_analytics(str(project.id))
        return Response(analytics)


# ── Workload ───────────────────────────────────────────────────────────────────

class WorkloadView(APIView):
    """Get workload distribution per assignee."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        workload = get_workload(str(project.id))
        return Response(workload)


# ── Deadline Risk ──────────────────────────────────────────────────────────────

class DeadlineRiskView(APIView):
    """Get tasks at risk of missing deadlines."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        risks = get_deadline_risk(str(project.id))
        return Response(risks)


# ── Reports ────────────────────────────────────────────────────────────────────

class ReportListCreateView(APIView):
    """List and generate sprint reports."""

    def get(self, request, project_pk):
        project = _get_project(request, project_pk)
        reports = SprintReport.objects.filter(sprint__project=project)[:20]
        return Response(SprintReportSerializer(reports, many=True).data)

    def post(self, request, project_pk):
        project = _get_project(request, project_pk)
        sprint_id = request.data.get('sprintId')
        report_type = request.data.get('reportType', 'sprint')
        sprint = get_object_or_404(Sprint, pk=sprint_id, project=project)
        report = generate_sprint_report(str(sprint.id), report_type)
        return Response(SprintReportSerializer(report).data, status=status.HTTP_201_CREATED)


class WeeklyReportView(APIView):
    """Generate a weekly report for the project."""

    def post(self, request, project_pk):
        from datetime import timedelta
        project = _get_project(request, project_pk)
        sprint = Sprint.objects.filter(project=project, is_active=True).first()
        if not sprint:
            sprint = Sprint.objects.filter(project=project).order_by('-end_date').first()
        if not sprint:
            sprint = Sprint.objects.create(
                project=project,
                name=f"{project.name} Sprint 1",
                goal="Default sprint for project tasks and reporting",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=14),
                is_active=True,
                created_by=request.user,
            )
        report = generate_sprint_report(str(sprint.id), 'weekly')
        return Response(SprintReportSerializer(report).data, status=status.HTTP_201_CREATED)


class MonthlyReportView(APIView):
    """Generate a monthly report for the project."""

    def post(self, request, project_pk):
        from datetime import timedelta
        project = _get_project(request, project_pk)
        sprint = Sprint.objects.filter(project=project, is_active=True).first()
        if not sprint:
            sprint = Sprint.objects.filter(project=project).order_by('-end_date').first()
        if not sprint:
            sprint = Sprint.objects.create(
                project=project,
                name=f"{project.name} Sprint 1",
                goal="Default sprint for project tasks and reporting",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=14),
                is_active=True,
                created_by=request.user,
            )
        report = generate_sprint_report(str(sprint.id), 'monthly')
        return Response(SprintReportSerializer(report).data, status=status.HTTP_201_CREATED)


# ── Export ─────────────────────────────────────────────────────────────────────

class ReportExportCSVView(APIView):
    """Export a report as CSV."""

    def get(self, request, project_pk, report_pk):
        project = _get_project(request, project_pk)
        report = get_object_or_404(SprintReport, pk=report_pk, sprint__project=project)
        csv_content = export_report_csv(str(report.id))
        return HttpResponse(csv_content, content_type='text/csv', headers={
            'Content-Disposition': f'attachment; filename="report-{report.pk[:8]}.csv"',
        })


class ReportExportExcelView(APIView):
    """Export a report as Excel."""

    def get(self, request, project_pk, report_pk):
        project = _get_project(request, project_pk)
        report = get_object_or_404(SprintReport, pk=report_pk, sprint__project=project)
        excel_bytes = export_report_excel(str(report.id))
        return HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={
            'Content-Disposition': f'attachment; filename="report-{report.pk[:8]}.xlsx"',
        })