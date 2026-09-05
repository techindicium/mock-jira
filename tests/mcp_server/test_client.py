import httpx
import pytest

from mcp_server.client import IssueTrackerClient
from mcp_server.errors import UpstreamError, UpstreamUnreachableError


def _client(handler):
    return IssueTrackerClient("http://issue-tracker-api", transport=httpx.MockTransport(handler))


@pytest.mark.anyio
async def test_list_projects_returns_api_response_unmodified():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/projects"
        return httpx.Response(
            200, json=[{"id": 1, "key": "SDLC", "name": "SDLC Track", "description": ""}]
        )

    result = await _client(handler).list_projects()
    assert result == [{"id": 1, "key": "SDLC", "name": "SDLC Track", "description": ""}]


@pytest.mark.anyio
async def test_create_project_returns_created_project():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/projects"
        return httpx.Response(
            201, json={"id": 1, "key": "SDLC", "name": "SDLC Track", "description": ""}
        )

    result = await _client(handler).create_project("SDLC", "SDLC Track")
    assert result["key"] == "SDLC"


@pytest.mark.anyio
async def test_create_project_duplicate_key_raises_upstream_error_verbatim():
    def handler(request):
        return httpx.Response(
            409,
            json={"message": "Project key 'SDLC' already exists", "code": "PROJECT_KEY_DUPLICATE"},
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).create_project("SDLC", "SDLC Track")
    assert exc_info.value.status_code == 409
    assert exc_info.value.message == "Project key 'SDLC' already exists"


@pytest.mark.anyio
async def test_create_project_blank_key_raises_upstream_error_for_422():
    def handler(request):
        return httpx.Response(422, json={"message": "key is required", "code": "VALIDATION_ERROR"})

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).create_project("", "SDLC Track")
    assert exc_info.value.status_code == 422
    assert exc_info.value.message == "key is required"


@pytest.mark.anyio
async def test_list_projects_unreachable_api_raises_upstream_unreachable_error():
    def handler(request):
        raise httpx.ConnectError("Connection refused", request=request)

    with pytest.raises(UpstreamUnreachableError):
        await _client(handler).list_projects()


@pytest.mark.anyio
async def test_list_issues_returns_api_response_unmodified():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/issues"
        return httpx.Response(
            200,
            json=[{
                "id": 1, "key": "SDLC-1", "project_id": 1, "summary": "Fix bug",
                "description": "", "issue_type": "bug", "status": "todo", "priority": "high",
                "assignee": "", "reporter": "", "created_at": "2026-09-05 00:00:00",
                "updated_at": "2026-09-05 00:00:00",
            }],
        )

    result = await _client(handler).list_issues()
    assert result[0]["key"] == "SDLC-1"


@pytest.mark.anyio
async def test_list_issues_passes_project_id_and_status_as_query_params():
    def handler(request):
        assert request.url.params["project_id"] == "1"
        assert request.url.params["status"] == "todo"
        return httpx.Response(200, json=[])

    await _client(handler).list_issues(project_id=1, status="todo")


@pytest.mark.anyio
async def test_get_issue_returns_the_issue():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/issues/1"
        return httpx.Response(
            200,
            json={
                "id": 1, "key": "SDLC-1", "project_id": 1, "summary": "Fix bug",
                "description": "", "issue_type": "bug", "status": "todo", "priority": "high",
                "assignee": "", "reporter": "", "created_at": "2026-09-05 00:00:00",
                "updated_at": "2026-09-05 00:00:00",
            },
        )

    result = await _client(handler).get_issue(1)
    assert result["key"] == "SDLC-1"


@pytest.mark.anyio
async def test_get_issue_unknown_id_raises_upstream_error_verbatim():
    def handler(request):
        return httpx.Response(
            404, json={"message": "Issue 999 not found", "code": "ISSUE_NOT_FOUND"}
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).get_issue(999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Issue 999 not found"


@pytest.mark.anyio
async def test_create_issue_returns_created_issue():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/issues"
        return httpx.Response(
            201,
            json={
                "id": 1, "key": "SDLC-1", "project_id": 1, "summary": "Fix bug",
                "description": "", "issue_type": "bug", "status": "todo", "priority": "high",
                "assignee": "", "reporter": "", "created_at": "2026-09-05 00:00:00",
                "updated_at": "2026-09-05 00:00:00",
            },
        )

    result = await _client(handler).create_issue(1, "Fix bug", "bug", "high")
    assert result["key"] == "SDLC-1"


@pytest.mark.anyio
async def test_create_issue_unknown_project_id_raises_upstream_error_verbatim():
    def handler(request):
        return httpx.Response(
            404, json={"message": "Project 999 not found", "code": "ISSUE_PROJECT_NOT_FOUND"}
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).create_issue(999, "Fix bug", "bug", "high")
    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Project 999 not found"


@pytest.mark.anyio
async def test_create_issue_invalid_issue_type_raises_upstream_error_for_422():
    def handler(request):
        return httpx.Response(
            422,
            json={"message": "issue_type must be one of: bug, task, story", "code": "VALIDATION_ERROR"},
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).create_issue(1, "Fix bug", "urgent", "high")
    assert exc_info.value.status_code == 422


@pytest.mark.anyio
async def test_update_issue_sends_only_provided_fields_and_returns_result():
    def handler(request):
        assert request.method == "PATCH"
        assert request.url.path == "/issues/1"
        import json as _json
        assert _json.loads(request.content) == {"status": "in_progress"}
        return httpx.Response(
            200,
            json={
                "id": 1, "key": "SDLC-1", "project_id": 1, "summary": "Fix bug",
                "description": "", "issue_type": "bug", "status": "in_progress", "priority": "high",
                "assignee": "", "reporter": "", "created_at": "2026-09-05 00:00:00",
                "updated_at": "2026-09-05 00:00:01",
            },
        )

    result = await _client(handler).update_issue(1, status="in_progress")
    assert result["status"] == "in_progress"


@pytest.mark.anyio
async def test_update_issue_unknown_id_raises_upstream_error_verbatim():
    def handler(request):
        return httpx.Response(
            404, json={"message": "Issue 999 not found", "code": "ISSUE_NOT_FOUND"}
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).update_issue(999, status="done")
    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_delete_issue_sends_delete_request():
    def handler(request):
        assert request.method == "DELETE"
        assert request.url.path == "/issues/1"
        return httpx.Response(204)

    await _client(handler).delete_issue(1)  # no return value, no exception


@pytest.mark.anyio
async def test_delete_issue_unknown_id_raises_upstream_error_verbatim():
    def handler(request):
        return httpx.Response(
            404, json={"message": "Issue 999 not found", "code": "ISSUE_NOT_FOUND"}
        )

    with pytest.raises(UpstreamError) as exc_info:
        await _client(handler).delete_issue(999)
    assert exc_info.value.status_code == 404
