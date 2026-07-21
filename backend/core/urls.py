from django.urls import path, include
from core.admin import nexus_admin
from apps.projects.internal_views import InternalProjectOverviewView
from apps.projects.ai_views import (
    AIChatStreamView, AITaskBreakdownView, AISprintPlanningView,
    AIProjectSummaryView, AIDocQAView, AIMeetingSummaryView,
    AIDeadlinePredictionView, AIRiskAnalysisView, AIWorkloadSuggestionView,
)

urlpatterns = [
    path('admin/', nexus_admin.urls),
    path('', include('django_prometheus.urls')),
    
    path('api/auth/', include('apps.accounts.urls')),
    path('api/auth', include('apps.accounts.urls')),
    
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/organizations', include('apps.organizations.urls')),
    
    path('api/projects/', include('apps.projects.urls')),
    path('api/projects', include('apps.projects.urls')),
    
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/notifications', include('apps.notifications.urls')),
    
    path('api/audit/', include('apps.audit.urls')),
    path('api/audit', include('apps.audit.urls')),
    
    path('api/github/', include('apps.github_integration.urls')),
    path('api/github', include('apps.github_integration.urls')),
    
    path('api/collab/', include('apps.collaboration.urls')),
    path('api/collab', include('apps.collaboration.urls')),
    
    path('api/agile/', include('apps.agile.urls')),
    path('api/agile', include('apps.agile.urls')),
    
    path('api/wiki/', include('apps.wiki.urls')),
    path('api/wiki', include('apps.wiki.urls')),
    
    path('api/internal/projects/<uuid:pk>/overview/', InternalProjectOverviewView.as_view()),
    path('api/ai/chat/', AIChatStreamView.as_view(), name='ai-chat'),
    path('api/ai/chat', AIChatStreamView.as_view()),
    path('api/chat/stream/', AIChatStreamView.as_view(), name='ai-chat-stream'),
    path('api/chat/stream', AIChatStreamView.as_view()),
    path('api/ai/task-breakdown/', AITaskBreakdownView.as_view(), name='ai-task-breakdown'),
    path('api/ai/task-breakdown', AITaskBreakdownView.as_view()),
    path('api/ai/sprint-planning/', AISprintPlanningView.as_view(), name='ai-sprint-planning'),
    path('api/ai/sprint-planning', AISprintPlanningView.as_view()),
    path('api/ai/project-summary/', AIProjectSummaryView.as_view(), name='ai-project-summary'),
    path('api/ai/project-summary', AIProjectSummaryView.as_view()),
    path('api/ai/doc-qa/', AIDocQAView.as_view(), name='ai-doc-qa'),
    path('api/ai/doc-qa', AIDocQAView.as_view()),
    path('api/ai/meeting-summary/', AIMeetingSummaryView.as_view(), name='ai-meeting-summary'),
    path('api/ai/meeting-summary', AIMeetingSummaryView.as_view()),
    path('api/ai/deadline-prediction/', AIDeadlinePredictionView.as_view(), name='ai-deadline-prediction'),
    path('api/ai/deadline-prediction', AIDeadlinePredictionView.as_view()),
    path('api/ai/risk-analysis/', AIRiskAnalysisView.as_view(), name='ai-risk-analysis'),
    path('api/ai/risk-analysis', AIRiskAnalysisView.as_view()),
    path('api/ai/workload-suggestion/', AIWorkloadSuggestionView.as_view(), name='ai-workload-suggestion'),
    path('api/ai/workload-suggestion', AIWorkloadSuggestionView.as_view()),
]
