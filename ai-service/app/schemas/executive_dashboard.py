"""
Executive Dashboard Schemas
===========================
Pydantic models for executive intelligence dashboard.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.ai_module import AIContext


# ── Company Health ───────────────────────────────────────────────────────────

class CompanyHealthRequest(BaseModel):
    """Request for company health metrics."""
    context: AIContext


class CompanyHealthResponse(BaseModel):
    """Response for company health metrics."""
    overall_score: float = Field(ge=0.0, le=100.0)
    project_velocity: float
    team_productivity: float
    risk_level: str  # low, medium, high
    health_trend: str  # improving, stable, declining


# ── Project Health ───────────────────────────────────────────────────────────

class ProjectHealthRequest(BaseModel):
    """Request for project health metrics."""
    context: AIContext


class ProjectHealthResponse(BaseModel):
    """Response for project health metrics."""
    project_id: str
    health_score: float = Field(ge=0.0, le=100.0)
    completion_rate: float
    velocity: float
    risk_factors: List[str]
    recommendations: List[str]


# ── Team Productivity ───────────────────────────────────────────────────────

class TeamProductivityRequest(BaseModel):
    """Request for team productivity metrics."""
    context: AIContext


class TeamMemberProductivity(BaseModel):
    """Productivity metrics for a team member."""
    user_id: str
    tasks_completed: int
    velocity: float
    focus_time: float
    collaboration_score: float


class TeamProductivityResponse(BaseModel):
    """Response for team productivity metrics."""
    team_id: str
    average_velocity: float
    total_tasks: int
    members: List[TeamMemberProductivity]
    bottlenecks: List[str]


# ── Engineering Metrics ─────────────────────────────────────────────────────

class EngineeringMetricsRequest(BaseModel):
    """Request for engineering metrics."""
    context: AIContext


class EngineeringMetricsResponse(BaseModel):
    """Response for engineering metrics."""
    code_churn: float
    test_coverage: float
    deployment_frequency: float
    lead_time: float
    mttr: float  # Mean time to recovery


# ── Sprint Analytics ─────────────────────────────────────────────────────────

class SprintAnalyticsRequest(BaseModel):
    """Request for sprint analytics."""
    context: AIContext
    sprint_id: Optional[str] = None


class SprintMetrics(BaseModel):
    """Metrics for a sprint."""
    sprint_id: str
    planned_points: int
    completed_points: int
    velocity: float
    burndown_rate: float


class SprintAnalyticsResponse(BaseModel):
    """Response for sprint analytics."""
    current_sprint: Optional[SprintMetrics]
    previous_sprints: List[SprintMetrics]
    predictions: dict


# ── Risk Dashboard ─────────────────────────────────────────────────────────

class RiskDashboardRequest(BaseModel):
    """Request for risk dashboard."""
    context: AIContext


class RiskItem(BaseModel):
    """Represents a risk item."""
    id: str
    type: str  # technical, resource, schedule, quality
    severity: str  # low, medium, high, critical
    description: str
    mitigation: str


class RiskDashboardResponse(BaseModel):
    """Response for risk dashboard."""
    risks: List[RiskItem]
    overall_risk_score: float = Field(ge=0.0, le=100.0)
    risk_trend: str


# ── AI Recommendations ─────────────────────────────────────────────────────

class AIRecommendationsRequest(BaseModel):
    """Request for AI recommendations."""
    context: AIContext


class Recommendation(BaseModel):
    """AI recommendation."""
    id: str
    category: str  # process, technical, resource, timeline
    priority: str  # low, medium, high
    title: str
    description: str
    impact_score: float = Field(ge=0.0, le=1.0)


class AIRecommendationsResponse(BaseModel):
    """Response for AI recommendations."""
    recommendations: List[Recommendation]


# ── Cost Estimation ─────────────────────────────────────────────────────────

class CostEstimationRequest(BaseModel):
    """Request for cost estimation."""
    context: AIContext
    project_id: Optional[str] = None


class CostBreakdown(BaseModel):
    """Cost breakdown for a project."""
    development: float
    testing: float
    infrastructure: float
    overhead: float


class CostEstimationResponse(BaseModel):
    """Response for cost estimation."""
    estimated_total: float
    breakdown: CostBreakdown
    confidence: float = Field(ge=0.0, le=1.0)


# ── Delivery Prediction ─────────────────────────────────────────────────────

class DeliveryPredictionRequest(BaseModel):
    """Request for delivery prediction."""
    context: AIContext
    project_id: str


class DeliveryPredictionResponse(BaseModel):
    """Response for delivery prediction."""
    predicted_completion: str
    confidence: float = Field(ge=0.0, le=1.0)
    risk_adjusted_date: str
    factors: List[str]


# ── Executive Summary ───────────────────────────────────────────────────────

class ExecutiveSummaryRequest(BaseModel):
    """Request for executive summary."""
    context: AIContext
    period: str = Field(default="weekly", description="Summary period: daily, weekly, monthly")


class ExecutiveSummaryResponse(BaseModel):
    """Response for executive summary."""
    period: str
    summary: str
    key_metrics: dict
    highlights: List[str]
    concerns: List[str]
    next_actions: List[str]