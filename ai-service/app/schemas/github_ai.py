"""
GitHub AI Schemas
=================
Pydantic models for AI-powered GitHub integration.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.ai_module import AIContext


# ── Repository Indexing ─────────────────────────────────────────────────────────

class RepositoryIndexRequest(BaseModel):
    """Request to index a GitHub repository."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="main", description="Branch to index")
    include_issues: bool = Field(default=True, description="Include issues")
    include_prs: bool = Field(default=True, description="Include pull requests")
    include_commits: bool = Field(default=True, description="Include commits")


class RepositoryIndexResponse(BaseModel):
    """Response for repository indexing."""
    repository_id: str
    indexed_commits: int
    indexed_issues: int
    indexed_prs: int
    status: str


# ── Commit Analysis ───────────────────────────────────────────────────────────

class CommitAnalysisRequest(BaseModel):
    """Request to analyze a commit."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    commit_sha: str = Field(..., description="Commit SHA")


class CodeChange(BaseModel):
    """Represents a code change in a commit."""
    file_path: str
    change_type: str  # added, modified, deleted
    additions: int
    deletions: int
    impact_score: float = Field(ge=0.0, le=1.0)


class CommitAnalysisResponse(BaseModel):
    """Response for commit analysis."""
    commit_sha: str
    message: str
    author: str
    changes: List[CodeChange]
    impact_summary: str
    risk_level: str  # low, medium, high
    suggested_tests: List[str]


# ── AI Code Review ───────────────────────────────────────────────────────────

class CodeReviewRequest(BaseModel):
    """Request for AI code review."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="Pull request number")
    review_type: str = Field(default="full", description="Review type: full, security, performance")


class CodeIssue(BaseModel):
    """Represents a code issue found in review."""
    file_path: str
    line_number: int
    severity: str  # critical, high, medium, low
    issue_type: str  # bug, security, performance, style
    description: str
    suggestion: str


class CodeReviewResponse(BaseModel):
    """Response for AI code review."""
    pr_number: int
    issues: List[CodeIssue]
    summary: str
    overall_score: float = Field(ge=0.0, le=100.0)
    recommendations: List[str]


# ── Bug Detection ─────────────────────────────────────────────────────────────

class BugDetectionRequest(BaseModel):
    """Request for bug detection."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: Optional[int] = Field(None, description="PR number to analyze")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze")


class BugDetectionResponse(BaseModel):
    """Response for bug detection."""
    bugs: List[CodeIssue]
    risk_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


# ── Security Analysis ─────────────────────────────────────────────────────────

class SecurityAnalysisRequest(BaseModel):
    """Request for security analysis."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: Optional[int] = Field(None, description="PR number to analyze")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze")


class SecurityFinding(BaseModel):
    """Represents a security finding."""
    file_path: str
    line_number: int
    severity: str  # critical, high, medium, low
    vulnerability_type: str
    cwe_id: Optional[str]
    description: str
    remediation: str


class SecurityAnalysisResponse(BaseModel):
    """Response for security analysis."""
    findings: List[SecurityFinding]
    security_score: float = Field(ge=0.0, le=100.0)
    risk_level: str  # low, medium, high, critical


# ── Architecture Suggestions ─────────────────────────────────────────────────

class ArchitectureSuggestionRequest(BaseModel):
    """Request for architecture suggestions."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    focus_area: Optional[str] = Field(None, description="Specific area to focus on")


class ArchitectureSuggestionResponse(BaseModel):
    """Response for architecture suggestions."""
    suggestions: List[str]
    patterns: List[str]
    improvements: List[str]
    complexity_score: float = Field(ge=0.0, le=1.0)


# ── Documentation Updates ─────────────────────────────────────────────────────

class DocumentationUpdateRequest(BaseModel):
    """Request for documentation updates."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pr_number: int = Field(..., description="PR number")
    update_type: str = Field(default="api", description="Update type: api, readme, changelog")


class DocumentationUpdateResponse(BaseModel):
    """Response for documentation updates."""
    updated_files: List[str]
    suggestions: List[str]
    changelog_entry: Optional[str]


# ── Commit to Task Linking ────────────────────────────────────────────────────

class CommitTaskLinkRequest(BaseModel):
    """Request to link commits to tasks."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    commit_sha: str = Field(..., description="Commit SHA")


class CommitTaskLinkResponse(BaseModel):
    """Response for commit-task linking."""
    commit_sha: str
    linked_tasks: List[str]
    confidence_scores: dict


# ── Release Summary ───────────────────────────────────────────────────────────

class ReleaseSummaryRequest(BaseModel):
    """Request for release summary."""
    context: AIContext
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    tag: str = Field(..., description="Release tag")


class ReleaseSummaryResponse(BaseModel):
    """Response for release summary."""
    tag: str
    version: str
    features: List[str]
    bug_fixes: List[str]
    breaking_changes: List[str]
    contributors: List[str]
    summary: str