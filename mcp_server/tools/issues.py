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


@mcp.tool()
async def update_issue(
    issue_id: int,
    summary: str | None = None,
    description: str | None = None,
    issue_type: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    reporter: str | None = None,
    status: str | None = None,
    id: int | None = None,
    key: str | None = None,
    project_id: int | None = None,
    sprint_id: int | None = None,
    unassign_sprint: bool = False,
) -> dict[str, Any]:
    """Update one or more mutable fields on an Issue in issue-tracker-api.

    `id`, `key`, and `project_id` are immutable and are silently ignored if present —
    an Issue's identity and project never change after creation.

    `sprint_id` assigns the Issue to that Sprint. `unassign_sprint=True` explicitly clears
    the Issue's Sprint assignment; if both are passed, `unassign_sprint` wins.
    """
    client = _client()
    if unassign_sprint:
        sprint_kwargs = {"sprint_id": None}
    elif sprint_id is not None:
        sprint_kwargs = {"sprint_id": sprint_id}
    else:
        sprint_kwargs = {}
    try:
        return await client.update_issue(
            issue_id,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            status=status,
            **sprint_kwargs,
        )
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def delete_issue(issue_id: int) -> dict[str, Any]:
    """Delete an Issue in issue-tracker-api and return a deletion confirmation."""
    client = _client()
    try:
        await client.delete_issue(issue_id)
        return {"deleted": True, "id": issue_id}
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_issue(
    project_id: int,
    summary: str,
    issue_type: str,
    priority: str,
    description: str | None = None,
    assignee: str | None = None,
    reporter: str | None = None,
) -> dict[str, Any]:
    """Create an Issue under a Project in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_issue(
            project_id, summary, issue_type, priority, description, assignee, reporter
        )
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
