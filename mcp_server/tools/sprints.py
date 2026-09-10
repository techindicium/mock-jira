from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_sprints(project_id: int) -> list[dict]:
    """List Sprints under a Project in issue-tracker-api."""
    client = _client()
    try:
        return await client.list_sprints(project_id)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_sprint(
    project_id: int,
    name: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Create a Sprint under a Project in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_sprint(project_id, name, start_date, end_date)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def update_sprint(
    sprint_id: int,
    name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Update one or more mutable fields on a Sprint in issue-tracker-api."""
    client = _client()
    try:
        return await client.update_sprint(
            sprint_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
