from django.urls import path
from .views import (
    SprintListCreateView, SprintDetailView,
    SprintBacklogListView, SprintBacklogAddView, SprintBacklogRemoveView,
    VelocityView, BurndownView, ProjectAnalyticsView,
    WorkloadView, DeadlineRiskView,
    ReportListCreateView, WeeklyReportView, MonthlyReportView,
    ReportExportCSVView, ReportExportExcelView,
)

urlpatterns = [
    # Sprints
    path('<uuid:project_pk>/sprints/', SprintListCreateView.as_view(), name='sprint-list'),
    path('<uuid:project_pk>/sprints', SprintListCreateView.as_view()),
    path('<uuid:project_pk>/sprints/<uuid:pk>/', SprintDetailView.as_view(), name='sprint-detail'),
    path('<uuid:project_pk>/sprints/<uuid:pk>', SprintDetailView.as_view()),

    # Sprint backlog
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog/', SprintBacklogListView.as_view(), name='sprint-backlog'),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog', SprintBacklogListView.as_view()),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog/add/', SprintBacklogAddView.as_view(), name='sprint-backlog-add'),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog/add', SprintBacklogAddView.as_view()),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog/<uuid:task_pk>/', SprintBacklogRemoveView.as_view(), name='sprint-backlog-remove'),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/backlog/<uuid:task_pk>', SprintBacklogRemoveView.as_view()),

    # Velocity & Burndown
    path('<uuid:project_pk>/velocity/', VelocityView.as_view(), name='velocity'),
    path('<uuid:project_pk>/velocity', VelocityView.as_view()),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/burndown/', BurndownView.as_view(), name='burndown'),
    path('<uuid:project_pk>/sprints/<uuid:sprint_pk>/burndown', BurndownView.as_view()),

    # Analytics
    path('<uuid:project_pk>/analytics/', ProjectAnalyticsView.as_view(), name='analytics'),
    path('<uuid:project_pk>/analytics', ProjectAnalyticsView.as_view()),
    path('<uuid:project_pk>/workload/', WorkloadView.as_view(), name='workload'),
    path('<uuid:project_pk>/workload', WorkloadView.as_view()),
    path('<uuid:project_pk>/deadline-risk/', DeadlineRiskView.as_view(), name='deadline-risk'),
    path('<uuid:project_pk>/deadline-risk', DeadlineRiskView.as_view()),

    # Reports
    path('<uuid:project_pk>/reports/', ReportListCreateView.as_view(), name='reports'),
    path('<uuid:project_pk>/reports', ReportListCreateView.as_view()),
    path('<uuid:project_pk>/reports/weekly/', WeeklyReportView.as_view(), name='report-weekly'),
    path('<uuid:project_pk>/reports/weekly', WeeklyReportView.as_view()),
    path('<uuid:project_pk>/reports/monthly/', MonthlyReportView.as_view(), name='report-monthly'),
    path('<uuid:project_pk>/reports/monthly', MonthlyReportView.as_view()),

    # Export
    path('<uuid:project_pk>/reports/<uuid:report_pk>/csv/', ReportExportCSVView.as_view(), name='report-csv'),
    path('<uuid:project_pk>/reports/<uuid:report_pk>/csv', ReportExportCSVView.as_view()),
    path('<uuid:project_pk>/reports/<uuid:report_pk>/excel/', ReportExportExcelView.as_view(), name='report-excel'),
    path('<uuid:project_pk>/reports/<uuid:report_pk>/excel', ReportExportExcelView.as_view()),
]