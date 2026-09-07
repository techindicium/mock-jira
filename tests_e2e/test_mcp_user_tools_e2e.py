import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_create_and_list_users_match_real_http_state(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        create_result = await session.call_tool(
            "create_user",
            {"name": "MCP E2E User", "email": "mcp-e2e-user@example.com", "role": "engineer"},
        )
        assert create_result.is_error is False
        created = create_result.structured_content
        assert created["name"] == "MCP E2E User"

        list_result = await session.call_tool("list_users", {})
        assert list_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        http_users = http_client.get("/users").json()

    mcp_users = list_result.structured_content["result"]
    assert any(u["id"] == created["id"] for u in mcp_users)
    assert any(u["id"] == created["id"] for u in http_users)


@pytest.mark.anyio
async def test_create_user_duplicate_email_errors_with_verbatim_message(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        first = await session.call_tool(
            "create_user", {"name": "Dup User", "email": "mcp-e2e-dup@example.com"}
        )
        assert first.is_error is False

        second = await session.call_tool(
            "create_user", {"name": "Dup User Again", "email": "mcp-e2e-dup@example.com"}
        )

    assert second.is_error is True
    assert "already exists" in second.content[0].text


@pytest.mark.anyio
async def test_create_user_schema_invalid_input_surfaces_protocol_level_error(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.call_tool("create_user", {})  # missing required "name"

    assert result.is_error is True
    assert result.content  # a message is present for the model to see


@pytest.mark.anyio
async def test_user_tools_unreachable_api_errors_with_clear_message(mcp_server_unreachable):
    async with connect(mcp_server_unreachable) as session:
        result = await session.call_tool("list_users", {})

    assert result.is_error is True
    assert "Could not reach issue-tracker-api" in result.content[0].text
