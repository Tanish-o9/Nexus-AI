from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolContext(BaseModel):
    """Request-scoped identity supplied by the graph, never by the LLM."""

    user_id: str
    org_id: str | None = None
    project_id: str | None = None


class ProjectOverviewInput(BaseModel):
    project_id: str | None = Field(
        default=None,
        description="Project UUID. Omit to use the project already selected in this chat.",
    )


class GitHubIssuesInput(BaseModel):
    repository: str = Field(
        ..., pattern=r"^[\w.-]+/[\w.-]+$", description="GitHub repository as owner/name."
    )
    query: str | None = Field(default=None, max_length=200, description="Optional issue search text.")
    state: Literal["open", "closed", "all"] = "open"
    limit: int = Field(default=10, ge=1, le=25)


class ToolError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class ToolResult(BaseModel):
    tool_name: str
    ok: bool
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: ToolError | None = None

    def to_model_content(self) -> str:
        """Compact, JSON-safe response injected into the next model turn."""
        return self.model_dump_json(exclude_none=True)
