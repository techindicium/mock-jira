import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_full_issue_lifecycle_over_real_mcp_protocol_cross_verified(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        project_result = await session.call_tool(
            "create_project", {"key": "MCPE2EI", "name": "MCP E2E Issue Project"}
        )
        project_id = project_result.structured_content["id"]

        created_result = await session.call_tool(
            "create_issue",
            {
                "project_id": project_id, "summary": "mcp e2e issue",
                "issue_type": "task", "priority": "medium",
            },
        )
        assert created_result.is_error is False
        issue_id = created_result.structured_content["id"]

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        assert http_client.get(f"/issues/{issue_id}").status_code == 200

    async with connect(mcp_base_url) as session:
        list_result = await session.call_tool("list_issues", {"project_id": project_id})
        assert any(i["id"] == issue_id for i in list_result.structured_content["result"])

        get_result = await session.call_tool("get_issue", {"issue_id": issue_id})
        assert get_result.structured_content["id"] == issue_id

        update_result = await session.call_tool(
            "update_issue", {"issue_id": issue_id, "status": "in_progress"}
        )
        assert update_result.structured_content["status"] == "in_progress"

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        assert http_client.get(f"/issues/{issue_id}").json()["status"] == "in_progress"

    async with connect(mcp_base_url) as session:
        delete_result = await session.call_tool("delete_issue", {"issue_id": issue_id})
        assert delete_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        gone_resp = http_client.get(f"/issues/{issue_id}")
        assert gone_resp.status_code == 404
