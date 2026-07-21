"""
Executive Dashboard Router
==========================
FastAPI routers for executive intelligence dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import verify_internal_secret
from app.memory.database import get_session
from app.schemas.executive_dashboard import (
    CompanyHealthRequest,
    CompanyHealthResponse,
    ProjectHealthRequest,
    ProjectHealthResponse,
    TeamProductivityRequest,
    TeamProductivityResponse,
    EngineeringMetricsRequest,
    EngineeringMetricsResponse,
    SprintAnalyticsRequest,
    SprintAnalyticsResponse,
    RiskDashboardRequest,
    RiskDashboardResponse,
    AIRecommendationsRequest,
    AIRecommendationsResponse,
    CostEstimationRequest,
    CostEstimationResponse,
    DeliveryPredictionRequest,
    DeliveryPredictionResponse,
    ExecutiveSummaryRequest,
    ExecutiveSummaryResponse,
)
from app.services.executive_dashboard import (
    get_company_health,
    get_project_health,
    get_team_productivity,
    get_engineering_metrics,
    get_sprint_analytics,
    get_risk_dashboard,
    get_ai_recommendations,
    get_cost_estimation,
    get_delivery_prediction,
    get_executive_summary,
)

router = APIRouter(prefix="/api/executive", tags=["executive-dashboard"])


def _error_response(exc: Exception, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Normalise exceptions into HTTP errors."""
    detail = str(exc) if str(exc) else "An unexpected error occurred."
    return HTTPException(status_code=status_code, detail=detail)


# ── Company Health ───────────────────────────────────────────────────────────

@router.post(
    "/health",
    response_model=CompanyHealthResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get company health metrics",
)
async def company_health_endpoint(body: CompanyHealthRequest, session: AsyncSession = Depends(get_session)):
    """Get company-wide health metrics."""
    try:
        return await get_company_health(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Project Health ─────────────────────────────────────────────────────────

@router.post(
    "/project-health",
    response_model=ProjectHealthResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get project health metrics",
)
async def project_health_endpoint(body: ProjectHealthRequest, session: AsyncSession = Depends(get_session)):
    """Get project health metrics."""
    try:
        return await get_project_health(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Team Productivity ───────────────────────────────────────────────────────

@router.post(
    "/team-productivity",
    response_model=TeamProductivityResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get team productivity metrics",
)
async def team_productivity_endpoint(body: TeamProductivityRequest, session: AsyncSession = Depends(get_session)):
    """Get team productivity metrics."""
    try:
        return await get_team_productivity(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Engineering Metrics ─────────────────────────────────────────────────────

@router.post(
    "/engineering-metrics",
    response_model=EngineeringMetricsResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get engineering metrics",
)
async def engineering_metrics_endpoint(body: EngineeringMetricsRequest, session: AsyncSession = Depends(get_session)):
    """Get engineering metrics."""
    try:
        return await get_engineering_metrics(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Sprint Analytics ─────────────────────────────────────────────────────────

@router.post(
    "/sprint-analytics",
    response_model=SprintAnalyticsResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get sprint analytics",
)
async def sprint_analytics_endpoint(body: SprintAnalyticsRequest, session: AsyncSession = Depends(get_session)):
    """Get sprint analytics."""
    try:
        return await get_sprint_analytics(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Risk Dashboard ─────────────────────────────────────────────────────────

@router.post(
    "/risk-dashboard",
    response_model=RiskDashboardResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get risk dashboard",
)
async def risk_dashboard_endpoint(body: RiskDashboardRequest, session: AsyncSession = Depends(get_session)):
    """Get risk dashboard data."""
    try:
        return await get_risk_dashboard(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── AI Recommendations ─────────────────────────────────────────────────────

@router.post(
    "/recommendations",
    response_model=AIRecommendationsResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get AI recommendations",
)
async def recommendations_endpoint(body: AIRecommendationsRequest, session: AsyncSession = Depends(get_session)):
    """Get AI-powered recommendations."""
    try:
        return await get_ai_recommendations(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Cost Estimation ─────────────────────────────────────────────────────────

@router.post(
    "/cost-estimation",
    response_model=CostEstimationResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get cost estimation",
)
async def cost_estimation_endpoint(body: CostEstimationRequest, session: AsyncSession = Depends(get_session)):
    """Get cost estimation for projects."""
    try:
        return await get_cost_estimation(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Delivery Prediction ─────────────────────────────────────────────────────

@router.post(
    "/delivery-prediction",
    response_model=DeliveryPredictionResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get delivery prediction",
)
async def delivery_prediction_endpoint(body: DeliveryPredictionRequest, session: AsyncSession = Depends(get_session)):
    """Get delivery prediction for a project."""
    try:
        return await get_delivery_prediction(session, body)
    except Exception as exc:
        raise _error_response(exc)


# ── Executive Summary ───────────────────────────────────────────────────────

@router.post(
    "/summary",
    response_model=ExecutiveSummaryResponse,
    dependencies=[Depends(verify_internal_secret)],
    summary="Get executive summary",
)
async def executive_summary_endpoint(body: ExecutiveSummaryRequest, session: AsyncSession = Depends(get_session)):
    """Get executive summary for a period."""
    try:
        return await get_executive_summary(session, body)
    except Exception as exc:
        raise _error_response(exc)