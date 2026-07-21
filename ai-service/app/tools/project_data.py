from __future__ import annotations

import httpx

from app.config import get_settings
from app.tools.registry import RegisteredTool, tool_registry
from app.tools.schemas import ProjectOverviewInput, ToolContext, ToolError, ToolResult


async def get_project_overview(
    payload: ProjectOverviewInput, context: ToolContext
) -> ToolResult:
    """Read one project through Django's internal, membership-checked endpoint."""
    project_id = payload.project_id or context.project_id
    if not project_id:
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError(
                code="project_context_required",
                message="Select a project before requesting project data.",
            ),
        )
    if context.project_id and project_id != context.project_id:
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError(
                code="project_scope_violation",
                message="The executor may only read the project selected for this chat.",
            ),
        )

    settings = get_settings()
    headers = {
        "X-Internal-Secret": settings.INTERNAL_SERVICE_SECRET,
        "X-Nexus-User-Id": context.user_id,
    }
    if context.org_id:
        headers["X-Nexus-Organization-Id"] = context.org_id

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                f"{settings.BACKEND_URL.rstrip('/')}/api/internal/projects/{project_id}/overview/",
                headers=headers,
            )
    except httpx.TimeoutException:
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError("backend_timeout", "Project data request timed out.", retryable=True),
        )
    except httpx.HTTPError:
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError("backend_unavailable", "Project data service is unavailable.", retryable=True),
        )

    if response.status_code in (401, 403, 404):
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError("project_not_available", "Project data is unavailable for this user."),
        )
    if response.is_error:
        return ToolResult(
            tool_name="get_project_overview",
            ok=False,
            error=ToolError("backend_error", "Project data service returned an error.", retryable=True),
        )

    return ToolResult(tool_name="get_project_overview", ok=True, data=response.json())


tool_registry.register(
    RegisteredTool(
        name="get_project_overview",
        description="Get the selected Nexus PM project's metadata and its tasks. Read-only.",
        input_model=ProjectOverviewInput,
        handler=get_project_overview,
    )
)
