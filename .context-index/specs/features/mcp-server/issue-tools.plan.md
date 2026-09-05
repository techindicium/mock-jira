<!-- partial_schema: plan@1 -->

# Implementation Plan: Issue MCP tools (list/get/create/update/delete)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/issue-tools.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-05)
> **Platform:** `mcp` Python SDK (official, PyPI `mcp`, already pinned via `requirements-mcp.txt`
> from `project-tools`), `httpx`, Python 3.11 — extends the existing `mcp_server/` package on
> branch `feat/mcp-server/core`

**Goal:** Extend the already-implemented `mcp_server/` package with five new MCP tools —
`list_issues`, `get_issue`, `create_issue`, `update_issue`, `delete_issue` — that thinly wrap
`issue-tracker-api`'s `/issues` endpoints, mirroring the exact HTTP-wrapper / typed-error /
tool-registration conventions the sibling `project-tools` spec already established.

**Architecture:** `mcp_server/client.py`'s `IssueTrackerClient` gains five new methods (extending
the same class the `list_projects`/`create_project` methods already live on), `mcp_server/errors.py`
is unchanged (the same `UpstreamError`/`UpstreamUnreachableError` pair already covers every 4xx/5xx
and network-failure case), and a new `mcp_server/tools/issues.py` registers the five tools on the
shared `mcp_server.server.mcp` `MCPServer` instance using the exact `_client()` /
`try/except UpstreamError/except UpstreamUnreachableError/finally: await client.aclose()` shape
`mcp_server/tools/projects.py` already uses. `mcp_server/server.py`'s `main()` gains one more
side-effecting import (`import mcp_server.tools.issues`) alongside the existing
`import mcp_server.tools.projects`. Per the constitution's "HTTP contract is the boundary" and the
charter's "pure client of issue-tracker-api" stance, nothing in this plan imports from `app/` or
opens the SQLite file — every read/write is a real HTTP call, mocked via `httpx.MockTransport` (for
client-layer tests) or the SDK's in-memory `Client(mcp)` harness (for tool-layer tests), never a
live server, per "fixture-backed, offline only."

**Constitution Validation (Step 3):** Checked every task's files/behavior against `Architecture
Boundaries`. No task adds a dependency on another repo in the workspace, touches auth, or changes
`issue-tracker-api`'s already-shipped HTTP contract (`app/routers/issues.py` is read-only reference
material, never modified) — this plan only adds a new *consumer* of that contract. No new pip
dependency is introduced (`mcp`, `httpx`, `anyio` are already pinned by `project-tools`).
`governance/boundaries.yaml` has no rules configured (`boundaries: []`), so no file-pattern flags
apply. No task in this plan is marked `[REQUIRES HUMAN APPROVAL]`.

**Design decision — `issue_type`/`priority`/`status` stay unconstrained `str` (not `Literal`):**
Upstream `app/models.py` declares `issue_type`, `priority`, and `status` as `Literal[...]` on
`IssueCreate`/`IssuePatch`, and `app/routers/issues.py`'s `validation_exception_handler` turns an
invalid literal into a `422 {"message": "<field> must be one of: ...", "code": "VALIDATION_ERROR"}`
response. The spec's Error Cases table requires a reachable `422 (invalid status/field value on
create or update)` → `MCP_UPSTREAM_ERROR` passthrough row. If this plan declared these three tool
parameters as MCP-schema `Literal` types, an invalid value would be rejected by the MCP SDK's own
pre-invocation schema validation (`MCP_INPUT_INVALID`) before ever reaching `issue-tracker-api`,
making that 422 row untestable/unreachable through this path — the same tension the reviewed
`project-tools` plan resolved in its **SA-1** note by keeping `key`/`name` as unconstrained `str`
rather than adding `minLength`. This plan makes the analogous choice: `issue_type`, `priority`
(both tools) and `status` (`update_issue` only) are typed as plain `str | None` (required `str` for
`issue_type`/`priority` on `create_issue`), so an invalid enum value is schema-valid at the MCP
layer and reaches `issue-tracker-api`, which returns its own `422` — passed through verbatim by the
existing `except UpstreamError as exc: raise ToolError(exc.message)` branch. `project_id`,
`summary`, `issue_id` remain required, unconstrained fields whose *absence* (not invalid value) is
what the MCP SDK's own required-argument validation catches for BEH-7.

**Review notes carried forward (PASS_WITH_NOTES, per Step 2 STEP_CONTEXT — already fixed in the
spec text this plan was written against):**
- **SA-1** (fixed in spec) — BEH-4b now explicitly covers `create_issue` naming an unknown
  `project_id`: `404` passed through verbatim, same as upstream `issue-lifecycle` BEH-2. Task 4
  covers this.
- **SA-2** (fixed in spec) — `update_issue`'s `id`, `key`, `project_id` fields are **explicit**
  parameters on the tool's input schema (not schema-excluded) and are **silently ignored** — never
  forwarded to `IssueTrackerClient.update_issue`'s payload. Task 5 implements and tests this
  exactly.
- **SA-3** (fixed in spec) — `delete_issue`'s success confirmation is now a defined shape:
  `{"deleted": true, "id": <id>}`. Task 6 implements and tests this exactly.
- **CON-1** (informational, not plan-actionable) — stale `charter-revision` stamp on the spec
  frontmatter is a spec-file concern, not something this plan edits.
- **CON-2** (informational, not plan-actionable) — `API_BASE_URL` precondition parity with
  `project-tools.spec.md` is a spec-file wording concern; the config plumbing itself
  (`mcp_server/config.py::get_api_base_url()`) already exists and is reused unchanged by every
  tool in this plan via the same `_client()` helper pattern.
- **SEC-1** (informational, no action required) — verbatim error passthrough is intentional and
  correct per the charter's explicit no-auth, fixture-backed stance; unchanged by this plan.

---

## File Structure

**Create:**
- `mcp_server/tools/issues.py` — registers `list_issues`, `get_issue`, `create_issue`,
  `update_issue`, `delete_issue` on the shared `mcp` `MCPServer` instance
- `tests/mcp_server/test_issue_tools.py` — BEH-1 through BEH-7 coverage at the tool layer, using
  `mcp.Client(mcp)` in-memory (no subprocess, no network), mirroring
  `tests/mcp_server/test_project_tools.py`'s `_FakeClient` pattern

**Modify:**
- `mcp_server/client.py` — add `list_issues`, `get_issue`, `create_issue`, `update_issue`,
  `delete_issue` methods to the existing `IssueTrackerClient` class
- `mcp_server/server.py` — add `import mcp_server.tools.issues` alongside the existing
  `import mcp_server.tools.projects` in `main()`
- `tests/mcp_server/test_client.py` — extend with `IssueTrackerClient` issue-method coverage

**Reference (read, do not modify):**
- `app/routers/issues.py` — exact route shapes this plan wraps: `POST /issues` (201, unknown
  `project_id` → 404 `{"message": "Project <id> not found", "code": "ISSUE_PROJECT_NOT_FOUND"}`),
  `GET /issues` (200, `project_id`/`status` query filters), `GET /issues/{id}` (200, unknown id →
  404 `{"message": "Issue <id> not found", "code": "ISSUE_NOT_FOUND"}`), `PATCH /issues/{id}` (200,
  only `_PATCHABLE_FIELDS` — `summary`, `description`, `issue_type`, `priority`, `assignee`,
  `reporter`, `status` — are ever written), `DELETE /issues/{id}` (204, empty body)
- `app/models.py` — `IssueCreate {project_id: int, summary: str, issue_type: Literal[...],
  priority: Literal[...], description|assignee|reporter: str | None}`, `IssueRead` (full response
  shape), `IssuePatch` (all fields optional)
- `app/errors.py` — confirms every error response (`400`/`404`/`422`) is a flat
  `{"message": ..., "code": ...}` JSON body — the shape `mcp_server/client.py`'s existing
  `_request()` error mapping already relies on; unchanged by this plan
- `mcp_server/client.py` (current state) — existing `list_projects`/`create_project`/`_request`
  methods this plan's new methods must match in style (same `_request` helper, same
  `httpx.AsyncClient`-backed constructor)
- `mcp_server/tools/projects.py` (current state) — existing `_client()` helper and
  `@mcp.tool()` / `try/except UpstreamError/except UpstreamUnreachableError/finally` shape this
  plan's new tools must match exactly
- `.context-index/specs/features/mcp-server/charter.md` — Capability Map (five Issue tool rows),
  Domain Model (`McpTool` entity), Invariants ("input_schema validates before the wrapped HTTP
  call", "error response always carries the underlying API's error message verbatim")
- `CLAUDE.md` — constitution: "HTTP contract is the boundary", "no inbound dependencies",
  "breaking API changes are coordinated, not silent"
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands

---

## Context Packets

> No `source-manifest.files[]` exists on this spec yet. Context packets fall back to charter +
> spec + constitution + the actual `issue-tracker-api` route/model source, per Step 2's
> "no source-manifest" fallback, matching how `project-tools.plan.md` was assembled.

### Task 1 Context
- Spec: BEH-1, BEH-2, BEH-3, Error Cases table (404 row, unreachable row)
- Charter: `charter.md` (Capability: `list_issues tool`, `get_issue tool`; Invariants — error
  passthrough)
- Source files: `app/routers/issues.py` (full read — `list_issues`/`get_issue` route shapes),
  `app/models.py` (full read — `IssueRead` field names/types)
- Source files (current state, full read): `mcp_server/client.py` (existing `list_projects`,
  `_request` pattern to extend)

### Task 2 Context
- Spec: BEH-4, BEH-4b, BEH-5, BEH-6, Error Cases table (all rows)
- Charter: `charter.md` (Capability: `create_issue tool`, `update_issue tool`, `delete_issue tool`)
- Source files: `app/routers/issues.py` (full read — `create_issue`, `patch_issue`, `delete_issue`
  route shapes, `_PATCHABLE_FIELDS` tuple, 204-empty-body delete response), `app/models.py` (full
  read — `IssueCreate`, `IssuePatch`)
- Source files (from Task 1, full read): `mcp_server/client.py` (extending further)

### Task 3 Context
- Spec: BEH-1, BEH-2, BEH-3
- Charter: `charter.md` (Capability: `list_issues tool`, `get_issue tool`; Exposed APIs table)
- Source files (from Task 1/2, full read): `mcp_server/client.py`
- Source files (current state, full read): `mcp_server/tools/projects.py` (the `_client()` /
  `@mcp.tool()` / error-mapping pattern to replicate), `mcp_server/server.py` (existing `main()` to
  extend with a second tools import)

### Task 4 Context
- Spec: BEH-4, BEH-4b, Error Cases table (`MCP_INPUT_INVALID` row, `MCP_UPSTREAM_ERROR` 404 row)
- Charter: `charter.md` (Capability: `create_issue tool`)
- Design decision (plan header): `issue_type`/`priority` stay unconstrained `str`, not `Literal`
- Source files (from Task 3, full read — extending, not replacing): `mcp_server/tools/issues.py`,
  `tests/mcp_server/test_issue_tools.py`

### Task 5 Context
- Spec: BEH-5, Preconditions (immutable `id`/`key`/`project_id`), review note SA-2 (plan header)
- Charter: `charter.md` (Capability: `update_issue tool`; Invariant: schema validates before HTTP
  call — satisfied here by declaring `id`/`key`/`project_id` explicitly, then dropping them before
  the client call, per the STEP_CONTEXT-fixed spec wording)
- Source files (from Task 4, full read — extending): `mcp_server/tools/issues.py`,
  `tests/mcp_server/test_issue_tools.py`

### Task 6 Context
- Spec: BEH-6, Postconditions, review note SA-3 (plan header — `{"deleted": true, "id": <id>}`
  shape)
- Charter: `charter.md` (Capability: `delete_issue tool`)
- Source files (from Task 5, full read — extending): `mcp_server/tools/issues.py`,
  `tests/mcp_server/test_issue_tools.py`

### Task 7 Context
- Spec: Error Cases table (`MCP_UPSTREAM_UNREACHABLE` row, all five tools)
- Charter: `charter.md` (Quality Attributes → Observability: "Tool errors surface the underlying
  API error message unchanged")
- Source files (from Task 1-6, full read — verifying only, no expected production-code change):
  `mcp_server/client.py`, `mcp_server/tools/issues.py`

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7

Every task in this plan modifies a file the immediately preceding task also touched or extended:
Tasks 1 and 2 both extend `mcp_server/client.py`/`tests/mcp_server/test_client.py`; Tasks 3-7 all
extend `mcp_server/tools/issues.py`/`tests/mcp_server/test_issue_tools.py` (Task 3 creates both
files, the rest extend them). There is no file-disjoint pair of tasks in this plan, so no group can
run independently of another — unlike `project-tools.plan.md`, which had two genuinely independent
foundation tasks (`config.py` vs `client.py`) before its tool-layer chain began.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | `IssueTrackerClient` read methods (`list_issues`, `get_issue`) | small | unit | — | 0 create, 2 modify |
| 2 | `IssueTrackerClient` write methods (`create_issue`, `update_issue`, `delete_issue`) | medium | unit | Task 1 | 0 create, 2 modify |
| 3 | `list_issues` + `get_issue` tools | medium | unit | Task 1, Task 2 | 2 create, 1 modify |
| 4 | `create_issue` tool | medium | unit | Task 3 | 0 create, 2 modify |
| 5 | `update_issue` tool (immutable fields silently ignored) | medium | unit | Task 4 | 0 create, 2 modify |
| 6 | `delete_issue` tool (`{"deleted": true, "id": <id>}`) | small | unit | Task 5 | 0 create, 2 modify |
| 7 | [Regression] Confirm unreachable-API passthrough (all five tools) | small | unit | Task 6 | 0 create, 1 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no `test_strategies` entries in `manifest.yaml` matching `mcp_server/**` paths). Per
Step 5, the Strategy Summary section is omitted since every task is `unit`. No
`infra_requirements:` is declared on the spec and no task needs external infrastructure — every
test in this plan runs against `httpx.MockTransport` or the SDK's own in-memory `Client(mcp)`
harness, never a live server — so the Test Infrastructure Requirements section is also omitted.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). `tests/mcp_server/test_client.py` is the shared per-behavior suite
for the HTTP-wrapper layer: already created by `project-tools`' Task 2, extended here by Task 1
(BEH-1/2/3) and Task 2 (BEH-4/4b/5/6). `tests/mcp_server/test_issue_tools.py` is the shared
per-behavior suite for the tool layer: created by Task 3 (BEH-1/2/3) and extended by Task 4
(BEH-4/4b), Task 5 (BEH-5), Task 6 (BEH-6), and Task 7 (the shared unreachable-API error row).

---

## Task Structure

### Task 1: `IssueTrackerClient` read methods (`list_issues`, `get_issue`) [specialist: none]

**Charter capability:** `list_issues` tool, `get_issue` tool (HTTP-wrapper layer)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/client.py` — add `list_issues`, `get_issue`
- Test: `tests/mcp_server/test_client.py` — extend

**Tests:** `tests/mcp_server/test_client.py` (extend — BEH-1, BEH-2, BEH-3, and the 404 Error Cases
row at the HTTP-wrapper layer; suite already created by `project-tools`' Task 2)

**Context to load:**
- Spec BEH-1, BEH-2, BEH-3, Error Cases table (404 row)
- `app/routers/issues.py` (`list_issues`, `get_issue` routes), `app/models.py` (`IssueRead`)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_client.py (append)
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: FAIL — `AttributeError: 'IssueTrackerClient' object has no attribute 'list_issues'` (and
`'get_issue'`), since neither method exists yet.

- [ ] **Implement**

```python
# mcp_server/client.py (append inside IssueTrackerClient, after create_project)
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
```

No change to `_request()` or `mcp_server/errors.py` — the existing 4xx/5xx → `UpstreamError` and
network-failure → `UpstreamUnreachableError` mapping already covers these two new methods.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: PASS

- [ ] **Commit**

Branch (already created): `feat/mcp-server/core`

```bash
git add mcp_server/client.py tests/mcp_server/test_client.py
git commit -m "feat(mcp-server): add IssueTrackerClient.list_issues and get_issue"
```

---

### Task 2: `IssueTrackerClient` write methods (`create_issue`, `update_issue`, `delete_issue`) [specialist: none]

**Charter capability:** `create_issue` tool, `update_issue` tool, `delete_issue` tool
(HTTP-wrapper layer)
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/client.py` — add `create_issue`, `update_issue`, `delete_issue`
- Test: `tests/mcp_server/test_client.py` — extend

**Tests:** `tests/mcp_server/test_client.py` (extend — BEH-4, BEH-4b, BEH-5, BEH-6, and the 422
Error Cases row; suite already extended by Task 1)

**Context to load:**
- Spec BEH-4, BEH-4b, BEH-5, BEH-6, Error Cases table (all rows)
- `app/routers/issues.py` (`create_issue`, `patch_issue`, `delete_issue` routes,
  `_PATCHABLE_FIELDS`), `app/models.py` (`IssueCreate`, `IssuePatch`)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_client.py (append)
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: FAIL — `AttributeError: 'IssueTrackerClient' object has no attribute 'create_issue'`
(and `'update_issue'`, `'delete_issue'`), since none exist yet.

- [ ] **Implement**

```python
# mcp_server/client.py (append inside IssueTrackerClient, after get_issue)
    async def create_issue(
        self,
        project_id: int,
        summary: str,
        issue_type: str,
        priority: str,
        description: str | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
    ) -> dict:
        payload: dict = {
            "project_id": project_id,
            "summary": summary,
            "issue_type": issue_type,
            "priority": priority,
        }
        if description is not None:
            payload["description"] = description
        if assignee is not None:
            payload["assignee"] = assignee
        if reporter is not None:
            payload["reporter"] = reporter
        response = await self._request("POST", "/issues", json=payload)
        return response.json()

    async def update_issue(self, issue_id: int, **fields) -> dict:
        payload = {key: value for key, value in fields.items() if value is not None}
        response = await self._request("PATCH", f"/issues/{issue_id}", json=payload)
        return response.json()

    async def delete_issue(self, issue_id: int) -> None:
        await self._request("DELETE", f"/issues/{issue_id}")
```

`delete_issue` deliberately does not call `.json()` on the response — `DELETE /issues/{id}`
responds `204` with an empty body (confirmed against `app/routers/issues.py`), so there is nothing
to parse; the tool layer (Task 6) synthesizes the `{"deleted": true, "id": <id>}` confirmation
itself. `update_issue` accepts `**fields` rather than named keyword parameters at the client layer
(the tool layer, Task 5, is where named/explicit parameters and the immutable-field-drop logic
live) — this mirrors `create_project`'s existing `description=None`-only-if-set pattern for the
optional fields.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_client.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/client.py tests/mcp_server/test_client.py
git commit -m "feat(mcp-server): add IssueTrackerClient.create_issue, update_issue, delete_issue"
```

---

### Task 3: `list_issues` + `get_issue` tools [specialist: none]

**Charter capability:** `list_issues` tool — wraps `GET /issues`; `get_issue` tool — wraps
`GET /issues/{id}`
**Depends on:** Task 1, Task 2
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `mcp_server/tools/issues.py`
- Create: `tests/mcp_server/test_issue_tools.py`
- Modify: `mcp_server/server.py` — add `import mcp_server.tools.issues` to `main()`

**Tests:** `tests/mcp_server/test_issue_tools.py` (create — first task to touch this behavior;
covers BEH-1, BEH-2, BEH-3, and BEH-7 for `list_issues`/`get_issue`)

**Context to load:**
- Spec BEH-1, BEH-2, BEH-3, BEH-7
- Charter Capability Map: `list_issues tool | Wraps GET /issues`, `get_issue tool | Wraps
  GET /issues/{id}`
- `mcp_server/client.py`, `mcp_server/tools/projects.py`, `mcp_server/server.py` (current state,
  full read)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_issue_tools.py
import pytest
from mcp import Client

import mcp_server.tools.issues as issues_tools
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.tools.issues'`, since the module
does not exist yet.

- [ ] **Implement**

```python
# mcp_server/tools/issues.py
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_issues(project_id: int | None = None, status: str | None = None) -> list[dict]:
    """List Issues known to issue-tracker-api, optionally filtered by project_id and/or status."""
    client = _client()
    try:
        return await client.list_issues(project_id, status)
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def get_issue(issue_id: int) -> dict[str, Any]:
    """Fetch one Issue by id from issue-tracker-api."""
    client = _client()
    try:
        return await client.get_issue(issue_id)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

```python
# mcp_server/server.py (modify main())
def main() -> None:
    import mcp_server.tools.issues  # noqa: F401  (import registers the tools as a side effect)
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)

    mcp.run()
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/issues.py mcp_server/server.py tests/mcp_server/test_issue_tools.py
git commit -m "feat(mcp-server): register list_issues and get_issue MCP tools"
```

---

### Task 4: `create_issue` tool [specialist: none]

**Charter capability:** `create_issue` tool — wraps `POST /issues`
**Depends on:** Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/tools/issues.py` — add `create_issue`
- Modify: `tests/mcp_server/test_issue_tools.py` — extend

**Tests:** `tests/mcp_server/test_issue_tools.py` (extend — BEH-4, BEH-4b, and the schema-invalid
`MCP_INPUT_INVALID` Error Cases row; suite already created by Task 3)

**Context to load:**
- Spec BEH-4, BEH-4b, Error Cases table (`MCP_INPUT_INVALID` row, 404 row)
- Design decision (plan header): `issue_type`/`priority` stay unconstrained `str`

- [ ] **Write failing test**

```python
# tests/mcp_server/test_issue_tools.py (append)
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: FAIL — `call_tool("create_issue", ...)` errors with an "unknown tool" result, since
`create_issue` is not registered yet.

- [ ] **Implement**

```python
# mcp_server/tools/issues.py (append)
@mcp.tool()
async def create_issue(
    project_id: int,
    summary: str,
    issue_type: str,
    priority: str,
    description: str | None = None,
    assignee: str | None = None,
    reporter: str | None = None,
) -> dict[str, Any]:
    """Create an Issue under a Project in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_issue(
            project_id, summary, issue_type, priority, description, assignee, reporter
        )
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

`project_id`, `summary`, `issue_type`, `priority` are required parameters — the SDK's own
pre-invocation argument validation rejects a call missing any of them (BEH-7) before `_client()`
ever runs. `issue_type`/`priority` are unconstrained `str` (see plan header design decision), so an
invalid value (e.g. `"urgent"`) is schema-valid and reaches `issue-tracker-api`, which returns its
own `422` — passed through verbatim by the `except UpstreamError` branch already covering BEH-4b.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/issues.py tests/mcp_server/test_issue_tools.py
git commit -m "feat(mcp-server): register create_issue MCP tool with 404/422 passthrough"
```

---

### Task 5: `update_issue` tool (immutable fields silently ignored) [specialist: none]

**Charter capability:** `update_issue` tool — wraps `PATCH /issues/{id}`, including status
transitions
**Depends on:** Task 4
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/tools/issues.py` — add `update_issue`
- Modify: `tests/mcp_server/test_issue_tools.py` — extend

**Tests:** `tests/mcp_server/test_issue_tools.py` (extend — BEH-5, including the immutable-field
silent-ignore behavior fixed by review note SA-2; suite already extended by Task 4)

**Context to load:**
- Spec BEH-5, Preconditions ("`id`, `key`, and `project_id` are not mutable... silently ignored if
  present"), review note SA-2 (plan header)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_issue_tools.py (append)
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: FAIL — `call_tool("update_issue", ...)` errors with an "unknown tool" result, since
`update_issue` is not registered yet.

- [ ] **Implement**

```python
# mcp_server/tools/issues.py (append)
@mcp.tool()
async def update_issue(
    issue_id: int,
    summary: str | None = None,
    description: str | None = None,
    issue_type: str | None = None,
    priority: str | None = None,
    assignee: str | None = None,
    reporter: str | None = None,
    status: str | None = None,
    id: int | None = None,
    key: str | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    """Update one or more mutable fields on an Issue in issue-tracker-api.

    `id`, `key`, and `project_id` are immutable and are silently ignored if present —
    an Issue's identity and project never change after creation.
    """
    client = _client()
    try:
        return await client.update_issue(
            issue_id,
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            assignee=assignee,
            reporter=reporter,
            status=status,
        )
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

`id`, `key`, `project_id` are declared as explicit optional parameters — per SA-2's resolution, the
tool's input schema accepts them (so a caller that (redundantly) echoes them back is not rejected
with `MCP_INPUT_INVALID`) but the implementation never reads them: only the seven mutable fields are
forwarded to `IssueTrackerClient.update_issue`'s `**fields`, matching upstream `PATCH
/issues/{id}`'s own `_PATCHABLE_FIELDS` tuple exactly.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/issues.py tests/mcp_server/test_issue_tools.py
git commit -m "feat(mcp-server): register update_issue MCP tool, silently ignoring immutable fields"
```

---

### Task 6: `delete_issue` tool (`{"deleted": true, "id": <id>}`) [specialist: none]

**Charter capability:** `delete_issue` tool — wraps `DELETE /issues/{id}`
**Depends on:** Task 5
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/tools/issues.py` — add `delete_issue`
- Modify: `tests/mcp_server/test_issue_tools.py` — extend

**Tests:** `tests/mcp_server/test_issue_tools.py` (extend — BEH-6, including the synthesized
success-confirmation shape fixed by review note SA-3; suite already extended by Task 5)

**Context to load:**
- Spec BEH-6, Postconditions, review note SA-3 (plan header — `{"deleted": true, "id": <id>}`)

- [ ] **Write failing test**

```python
# tests/mcp_server/test_issue_tools.py (append)
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
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: FAIL — `call_tool("delete_issue", ...)` errors with an "unknown tool" result, since
`delete_issue` is not registered yet.

- [ ] **Implement**

```python
# mcp_server/tools/issues.py (append)
@mcp.tool()
async def delete_issue(issue_id: int) -> dict[str, Any]:
    """Delete an Issue in issue-tracker-api and return a deletion confirmation."""
    client = _client()
    try:
        await client.delete_issue(issue_id)
        return {"deleted": True, "id": issue_id}
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

`DELETE /issues/{id}` responds `204` with an empty body (confirmed against
`app/routers/issues.py`), so `IssueTrackerClient.delete_issue` (Task 2) returns nothing to parse —
the tool synthesizes the `{"deleted": true, "id": <id>}` confirmation itself, per SA-3.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/issues.py tests/mcp_server/test_issue_tools.py
git commit -m "feat(mcp-server): register delete_issue MCP tool with structured deletion confirmation"
```

---

### Task 7: [REGRESSION/CONSOLIDATION] Confirm unreachable-API passthrough for all five tools [specialist: none]

> **Note on task kind:** unlike Tasks 1-6, this is a regression/consolidation task, not a
> greenfield TDD task — the `except UpstreamUnreachableError` branch already exists on every tool
> (added in Tasks 3-6), so there is no new production code expected here. It is still run through
> the same write-test → verify → (no-op) → verify checklist shape for consistency with the rest of
> this plan, but its "Verify test fails" step is a sanity check confirming the row is genuinely
> covered end-to-end, not a red step preceding new implementation. This mirrors
> `project-tools.plan.md`'s Task 5, which uses the identical pattern for the same reason.

**Charter capability:** `list_issues`, `get_issue`, `create_issue`, `update_issue`, `delete_issue`
tools (shared Error Cases row: `MCP_UPSTREAM_UNREACHABLE`)
**Depends on:** Task 6
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `tests/mcp_server/test_issue_tools.py` — extend

**Tests:** `tests/mcp_server/test_issue_tools.py` (extend — Error Cases table's "API unreachable"
row across all five tools; suite already extended by Task 6)

**Context to load:**
- Spec Error Cases table: "API unreachable → Tool call errors with a clear connection message →
  `MCP_UPSTREAM_UNREACHABLE`"

- [ ] **Write failing test**

```python
# tests/mcp_server/test_issue_tools.py (append)
from mcp_server.errors import UpstreamUnreachableError  # noqa: F811 (re-import for clarity at point of use)

_UNREACHABLE_MESSAGE = "Could not reach issue-tracker-api at http://issue-tracker-api: connection refused"


class _UnreachableClient(_FakeClient):
    async def list_issues(self, project_id=None, status=None):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def get_issue(self, issue_id):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def create_issue(self, *args, **kwargs):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def update_issue(self, issue_id, **fields):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)

    async def delete_issue(self, issue_id):
        raise UpstreamUnreachableError(_UNREACHABLE_MESSAGE)


@pytest.mark.anyio
@pytest.mark.parametrize(
    "tool_name, arguments",
    [
        ("list_issues", {}),
        ("get_issue", {"issue_id": 1}),
        ("create_issue", {"project_id": 1, "summary": "x", "issue_type": "bug", "priority": "low"}),
        ("update_issue", {"issue_id": 1, "status": "done"}),
        ("delete_issue", {"issue_id": 1}),
    ],
)
async def test_issue_tool_unreachable_api_errors_with_clear_message(monkeypatch, tool_name, arguments):
    monkeypatch.setattr(issues_tools, "_client", lambda: _UnreachableClient())

    async with Client(mcp) as client:
        result = await client.call_tool(tool_name, arguments)

    assert result.is_error is True
    assert "issue-tracker-api" in result.content[0].text
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: this parametrized test should already PASS if Tasks 3-6's `except
UpstreamUnreachableError as exc: raise ToolError(str(exc))` mapping is correct on each tool — run
it in isolation *before* Tasks 3-6 land to confirm it fails without that mapping (e.g. temporarily
comment out one tool's `except UpstreamUnreachableError` branch) if a true red/green cycle is
wanted; in this plan's intended execution order (Tasks 3-6 already complete), this task is a
confirmation, not new behavior.

- [ ] **Implement**

No implementation step is expected: the `except UpstreamUnreachableError as exc: raise
ToolError(str(exc)) from exc` branch already exists on all five tools (Tasks 3-6). If any
parametrized case unexpectedly fails, the fix belongs in that tool's existing branch, not in new
production code.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/mcp_server/test_issue_tools.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests/mcp_server/test_issue_tools.py
git commit -m "test(mcp-server): confirm unreachable-API passthrough for all five issue tools"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` exists and is used in place of the constitution's generic gate list:

- **Test Suite** (`test`, deterministic, required, severity error): `.venv/bin/python3 -m pytest -q`
  — runs `tests/mcp_server/**` alongside the existing `tests/**` suite; nothing in this plan
  modifies existing `issue-tracker-api` tests or the already-passing `project-tools` tool tests.
- **Linter** (`lint`, deterministic, required, severity error): `.venv/bin/ruff check .` — covers
  the new `mcp_server/tools/issues.py` and the extended `mcp_server/client.py`/`server.py`.
- **JS Unit Tests** (`test-js`, deterministic, required): `node --test "tests_js/**/*.test.js"` —
  unaffected; this plan touches no JS.
- **Integration Tests** (`integration-test`, deterministic, required): command is unwired
  (`command: ""` in `gates.yaml`). This gate is **skipped** for this plan; every test here runs
  against `httpx.MockTransport` or the SDK's in-memory `Client(mcp)` harness, never a live
  `issue-tracker-api` process.
- All acceptance criteria from `issue-tools.spec.md` satisfied (BEH-1 through BEH-7).
