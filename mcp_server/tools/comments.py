from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_issue_comments(issue_id: int) -> list[dict]:
    """List an Issue's Comments, chronologically, from issue-tracker-api."""
    client = _client()
    try:
        return await client.list_comments(issue_id)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_issue_comment(issue_id: int, body: str) -> dict[str, Any]:
    """Add a Comment to an Issue in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_comment(issue_id, body)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
