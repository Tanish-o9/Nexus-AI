"""
Tests for GitHub AI Integration
================================
Tests for repository indexing, code review, bug detection, and security analysis.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.schemas.github_ai import (
    RepositoryIndexRequest,
    CommitAnalysisRequest,
    CodeReviewRequest,
    BugDetectionRequest,
    SecurityAnalysisRequest,
    ArchitectureSuggestionRequest,
    DocumentationUpdateRequest,
    CommitTaskLinkRequest,
    ReleaseSummaryRequest,
)
from app.schemas.ai_module import AIContext
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


# ── Repository Indexing Tests ─────────────────────────────────────────────────

class TestRepositoryIndexing:
    @pytest.mark.asyncio
    async def test_index_repository(self, ai_context, mock_session):
        """Test repository indexing."""
        request = RepositoryIndexRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
        )
        
        result = await index_repository(mock_session, request)
        
        assert result.repository_id == "octocat/hello-world"
        assert result.status == "indexed"


# ── Commit Analysis Tests ─────────────────────────────────────────────────────

class TestCommitAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_commit(self, ai_context, mock_session):
        """Test commit analysis."""
        request = CommitAnalysisRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            commit_sha="abc123",
        )
        
        result = await analyze_commit(mock_session, request)
        
        assert result.commit_sha == "abc123"
        assert result.risk_level == "low"


# ── Code Review Tests ─────────────────────────────────────────────────────────

class TestCodeReview:
    @pytest.mark.asyncio
    async def test_ai_code_review(self, ai_context, mock_session):
        """Test AI code review."""
        request = CodeReviewRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            pr_number=1,
        )
        
        result = await ai_code_review(mock_session, request)
        
        assert result.pr_number == 1
        assert result.overall_score == 85.0


# ── Bug Detection Tests ─────────────────────────────────────────────────────────

class TestBugDetection:
    @pytest.mark.asyncio
    async def test_detect_bugs(self, ai_context, mock_session):
        """Test bug detection."""
        request = BugDetectionRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            pr_number=1,
        )
        
        result = await detect_bugs(mock_session, request)
        
        assert result.risk_score == 0.1
        assert result.confidence == 0.9


# ── Security Analysis Tests ───────────────────────────────────────────────────

class TestSecurityAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_security(self, ai_context, mock_session):
        """Test security analysis."""
        request = SecurityAnalysisRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            pr_number=1,
        )
        
        result = await analyze_security(mock_session, request)
        
        assert result.security_score == 95.0
        assert result.risk_level == "low"


# ── Architecture Suggestion Tests ─────────────────────────────────────────────

class TestArchitectureSuggestions:
    @pytest.mark.asyncio
    async def test_suggest_architecture(self, ai_context, mock_session):
        """Test architecture suggestions."""
        request = ArchitectureSuggestionRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
        )
        
        result = await suggest_architecture(mock_session, request)
        
        assert len(result.suggestions) > 0
        assert result.complexity_score == 0.5


# ── Documentation Update Tests ─────────────────────────────────────────────────

class TestDocumentationUpdates:
    @pytest.mark.asyncio
    async def test_update_documentation(self, ai_context, mock_session):
        """Test documentation updates."""
        request = DocumentationUpdateRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            pr_number=1,
        )
        
        result = await update_documentation(mock_session, request)
        
        assert "README.md" in result.updated_files


# ── Commit Task Linking Tests ─────────────────────────────────────────────────

class TestCommitTaskLinking:
    @pytest.mark.asyncio
    async def test_link_commit_to_task(self, ai_context, mock_session):
        """Test commit to task linking."""
        request = CommitTaskLinkRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            commit_sha="abc123",
        )
        
        result = await link_commit_to_task(mock_session, request)
        
        assert result.commit_sha == "abc123"


# ── Release Summary Tests ─────────────────────────────────────────────────────

class TestReleaseSummary:
    @pytest.mark.asyncio
    async def test_generate_release_summary(self, ai_context, mock_session):
        """Test release summary generation."""
        request = ReleaseSummaryRequest(
            context=ai_context,
            owner="octocat",
            repo="hello-world",
            tag="v1.0.0",
        )
        
        result = await generate_release_summary(mock_session, request)
        
        assert result.tag == "v1.0.0"
        assert len(result.features) > 0