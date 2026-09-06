import pytest

from tests_e2e.mcp_client import connect

_EXPECTED_TOOL_NAMES = {
    "list_projects",
    "create_project",
    "list_issues",
    "get_issue",
    "create_issue",
    "update_issue",
    "delete_issue",
}


@pytest.mark.anyio
async def test_real_client_discovers_all_seven_tools_with_correct_schemas(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.list_tools()

    names = {tool.name for tool in result.tools}
    assert names == _EXPECTED_TOOL_NAMES

    by_name = {tool.name: tool for tool in result.tools}
    assert set(by_name["create_project"].input_schema["required"]) == {"key", "name"}
    assert set(by_name["get_issue"].input_schema["required"]) == {"issue_id"}
    assert set(by_name["create_issue"].input_schema["required"]) >= {
        "project_id", "summary", "issue_type", "priority",
    }
    assert "issue_id" not in by_name.get("list_issues").input_schema.get("required", [])
