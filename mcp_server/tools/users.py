from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_users() -> list[dict]:
    """List all Users known to issue-tracker-api."""
    client = _client()
    try:
        return await client.list_users()
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_user(name: str, email: str | None = None, role: str | None = None) -> dict[str, Any]:
    """Create a User in issue-tracker-api.

    `role` is a free-text string at the tool boundary — this tool declares no enum for it and
    delegates all value validation to issue-tracker-api's POST /users verbatim (same delegation
    posture as create_issue's issue_type/priority). An invalid role, if the API ever rejects one,
    surfaces as the existing 422 MCP_UPSTREAM_ERROR case, not a distinct error code.
    """
    client = _client()
    try:
        return await client.create_user(name, email, role)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
