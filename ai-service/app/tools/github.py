from __future__ import annotations

import httpx

from app.config import get_settings
from app.tools.registry import RegisteredTool, tool_registry
from app.tools.schemas import GitHubIssuesInput, ToolContext, ToolError, ToolResult


async def search_github_issues(payload: GitHubIssuesInput, context: ToolContext) -> ToolResult:
    """Read issues from one GitHub repository; mutations are deliberately unsupported."""
    settings = get_settings()
    if not settings.GITHUB_TOKEN:
        return ToolResult(
            tool_name="search_github_issues",
            ok=False,
            error=ToolError("github_not_configured", "GitHub integration is not configured."),
        )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    params = {"state": payload.state, "per_page": payload.limit}
    if payload.query:
        params["q"] = f"repo:{payload.repository} is:issue {payload.query}"
        url = "https://api.github.com/search/issues"
    else:
        url = f"https://api.github.com/repos/{payload.repository}/issues"

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=headers, params=params)
    except httpx.TimeoutException:
        return ToolResult(
            tool_name="search_github_issues", ok=False,
            error=ToolError(code="github_timeout", message="GitHub timed out.", retryable=True),
        )
    except httpx.HTTPError:
        return ToolResult(
            tool_name="search_github_issues", ok=False,
            error=ToolError(code="github_unavailable", message="GitHub is unavailable.", retryable=True),
        )

    if response.status_code in (401, 403, 404):
        return ToolResult(
            tool_name="search_github_issues", ok=False,
            error=ToolError(code="github_not_available", message="Repository data is unavailable."),
        )
    if response.is_error:
        return ToolResult(
            tool_name="search_github_issues", ok=False,
            error=ToolError(code="github_error", message="GitHub returned an error.", retryable=True),
        )

    body = response.json()
    issues = body["items"] if isinstance(body, dict) else body
    return ToolResult(
        tool_name="search_github_issues",
        ok=True,
        data=[
            {"number": issue["number"], "title": issue["title"], "state": issue["state"], "url": issue["html_url"]}
            for issue in issues[:payload.limit]
            if "pull_request" not in issue
        ],
    )


tool_registry.register(
    RegisteredTool(
        name="search_github_issues",
        description="Search open, closed, or all issues in a GitHub repository. Read-only.",
        input_model=GitHubIssuesInput,
        handler=search_github_issues,
    )
)
