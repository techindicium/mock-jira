import pytest
from mcp import Client

import mcp_server.tools.projects as projects_tools
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
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


class _FakeCreateClient(_FakeClient):
    def __init__(self, created=None, error=None):
        super().__init__()
        self._created = created
        self._error = error

    async def create_project(self, key, name, description=None):
        if self._error is not None:
            raise self._error
        return self._created


@pytest.mark.anyio
async def test_create_project_tool_returns_created_project(monkeypatch):
    created = {"id": 1, "key": "SDLC", "name": "SDLC Track", "description": ""}
    monkeypatch.setattr(projects_tools, "_client", lambda: _FakeCreateClient(created=created))

    async with Client(mcp) as client:
        result = await client.call_tool("create_project", {"key": "SDLC", "name": "SDLC Track"})

    assert result.is_error is False
    # `create_project`'s return type is a plain `dict` (already object-shaped), so — unlike the
    # list-returning `list_projects` above — structured_content is expected to be the dict
    # itself, with no extra "result" wrapper. Verified against the installed mcp==2.1.1 SDK.
    assert result.structured_content == created


@pytest.mark.anyio
async def test_create_project_tool_duplicate_key_errors_with_verbatim_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(409, "Project key 'SDLC' already exists"))
    monkeypatch.setattr(projects_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_project", {"key": "SDLC", "name": "SDLC Track"})

    assert result.is_error is True
    assert "Project key 'SDLC' already exists" in result.content[0].text


@pytest.mark.anyio
async def test_create_project_tool_blank_key_errors_with_verbatim_422_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(422, "key is required"))
    monkeypatch.setattr(projects_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        # Note: "" is a syntactically valid str, so this reaches the (faked) HTTP call rather
        # than failing schema validation — see SA-1 in the plan header.
        result = await client.call_tool("create_project", {"key": "", "name": "SDLC Track"})

    assert result.is_error is True
    assert "key is required" in result.content[0].text


@pytest.mark.anyio
async def test_create_project_tool_missing_key_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeCreateClient()

    monkeypatch.setattr(projects_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        result = await client.call_tool("create_project", {"name": "SDLC Track"})  # missing "key"

    assert result.is_error is True
    assert called["value"] is False  # schema validation rejected the call before _client() ran


_UNREACHABLE_MESSAGE = "Could not reach issue-tracker-api at http://issue-tracker-api: connection refused"


class _UnreachableListClient(_FakeClient):
    async def list_projects(self):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)


@pytest.mark.anyio
async def test_list_projects_tool_unreachable_api_errors_with_clear_message(monkeypatch):
    monkeypatch.setattr(projects_tools, "_client", lambda: _UnreachableListClient())

    async with Client(mcp) as client:
        result = await client.call_tool("list_projects", {})

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text


@pytest.mark.anyio
async def test_create_project_tool_unreachable_api_errors_with_clear_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamUnreachableError(_UNREACHABLE_MESSAGE))
    monkeypatch.setattr(projects_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_project", {"key": "SDLC", "name": "SDLC Track"})

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text
