import pytest
from mcp import Client

import mcp_server.tools.users as users_tools
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


class _FakeClient:
    """Stands in for IssueTrackerClient — Task 1 already covers the real HTTP wiring."""

    def __init__(self, users=None):
        self._users = users or []

    async def list_users(self):
        return self._users

    async def aclose(self):
        pass


@pytest.mark.anyio
async def test_list_users_tool_returns_api_result_unmodified(monkeypatch):
    fake = _FakeClient(
        users=[{"id": 1, "name": "Mei Tan", "email": "mei@example.com", "role": "engineer"}]
    )
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_users", {})

    assert result.is_error is False
    # A bare `list` return is wrapped under a "result" key for structured_content, matching the
    # convention already confirmed for list_projects/list_issues.
    assert result.structured_content == {"result": fake._users}


class _FakeCreateClient(_FakeClient):
    def __init__(self, created=None, error=None):
        super().__init__()
        self._created = created
        self._error = error

    async def create_user(self, name, email=None, role=None):
        if self._error is not None:
            raise self._error
        return self._created


@pytest.mark.anyio
async def test_create_user_tool_returns_created_user(monkeypatch):
    created = {"id": 1, "name": "Mei Tan", "email": "mei@example.com", "role": "engineer"}
    monkeypatch.setattr(users_tools, "_client", lambda: _FakeCreateClient(created=created))

    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_user",
            {"name": "Mei Tan", "email": "mei@example.com", "role": "engineer"},
        )

    assert result.is_error is False
    assert result.structured_content == created


@pytest.mark.anyio
async def test_create_user_tool_duplicate_email_errors_with_verbatim_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(409, "Email 'mei@example.com' already exists"))
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_user", {"name": "Mei Tan", "email": "mei@example.com"}
        )

    assert result.is_error is True
    assert "already exists" in result.content[0].text


@pytest.mark.anyio
async def test_create_user_tool_blank_name_errors_with_verbatim_422_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(422, "name is required"))
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        # Note: "" is a syntactically valid str, so this reaches the (faked) HTTP call rather
        # than failing schema validation — same SA-1 note as project-tools' analogous test.
        result = await client.call_tool("create_user", {"name": ""})

    assert result.is_error is True
    assert "name is required" in result.content[0].text


@pytest.mark.anyio
async def test_create_user_tool_missing_name_errors_before_http_request(monkeypatch):
    called = {"value": False}

    def _client_spy():
        called["value"] = True
        return _FakeCreateClient()

    monkeypatch.setattr(users_tools, "_client", _client_spy)

    async with Client(mcp) as client:
        result = await client.call_tool("create_user", {})  # missing required "name"

    assert result.is_error is True
    assert called["value"] is False  # schema validation rejected the call before _client() ran


_UNREACHABLE_MESSAGE = "Could not reach issue-tracker-api at http://issue-tracker-api: connection refused"


class _UnreachableListClient(_FakeClient):
    async def list_users(self):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)


@pytest.mark.anyio
async def test_list_users_tool_unreachable_api_errors_with_clear_message(monkeypatch):
    monkeypatch.setattr(users_tools, "_client", lambda: _UnreachableListClient())

    async with Client(mcp) as client:
        result = await client.call_tool("list_users", {})

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text


@pytest.mark.anyio
async def test_create_user_tool_unreachable_api_errors_with_clear_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamUnreachableError(_UNREACHABLE_MESSAGE))
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_user", {"name": "Mei Tan"})

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text
