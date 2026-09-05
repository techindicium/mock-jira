from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_projects() -> list[dict]:
    """List all Projects known to issue-tracker-api."""
    client = _client()
    try:
        return await client.list_projects()
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
