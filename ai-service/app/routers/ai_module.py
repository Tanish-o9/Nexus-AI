"""
AI Module Router
================
FastAPI routers for all AI module features.
Each endpoint is secured via the internal service secret dependency.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import verify_internal_secret
from app.schemas.ai_module import (
    AIContext,
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    SprintPlanningRequest,
    SprintPlanningResponse,
    ProjectSummaryRequest,
    ProjectSummaryResponse,
    DocQARequest,
    DocQAResponse,
    MeetingSummaryRequest,
    MeetingSummaryResponse,
    PRReviewRequest,
    PRReviewResponse,
    BugExplanationRequest,
    BugExplanationResponse,
    DeadlinePredictionRequest,
    DeadlinePredictionResponse,
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    WorkloadSuggestionRequest,
    WorkloadSuggestionResponse,
    StandupSummaryRequest,
    StandupSummaryResponse,
    WeeklySummaryRequest,
    WeeklySummaryResponse,
    ReleaseNotesRequest,
    ReleaseNotesResponse,
    SmartTaskAssignmentRequest,
    SmartTaskAssignmentResponse,
    DuplicateTaskDetectionRequest,
    DuplicateTaskResponse,
    ProjectHealthScoreRequest,
    ProjectHealthScoreResponse,
)
from app.services.ai_module_service import (
    ai_chat,
    task_breakdown,
    sprint_planning,
    project_summary,
    doc_qa,
    meeting_summary,
    pr_review,
    bug_explanation,
    deadline_prediction,
    risk_analysis,
    workload_suggestion,
    standup_summary,
    weekly_summary,
    release_notes,
    smart_task_assignment,
    duplicate_task_detection,
    project_health_score,
)

router = APIRouter(prefix="/api/ai", tags=["ai-module"], dependencies=[Depends(verify_internal_secret)])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AI Chat
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/chat", summary="General-purpose AI chat with project context")
async def chat_endpoint(
    body: dict,
):
    """
    Send a message to the AI assistant with project context.

    Request body:
    {
        "message": "string",
        "context": {"session_id": "...", "user_id": "...", "org_id": "...", "project_id": "..."},
        "history": [{"role": "user", "content": "..."}]
    }
    """
    try:
        context = AIContext(**body.get("context", {}))
        result = await ai_chat(
            message=body["message"],
            context=context,
            history=body.get("history"),
        )
        return {"content": result, "session_id": context.session_id}
    except KeyError as exc:
        raise _error_response(exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Task Breakdown
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/task-breakdown",
    response_model=TaskBreakdownResponse,
    summary="Decompose a complex task into structured subtasks",
)
async def task_breakdown_endpoint(body: TaskBreakdownRequest):
    """Break a complex task description into ordered, actionable subtasks."""
    try:
        return await task_breakdown(body)
    except ValueError as exc:
        raise _error_response(exc, status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Sprint Planning
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/sprint-planning",
    response_model=SprintPlanningResponse,
    summary="Plan a sprint from backlog items",
)
async def sprint_planning_endpoint(body: SprintPlanningRequest):
    """Plan a sprint given duration, team capacity, and backlog items."""
    try:
        return await sprint_planning(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Project Summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/project-summary",
    response_model=ProjectSummaryResponse,
    summary="Generate a project status summary",
)
async def project_summary_endpoint(body: ProjectSummaryRequest):
    """Generate a comprehensive project summary with health metrics."""
    try:
        return await project_summary(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Documentation Q&A (RAG)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/doc-qa",
    response_model=DocQAResponse,
    summary="Question answering over ingested documents using RAG",
)
async def doc_qa_endpoint(body: DocQARequest):
    """
    Answer questions using semantic search over ingested documents.

    Uses hybrid search (vector + keyword) and optional cross-encoder
    re-ranking for maximum relevance.
    """
    try:
        return await doc_qa(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Meeting Summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/meeting-summary",
    response_model=MeetingSummaryResponse,
    summary="Summarise meeting notes into structured output",
)
async def meeting_summary_endpoint(body: MeetingSummaryRequest):
    """Convert raw meeting notes into a structured summary with action items."""
    try:
        return await meeting_summary(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PR Review
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/pr-review",
    response_model=PRReviewResponse,
    summary="Review a GitHub pull request",
)
async def pr_review_endpoint(body: PRReviewRequest):
    """Analyse a GitHub PR and provide code review feedback."""
    try:
        return await pr_review(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Bug Explanation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/bug-explanation",
    response_model=BugExplanationResponse,
    summary="Analyse and explain a bug",
)
async def bug_explanation_endpoint(body: BugExplanationRequest):
    """Analyse a bug description, error message, or code snippet."""
    try:
        return await bug_explanation(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Deadline Prediction
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/deadline-prediction",
    response_model=DeadlinePredictionResponse,
    summary="Predict task completion dates",
)
async def deadline_prediction_endpoint(body: DeadlinePredictionRequest):
    """Predict realistic completion dates for tasks based on project context."""
    try:
        return await deadline_prediction(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Risk Analysis
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/risk-analysis",
    response_model=RiskAnalysisResponse,
    summary="Analyse project risks",
)
async def risk_analysis_endpoint(body: RiskAnalysisRequest):
    """Identify, assess, and prioritise project risks."""
    try:
        return await risk_analysis(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Workload Suggestion
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/workload-suggestion",
    response_model=WorkloadSuggestionResponse,
    summary="Suggest optimal task assignments for team members",
)
async def workload_suggestion_endpoint(body: WorkloadSuggestionRequest):
    """Distribute tasks across team members considering skills and current load."""
    try:
        return await workload_suggestion(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Daily Standup Summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/standup-summary",
    response_model=StandupSummaryResponse,
    summary="Generate a daily standup summary from team updates",
)
async def standup_summary_endpoint(body: StandupSummaryRequest):
    """Generate a concise standup summary highlighting progress, blockers, and action items."""
    try:
        return await standup_summary(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Weekly Project Summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/weekly-summary",
    response_model=WeeklySummaryResponse,
    summary="Generate a weekly project summary",
)
async def weekly_summary_endpoint(body: WeeklySummaryRequest):
    """Generate a comprehensive weekly project summary with metrics and achievements."""
    try:
        return await weekly_summary(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Release Notes Generator
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/release-notes",
    response_model=ReleaseNotesResponse,
    summary="Generate release notes from commits",
)
async def release_notes_endpoint(body: ReleaseNotesRequest):
    """Generate professional release notes from a list of commits/PRs."""
    try:
        return await release_notes(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Smart Task Assignment
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/smart-task-assignment",
    response_model=SmartTaskAssignmentResponse,
    summary="Get AI-powered task assignment recommendations",
)
async def smart_task_assignment_endpoint(body: SmartTaskAssignmentRequest):
    """Recommend the best person to assign a task to based on skills, workload, and context."""
    try:
        return await smart_task_assignment(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 16. Duplicate Task Detection
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/duplicate-task-detection",
    response_model=DuplicateTaskResponse,
    summary="Detect duplicate or similar tasks",
)
async def duplicate_task_detection_endpoint(body: DuplicateTaskDetectionRequest):
    """Check if a new task is a duplicate of existing tasks using AI similarity analysis."""
    try:
        return await duplicate_task_detection(body)
    except Exception as exc:
        raise _error_response(exc)


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Project Health Score
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/project-health-score",
    response_model=ProjectHealthScoreResponse,
    summary="Calculate comprehensive project health metrics",
)
async def project_health_score_endpoint(body: ProjectHealthScoreRequest):
    """Calculate a comprehensive health score (0-100) with actionable recommendations."""
    try:
        return await project_health_score(body)
    except Exception as exc:
        raise _error_response(exc)