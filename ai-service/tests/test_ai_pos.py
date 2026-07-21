"""
Tests for AI-Native Project Operating System
============================================
Tests for AI agents in the Project Operating System.
"""

import pytest
from unittest.mock import AsyncMock
from app.schemas.ai_pos import (
    ProjectArchitectRequest,
    CTORequest,
    ProjectManagerRequest,
    DeveloperAssistantRequest,
    QAAssistantRequest,
    MeetingIntelligenceRequest,
    KnowledgeAssistantRequest,
    ExecutiveAssistantRequest,
    DecisionSupportRequest,
    WorkflowEngineRequest,
    CrossProjectKnowledgeRequest,
)
from app.schemas.ai_module import AIContext
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


# ── AI Project Architect Tests ─────────────────────────────────────────────

class TestProjectArchitect:
    @pytest.mark.asyncio
    async def test_project_architect(self, ai_context, mock_session):
        """Test AI Project Architect."""
        request = ProjectArchitectRequest(
            context=ai_context,
            project_name="Test Project",
            description="A test project",
        )
        
        result = await project_architect(mock_session, request)
        
        assert "Microservices" in result.architecture
        assert len(result.tech_stack) > 0


# ── AI CTO Tests ───────────────────────────────────────────────────────────

class TestCTO:
    @pytest.mark.asyncio
    async def test_ai_cto(self, ai_context, mock_session):
        """Test AI CTO."""
        request = CTORequest(
            context=ai_context,
            question="What architecture should we use?",
        )
        
        result = await ai_cto(mock_session, request)
        
        assert "cloud-native" in result.recommendation.lower()
        assert len(result.implementation_plan) > 0


# ── AI Project Manager Tests ─────────────────────────────────────────────

class TestProjectManager:
    @pytest.mark.asyncio
    async def test_ai_project_manager(self, ai_context, mock_session):
        """Test AI Project Manager."""
        request = ProjectManagerRequest(
            context=ai_context,
            action="plan",
        )
        
        result = await ai_project_manager(mock_session, request)
        
        assert result.status == "in_progress"
        assert len(result.tasks) > 0


# ── AI Developer Assistant Tests ───────────────────────────────────────────

class TestDeveloperAssistant:
    @pytest.mark.asyncio
    async def test_ai_developer_assistant(self, ai_context, mock_session):
        """Test AI Developer Assistant."""
        request = DeveloperAssistantRequest(
            context=ai_context,
            task="Create a login function",
        )
        
        result = await ai_developer_assistant(mock_session, request)
        
        assert "def" in result.code
        assert result.explanation


# ── AI QA Assistant Tests ─────────────────────────────────────────────────

class TestQAAssistant:
    @pytest.mark.asyncio
    async def test_ai_qa_assistant(self, ai_context, mock_session):
        """Test AI QA Assistant."""
        request = QAAssistantRequest(
            context=ai_context,
            code="def test():\n    pass",
        )
        
        result = await ai_qa_assistant(mock_session, request)
        
        assert result.coverage > 0
        assert len(result.test_cases) > 0


# ── AI Meeting Intelligence Tests ─────────────────────────────────────────

class TestMeetingIntelligence:
    @pytest.mark.asyncio
    async def test_ai_meeting_intelligence(self, ai_context, mock_session):
        """Test AI Meeting Intelligence."""
        request = MeetingIntelligenceRequest(
            context=ai_context,
            transcript="Meeting transcript...",
        )
        
        result = await ai_meeting_intelligence(mock_session, request)
        
        assert result.summary
        assert len(result.action_items) > 0


# ── AI Knowledge Assistant Tests ─────────────────────────────────────────

class TestKnowledgeAssistant:
    @pytest.mark.asyncio
    async def test_ai_knowledge_assistant(self, ai_context, mock_session):
        """Test AI Knowledge Assistant."""
        request = KnowledgeAssistantRequest(
            context=ai_context,
            query="How to deploy?",
        )
        
        result = await ai_knowledge_assistant(mock_session, request)
        
        assert result.answer
        assert len(result.sources) > 0


# ── AI Executive Assistant Tests ───────────────────────────────────────────

class TestExecutiveAssistant:
    @pytest.mark.asyncio
    async def test_ai_executive_assistant(self, ai_context, mock_session):
        """Test AI Executive Assistant."""
        request = ExecutiveAssistantRequest(
            context=ai_context,
            report_type="weekly",
        )
        
        result = await ai_executive_assistant(mock_session, request)
        
        assert "weekly" in result.summary.lower()
        assert len(result.recommendations) > 0


# ── AI Decision Support Tests ─────────────────────────────────────────────

class TestDecisionSupport:
    @pytest.mark.asyncio
    async def test_ai_decision_support(self, ai_context, mock_session):
        """Test AI Decision Support."""
        request = DecisionSupportRequest(
            context=ai_context,
            decision_type="tech_stack",
            options=["Python", "Node.js", "Go"],
        )
        
        result = await ai_decision_support(mock_session, request)
        
        assert result.confidence > 0
        assert len(result.pros_cons) > 0


# ── Autonomous Workflow Engine Tests ─────────────────────────────────────

class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_autonomous_workflow_engine(self, ai_context, mock_session):
        """Test Autonomous Workflow Engine."""
        request = WorkflowEngineRequest(
            context=ai_context,
            workflow_type="deployment",
            trigger="manual",
        )
        
        result = await autonomous_workflow_engine(mock_session, request)
        
        assert result.status == "running"
        assert result.steps_completed > 0


# ── Cross-Project Knowledge Tests ─────────────────────────────────────────

class TestCrossProjectKnowledge:
    @pytest.mark.asyncio
    async def test_cross_project_knowledge(self, ai_context, mock_session):
        """Test Cross-Project Knowledge Sharing."""
        request = CrossProjectKnowledgeRequest(
            context=ai_context,
            source_project="proj-1",
            target_project="proj-2",
            knowledge_type="patterns",
        )
        
        result = await cross_project_knowledge(mock_session, request)
        
        assert len(result.shared_knowledge) > 0
        assert len(result.patterns) > 0