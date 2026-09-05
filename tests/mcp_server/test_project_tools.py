import pytest
from mcp import Client

import mcp_server.tools.projects as projects_tools
from mcp_server.server import mcp


class _FakeClient:
    """Stands in for IssueTrackerClient — Task 2 already covers the real HTTP wiring."""

    def __init__(self, projects=None):
        self._projects = projects or []

    async def list_projects(self):
        return self._projects

    async def aclose(self):
        pass


@pytest.mark.anyio
async def test_list_projects_tool_returns_api_result_unmodified(monkeypatch):
    fake = _FakeClient(projects=[{"id": 1, "key": "SDLC", "name": "SDLC Track", "description": ""}])
    monkeypatch.setattr(projects_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_projects", {})

    assert result.is_error is False
    # Verified against the installed mcp==2.1.1 SDK
    # (mcp/server/mcpserver/utilities/func_metadata.py FuncMetadata.convert_result):
    # a bare `list` return is not itself a JSON object, so the SDK wraps it under a
    # "result" key for structured_content.
    assert result.structured_content == {"result": fake._projects}
