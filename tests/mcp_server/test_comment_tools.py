import pytest
from mcp import Client

import mcp_server.tools.comments as comments_tools
from mcp_server.errors import UpstreamError
from mcp_server.server import mcp


class _FakeClient:
    def __init__(self, comments=None, comment=None):
        self._comments = comments or []
        self._comment = comment

    async def list_comments(self, issue_id):
        return self._comments

    async def create_comment(self, issue_id, body):
        return self._comment

    async def aclose(self):
        pass


_SAMPLE_COMMENT = {
    "id": 1, "issue_id": 1, "body": "via mcp", "author": "", "created_at": "2026-09-09 00:00:00",
}


@pytest.mark.anyio
async def test_list_issue_comments_tool_returns_api_result_unmodified(monkeypatch):
    fake = _FakeClient(comments=[_SAMPLE_COMMENT])
    monkeypatch.setattr(comments_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_issue_comments", {"issue_id": 1})

    assert result.is_error is False
    assert result.structured_content == {"result": [_SAMPLE_COMMENT]}


@pytest.mark.anyio
async def test_create_issue_comment_tool_returns_the_comment(monkeypatch):
    fake = _FakeClient(comment=_SAMPLE_COMMENT)
    monkeypatch.setattr(comments_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_issue_comment", {"issue_id": 1, "body": "via mcp"})

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_COMMENT


class _NotFoundListClient(_FakeClient):
    async def list_comments(self, issue_id):
        raise UpstreamError(404, "Issue 999999 not found")


@pytest.mark.anyio
async def test_list_issue_comments_tool_unknown_issue_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(comments_tools, "_client", lambda: _NotFoundListClient())

    async with Client(mcp) as client:
        result = await client.call_tool("list_issue_comments", {"issue_id": 999999})

    assert result.is_error is True
