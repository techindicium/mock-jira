import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_create_and_list_projects_match_real_http_state(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        create_result = await session.call_tool(
            "create_project", {"key": "MCPE2E", "name": "MCP E2E Project"}
        )
        assert create_result.is_error is False
        created = create_result.structured_content
        assert created["key"] == "MCPE2E"

        list_result = await session.call_tool("list_projects", {})
        assert list_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        http_projects = http_client.get("/projects").json()

    mcp_projects = list_result.structured_content["result"]
    assert any(p["key"] == "MCPE2E" for p in mcp_projects)
    assert {p["id"] for p in mcp_projects} == {p["id"] for p in http_projects}
    assert any(p["id"] == created["id"] for p in http_projects)
