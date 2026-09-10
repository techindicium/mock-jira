import pytest
from mcp import Client

import mcp_server.tools.sprints as sprints_tools
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


class _FakeClient:
    def __init__(self, sprints=None, sprint=None):
        self._sprints = sprints or []
        self._sprint = sprint

    async def list_sprints(self, project_id):
        return self._sprints

    async def create_sprint(self, project_id, name, start_date=None, end_date=None):
        return self._sprint

    async def update_sprint(self, sprint_id, **fields):
        return self._sprint

    async def aclose(self):
        pass


_SAMPLE_SPRINT = {"id": 1, "project_id": 1, "name": "Sprint 1", "start_date": None, "end_date": None, "status": "planned"}


@pytest.mark.anyio
async def test_create_sprint_tool_returns_the_sprint(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprint=_SAMPLE_SPRINT))

    async with Client(mcp) as client:
        result = await client.call_tool("create_sprint", {"project_id": 1, "name": "Sprint 1"})

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_SPRINT


@pytest.mark.anyio
async def test_list_sprints_tool_returns_api_result_unmodified(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprints=[_SAMPLE_SPRINT]))

    async with Client(mcp) as client:
        result = await client.call_tool("list_sprints", {"project_id": 1})

    assert result.is_error is False
    assert result.structured_content == {"result": [_SAMPLE_SPRINT]}


@pytest.mark.anyio
async def test_update_sprint_tool_returns_updated_sprint(monkeypatch):
    updated = {**_SAMPLE_SPRINT, "status": "active"}
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprint=updated))

    async with Client(mcp) as client:
        result = await client.call_tool("update_sprint", {"sprint_id": 1, "status": "active"})

    assert result.is_error is False
    assert result.structured_content == updated


class _NotFoundListClient(_FakeClient):
    async def list_sprints(self, project_id):
        raise UpstreamError(404, "Project 999 not found")


@pytest.mark.anyio
async def test_list_sprints_tool_unknown_project_id_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _NotFoundListClient())

    async with Client(mcp) as client:
        result = await client.call_tool("list_sprints", {"project_id": 999})

    assert result.is_error is True
    assert "Project 999 not found" in result.content[0].text


class _NotFoundCreateClient(_FakeClient):
    async def create_sprint(self, project_id, name, start_date=None, end_date=None):
        raise UpstreamError(404, "Project 999 not found")


@pytest.mark.anyio
async def test_create_sprint_tool_unknown_project_id_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _NotFoundCreateClient())

    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_sprint", {"project_id": 999, "name": "Sprint 1"}
        )

    assert result.is_error is True
    assert "Project 999 not found" in result.content[0].text


class _NotFoundUpdateClient(_FakeClient):
    async def update_sprint(self, sprint_id, **fields):
        raise UpstreamError(404, "Sprint 999 not found")


@pytest.mark.anyio
async def test_update_sprint_tool_unknown_id_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _NotFoundUpdateClient())

    async with Client(mcp) as client:
        result = await client.call_tool("update_sprint", {"sprint_id": 999, "status": "active"})

    assert result.is_error is True
    assert "Sprint 999 not found" in result.content[0].text


_UNREACHABLE_MESSAGE = "Could not reach issue-tracker-api at http://issue-tracker-api: connection refused"


class _UnreachableClient(_FakeClient):
    async def list_sprints(self, project_id):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def create_sprint(self, project_id, name, start_date=None, end_date=None):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def update_sprint(self, sprint_id, **fields):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tool_name, arguments",
    [
        ("list_sprints", {"project_id": 1}),
        ("create_sprint", {"project_id": 1, "name": "Sprint 1"}),
        ("update_sprint", {"sprint_id": 1, "status": "active"}),
    ],
)
async def test_sprint_tool_unreachable_api_errors_with_clear_message(monkeypatch, tool_name, arguments):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _UnreachableClient())

    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, arguments)

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text
