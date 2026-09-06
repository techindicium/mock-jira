import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_schema_invalid_tool_input_surfaces_protocol_level_error(mcp_dual_server):  # BEH-4
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.call_tool("get_issue", {})  # missing required "issue_id"

    assert result.is_error is True
    assert result.content  # a message is present for the model to see


@pytest.mark.anyio
async def test_unreachable_upstream_surfaces_protocol_level_connection_error(  # BEH-5
    mcp_server_unreachable,
):
    async with connect(mcp_server_unreachable) as session:
        result = await session.call_tool("list_projects", {})

    assert result.is_error is True
    assert "Could not reach issue-tracker-api" in result.content[0].text
