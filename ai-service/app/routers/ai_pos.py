"""
AI-Native Project Operating System Router
========================================
FastAPI routers for AI agents in the Project Operating System.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.ai_pos import (
    ProjectArchitectRequest,
    ProjectArchitectureResponse,
    CTORequest,
    CTOResponse,
    ProjectManagerRequest,
    ProjectManagerResponse,
    DeveloperAssistantRequest,
    DeveloperAssistantResponse,
    QAAssistantRequest,
    QAAssistantResponse,
    MeetingIntelligenceRequest,
    MeetingIntelligenceResponse,
    KnowledgeAssistantRequest,
    KnowledgeAssistantResponse,
    ExecutiveAssistantRequest,
    ExecutiveAssistantResponse,
    DecisionSupportRequest,
    DecisionSupportResponse,
    WorkflowEngineRequest,
    WorkflowEngineResponse,
    CrossProjectKnowledgeRequest,
    CrossProjectKnowledgeResponse,
)
from app.services.ai_pos import (
    project_architect,
    ai_cto,
    ai_project_manager,
    ai_developer_assistant,
    ai_qa_assistant,
    ai_meeting_intelligence,
    ai_knowledge_assistant,
    ai_executive_assistant,
    ai_decision_support,
    autonomous_workflow_engine,
    cross_project_knowledge,
)

router = APIRouter(prefix="/api/ai-pos", tags=["ai-pos"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── AI Project Architect ─────────────────────────────────────────────────────

@router.post(
    "/architect",
    response_model=ProjectArchitectureResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Project Architect",
)
async def project_architect_endpoint(body: ProjectArchitectRequest, session: AsyncSession = Depends(get_session)):
    """AI Project Architect - designs project architecture."""
    try:
        return await project_architect(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI CTO ───────────────────────────────────────────────────────────────────

@router.post(
    "/cto",
    response_model=CTOResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI CTO",
)
async def ai_cto_endpoint(body: CTORequest, session: AsyncSession = Depends(get_session)):
    """AI CTO - provides technical leadership."""
    try:
        return await ai_cto(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Project Manager ─────────────────────────────────────────────────────

@router.post(
    "/pm",
    response_model=ProjectManagerResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Project Manager",
)
async def ai_project_manager_endpoint(body: ProjectManagerRequest, session: AsyncSession = Depends(get_session)):
    """AI Project Manager - manages project execution."""
    try:
        return await ai_project_manager(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Developer Assistant ───────────────────────────────────────────────────

@router.post(
    "/developer",
    response_model=DeveloperAssistantResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Developer Assistant",
)
async def ai_developer_assistant_endpoint(body: DeveloperAssistantRequest, session: AsyncSession = Depends(get_session)):
    """AI Developer Assistant - helps with code implementation."""
    try:
        return await ai_developer_assistant(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI QA Assistant ─────────────────────────────────────────────────────────

@router.post(
    "/qa",
    response_model=QAAssistantResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI QA Assistant",
)
async def ai_qa_assistant_endpoint(body: QAAssistantRequest, session: AsyncSession = Depends(get_session)):
    """AI QA Assistant - creates test plans and analyzes quality."""
    try:
        return await ai_qa_assistant(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Meeting Intelligence ─────────────────────────────────────────────────

@router.post(
    "/meetings",
    response_model=MeetingIntelligenceResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Meeting Intelligence",
)
async def ai_meeting_intelligence_endpoint(body: MeetingIntelligenceRequest, session: AsyncSession = Depends(get_session)):
    """AI Meeting Intelligence - analyzes meeting transcripts."""
    try:
        return await ai_meeting_intelligence(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Knowledge Assistant ─────────────────────────────────────────────────

@router.post(
    "/knowledge",
    response_model=KnowledgeAssistantResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Knowledge Assistant",
)
async def ai_knowledge_assistant_endpoint(body: KnowledgeAssistantRequest, session: AsyncSession = Depends(get_session)):
    """AI Knowledge Assistant - answers questions using RAG."""
    try:
        return await ai_knowledge_assistant(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Executive Assistant ─────────────────────────────────────────────────

@router.post(
    "/executive",
    response_model=ExecutiveAssistantResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Executive Assistant",
)
async def ai_executive_assistant_endpoint(body: ExecutiveAssistantRequest, session: AsyncSession = Depends(get_session)):
    """AI Executive Assistant - provides executive summaries."""
    try:
        return await ai_executive_assistant(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Decision Support ─────────────────────────────────────────────────────

@router.post(
    "/decisions",
    response_model=DecisionSupportResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI Decision Support",
)
async def ai_decision_support_endpoint(body: DecisionSupportRequest, session: AsyncSession = Depends(get_session)):
    """AI Decision Support - helps with decision making."""
    try:
        return await ai_decision_support(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Autonomous Workflow Engine ─────────────────────────────────────────────

@router.post(
    "/workflows",
    response_model=WorkflowEngineResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Autonomous Workflow Engine",
)
async def autonomous_workflow_engine_endpoint(body: WorkflowEngineRequest, session: AsyncSession = Depends(get_session)):
    """Autonomous Workflow Engine - executes automated workflows."""
    try:
        return await autonomous_workflow_engine(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Cross-Project Knowledge Sharing ─────────────────────────────────────────

@router.post(
    "/cross-project",
    response_model=CrossProjectKnowledgeResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Cross-Project Knowledge Sharing",
)
async def cross_project_knowledge_endpoint(body: CrossProjectKnowledgeRequest, session: AsyncSession = Depends(get_session)):
    """Cross-Project Knowledge Sharing - shares knowledge between projects."""
    try:
        return await cross_project_knowledge(session, body)
    except Exception as exc:
        raise _error_response(exc)