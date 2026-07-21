"""
Tests for Executive Dashboard
=============================
Tests for company health, project metrics, and executive intelligence.
"""

import pytest
from unittest.mock import AsyncMock
from app.schemas.executive_dashboard import (
    CompanyHealthRequest,
    ProjectHealthRequest,
    TeamProductivityRequest,
    EngineeringMetricsRequest,
    SprintAnalyticsRequest,
    RiskDashboardRequest,
    AIRecommendationsRequest,
    CostEstimationRequest,
    DeliveryPredictionRequest,
    ExecutiveSummaryRequest,
)
from app.schemas.ai_module import AIContext
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


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def ai_context() -> AIContext:
    """Test AI context."""
    return AIContext(
        session_id="test-session",
        user_id="test-user",
        org_id="test-org",
        project_id="test-project",
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


# ── Company Health Tests ─────────────────────────────────────────────────────

class TestCompanyHealth:
    @pytest.mark.asyncio
    async def test_get_company_health(self, ai_context, mock_session):
        """Test company health metrics."""
        request = CompanyHealthRequest(context=ai_context)
        
        result = await get_company_health(mock_session, request)
        
        assert result.overall_score == 75.0
        assert result.risk_level == "medium"


# ── Project Health Tests ─────────────────────────────────────────────────────

class TestProjectHealth:
    @pytest.mark.asyncio
    async def test_get_project_health(self, ai_context, mock_session):
        """Test project health metrics."""
        request = ProjectHealthRequest(context=ai_context)
        
        result = await get_project_health(mock_session, request)
        
        assert result.health_score == 75.0
        assert len(result.risk_factors) > 0


# ── Team Productivity Tests ─────────────────────────────────────────────────

class TestTeamProductivity:
    @pytest.mark.asyncio
    async def test_get_team_productivity(self, ai_context, mock_session):
        """Test team productivity metrics."""
        request = TeamProductivityRequest(context=ai_context)
        
        result = await get_team_productivity(mock_session, request)
        
        assert result.average_velocity == 8.5
        assert len(result.members) > 0


# ── Engineering Metrics Tests ─────────────────────────────────────────────────

class TestEngineeringMetrics:
    @pytest.mark.asyncio
    async def test_get_engineering_metrics(self, ai_context, mock_session):
        """Test engineering metrics."""
        request = EngineeringMetricsRequest(context=ai_context)
        
        result = await get_engineering_metrics(mock_session, request)
        
        assert result.test_coverage == 0.78
        assert result.deployment_frequency == 5.0


# ── Sprint Analytics Tests ───────────────────────────────────────────────────

class TestSprintAnalytics:
    @pytest.mark.asyncio
    async def test_get_sprint_analytics(self, ai_context, mock_session):
        """Test sprint analytics."""
        request = SprintAnalyticsRequest(context=ai_context)
        
        result = await get_sprint_analytics(mock_session, request)
        
        assert result.current_sprint is not None
        assert result.current_sprint.velocity == 8.5


# ── Risk Dashboard Tests ─────────────────────────────────────────────────────

class TestRiskDashboard:
    @pytest.mark.asyncio
    async def test_get_risk_dashboard(self, ai_context, mock_session):
        """Test risk dashboard."""
        request = RiskDashboardRequest(context=ai_context)
        
        result = await get_risk_dashboard(mock_session, request)
        
        assert result.overall_risk_score == 35.0
        assert len(result.risks) > 0


# ── AI Recommendations Tests ─────────────────────────────────────────────────

class TestAIRecommendations:
    @pytest.mark.asyncio
    async def test_get_ai_recommendations(self, ai_context, mock_session):
        """Test AI recommendations."""
        request = AIRecommendationsRequest(context=ai_context)
        
        result = await get_ai_recommendations(mock_session, request)
        
        assert len(result.recommendations) > 0
        assert result.recommendations[0].impact_score == 0.85


# ── Cost Estimation Tests ───────────────────────────────────────────────────

class TestCostEstimation:
    @pytest.mark.asyncio
    async def test_get_cost_estimation(self, ai_context, mock_session):
        """Test cost estimation."""
        request = CostEstimationRequest(context=ai_context)
        
        result = await get_cost_estimation(mock_session, request)
        
        assert result.estimated_total == 50000.0
        assert result.confidence == 0.85


# ── Delivery Prediction Tests ─────────────────────────────────────────────────

class TestDeliveryPrediction:
    @pytest.mark.asyncio
    async def test_get_delivery_prediction(self, ai_context, mock_session):
        """Test delivery prediction."""
        request = DeliveryPredictionRequest(
            context=ai_context,
            project_id="proj-123",
        )
        
        result = await get_delivery_prediction(mock_session, request)
        
        assert result.confidence == 0.75
        assert len(result.factors) > 0


# ── Executive Summary Tests ─────────────────────────────────────────────────

class TestExecutiveSummary:
    @pytest.mark.asyncio
    async def test_get_executive_summary(self, ai_context, mock_session):
        """Test executive summary."""
        request = ExecutiveSummaryRequest(
            context=ai_context,
            period="weekly",
        )
        
        result = await get_executive_summary(mock_session, request)
        
        assert result.period == "weekly"
        assert len(result.highlights) > 0
        assert len(result.next_actions) > 0