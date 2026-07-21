"""
AI Module Schemas
=================
Request/Response models for all AI module features.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# ── Shared ─────────────────────────────────────────────────────────────────────

class AIContext(BaseModel):
    """Context passed to every AI feature call."""
    session_id: str
    user_id: str
    org_id: str | None = None
    project_id: str | None = None


# ── Task Breakdown ─────────────────────────────────────────────────────────────

class TaskBreakdownRequest(BaseModel):
    context: AIContext
    task_description: str = Field(..., min_length=10, max_length=5000)
    include_estimated_hours: bool = False
    format: Literal["markdown", "json"] = "markdown"


class TaskBreakdownItem(BaseModel):
    title: str
    description: str
    estimated_hours: float | None = None
    dependencies: list[str] = []
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    assignee_suggestion: str | None = None


class TaskBreakdownResponse(BaseModel):
    task_summary: str
    subtasks: list[TaskBreakdownItem]
    total_estimated_hours: float | None = None
    notes: str = ""


# ── Sprint Planning ────────────────────────────────────────────────────────────

class SprintGoal(BaseModel):
    title: str
    description: str
    tasks: list[str]


class SprintPlanningRequest(BaseModel):
    context: AIContext
    sprint_duration_days: int = Field(default=14, ge=1, le=30)
    team_capacity_hours: float | None = Field(default=None, ge=0, description="Total team hours available")
    backlog_items: list[str] = Field(default_factory=list, description="Backlog item IDs or titles")
    focus_area: str | None = Field(default=None, description="Optional focus area for the sprint")


class SprintPlanningResponse(BaseModel):
    sprint_goals: list[SprintGoal]
    recommended_velocity: str
    risk_factors: list[str]
    capacity_utilization: str
    notes: str = ""


# ── Project Summary ────────────────────────────────────────────────────────────

class ProjectSummaryRequest(BaseModel):
    context: AIContext
    include_recent_activity: bool = True
    focus_areas: list[str] = Field(default_factory=list, description="Specific areas to focus on")


class ProjectSummaryResponse(BaseModel):
    overview: str
    status: Literal["on_track", "at_risk", "blocked", "unknown"]
    recent_activity: str = ""
    open_risks: list[str] = []
    next_milestones: list[str] = []
    health_metrics: dict[str, Any] = Field(default_factory=dict)
    summary: str


# ── Documentation Q&A (RAG) ────────────────────────────────────────────────────

class DocQARequest(BaseModel):
    context: AIContext
    question: str = Field(..., min_length=5, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = True


class DocQAResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    follow_up_questions: list[str] = Field(default_factory=list)


# ── Meeting Summary ────────────────────────────────────────────────────────────

class MeetingSummaryRequest(BaseModel):
    context: AIContext
    meeting_notes: str = Field(..., min_length=50, max_length=30000)
    meeting_type: Literal["standup", "sprint_planning", "retrospective", "general"] = "general"


class ActionItem(BaseModel):
    owner: str
    task: str
    deadline: str | None = None


class MeetingSummaryResponse(BaseModel):
    title: str
    date: date
    attendees_summary: str = ""
    key_discussion_points: list[str]
    decisions: list[str] = []
    action_items: list[ActionItem]
    next_steps: list[str]
    full_summary: str


# ── PR Review ──────────────────────────────────────────────────────────────────

class PRReviewRequest(BaseModel):
    context: AIContext
    repository: str = Field(..., pattern=r"^[\w.-]+/[\w.-]+$")
    pr_number: int = Field(..., ge=1)
    review_focus: list[str] = Field(default_factory=list, description="Areas to focus on: security, performance, style, logic")


class PRReviewResponse(BaseModel):
    summary: str
    code_quality_issues: list[str] = []
    security_concerns: list[str] = []
    performance_notes: list[str] = []
    suggested_improvements: list[str] = []
    overall_assessment: Literal["approved", "changes_requested", "needs_discussion"]


# ── Bug Explanation ─────────────────────────────────────────────────────────────

class BugExplanationRequest(BaseModel):
    context: AIContext
    code_snippet: str | None = Field(default=None, description="Source code or stack trace")
    error_message: str | None = Field(default=None, description="Error message or bug description")
    behavior_description: str | None = Field(default=None, description="What happened vs expected")
    language: str = "python"
    project_context: str | None = Field(default=None, description="Additional project context")


class BugExplanationResponse(BaseModel):
    root_cause: str
    explanation: str
    suggested_fix: str
    severity: Literal["critical", "high", "medium", "low"]
    related_files: list[str] = []
    prevention_tips: list[str] = []


# ── Deadline Prediction ────────────────────────────────────────────────────────

class DeadlinePredictionRequest(BaseModel):
    context: AIContext
    task_ids: list[str] = Field(default_factory=list, description="Specific tasks to predict deadlines for")
    include_all_pending: bool = False
    assumptions: list[str] = Field(default_factory=list)


class TaskDeadlinePrediction(BaseModel):
    task_id: str
    task_title: str
    predicted_completion_date: date
    confidence: Literal["high", "medium", "low"]
    risk_factors: list[str] = []


class DeadlinePredictionResponse(BaseModel):
    predictions: list[TaskDeadlinePrediction]
    overall_risk: Literal["on_track", "at_risk", "behind"]
    methodology: str
    notes: str = ""


# ── Risk Analysis ──────────────────────────────────────────────────────────────

class RiskAnalysisRequest(BaseModel):
    context: AIContext
    focus_areas: list[str] = Field(default_factory=list)
    include_mitigation: bool = True


class RiskItem(BaseModel):
    risk: str
    probability: Literal["high", "medium", "low"]
    impact: Literal["high", "medium", "low"]
    mitigation: str = ""
    owner: str = ""


class RiskAnalysisResponse(BaseModel):
    summary: str
    risks: list[RiskItem]
    top_priority: str
    overall_health: Literal["healthy", "caution", "critical"]
    recommendations: list[str] = []


# ── Workload Suggestion ────────────────────────────────────────────────────────

class TeamMember(BaseModel):
    name: str
    current_load: float = Field(default=0.0, ge=0, description="Current workload percentage")
    skills: list[str] = Field(default_factory=list)


class WorkloadSuggestionRequest(BaseModel):
    context: AIContext
    team_members: list[TeamMember]
    upcoming_tasks: list[str] = Field(default_factory=list, description="Tasks to distribute")
    consider_skills: bool = True
    balance_factor: float = Field(default=0.8, ge=0, le=1, description="0=optimize for speed, 1=optimize for balance")


class WorkloadAssignment(BaseModel):
    task: str
    assignee: str
    rationale: str
    estimated_hours: float | None = None


class WorkloadSuggestionResponse(BaseModel):
    assignments: list[WorkloadAssignment]
    team_utilization: dict[str, float]
    recommendations: list[str] = []
    summary: str


# ── Daily Standup Summary ────────────────────────────────────────────────────────

class StandupSummaryRequest(BaseModel):
    context: AIContext
    team_updates: list[str] = Field(..., min_length=1, description="Team member updates")
    include_blockers: bool = True
    include_action_items: bool = True


class StandupSummaryResponse(BaseModel):
    summary: str
    blockers: list[str] = []
    action_items: list[ActionItem] = []
    team_morale: str = ""
    sprint_health: str = ""


# ── Weekly Project Summary ──────────────────────────────────────────────────────

class WeeklySummaryRequest(BaseModel):
    context: AIContext
    week_start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    include_metrics: bool = True
    include_highlights: bool = True
    include_challenges: bool = True


class WeeklySummaryResponse(BaseModel):
    week_summary: str
    key_achievements: list[str] = []
    challenges_faced: list[str] = []
    metrics: dict[str, Any] = Field(default_factory=dict)
    next_week_priorities: list[str] = []
    overall_sentiment: str = ""


# ── Release Notes Generator ─────────────────────────────────────────────────────

class ReleaseNotesRequest(BaseModel):
    context: AIContext
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    commits: list[str] = Field(..., min_length=1, description="List of commit messages or PR titles")
    include_footer: bool = True
    include_breaking_changes: bool = True


class ReleaseNotesResponse(BaseModel):
    version: str
    release_date: str
    summary: str
    features: list[str] = []
    bug_fixes: list[str] = []
    breaking_changes: list[str] = []
    known_issues: list[str] = []
    upgrade_notes: str = ""


# ── Smart Task Assignment ───────────────────────────────────────────────────────

class SmartTaskAssignmentRequest(BaseModel):
    context: AIContext
    task_description: str = Field(..., min_length=10, max_length=2000)
    required_skills: list[str] = Field(default_factory=list)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    deadline: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class SmartTaskAssignmentResponse(BaseModel):
    recommended_assignee: str
    confidence: Literal["high", "medium", "low"]
    rationale: str
    alternative_assignees: list[str] = []
    required_skills_match: dict[str, bool] = Field(default_factory=dict)
    workload_impact: str = ""


# ── Duplicate Task Detection ────────────────────────────────────────────────────

class DuplicateTaskDetectionRequest(BaseModel):
    context: AIContext
    new_task_description: str = Field(..., min_length=10, max_length=2000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class DuplicateTaskResponse(BaseModel):
    is_duplicate: bool
    similar_tasks: list[dict[str, Any]] = Field(default_factory=list)
    similarity_scores: list[float] = Field(default_factory=list)
    recommendation: str = ""


# ── Project Health Score ────────────────────────────────────────────────────────

class ProjectHealthScoreRequest(BaseModel):
    context: AIContext
    include_detailed_breakdown: bool = True


class ProjectHealthScoreResponse(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Health score from 0-100")
    health_status: Literal["excellent", "good", "fair", "poor", "critical"]
    breakdown: dict[str, float] = Field(default_factory=dict, description="Scores by category")
    recommendations: list[str] = []
    risk_factors: list[str] = []
    summary: str = ""