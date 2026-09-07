<!-- partial_schema: plan@1 -->

# Implementation Plan: User MCP tools (list_users, create_user)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/user-tools.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-07)
> **Platform:** Python 3.11, no web framework in mcp-server itself (uses the `mcp` SDK's `MCPServer`), `httpx` for upstream HTTP calls

**Goal:** Add `list_users` and `create_user` MCP tools that wrap `issue-tracker-api`'s new `/users` endpoints, mirroring the existing `project-tools`/`issue-tools` pattern exactly (thin wrapper, schema-first validation, verbatim upstream error passthrough), and keep the sibling `mcp-e2e` spec's tool-discovery contract truthful (7 → 9 tools).

**Architecture:** Follows `mcp_server/tools/projects.py` almost verbatim: a `_client()` helper constructing an `IssueTrackerClient`, `@mcp.tool()`-decorated async functions with typed parameters (schema validation happens via the SDK's function-metadata conversion before the function body runs — no manual schema declaration needed), `UpstreamError`/`UpstreamUnreachableError` mapped to `ToolError`. `IssueTrackerClient` (in `mcp_server/client.py`) gets two new methods (`list_users`, `create_user`) alongside its existing `list_projects`/`create_project`/issue methods. The new tools module is imported from `mcp_server/server.py`'s `main()` the same way `projects`/`issues` already are — this is the exact spot the charter's known historical bug (shadow `MCPServer` instance) was fixed, so no change to that re-import pattern is needed, just one more import line alongside the existing two.

---

## File Structure

**Create:**
- `mcp_server/tools/users.py` — `list_users`/`create_user` tool definitions
- `tests/mcp_server/test_user_tools.py` — unit tests against a fake `IssueTrackerClient`, mirroring `tests/mcp_server/test_project_tools.py`
- `tests_e2e/test_mcp_user_tools_e2e.py` — real MCP client/transport e2e tests for both tools

**Modify:**
- `mcp_server/client.py` — add `list_users()` and `create_user(name, email=None, role=None)` methods to `IssueTrackerClient`
- `mcp_server/server.py` — add `import mcp_server.tools.users` inside `main()`, alongside the existing `issues`/`projects` imports
- `tests_e2e/test_mcp_tool_discovery_e2e.py` — add `"list_users"`, `"create_user"` to `_EXPECTED_TOOL_NAMES`; update the test name/assertion set from "seven tools" to the true count (9); add `create_user`'s required-fields assertion
- `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` — BEH-1 wording 7 → 9 tools registered; source-manifest re-stamp once its test file is touched (Task 5)

**Reference (read, do not modify):**
- `mcp_server/tools/projects.py` — the exact pattern to follow (no filter tool, single create tool with optional field)
- `mcp_server/errors.py` — `UpstreamError`/`UpstreamUnreachableError` definitions
- `mcp_server/config.py` — `get_api_base_url()`
- `tests/mcp_server/test_project_tools.py` — unit test pattern (fake client via `monkeypatch.setattr(module, "_client", ...)`, `mcp.Client`/`call_tool`)
- `tests_e2e/mcp_client.py` — real MCP client `connect()` helper
- `tests_e2e/servers.py` — `start_mcp_server`/`start_issue_tracker_api` real-process fixtures
- `tests_e2e/conftest.py` — `mcp_dual_server`/`mcp_server_unreachable` fixtures already available, reused unmodified
- `app/routers/users.py`, `app/models.py` (`UserCreate`/`UserRead`) — upstream request/response shape and error codes (`USER_EMAIL_DUPLICATE` 409, `VALIDATION_ERROR` 422)

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/mcp-server/user-tools.spec.md` (BEH-1 through BEH-5, Error Cases table)
- Charter: `.context-index/specs/features/mcp-server/charter.md` (capabilities: `list_users tool`, `create_user tool`)
- Source files: `mcp_server/client.py` (full read — existing `list_projects`/`create_project`/`_request` methods to follow verbatim)
- Upstream contract: `app/routers/users.py`, `app/models.py` (`UserCreate`/`UserRead` field shapes)

### Task 2 Context
- Spec: `.context-index/specs/features/mcp-server/user-tools.spec.md` (BEH-1 through BEH-5)
- Source files: `mcp_server/tools/projects.py` (full read — pattern to mirror), `mcp_server/server.py` (the `main()` import list to extend), `mcp_server/errors.py`, `mcp_server/config.py`

### Task 3 Context
- Source files: `tests/mcp_server/test_project_tools.py` (full read — unit test pattern), `tests/mcp_server/conftest.py` (`anyio_backend` fixture, already present, no change needed)
- Task 1/2 output: `mcp_server/tools/users.py`, `mcp_server/client.py`

### Task 4 Context
- Source files: `tests_e2e/mcp_client.py`, `tests_e2e/servers.py`, `tests_e2e/conftest.py` (all read-only, already provide everything needed), `tests_e2e/test_mcp_project_tools_e2e.py` (full read — e2e pattern to mirror), `tests_e2e/test_mcp_error_paths_e2e.py` (full read — BEH-4/BEH-5 error-path e2e pattern)

### Task 5 Context
- `tests_e2e/test_mcp_tool_discovery_e2e.py` (full read — current 7-tool assertion)
- `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` (BEH-1 wording, source-manifest frontmatter)

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 (client method, then tools module, then unit tests — each depends on the prior)
- Group B (sequential): Task 4 → Task 5 (e2e tests for the new tools, then the tool-discovery count update — Task 5 depends on Task 4's tools existing over the real transport)

Group B depends on Group A's Task 2 (tools must be registered before any e2e test can call them), so in practice Group A completes fully before Group B starts; the two groups are shown separately only because their internal ordering constraints differ.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | IssueTrackerClient User methods | small | unit | — | 0 create, 1 modify |
| 2 | User MCP tools module + registration | small | unit | Task 1 | 1 create, 1 modify |
| 3 | Unit tests for User tools | small | unit | Task 2 | 1 create, 0 modify |
| 4 | Real MCP client/transport e2e tests | medium | integration | Task 2 | 1 create, 0 modify |
| 5 | Update mcp-e2e tool-discovery count (7 → 9) | small | integration | Task 4 | 0 create, 2 modify |

---

## Task Structure

### Task 1: IssueTrackerClient User methods [specialist: none]

**Charter capability:** `list_users tool`, `create_user tool` (shared HTTP-layer prerequisite)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/client.py` (add two methods after the existing issue methods)
- Test: `tests/mcp_server/test_client.py` (extend with User-method coverage, mirroring the existing `list_projects`/`create_project` tests in that file)

**Tests:** `tests/mcp_server/test_client.py` — extend the existing file with `IssueTrackerClient.list_users`/`create_user` coverage against a mocked `httpx` transport (same pattern the file already uses for Project/Issue methods).

**Context to load:**
- `mcp_server/client.py` (full file — follow `list_projects`/`create_project`/`_request` exactly)
- `app/routers/users.py`, `app/models.py` (`UserCreate` field shape: `name` required, `email`/`role` optional)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_client.py — appended
@pytest.mark.anyio
async def test_list_users_returns_json_array(respx_mock_or_transport):
    ...  # follow the file's existing mocking pattern for list_projects

@pytest.mark.anyio
async def test_create_user_sends_name_email_role_and_returns_created_user():
    ...  # follow the file's existing pattern for create_project, omitting absent fields
```

(Read `tests/mcp_server/test_client.py` first to match its exact existing mocking idiom — do not
invent a new one.)

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/test_client.py`
Expected: FAIL — `AttributeError: 'IssueTrackerClient' object has no attribute 'list_users'`

- [ ] **Implement**

```python
# mcp_server/client.py — add alongside list_projects/create_project
async def list_users(self) -> list[dict]:
    response = await self._request("GET", "/users")
    return response.json()

async def create_user(self, name: str, email: str | None = None, role: str | None = None) -> dict:
    payload: dict = {"name": name}
    if email is not None:
        payload["email"] = email
    if role is not None:
        payload["role"] = role
    response = await self._request("POST", "/users", json=payload)
    return response.json()
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/test_client.py`
Expected: PASS

- [ ] **Commit**

Branch (already created): `feature/mcp-server-user-tools`

```bash
git add mcp_server/client.py tests/mcp_server/test_client.py
git commit -m "feat(mcp-server): add User HTTP methods to IssueTrackerClient"
```

---

### Task 2: User MCP tools module + registration [specialist: none]

**Depends on:** Task 1
**Charter capability:** `list_users tool`, `create_user tool`
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/tools/users.py`
- Modify: `mcp_server/server.py` (add one import line inside `main()`)
- Test: `tests/mcp_server/test_user_tools.py` (Task 3 — written next, but this task's own "verify test passes" step uses a throwaway inline check since the full test file is Task 3's deliverable; alternatively fold Tasks 2+3 verification together — see note below)

**Tests:** `tests/mcp_server/test_user_tools.py` — new suite (Task 3 creates the file; this task's tool code is what that suite exercises). Per this plan's task ordering, write Task 2's implementation and Task 3's tests together in practice if that is more natural — the split exists for TDD granularity, not to force two separate commits when one coherent commit is clearer. If done as one unit, still perform the write-test → verify-fail → implement → verify-pass → commit cycle described across Tasks 2 and 3.

**Context to load:**
- `mcp_server/tools/projects.py` (full file — the exact pattern: `_client()` helper, `@mcp.tool()` functions, `ToolError` mapping)
- `mcp_server/server.py` (the `main()` function's import block)
- `mcp_server/errors.py`, `mcp_server/config.py`

- [ ] **Write failing test**

See Task 3 for the full test file content — this task and Task 3 are implemented together (write the failing tests from Task 3 first, per the TDD cycle, then return to this task's implementation).

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/test_user_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.tools.users'`

- [ ] **Implement**

```python
# mcp_server/tools/users.py
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_users() -> list[dict]:
    """List all Users known to issue-tracker-api."""
    client = _client()
    try:
        return await client.list_users()
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_user(name: str, email: str | None = None, role: str | None = None) -> dict[str, Any]:
    """Create a User in issue-tracker-api.

    `role` is a free-text string — this tool declares no enum for it and delegates all value
    validation to issue-tracker-api's POST /users verbatim (same posture as create_issue's
    issue_type/priority). An invalid role, if the API ever rejects one, surfaces as the existing
    422 MCP_UPSTREAM_ERROR case, not a distinct error code.
    """
    client = _client()
    try:
        return await client.create_user(name, email, role)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

```python
# mcp_server/server.py — inside main(), alongside the existing two imports
def main() -> None:
    import mcp_server.tools.issues
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)
    import mcp_server.tools.users  # noqa: F401  (import registers the tools as a side effect)
    ...
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/test_user_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/users.py mcp_server/server.py
git commit -m "feat(mcp-server): add list_users/create_user MCP tools"
```

---

### Task 3: Unit tests for User tools [specialist: none]

**Depends on:** Task 2
**Charter capability:** `list_users tool`, `create_user tool`
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `tests/mcp_server/test_user_tools.py`
- Test: `tests/mcp_server/test_user_tools.py` (this file IS the test)

**Tests:** `tests/mcp_server/test_user_tools.py` — mirrors `tests/mcp_server/test_project_tools.py` structure exactly (fake client class, `monkeypatch.setattr(users_tools, "_client", ...)`, `mcp.Client`/`call_tool`, `structured_content` assertions).

**Context to load:**
- `tests/mcp_server/test_project_tools.py` (full file — the pattern to copy and adapt)
- `mcp_server/errors.py`

- [ ] **Write failing test**

```python
# tests/mcp_server/test_user_tools.py
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
    fake = _FakeClient(users=[{"id": 1, "name": "Mei Tan", "email": "mei@example.com", "role": "engineer"}])
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_users", {})

    assert result.is_error is False
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
        result = await client.call_tool("create_user", {"name": "Mei Tan", "email": "mei@example.com", "role": "engineer"})

    assert result.is_error is False
    assert result.structured_content == created


@pytest.mark.anyio
async def test_create_user_tool_duplicate_email_errors_with_verbatim_message(monkeypatch):
    fake = _FakeCreateClient(error=UpstreamError(409, "Email 'mei@example.com' already exists"))
    monkeypatch.setattr(users_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_user", {"name": "Mei Tan", "email": "mei@example.com"})

    assert result.is_error is True
    assert "already exists" in result.content[0].text


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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/test_user_tools.py`
Expected: FAIL until Task 2's implementation exists (both tasks are executed together per the TDD cycle noted above).

- [ ] **Implement**

(Covered by Task 2's implementation step — this task's file IS the test authored in that cycle.)

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests/mcp_server/`
Expected: PASS (all of `test_project_tools.py`, `test_issue_tools.py`, `test_user_tools.py`, `test_client.py`, `test_config.py`)

- [ ] **Commit**

```bash
git add tests/mcp_server/test_user_tools.py
git commit -m "test(mcp-server): unit tests for list_users/create_user tools"
```

---

### Task 4: Real MCP client/transport e2e tests [specialist: none]

**Depends on:** Task 2
**Charter capability:** `list_users tool`, `create_user tool`, `End-to-end MCP test suite`
**Strategy:** integration (source: detected — real subprocess servers + real MCP client, matching `mcp-e2e.spec.md`'s existing suite; confidence: high)
**Files:**
- Create: `tests_e2e/test_mcp_user_tools_e2e.py`
- Test: `tests_e2e/test_mcp_user_tools_e2e.py` (this file IS the test)

**Tests:** `tests_e2e/test_mcp_user_tools_e2e.py` — real `mcp.ClientSession` over real streamable-http transport against the real `mcp_dual_server` fixture (already defined in `tests_e2e/conftest.py`, no change needed), cross-verified via a direct real HTTP call to `issue-tracker-api`, mirroring `tests_e2e/test_mcp_project_tools_e2e.py`. Also covers this spec's BEH-3 (duplicate email 409) and BEH-4 (schema-invalid input) using the same `mcp_dual_server`/`mcp_server_unreachable` fixtures `test_mcp_error_paths_e2e.py` already uses — no new fixture needed.

**Context to load:**
- `tests_e2e/test_mcp_project_tools_e2e.py` (full file — pattern to mirror for BEH-1/BEH-2)
- `tests_e2e/test_mcp_error_paths_e2e.py` (full file — pattern to mirror for BEH-4/BEH-5 additions)
- `tests_e2e/mcp_client.py`, `tests_e2e/servers.py`, `tests_e2e/conftest.py` (read only — fixtures already exist)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_user_tools_e2e.py
import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_create_and_list_users_match_real_http_state(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        create_result = await session.call_tool(
            "create_user", {"name": "MCP E2E User", "email": "mcp-e2e-user@example.com", "role": "engineer"}
        )
        assert create_result.is_error is False
        created = create_result.structured_content
        assert created["name"] == "MCP E2E User"

        list_result = await session.call_tool("list_users", {})
        assert list_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        http_users = http_client.get("/users").json()

    mcp_users = list_result.structured_content["result"]
    assert any(u["id"] == created["id"] for u in mcp_users)
    assert any(u["id"] == created["id"] for u in http_users)


@pytest.mark.anyio
async def test_create_user_duplicate_email_errors_with_verbatim_message(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        first = await session.call_tool(
            "create_user", {"name": "Dup User", "email": "mcp-e2e-dup@example.com"}
        )
        assert first.is_error is False

        second = await session.call_tool(
            "create_user", {"name": "Dup User Again", "email": "mcp-e2e-dup@example.com"}
        )

    assert second.is_error is True
    assert "already exists" in second.content[0].text


@pytest.mark.anyio
async def test_create_user_schema_invalid_input_surfaces_protocol_level_error(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.call_tool("create_user", {})  # missing required "name"

    assert result.is_error is True
    assert result.content


@pytest.mark.anyio
async def test_user_tools_unreachable_api_errors_with_clear_message(mcp_server_unreachable):
    async with connect(mcp_server_unreachable) as session:
        result = await session.call_tool("list_users", {})

    assert result.is_error is True
    assert "Could not reach issue-tracker-api" in result.content[0].text
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_mcp_user_tools_e2e.py`
Expected: FAIL (before Task 2 lands) or PASS immediately if run after Task 2 — since this task depends on Task 2, run this after Task 2's tools exist; the "fails first" TDD guarantee is satisfied by Task 2/3's own cycle. If Task 2 is already merged when this file is authored, write the test, confirm it currently fails only if a deliberate typo/wrong-tool-name check is inserted first, then fix — or, more practically, treat this suite as regression coverage authored immediately after Task 2/3 land, verified failing by temporarily reverting the `main()` import (documented here for auditability, not as a literal required step if the team judges it redundant given Tasks 2/3 already TDD'd the same code path from the unit-test side).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_mcp_user_tools_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_user_tools_e2e.py
git commit -m "test(mcp-server): e2e coverage for list_users/create_user over real MCP transport"
```

---

### Task 5: Update mcp-e2e tool-discovery count (7 → 9) [specialist: none]

**Depends on:** Task 4
**Charter capability:** `End-to-end MCP test suite` (sibling spec touch, per review CON-1)
**Strategy:** integration (source: detected, confidence: high — same suite as Task 4)
**Files:**
- Modify: `tests_e2e/test_mcp_tool_discovery_e2e.py`
- Modify: `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` (BEH-1 wording only; re-stamp source-manifest since its test file changed)

**Tests:** `tests_e2e/test_mcp_tool_discovery_e2e.py` (existing file, modified in place)

**Context to load:**
- `tests_e2e/test_mcp_tool_discovery_e2e.py` (full file)
- `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` (BEH-1, source-manifest frontmatter)

- [ ] **Write failing test**

Modify the existing test in place:

```python
# tests_e2e/test_mcp_tool_discovery_e2e.py
_EXPECTED_TOOL_NAMES = {
    "list_projects",
    "create_project",
    "list_issues",
    "get_issue",
    "create_issue",
    "update_issue",
    "delete_issue",
    "list_users",
    "create_user",
}


@pytest.mark.anyio
async def test_real_client_discovers_all_nine_tools_with_correct_schemas(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.list_tools()

    names = {tool.name for tool in result.tools}
    assert names == _EXPECTED_TOOL_NAMES

    by_name = {tool.name: tool for tool in result.tools}
    assert set(by_name["create_project"].input_schema["required"]) == {"key", "name"}
    assert set(by_name["get_issue"].input_schema["required"]) == {"issue_id"}
    assert set(by_name["create_issue"].input_schema["required"]) >= {
        "project_id", "summary", "issue_type", "priority",
    }
    assert "issue_id" not in by_name.get("list_issues").input_schema.get("required", [])
    assert set(by_name["create_user"].input_schema["required"]) == {"name"}
    assert by_name.get("list_users").input_schema.get("required", []) == []
```

Rename the test function from `test_real_client_discovers_all_seven_tools_with_correct_schemas`
to `test_real_client_discovers_all_nine_tools_with_correct_schemas` (the old name asserts a fact
that Task 2 makes false).

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_mcp_tool_discovery_e2e.py`
Expected: FAIL against pre-Task-5 code with the old 7-name set (this test file change is what
makes the assertion match Task 2's already-landed 9-tool reality — if Tasks 2-4 already landed,
this "fails" only in the sense that the OLD assertion would have failed had it not been updated;
verify by temporarily checking out the pre-change file and confirming the old set diverges).

- [ ] **Implement**

Update `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` BEH-1:

```markdown
- **BEH-1** — **When** a real MCP client sends the protocol's tool-listing call to the live
  server, **then** it returns all 9 registered tools with their correct names and input schemas.
```

Re-stamp its source manifest (its test file changed):

```bash
adev source-manifest compute --spec .context-index/specs/features/mcp-server/mcp-e2e.spec.md \
  --files tests_e2e/test_mcp_tool_discovery_e2e.py tests_e2e/mcp_client.py tests_e2e/servers.py \
          requirements-e2e.txt tests/test_requirements_files.py tests_e2e/conftest.py \
          tests_e2e/test_mcp_client_helper.py tests_e2e/test_mcp_error_paths_e2e.py \
          tests_e2e/test_mcp_issue_tools_e2e.py tests_e2e/test_mcp_project_tools_e2e.py \
          tests_e2e/test_mcp_server_fixture.py tests_e2e/test_mcp_server_unreachable_fixture.py
```

(Reuse the exact file list already stamped on `mcp-e2e.spec.md`'s frontmatter — only the content
hash changes, not the file list, since no new file was added to that spec's own manifest.)

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/`
Expected: PASS (full e2e suite, including the renamed 9-tool discovery test)

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_tool_discovery_e2e.py .context-index/specs/features/mcp-server/mcp-e2e.spec.md
git commit -m "test(mcp-server): update mcp-e2e tool-discovery count to 9 (list_users/create_user added)

Spec: .context-index/specs/features/mcp-server/mcp-e2e.spec.md"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:
- Tests pass: `.venv/bin/python3 -m pytest -q` (fast tier, error severity)
- Lint passes: `.venv/bin/ruff check .` (fast tier, error severity)
- E2E smoke suite: `.venv/bin/python3 -m pytest -q tests_e2e/` (e2e tier, warning severity — not a merge blocker but must be run and reported per this task's own instructions)
- All acceptance criteria from `user-tools.spec.md` satisfied
- No integration-test gate configured (unwired sentinel in `gates.yaml`) — not applicable
