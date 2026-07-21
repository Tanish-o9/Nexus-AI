import pytest

from app.tools import tool_registry
from app.tools.project_data import get_project_overview
from app.tools.schemas import ProjectOverviewInput, ToolContext


def test_tool_registry_exposes_only_typed_tools():
    definitions = tool_registry.definitions()
    names = {definition["function"]["name"] for definition in definitions}
    assert names == {"get_project_overview", "search_github_issues"}
    assert all(definition["function"]["parameters"]["type"] == "object" for definition in definitions)


@pytest.mark.asyncio
async def test_unknown_tool_is_returned_as_structured_error():
    result = await tool_registry.execute("delete_everything", {}, ToolContext(user_id="user-1"))
    assert not result.ok
    assert result.error.code == "unknown_tool"


@pytest.mark.asyncio
async def test_invalid_tool_arguments_do_not_raise():
    result = await tool_registry.execute(
        "search_github_issues", {"repository": "not-a-repository"}, ToolContext(user_id="user-1")
    )
    assert not result.ok
    assert result.error.code == "invalid_arguments"


@pytest.mark.asyncio
async def test_project_tool_rejects_cross_project_request_before_http():
    result = await get_project_overview(
        ProjectOverviewInput(project_id="project-b"),
        ToolContext(user_id="user-1", project_id="project-a"),
    )
    assert not result.ok
    assert result.error.code == "project_scope_violation"
