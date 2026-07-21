"""
GitHub AI Router
================
FastAPI routers for AI-powered GitHub integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.github_ai import (
    RepositoryIndexRequest,
    RepositoryIndexResponse,
    CommitAnalysisRequest,
    CommitAnalysisResponse,
    CodeReviewRequest,
    CodeReviewResponse,
    BugDetectionRequest,
    BugDetectionResponse,
    SecurityAnalysisRequest,
    SecurityAnalysisResponse,
    ArchitectureSuggestionRequest,
    ArchitectureSuggestionResponse,
    DocumentationUpdateRequest,
    DocumentationUpdateResponse,
    CommitTaskLinkRequest,
    CommitTaskLinkResponse,
    ReleaseSummaryRequest,
    ReleaseSummaryResponse,
)
from app.services.github_ai import (
    index_repository,
    analyze_commit,
    ai_code_review,
    detect_bugs,
    analyze_security,
    suggest_architecture,
    update_documentation,
    link_commit_to_task,
    generate_release_summary,
)

router = APIRouter(prefix="/api/github-ai", tags=["github-ai"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── Repository Indexing ─────────────────────────────────────────────────────────

@router.post(
    "/index",
    response_model=RepositoryIndexResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Index a GitHub repository",
)
async def index_repository_endpoint(body: RepositoryIndexRequest, session: AsyncSession = Depends(get_session)):
    """Index a GitHub repository for AI analysis."""
    try:
        return await index_repository(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Commit Analysis ───────────────────────────────────────────────────────────

@router.post(
    "/commits/analyze",
    response_model=CommitAnalysisResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Analyze a commit",
)
async def analyze_commit_endpoint(body: CommitAnalysisRequest, session: AsyncSession = Depends(get_session)):
    """Analyze a commit for impact and changes."""
    try:
        return await analyze_commit(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Code Review ───────────────────────────────────────────────────────────

@router.post(
    "/reviews",
    response_model=CodeReviewResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="AI code review",
)
async def code_review_endpoint(body: CodeReviewRequest, session: AsyncSession = Depends(get_session)):
    """Perform AI-powered code review on a PR."""
    try:
        return await ai_code_review(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Bug Detection ─────────────────────────────────────────────────────────────

@router.post(
    "/bugs/detect",
    response_model=BugDetectionResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Detect bugs in code",
)
async def detect_bugs_endpoint(body: BugDetectionRequest, session: AsyncSession = Depends(get_session)):
    """Detect potential bugs in code changes."""
    try:
        return await detect_bugs(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Security Analysis ─────────────────────────────────────────────────────────

@router.post(
    "/security/analyze",
    response_model=SecurityAnalysisResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Security analysis",
)
async def security_analysis_endpoint(body: SecurityAnalysisRequest, session: AsyncSession = Depends(get_session)):
    """Perform security analysis on code changes."""
    try:
        return await analyze_security(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Architecture Suggestions ─────────────────────────────────────────────────

@router.post(
    "/architecture/suggest",
    response_model=ArchitectureSuggestionResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Architecture suggestions",
)
async def architecture_suggestion_endpoint(body: ArchitectureSuggestionRequest, session: AsyncSession = Depends(get_session)):
    """Provide architecture suggestions for a repository."""
    try:
        return await suggest_architecture(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Documentation Updates ─────────────────────────────────────────────────────

@router.post(
    "/docs/update",
    response_model=DocumentationUpdateResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Update documentation",
)
async def documentation_update_endpoint(body: DocumentationUpdateRequest, session: AsyncSession = Depends(get_session)):
    """Generate documentation updates based on PR changes."""
    try:
        return await update_documentation(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Commit to Task Linking ────────────────────────────────────────────────────

@router.post(
    "/commits/link",
    response_model=CommitTaskLinkResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Link commit to task",
)
async def link_commit_endpoint(body: CommitTaskLinkRequest, session: AsyncSession = Depends(get_session)):
    """Link a commit to relevant tasks using AI analysis."""
    try:
        return await link_commit_to_task(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Release Summary ───────────────────────────────────────────────────────────

@router.post(
    "/releases/summary",
    response_model=ReleaseSummaryResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Generate release summary",
)
async def release_summary_endpoint(body: ReleaseSummaryRequest, session: AsyncSession = Depends(get_session)):
    """Generate a release summary from tags and commits."""
    try:
        return await generate_release_summary(session, body)
    except Exception as exc:
        raise _error_response(exc)