import httpx

from mcp_server.errors import UpstreamError, UpstreamUnreachableError


class IssueTrackerClient:
    def __init__(self, base_url: str, transport: httpx.AsyncBaseTransport | None = None):
        self._http = httpx.AsyncClient(base_url=base_url, transport=transport)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def list_projects(self) -> list[dict]:
        response = await self._request("GET", "/projects")
        return response.json()

    async def create_project(self, key: str, name: str, description: str | None = None) -> dict:
        payload: dict = {"key": key, "name": name}
        if description is not None:
            payload["description"] = description
        response = await self._request("POST", "/projects", json=payload)
        return response.json()

    async def list_issues(self, project_id: int | None = None, status: str | None = None) -> list[dict]:
        params: dict = {}
        if project_id is not None:
            params["project_id"] = project_id
        if status is not None:
            params["status"] = status
        response = await self._request("GET", "/issues", params=params)
        return response.json()

    async def get_issue(self, issue_id: int) -> dict:
        response = await self._request("GET", f"/issues/{issue_id}")
        return response.json()

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            response = await self._http.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise UpstreamUnreachableError(
                f"Could not reach issue-tracker-api at {self._http.base_url}: {exc}"
            ) from exc
        if response.status_code >= 400:
            body = response.json()
            message = body.get("message", response.text)
            raise UpstreamError(response.status_code, message)
        return response
