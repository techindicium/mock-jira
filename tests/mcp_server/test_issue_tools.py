import pytest
from mcp import Client

import mcp_server.tools.issues as issues_tools
from mcp_server.errors import UpstreamError
from mcp_server.server import mcp


class _FakeClient:
    """Stands in for IssueTrackerClient — Tasks 1/2 already cover the real HTTP wiring."""

    def __init__(self, issues=None, issue=None):
        self._issues = issues or []
        self._issue = issue

    async def list_issues(self, project_id=None, status=None):
        return self._issues

    async def get_issue(self, issue_id):
        return self._issue

    async def aclose(self):
        pass


_SAMPLE_ISSUE = {
    "id": 1, "key": "SDLC-1", "project_id": 1, "summary": "Fix bug", "description": "",
    "issue_type": "bug", "status": "todo", "priority": "high", "assignee": "", "reporter": "",
    "created_at": "2026-09-05 00:00:00", "updated_at": "2026-09-05 00:00:00",
}


@pytest.mark.anyio
async def test_list_issues_tool_returns_api_result_unmodified(monkeypatch):
    fake = _FakeClient(issues=[_SAMPLE_ISSUE])
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_issues", {})

    assert result.is_error is False
    # A bare `list` return is wrapped under a "result" key for structured_content, matching the
    # convention already confirmed for list_projects in test_project_tools.py.
    assert result.structured_content == {"result": [_SAMPLE_ISSUE]}


@pytest.mark.anyio
async def test_get_issue_tool_returns_the_issue(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _FakeClient(issue=_SAMPLE_ISSUE))

    async with Client(mcp) as client:
        result = await client.call_tool("get_issue", {"issue_id": 1})

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_ISSUE


class _NotFoundGetClient(_FakeClient):
    async def get_issue(self, issue_id):
        raise UpstreamError(404, "Issue 999 not found")


@pytest.mark.anyio
async def test_get_issue_tool_unknown_id_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _NotFoundGetClient())

    async with Client(mcp) as client:
        result = await client.call_tool("get_issue", {"issue_id": 999})

    assert result.is_error is True
    assert "Issue 999 not found" in result.content[0].text


@pytest.mark.anyio
async def test_get_issue_tool_missing_issue_id_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeClient()

    monkeypatch.setattr(issues_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        result = await client.call_tool("get_issue", {})  # missing required "issue_id"

    assert result.is_error is True
    assert called["value"] is False  # schema validation rejected the call before _client() ran


@pytest.mark.anyio
async def test_list_issues_tool_invalid_project_id_type_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeClient()

    monkeypatch.setattr(issues_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        # "project_id" is declared int; a non-numeric string fails schema validation.
        result = await client.call_tool("list_issues", {"project_id": "not-a-number"})

    assert result.is_error is True
    assert called["value"] is False


class _FakeCreateClient(_FakeClient):
    def __init__(self, created=None, error=None):
        super().__init__()
        self._created = created
        self._error = error

    async def create_issue(self, project_id, summary, issue_type, priority, description=None, assignee=None, reporter=None):
        if self._error is not None:
            raise self._error
        return self._created


@pytest.mark.anyio
async def test_create_issue_tool_returns_created_issue(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _FakeCreateClient(created=_SAMPLE_ISSUE))

    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_issue",
            {"project_id": 1, "summary": "Fix bug", "issue_type": "bug", "priority": "high"},
        )

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_ISSUE


@pytest.mark.anyio
async def test_create_issue_tool_unknown_project_id_errors_with_verbatim_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(404, "Project 999 not found"))
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_issue",
            {"project_id": 999, "summary": "Fix bug", "issue_type": "bug", "priority": "high"},
        )

    assert result.is_error is True
    assert "Project 999 not found" in result.content[0].text


@pytest.mark.anyio
async def test_create_issue_tool_missing_required_field_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeCreateClient()

    monkeypatch.setattr(issues_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        # missing "priority"
        result = await client.call_tool(
            "create_issue", {"project_id": 1, "summary": "Fix bug", "issue_type": "bug"}
        )

    assert result.is_error is True
    assert called["value"] is False  # schema validation rejected the call before _client() ran


class _FakeUpdateClient(_FakeClient):
    def __init__(self, updated=None, error=None):
        super().__init__()
        self._updated = updated
        self._error = error
        self.received_kwargs = None

    async def update_issue(self, issue_id, **fields):
        self.received_kwargs = fields
        if self._error is not None:
            raise self._error
        return self._updated


@pytest.mark.anyio
async def test_update_issue_tool_updates_mutable_fields_and_returns_result(monkeypatch):
    updated = {**_SAMPLE_ISSUE, "status": "in_progress"}
    fake = _FakeUpdateClient(updated=updated)
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("update_issue", {"issue_id": 1, "status": "in_progress"})

    assert result.is_error is False
    assert result.structured_content == updated
    assert fake.received_kwargs["status"] == "in_progress"


@pytest.mark.anyio
async def test_update_issue_tool_ignores_immutable_fields(monkeypatch):
    fake = _FakeUpdateClient(updated=_SAMPLE_ISSUE)
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        await client.call_tool(
            "update_issue",
            {"issue_id": 1, "id": 999, "key": "OTHER-9", "project_id": 2, "status": "done"},
        )

    # id/key/project_id are declared on the tool's input schema (explicit, not schema-excluded)
    # but never reach the client call — only the mutable fields do.
    assert fake.received_kwargs == {
        "summary": None,
        "description": None,
        "issue_type": None,
        "priority": None,
        "assignee": None,
        "reporter": None,
        "status": "done",
    }


@pytest.mark.anyio
async def test_update_issue_tool_unknown_id_errors_with_verbatim_message(monkeypatch):
    fake = _FakeUpdateClient(error=UpstreamError(404, "Issue 999 not found"))
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("update_issue", {"issue_id": 999, "status": "done"})

    assert result.is_error is True
    assert "Issue 999 not found" in result.content[0].text


@pytest.mark.anyio
async def test_update_issue_tool_missing_issue_id_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeUpdateClient()

    monkeypatch.setattr(issues_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        result = await client.call_tool("update_issue", {"status": "done"})  # missing "issue_id"

    assert result.is_error is True
    assert called["value"] is False


class _FakeDeleteClient(_FakeClient):
    def __init__(self, error=None):
        super().__init__()
        self._error = error

    async def delete_issue(self, issue_id):
        if self._error is not None:
            raise self._error


@pytest.mark.anyio
async def test_delete_issue_tool_returns_deleted_confirmation(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _FakeDeleteClient())

    async with Client(mcp) as client:
        result = await client.call_tool("delete_issue", {"issue_id": 1})

    assert result.is_error is False
    assert result.structured_content == {"deleted": True, "id": 1}


@pytest.mark.anyio
async def test_delete_issue_tool_unknown_id_errors_with_verbatim_message(monkeypatch):
    fake = _FakeDeleteClient(error=UpstreamError(404, "Issue 999 not found"))
    monkeypatch.setattr(issues_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("delete_issue", {"issue_id": 999})

    assert result.is_error is True
    assert "Issue 999 not found" in result.content[0].text


@pytest.mark.anyio
async def test_delete_issue_tool_missing_issue_id_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeDeleteClient()

    monkeypatch.setattr(issues_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        result = await client.call_tool("delete_issue", {})  # missing required "issue_id"

    assert result.is_error is True
    assert called["value"] is False
