"""
AI-Native Project Operating System Schemas
========================================
Pydantic models for AI agents in the Project Operating System.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.ai_module import AIContext


# ── AI Project Architect ─────────────────────────────────────────────────────

class ProjectArchitectRequest(BaseModel):
    """Request for AI Project Architect."""
    context: AIContext
    project_name: str
    description: str
    requirements: Optional[List[str]] = None


class ProjectArchitectureResponse(BaseModel):
    """Response from AI Project Architect."""
    architecture: str
    tech_stack: List[str]
    milestones: List[str]
    risks: List[str]


# ── AI CTO ───────────────────────────────────────────────────────────────────

class CTORequest(BaseModel):
    """Request for AI CTO."""
    context: AIContext
    question: str
    context_data: Optional[Dict[str, Any]] = None


class CTOResponse(BaseModel):
    """Response from AI CTO."""
    recommendation: str
    technical_decision: str
    implementation_plan: List[str]


# ── AI Project Manager ─────────────────────────────────────────────────────

class ProjectManagerRequest(BaseModel):
    """Request for AI Project Manager."""
    context: AIContext
    action: str  # plan, track, delegate, report
    details: Optional[Dict[str, Any]] = None


class ProjectManagerResponse(BaseModel):
    """Response from AI Project Manager."""
    status: str
    tasks: List[str]
    timeline: str
    next_steps: List[str]


# ── AI Developer Assistant ───────────────────────────────────────────────────

class DeveloperAssistantRequest(BaseModel):
    """Request for AI Developer Assistant."""
    context: AIContext
    task: str
    code_context: Optional[str] = None
    language: Optional[str] = None


class DeveloperAssistantResponse(BaseModel):
    """Response from AI Developer Assistant."""
    code: str
    explanation: str
    tests: Optional[str] = None


# ── AI QA Assistant ─────────────────────────────────────────────────────────

class QAAssistantRequest(BaseModel):
    """Request for AI QA Assistant."""
    context: AIContext
    code: str
    test_type: Optional[str] = "unit"


class QAAssistantResponse(BaseModel):
    """Response from AI QA Assistant."""
    test_cases: List[str]
    coverage: float
    suggestions: List[str]


# ── AI Meeting Intelligence ─────────────────────────────────────────────────

class MeetingIntelligenceRequest(BaseModel):
    """Request for AI Meeting Intelligence."""
    context: AIContext
    transcript: str
    participants: Optional[List[str]] = None


class ActionItem(BaseModel):
    """Action item from meeting."""
    task: str
    assignee: str
    due_date: Optional[str] = None


class MeetingIntelligenceResponse(BaseModel):
    """Response from AI Meeting Intelligence."""
    summary: str
    action_items: List[ActionItem]
    decisions: List[str]
    next_meeting: Optional[str] = None


# ── AI Knowledge Assistant ─────────────────────────────────────────────────

class KnowledgeAssistantRequest(BaseModel):
    """Request for AI Knowledge Assistant."""
    context: AIContext
    query: str
    project_id: Optional[str] = None


class KnowledgeAssistantResponse(BaseModel):
    """Response from AI Knowledge Assistant."""
    answer: str
    sources: List[str]
    related: List[str]


# ── AI Executive Assistant ─────────────────────────────────────────────────

class ExecutiveAssistantRequest(BaseModel):
    """Request for AI Executive Assistant."""
    context: AIContext
    report_type: str  # daily, weekly, monthly
    focus: Optional[str] = None


class ExecutiveAssistantResponse(BaseModel):
    """Response from AI Executive Assistant."""
    summary: str
    key_metrics: Dict[str, Any]
    recommendations: List[str]
    risks: List[str]


# ── AI Decision Support ─────────────────────────────────────────────────────

class DecisionSupportRequest(BaseModel):
    """Request for AI Decision Support."""
    context: AIContext
    decision_type: str
    options: List[str]
    criteria: Optional[List[str]] = None


class DecisionSupportResponse(BaseModel):
    """Response from AI Decision Support."""
    recommendation: str
    confidence: float
    pros_cons: Dict[str, List[str]]
    next_steps: List[str]


# ── Autonomous Workflow Engine ─────────────────────────────────────────────

class WorkflowEngineRequest(BaseModel):
    """Request for Autonomous Workflow Engine."""
    context: AIContext
    workflow_type: str
    trigger: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowEngineResponse(BaseModel):
    """Response from Autonomous Workflow Engine."""
    workflow_id: str
    status: str
    steps_completed: int
    total_steps: int
    result: Optional[Dict[str, Any]] = None


# ── Cross-Project Knowledge Sharing ─────────────────────────────────────────

class CrossProjectKnowledgeRequest(BaseModel):
    """Request for Cross-Project Knowledge Sharing."""
    context: AIContext
    source_project: str
    target_project: str
    knowledge_type: str  # patterns, solutions, risks, best_practices


class CrossProjectKnowledgeResponse(BaseModel):
    """Response from Cross-Project Knowledge Sharing."""
    shared_knowledge: List[str]
    patterns: List[str]
    recommendations: List[str]