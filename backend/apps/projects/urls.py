from django.urls import path
from .views import (
    ProjectListCreateView, ProjectDetailView, GlobalAnalyticsView,
    TaskListCreateView, TaskDetailView, TaskRateView,
    LabelListCreateView, KanbanColumnListCreateView, KanbanColumnDetailView,
    ChecklistItemListCreateView, ChecklistItemDetailView,
    TaskCommentListCreateView, TaskAttachmentListCreateView,
    TimeEntryListCreateView, TaskDependencyListCreateView,
    ProjectMemberListView, ProjectMemberInviteView, ProjectMemberDetailView,
    ActivityLogListView,
    MilestoneListCreateView, MilestoneDetailView,
)

urlpatterns = [
    # Global Analytics
    path('analytics/global/', GlobalAnalyticsView.as_view(), name='global-analytics'),
    path('analytics/global', GlobalAnalyticsView.as_view()),

    # Projects
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<uuid:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<uuid:pk>', ProjectDetailView.as_view()),

    # Columns
    path('<uuid:project_pk>/columns/', KanbanColumnListCreateView.as_view()),
    path('<uuid:project_pk>/columns', KanbanColumnListCreateView.as_view()),
    path('<uuid:project_pk>/columns/<uuid:pk>/', KanbanColumnDetailView.as_view()),
    path('<uuid:project_pk>/columns/<uuid:pk>', KanbanColumnDetailView.as_view()),

    # Labels
    path('<uuid:project_pk>/labels/', LabelListCreateView.as_view()),
    path('<uuid:project_pk>/labels', LabelListCreateView.as_view()),

    # Tasks (nested under project)
    path('<uuid:project_pk>/tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('<uuid:project_pk>/tasks', TaskListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<uuid:project_pk>/tasks/<uuid:pk>', TaskDetailView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:pk>/rate/', TaskRateView.as_view(), name='task-rate'),
    path('<uuid:project_pk>/tasks/<uuid:pk>/rate', TaskRateView.as_view()),

    # Checklist Items
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/checklist/', ChecklistItemListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/checklist', ChecklistItemListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/checklist/<uuid:pk>/', ChecklistItemDetailView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/checklist/<uuid:pk>', ChecklistItemDetailView.as_view()),

    # Comments, Attachments, Time, Dependencies
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/comments/', TaskCommentListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/comments', TaskCommentListCreateView.as_view()),
    
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/attachments/', TaskAttachmentListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/attachments', TaskAttachmentListCreateView.as_view()),
    
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/time/', TimeEntryListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/time', TimeEntryListCreateView.as_view()),
    
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/dependencies/', TaskDependencyListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/dependencies', TaskDependencyListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/dependencies/<uuid:pk>/', TaskDependencyListCreateView.as_view()),
    path('<uuid:project_pk>/tasks/<uuid:task_pk>/dependencies/<uuid:pk>', TaskDependencyListCreateView.as_view()),

    # Project Members
    path('<uuid:project_pk>/members/', ProjectMemberListView.as_view(), name='project-member-list'),
    path('<uuid:project_pk>/members', ProjectMemberListView.as_view()),
    path('<uuid:project_pk>/members/invite/', ProjectMemberInviteView.as_view(), name='project-member-invite'),
    path('<uuid:project_pk>/members/invite', ProjectMemberInviteView.as_view()),
    path('<uuid:project_pk>/members/<uuid:pk>/', ProjectMemberDetailView.as_view(), name='project-member-detail'),
    path('<uuid:project_pk>/members/<uuid:pk>', ProjectMemberDetailView.as_view()),

    # Activity Logs
    path('<uuid:project_pk>/activity/', ActivityLogListView.as_view(), name='project-activity-log'),
    path('<uuid:project_pk>/activity', ActivityLogListView.as_view()),

    # Milestones
    path('<uuid:project_pk>/milestones/', MilestoneListCreateView.as_view(), name='project-milestones'),
    path('<uuid:project_pk>/milestones', MilestoneListCreateView.as_view()),
    path('<uuid:project_pk>/milestones/<uuid:pk>/', MilestoneDetailView.as_view(), name='project-milestone-detail'),
    path('<uuid:project_pk>/milestones/<uuid:pk>', MilestoneDetailView.as_view()),
]
