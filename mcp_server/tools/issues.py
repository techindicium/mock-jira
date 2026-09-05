from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_issues(project_id: int | None = None, status: str | None = None) -> list[dict]:
    """List Issues known to issue-tracker-api, optionally filtered by project_id and/or status."""
    client = _client()
    try:
        return await client.list_issues(project_id, status)
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def get_issue(issue_id: int) -> dict[str, Any]:
    """Fetch one Issue by id from issue-tracker-api."""
    client = _client()
    try:
        return await client.get_issue(issue_id)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
