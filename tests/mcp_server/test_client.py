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
