<!-- partial_schema: plan@1 -->

# Implementation Plan: Project MCP tools (list_projects, create_project)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/project-tools.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-05)
> **Platform:** `mcp` Python SDK (official, PyPI `mcp`), `httpx`, Python 3.11 — new standalone process, separate from the FastAPI `app/` package

**Goal:** Stand up a new `mcp_server/` package — a second, independent Python process alongside
`issue-tracker-api` — exposing `list_projects` and `create_project` as MCP tools that thinly wrap
`issue-tracker-api`'s `GET /projects` and `POST /projects` endpoints over HTTP.

**Architecture:** This is the first code written for the `mcp-server` module (no `mcp_server/`
package exists yet), so this plan also establishes the base layout the sibling `issue-tools` spec
will build on. The package is layered in three parts: `mcp_server/config.py` (reads
`API_BASE_URL`), `mcp_server/client.py` (an `httpx.AsyncClient`-backed `IssueTrackerClient` that
translates method calls into HTTP requests and maps HTTP/network failures onto two typed
exceptions), and `mcp_server/tools/projects.py` (registers the two MCP tools on a shared
`mcp_server.server.mcp` `MCPServer` instance, using the SDK's built-in argument-schema validation
for BEH-4 and re-raising the client's typed exceptions as `ToolError` so the model sees the
upstream message verbatim for BEH-3/BEH-5). Per the constitution's "HTTP contract is the
boundary" and the charter's "pure client of issue-tracker-api" stance, this package never imports
anything from `app/` and never opens the SQLite file — every read and write is delegated to a
real HTTP call (mocked via `httpx.MockTransport` in tests, never a live server, per "fixture-
backed, offline only").

**mcp Python SDK version note:** `pip install mcp` currently resolves to `2.1.1` (confirmed via
`pip index versions mcp` against the live PyPI index during planning — versions `2.0.0+` are
current, `1.x` is the prior line). The SDK's own `docs/whats-new.md` states the `2.x` line
**removed** (not deprecated) the older `mcp.server.fastmcp.FastMCP` import path in favor of
`from mcp.server.mcpserver import MCPServer`, and errors are raised as
`mcp.server.mcpserver.exceptions.ToolError` rather than returned as plain strings. This plan
targets that current `2.x` API throughout (`MCPServer`, `ToolError`, `from mcp import Client` for
in-memory testing). If `/adev:implement` finds an already-pinned older `mcp==1.x` elsewhere in the
workspace, treat that as a signal to re-verify these import paths before writing code, but do not
assume it — this repo has no existing `mcp` pin (greenfield).

**Constitution Validation (Step 3):** Checked every task's files/behavior against `Architecture
Boundaries`. None of these tasks add a dependency on another repo in the workspace (the new
`mcp` and `httpx` pip packages are dependencies of a Python package, not a workspace repo), touch
auth, or change `issue-tracker-api`'s already-shipped HTTP contract — this plan only adds a new
*consumer* of that contract, read-only with respect to `app/`. `governance/boundaries.yaml` has no
rules configured (`boundaries: []`), so no file-pattern flags apply. No task in this plan is
marked `[REQUIRES HUMAN APPROVAL]`.

**Dependency-file scoping decision:** Since `mcp-server` is chartered as "a NEW, separate Python
process" (unlike `kanban-ui`, which shares `issue-tracker-api`'s process), this plan adds a
second file, `requirements-mcp.txt`, rather than appending to the existing `requirements.txt`
that `issue-tracker-api` uses — this keeps each process's *runtime* dependency set legible ahead
of the still-unbuilt `docker-packaging` cross-cutting spec, which already describes two separate
Dockerfiles/images. `CLAUDE.md`'s `## Commands` section currently documents only
`pip install -r requirements.txt`; this plan does not edit the constitution (that is a
`/adev:sync`-driven artifact, out of scope for a feature plan), but flags a follow-up hygiene
note: once this plan lands, `## Commands` should gain a
`pip install -r requirements-mcp.txt` line so a fresh contributor can find both install steps.
This mirrors how `project-management.plan.md` flagged a `platform-context.yaml` gap without
blocking on it.

**Review notes carried forward (PASS_WITH_NOTES):**
- **SA-1** (warning) — already resolved in the reviewed spec itself: the spec's Error Cases table
  now carries an explicit `422` (blank `key`/`name`) → `MCP_UPSTREAM_ERROR` row, and BEH-4 is
  read narrowly (only "missing key", not "empty-string key," is a schema failure). This plan
  therefore deliberately does **not** add `minLength: 1` (or any `Annotated[..., Field(...)]`
  constraint) to `key`/`name` on the `create_project` tool's input — a blank string must remain
  schema-valid so it reaches `issue-tracker-api` and comes back as the API's own `422`
  (`app/routers/projects.py`'s existing `VALIDATION_ERROR` check), which the tool then passes
  through verbatim as `MCP_UPSTREAM_ERROR` (see Task 4). Adding client-side `minLength`
  enforcement would make that 422 path unreachable via this tool, silently narrowing the
  reviewed contract.
- **CON-1** (suggestion) — the reviewer's cross-spec alignment suggestion is satisfied by SA-1's
  fix landing in the spec; no plan-level action needed.

---

## File Structure

**Create:**
- `requirements-mcp.txt` — deps: `mcp` (official MCP Python SDK), `httpx` (async HTTP client to
  `issue-tracker-api`), `anyio` (direct dependency for `@pytest.mark.anyio` async tests; also a
  transitive dependency of `mcp` itself)
- `mcp_server/__init__.py` — package marker
- `mcp_server/config.py` — `get_api_base_url()`: reads `API_BASE_URL`, raises a clear error if unset
- `mcp_server/errors.py` — `UpstreamError` (carries `status_code` + verbatim `message`),
  `UpstreamUnreachableError`
- `mcp_server/client.py` — `IssueTrackerClient`: `httpx.AsyncClient`-backed wrapper with
  `list_projects()` / `create_project(key, name, description=None)`, mapping HTTP 4xx/5xx
  responses to `UpstreamError` and network failures to `UpstreamUnreachableError`
- `mcp_server/server.py` — the shared `mcp = MCPServer("mock-jira-mcp")` instance and the
  process `main()` entrypoint (stdio transport, the SDK default — no network port is opened by
  this spec's scope; an HTTP-based transport, if needed for the containerized deployment, is the
  still-unbuilt `docker-packaging` spec's concern, not this one's)
- `mcp_server/tools/__init__.py` — package marker
- `mcp_server/tools/projects.py` — registers `list_projects` and `create_project` on `mcp`
- `tests/mcp_server/__init__.py` — package marker
- `tests/mcp_server/conftest.py` — `anyio_backend` fixture (`"asyncio"`) shared by every async test in this module
- `tests/mcp_server/test_config.py` — `get_api_base_url()` coverage (Preconditions)
- `tests/mcp_server/test_client.py` — `IssueTrackerClient` coverage against `httpx.MockTransport`
  (no live server, no real network — "fixture-backed, offline only")
- `tests/mcp_server/test_project_tools.py` — BEH-1 through BEH-5 coverage at the tool layer, using
  `mcp.Client(mcp)` in-memory (no subprocess, no network)

**Modify:** none — this is the first implementation work for the `mcp-server` module. Nothing
under `app/` (issue-tracker-api's own package) is touched.

**Reference (read, do not modify):**
- `app/routers/projects.py` — exact route shapes this plan wraps: `POST /projects` (201, body
  `{id, key, name, description}`; 422 `{"message": "...", "code": "VALIDATION_ERROR"}` for blank/
  missing `key`/`name` that reaches the API; 409 `{"message": "Project key '<key>' already
  exists", "code": "PROJECT_KEY_DUPLICATE"}`) and `GET /projects` (200, list of the same shape)
- `app/models.py` — `ProjectCreate {key: str, name: str, description: str | None}`,
  `ProjectRead {id: int, key: str, name: str, description: str}`
- `app/errors.py` — confirms every error response (`400`/`404`/`409`/`422`) is a flat
  `{"message": ..., "code": ...}` JSON body, never nested under `"detail"` — the shape
  `mcp_server/client.py`'s error mapping relies on
- `.context-index/specs/features/mcp-server/charter.md` — Capability Map, Domain Model
  (`McpTool` entity), Invariants ("input_schema validates before the wrapped HTTP call",
  "error response always carries the underlying API's error message verbatim")
- `.context-index/specs/features/mcp-server/issue-tools.spec.md` — sibling spec (not yet planned);
  read only to keep `mcp_server/tools/` and `mcp_server/client.py` shaped for extension (more
  tools, more `IssueTrackerClient` methods) without this plan doing that work
- `CLAUDE.md` — constitution: "HTTP contract is the boundary", "no inbound dependencies",
  "fixture-backed, offline only"
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands

---

## Context Packets

> No `source-manifest.files[]` exists on this spec yet (greenfield — first implementation for
> `mcp-server`), and the sibling `issue-tools.spec.md` is `review-pending` with no source-manifest
> of its own either. No `orientation/architecture.md`, ADRs, or samples exist in this repo yet.
> Context packets below fall back to charter + spec + constitution + the actual
> `issue-tracker-api` route/model source, per Step 2's "no source-manifest" fallback.

### Task 1 Context
- Spec: `project-tools.spec.md` Preconditions ("The MCP server process has been configured with
  the API's base URL via `API_BASE_URL`")
- Charter: `charter.md` (Domain Model → `McpTool` entity; Quality Attributes → Security: "Bound to
  localhost only by default")
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty, no rules to apply
- Heuristics: none available for module `mcp-server`

### Task 2 Context
- Spec: `project-tools.spec.md` BEH-1, BEH-2, BEH-3, Error Cases table (all four rows), BEH-5
- Charter: `charter.md` (Invariants: "A tool call's error response always carries the underlying
  API's error message verbatim; the MCP layer never swallows or rewrites it")
- Source files: `app/routers/projects.py` (full read — exact request/response shapes),
  `app/models.py` (full read — `ProjectCreate`/`ProjectRead` field names/types), `app/errors.py`
  (full read — confirms the flat `{message, code}` envelope on every error status)
- Source files (from Task 1): `mcp_server/config.py` (signature only — `client.py` does not call
  it directly; `base_url` is passed in by the caller)

### Task 3 Context
- Spec: `project-tools.spec.md` BEH-1
- Charter: `charter.md` (Capability: `list_projects` tool; Exposed APIs table)
- Source files (from Task 2, full read): `mcp_server/client.py`, `mcp_server/errors.py`
- Source files (from Task 1, full read): `mcp_server/config.py`

### Task 4 Context
- Spec: `project-tools.spec.md` BEH-2, BEH-3, BEH-4, Error Cases table (input-schema row, 409
  row, 422 row)
- Charter: `charter.md` (Capability: `create_project` tool)
- Review note SA-1 (see plan header): do not add `minLength` to `key`/`name`
- Source files (from Task 3, full read — extending, not replacing):
  `mcp_server/tools/projects.py`, `tests/mcp_server/test_project_tools.py`

### Task 5 Context
- Spec: `project-tools.spec.md` BEH-5 (both tools)
- Charter: `charter.md` (Quality Attributes → Observability: "Tool errors surface the underlying
  API error message unchanged")
- Source files (from Task 2/4, full read — verifying only, no expected change):
  `mcp_server/client.py`, `mcp_server/tools/projects.py`

---

## Parallelization

- Group A (independent): Task 1
- Group B (independent): Task 2
- Group C (sequential): Task 3 → Task 4 → Task 5

Task 1 (`mcp_server/config.py`) and Task 2 (`mcp_server/client.py` + `mcp_server/errors.py`)
touch disjoint files and neither imports the other — `client.py`'s `IssueTrackerClient` takes
`base_url` as a plain constructor argument rather than calling `get_api_base_url()` itself, so
Groups A and B can run in parallel. Group C cannot start until both land: Task 3
(`mcp_server/tools/projects.py`, first cut) imports both `mcp_server.config.get_api_base_url` and
`mcp_server.client.IssueTrackerClient`. Tasks 3 → 4 → 5 are then strictly sequential — each
extends the same two files (`mcp_server/tools/projects.py`, `tests/mcp_server/test_project_tools.py`).

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Package scaffold + `API_BASE_URL` config | small | unit | — | 4 create, 0 modify |
| 2 | `IssueTrackerClient` HTTP wrapper | medium | unit | — | 3 create, 0 modify |
| 3 | `list_projects` tool | small | unit | Task 1, Task 2 | 3 create, 0 modify |
| 4 | `create_project` tool | medium | unit | Task 3 | 0 create, 2 modify |
| 5 | Confirm unreachable-API passthrough (both tools) | small | unit | Task 4 | 0 create, 1 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no `test_strategies` entries in `manifest.yaml` matching `mcp_server/**` paths). Per
Step 5, the Strategy Summary section is omitted since every task is `unit`. No
`infra_requirements:` is declared on the spec and no task needs external infrastructure — every
test in this plan runs against `httpx.MockTransport` or the SDK's own in-memory `Client(mcp)`
harness, never a live server — so the Test Infrastructure Requirements section is also omitted.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). Tasks 1 and 2 are foundation tasks not tied to a single spec
behavior (mirroring how the sibling `project-management.plan.md` gave its own foundation task a
dedicated suite) and each gets its own suite (`test_config.py`, `test_client.py`) created once.
`tests/mcp_server/test_project_tools.py` is the shared per-behavior suite for the tool layer: created
once by Task 3 (BEH-1) and extended by Task 4 (BEH-2/3/4) and Task 5 (BEH-5).

---

## Task Structure

### Task 1: Package scaffold + `API_BASE_URL` config [specialist: none]

**Charter capability:** `McpTool` foundation (all tools depend on knowing where `issue-tracker-api` is)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `requirements-mcp.txt`
- Create: `mcp_server/__init__.py`
- Create: `mcp_server/config.py`
- Create: `tests/mcp_server/__init__.py`
- Create: `tests/mcp_server/conftest.py`
- Test: `tests/mcp_server/test_config.py`

**Tests:** `tests/mcp_server/test_config.py` (create — first task to touch this behavior)

**Context to load:**
- Spec Preconditions: "The MCP server process has been configured with the API's base URL via
  `API_BASE_URL`."

- [ ] **Write failing test**

```python
# tests/mcp_server/test_config.py
import pytest

from mcp_server.config import get_api_base_url


def test_get_api_base_url_returns_configured_value(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000")
    assert get_api_base_url() == "http://localhost:8000"


def test_get_api_base_url_raises_clear_error_when_unset(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="API_BASE_URL"):
        get_api_base_url()
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_config.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server'` (the package does not exist
yet).

- [ ] **Implement**

```python
# mcp_server/config.py
import os


def get_api_base_url() -> str:
    value = os.environ.get("API_BASE_URL")
    if not value:
        raise RuntimeError(
            "API_BASE_URL environment variable is required to reach issue-tracker-api"
        )
    return value
```

`mcp_server/__init__.py` and `tests/mcp_server/__init__.py` are empty package markers.
`tests/mcp_server/conftest.py` provides the shared `anyio_backend` fixture every async test in
this module needs (first consumed by Task 2):

```python
# tests/mcp_server/conftest.py
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
```

```text
# requirements-mcp.txt
mcp
httpx
anyio
```

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_config.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/mcp-server/project-tools`

```bash
git add requirements-mcp.txt mcp_server/__init__.py mcp_server/config.py tests/mcp_server/__init__.py tests/mcp_server/conftest.py tests/mcp_server/test_config.py
git commit -m "feat(mcp-server): scaffold mcp_server package with API_BASE_URL config"
```

---

### Task 2: `IssueTrackerClient` HTTP wrapper [specialist: none]

**Charter capability:** Shared HTTP wiring for `list_projects`/`create_project` tools
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/errors.py`
- Create: `mcp_server/client.py`
- Test: `tests/mcp_server/test_client.py`

**Tests:** `tests/mcp_server/test_client.py` (create — first task to touch this behavior; covers
BEH-1/2/3/5 at the HTTP-wrapper layer, plus the spec's 422 error-case row)

**Context to load:**
- Spec BEH-1, BEH-2, BEH-3, BEH-5, and the full Error Cases table
- `app/routers/projects.py`, `app/models.py`, `app/errors.py` (exact shapes: `GET /projects` →
  200 list; `POST /projects` → 201 `{id, key, name, description}`; 409
  `{"message": "Project key '<key>' already exists", "code": "PROJECT_KEY_DUPLICATE"}`; 422
  `{"message": "key is required", "code": "VALIDATION_ERROR"}` or similar for `name`)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_client.py
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
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.client'` (and
`'mcp_server.errors'`), since neither module exists yet.

- [ ] **Implement**

```python
# mcp_server/errors.py
class UpstreamError(Exception):
    """issue-tracker-api returned an HTTP error response (4xx/5xx)."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class UpstreamUnreachableError(Exception):
    """issue-tracker-api could not be reached at all (connection refused, DNS, timeout)."""
```

```python
# mcp_server/client.py
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
```

`httpx.MockTransport` intercepts every request in-process — no live server, no real network,
consistent with the constitution's "fixture-backed, offline only" principle.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/errors.py mcp_server/client.py tests/mcp_server/test_client.py
git commit -m "feat(mcp-server): add IssueTrackerClient HTTP wrapper with typed upstream errors"
```

---

### Task 3: `list_projects` tool [specialist: none]

**Charter capability:** `list_projects` tool — wraps `GET /projects`
**Depends on:** Task 1, Task 2
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/server.py`
- Create: `mcp_server/tools/__init__.py`
- Create: `mcp_server/tools/projects.py`
- Test: `tests/mcp_server/test_project_tools.py`

**Tests:** `tests/mcp_server/test_project_tools.py` (create — first task to touch this behavior;
covers BEH-1)

**Context to load:**
- Spec BEH-1
- Charter Capability Map: `list_projects tool | Wraps GET /projects`
- `mcp_server/client.py`, `mcp_server/config.py` (from Tasks 1/2, full read)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_project_tools.py
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
    # A bare `list` return is not itself a JSON object, so the SDK wraps it under a "result" key
    # for structured_content (the same convention the SDK docs show for a scalar `int` return —
    # `{"result": 3}`). Confirm this exact shape against the installed SDK version during
    # implementation; if it differs, this is the one assertion to adjust.
    assert result.structured_content == {"result": fake._projects}
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.server'` (and
`'mcp_server.tools'`), since neither exists yet.

- [ ] **Implement**

```python
# mcp_server/server.py
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mock-jira-mcp")


def main() -> None:
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)

    mcp.run()


if __name__ == "__main__":
    main()
```

```python
# mcp_server/tools/projects.py
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_projects() -> list[dict]:
    """List all Projects known to issue-tracker-api."""
    client = _client()
    try:
        return await client.list_projects()
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

`mcp_server/tools/__init__.py` is an empty package marker.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/server.py mcp_server/tools/__init__.py mcp_server/tools/projects.py tests/mcp_server/test_project_tools.py
git commit -m "feat(mcp-server): register list_projects MCP tool"
```

---

### Task 4: `create_project` tool [specialist: none]

**Charter capability:** `create_project` tool — wraps `POST /projects`
**Depends on:** Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/tools/projects.py` — add `create_project`
- Modify: `tests/mcp_server/test_project_tools.py` — extend

**Tests:** `tests/mcp_server/test_project_tools.py` (extend — BEH-2, BEH-3, BEH-4, and the spec's
422 Error Cases row; suite already created by Task 3)

**Context to load:**
- Spec BEH-2, BEH-3, BEH-4, and the full Error Cases table (`MCP_INPUT_INVALID`,
  `MCP_UPSTREAM_ERROR` ×2)
- Review note SA-1 (plan header): no `minLength` on `key`/`name` — a blank string must stay
  schema-valid so the API's own 422 is reachable

- [ ] **Write failing test**

```python
# tests/mcp_server/test_project_tools.py (append)
from mcp_server.errors import UpstreamError


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
    # itself, with no extra "result" wrapper. Confirm against the installed SDK during
    # implementation; if it differs, this is the one assertion to adjust.
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
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: FAIL — `call_tool("create_project", ...)` errors with an "unknown tool" result, since
`create_project` is not registered yet.

- [ ] **Implement**

```python
# mcp_server/tools/projects.py (append)
from mcp_server.errors import UpstreamError  # add alongside the existing UpstreamUnreachableError import


@mcp.tool()
async def create_project(key: str, name: str, description: str | None = None) -> dict:
    """Create a Project in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_project(key, name, description)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

`key`/`name` are required, unconstrained `str` parameters (no `Annotated[..., Field(min_length=1)]`
— see SA-1). A call omitting either is rejected by the SDK's own pre-invocation argument
validation before `_client()` ever runs (BEH-4); a call supplying `""` is schema-valid and reaches
`issue-tracker-api`, which returns its own `422` (BEH-2/3 Error Cases table, `422` row).

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/projects.py tests/mcp_server/test_project_tools.py
git commit -m "feat(mcp-server): register create_project MCP tool with verbatim upstream error passthrough"
```

---

### Task 5: Confirm unreachable-API passthrough for both tools [specialist: none]

**Charter capability:** `list_projects` tool, `create_project` tool (BEH-5, shared across both)
**Depends on:** Task 4
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `tests/mcp_server/test_project_tools.py` — extend

**Tests:** `tests/mcp_server/test_project_tools.py` (extend — BEH-5; suite already created by
Task 3)

**Context to load:**
- Spec BEH-5: "When issue-tracker-api is unreachable, then both tools return a clear
  connection-error message rather than hanging or failing silently."

- [ ] **Write failing test**

```python
# tests/mcp_server/test_project_tools.py (append)
from mcp_server.errors import UpstreamUnreachableError

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
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: this specific pair should already PASS if Tasks 3/4's `except UpstreamUnreachableError as
exc: raise ToolError(str(exc))` mapping is correct — run it in isolation *before* Tasks 3/4 land
to confirm it fails without that mapping (e.g. temporarily comment out the `except
UpstreamUnreachableError` branch) if you want a true red/green cycle; in this plan's intended
execution order (Tasks 3 and 4 already complete), this task is a confirmation, not new behavior.

- [ ] **Implement**

No implementation step is expected: the `except UpstreamUnreachableError as exc: raise
ToolError(str(exc)) from exc` branch already exists in both `list_projects` and `create_project`
(Tasks 3 and 4). If this test unexpectedly fails, the fix belongs in that existing branch, not in
new production code.

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/mcp_server/test_project_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests/mcp_server/test_project_tools.py
git commit -m "test(mcp-server): confirm unreachable-API passthrough for list_projects and create_project"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` exists and is used in place of the constitution's generic gate list:

- **Test Suite** (`test`, deterministic, required, severity error): `python3 -m pytest -q` — runs
  `tests/mcp_server/**` alongside the existing `tests/**` suite; nothing in this plan modifies
  existing `issue-tracker-api` tests.
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .` — covers the new
  `mcp_server/` package.
- **JS Unit Tests** (`test-js`, deterministic, required): `node --test "tests_js/**/*.test.js"` —
  unaffected; this plan touches no JS.
- **Integration Tests** (`integration-test`, deterministic, required): command is unwired
  (`command: ""` in `gates.yaml`). This gate is **skipped** for this plan; every test here runs
  against `httpx.MockTransport` or the SDK's in-memory `Client(mcp)` harness, never a live
  `issue-tracker-api` process.
- All acceptance criteria from `project-tools.spec.md` satisfied (BEH-1 through BEH-5).
