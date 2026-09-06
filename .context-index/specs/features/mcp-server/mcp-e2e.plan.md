<!-- partial_schema: plan@1 -->

# Implementation Plan: End-to-end MCP test suite (real client/transport)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Spec:** .context-index/specs/features/mcp-server/mcp-e2e.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-06)
> **Platform:** Python 3.12, `mcp` SDK 2.1.1 (real client + real server), `httpx`, `anyio`,
> `pytest` 9.1.1 with `pytest.mark.anyio` — reuses this repo's existing `tests_e2e/` real-process
> e2e suite, never `mcp_server`'s internal Python objects.

**Goal:** Add a real-client, real-transport e2e test suite that drives the already-implemented
`mcp-server` (both `project-tools` and `issue-tools` are `validated`) entirely through the actual
MCP protocol over its streamable-http transport, cross-verified against `issue-tracker-api` over
real HTTP — the same integration surface an external agent uses.

**Architecture:** This plan adds one new real-process helper (`start_mcp_server`, alongside the
already-implemented `start_issue_tracker_api`) to `tests_e2e/servers.py`, two new pytest fixtures
in `tests_e2e/conftest.py` wiring server processes together for two distinct topologies (a
shared dual-server pair for BEH-1 through BEH-4, and BEH-5's own single-process, dead-upstream
fixture per the review's SA-1 fix), and a small real MCP client helper
(`tests_e2e/mcp_client.py`) wrapping the `mcp` SDK's `streamable_http_client` +
`ClientSession` connect/initialize pattern. Five new test modules under `tests_e2e/` then drive
every behavior through that helper. All work here is additive — no `mcp_server/` source file
changes, since both wrapped specs are already `validated`.

**mcp Python SDK version note (verified against the installed 2.1.1 SDK, matching the sibling
`project-tools.plan.md`'s note):** `streamable_http_client` lives at
`mcp.client.streamable_http.streamable_http_client` (not `streamablehttp_client`) and is an
`@asynccontextmanager` yielding a `(read_stream, write_stream)` 2-tuple — confirmed via
`inspect.getsource` against `.venv/lib/python3.12/site-packages/mcp/client/streamable_http.py`
during planning, since the name is easy to get wrong by analogy with other SDK versions.
`mcp.ClientSession(read_stream, write_stream)` is itself an async context manager; its
`initialize()` performs the MCP handshake, `list_tools()` returns `ListToolsResult`, and
`call_tool(name, arguments)` returns a `CallToolResult` — **never raises** for a tool-level or
schema-validation failure. Per `mcp/types.py`'s own docstring on `CallToolResult` and confirmed
in `mcp/server/mcpserver/server.py:441` (`return CallToolResult(..., is_error=True)`), both
schema-invalid input (BEH-4) and a `ToolError` raised inside a tool body (BEH-5, via
`mcp_server`'s existing `UpstreamUnreachableError` → `ToolError` mapping in
`mcp_server/tools/*.py`) surface identically: a normal `CallToolResult` return with
`is_error=True` and the message in `result.content[0].text`. This is the exact mechanism the
existing in-process unit tests (`tests/mcp_server/test_issue_tools.py`) already assert on for
BEH-4/BEH-5 at the tool layer — this plan asserts the same outcome, but over the real transport.
The MCP endpoint path is the SDK's default `streamable_http_path="/mcp"`
(`MCPServer.run_streamable_http_async`'s default, confirmed via `inspect.getsource`) — every
helper in this plan connects to `f"{mcp_base_url}/mcp"`, never the bare base URL.

**Dependency wiring decision:** `requirements-e2e.txt` currently lists only `playwright` (used by
`tests_e2e/browser.py` for the `kanban-ui` ui-e2e suite). `requirements-mcp.txt` already pins
`mcp`, `httpx`, `anyio` for `mcp_server/` itself. Per the pipeline's guidance to avoid installing
the `mcp` SDK twice under different names, Task 1 adds a single `-r requirements-mcp.txt` line to
`requirements-e2e.txt` (a standard pip requirements-file include) rather than re-listing `mcp`,
`httpx`, `anyio` there directly — one source of truth for the `mcp` SDK's pinned version, reused
by both the shipped server and this test-only client code.

**Health-check design decision:** `start_issue_tracker_api` polls `GET /` (the FastAPI app's root
route) until it answers 200. `mcp-server`'s streamable-http endpoint has no equivalent bare-GET
health route — `docker-compose.yml` itself defines no healthcheck for the `mcp-server` service
(only `issue-tracker-api` has one; `mcp-server`'s compose entry only depends on
`issue-tracker-api`'s healthcheck), so there is no existing repo convention to match here. This
plan's `start_mcp_server` therefore polls with a plain TCP connect (`socket.create_connection`)
to the process's port, treating "the OS accepts a connection" as "the ASGI server has bound the
port and is ready" — deliberately coarser than a full MCP handshake, so this fixture stays
health-check-agnostic of BEH-5's own dead-upstream scenario (which must still let `mcp-server`
itself start up cleanly; only its *tool calls* fail). Full protocol correctness is asserted by
the tests themselves via the real MCP client, never by the fixture.

**Fixture topology decision (review note SA-1, already fixed in the reviewed spec):** BEH-1
through BEH-4 share one session-scoped `mcp_dual_server` fixture (mirroring the existing shared
`server` fixture's pattern in `tests_e2e/conftest.py` — tests use unique keys per project/issue to
avoid cross-test collisions in the shared database, e.g. `E2EMCP...`). BEH-5 gets its own
function-scoped `mcp_server_unreachable` fixture that starts **only** `mcp-server`. Both fixtures
are torn down (subprocess terminate/kill, per the existing `start_issue_tracker_api` convention)
at the end of their scope, satisfying the spec's Postcondition ("Both server processes are torn
down after the test session") for whichever processes each fixture actually started.

**Constitution Validation (Step 3):** Checked every task's files against `Architecture
Boundaries`. No task changes `issue-tracker-api`'s or `mcp-server`'s existing HTTP/MCP contract —
this plan only adds test-only consumers of both, over their already-shipped surfaces. No new
inbound dependency is introduced (the `mcp`/`httpx`/`anyio` packages are already a pip dependency
of this same repo's `mcp_server/`, reused via `-r requirements-mcp.txt`, not a new workspace repo
dependency). `governance/boundaries.yaml` has no rules configured (`boundaries: []`), so no
file-pattern flags apply. No task is marked `[REQUIRES HUMAN APPROVAL]`.

**Review notes carried forward (PASS_WITH_NOTES, verdict from `mcp-e2e.review.md`):**
- **SA-1** (warning) — already resolved in the reviewed spec (BEH-5 now names its own dedicated
  fixture explicitly) and carried through in this plan's Fixture topology decision above.
- **CON-1** (warning) — already resolved: the parent charter's Dependencies table now lists
  `docker-packaging` (confirmed by re-reading `charter.md` during Step 2 context loading).
- **SA-2** (suggestion) — no plan-level action needed; this plan's tests assert on the SDK's own
  `CallToolResult.is_error`/`content` fields, not on the spec's `E2E_*` labels, so the naming
  distinction SA-2 asked to clarify doesn't affect any assertion here.

---

## File Structure

**Create:**
- `tests_e2e/mcp_client.py` — `connect(mcp_base_url)`: an async context manager wrapping
  `streamable_http_client` + `ClientSession`, yielding an already-`initialize()`d session
- `tests_e2e/test_mcp_server_fixture.py` — coverage for the new `start_mcp_server` helper
- `tests_e2e/test_mcp_server_unreachable_fixture.py` — coverage for the `mcp_server_unreachable`
  fixture (BEH-5's dedicated topology)
- `tests_e2e/test_mcp_client_helper.py` — coverage for `tests_e2e/mcp_client.py` itself
- `tests_e2e/test_mcp_tool_discovery_e2e.py` — BEH-1
- `tests_e2e/test_mcp_project_tools_e2e.py` — BEH-2
- `tests_e2e/test_mcp_issue_tools_e2e.py` — BEH-3
- `tests_e2e/test_mcp_error_paths_e2e.py` — BEH-4, BEH-5
- `tests/test_requirements_files.py` — content check for the `requirements-e2e.txt` wiring

**Modify:**
- `requirements-e2e.txt:1` — add `-r requirements-mcp.txt` so `pip install -r
  requirements-e2e.txt` pulls in the `mcp` SDK/`httpx`/`anyio` this suite's client code needs,
  without re-pinning them separately
- `tests_e2e/servers.py` — add `start_mcp_server(api_base_url)`, a new context manager alongside
  the existing `start_issue_tracker_api` (which is reused unmodified)
- `tests_e2e/conftest.py` — add `mcp_dual_server` (session-scoped) and `mcp_server_unreachable`
  (function-scoped) fixtures

**Reference (read, do not modify):**
- `tests_e2e/servers.py::start_issue_tracker_api` — the real-server-process convention this plan
  matches exactly (ephemeral port via `_free_port()`, `subprocess.Popen`, poll-until-ready loop
  with a documented timeout, terminate-then-kill teardown, `E2EServerStartTimeout` on failure)
- `tests_e2e/conftest.py` — existing `server`/`ui_board_server` fixtures for the shared-vs-isolated
  fixture-scope convention this plan's two new fixtures follow
- `mcp_server/server.py` — confirms `PORT` env var selects `streamable-http` transport
  (`host="0.0.0.0"`) vs. `stdio` when unset; this plan always sets `PORT`
- `mcp_server/config.py` — confirms `API_BASE_URL` is the only env var `mcp-server` reads to find
  `issue-tracker-api`
- `mcp_server/tools/issues.py`, `mcp_server/tools/projects.py` — confirms exactly which tool calls
  can raise `ToolError` (schema validation, `UpstreamError`, `UpstreamUnreachableError`) and that
  every one of the 7 tools is registered via `@mcp.tool()` on import
- `mcp_server/client.py` — the exact wording of `UpstreamUnreachableError`'s message
  (`f"Could not reach issue-tracker-api at {base_url}: {exc}"`), asserted verbatim by this plan's
  BEH-5 test
- `tests/mcp_server/test_issue_tools.py`, `tests/mcp_server/test_project_tools.py` — the existing
  in-process (`mcp.Client(mcp)`) unit-test conventions for BEH-1 through BEH-5 at the tool layer;
  this plan asserts the same outcomes over the real transport instead
- `docker/mcp-server/Dockerfile`, `docker-compose.yml` — confirms `PORT`/`API_BASE_URL` are the
  only two env vars `mcp-server` needs in any deployment topology, matching what this plan's
  fixtures set
- `tests/test_docker_deploy.py` — the existing convention for asserting on a config file's raw
  text content, matched by the new `tests/test_requirements_files.py`
- `.context-index/specs/features/mcp-server/charter.md` — Capability Map (all 7 tool capabilities
  `validated`), Invariants (schema validates before HTTP call; error messages pass through
  verbatim)
- `CLAUDE.md` — constitution: "The HTTP contract is the boundary", "Fixture-backed, offline
  only", "No inbound dependencies"
- `.context-index/governance/gates.yaml` — `e2e-smoke` gate command
  (`.venv/bin/python3 -m pytest -q tests_e2e/`), already wired and unaffected by this plan

---

## Context Packets

> No `source-manifest.files[]` exists on this spec (no source-manifest fallback path per Step 2:
> this plan's context comes from the charter, the sibling specs/plans/tests already implementing
> `mcp_server/`, and the actual installed `mcp` SDK source read during planning). No
> `orientation/architecture.md`, ADRs, or samples exist in this repo yet. `boundaries.yaml` is
> empty; heuristics for module `mcp-server` returned none (`adev heuristics retrieve` → `__NONE__`).

### Task 1 Context
- Spec: Preconditions (both mcp-server specs implemented; `mcp-server` configured via
  `API_BASE_URL`/`PORT`)
- `requirements-mcp.txt` (full read — the exact pins this task's include line pulls in)
- `requirements-e2e.txt` (full read — current single-line content)
- `tests/test_docker_deploy.py` (full read — the raw-content-assertion convention to follow)

### Task 2 Context
- Spec: Preconditions (two real processes, wired via `API_BASE_URL`/`PORT`), Postconditions
  ("Both server processes are torn down after the test session")
- `tests_e2e/servers.py` (full read — `start_issue_tracker_api`, `_free_port()`,
  `E2EServerStartTimeout`, exact teardown sequence to mirror)
- `mcp_server/server.py`, `mcp_server/config.py` (full read — env vars and transport selection)
- `docker/mcp-server/Dockerfile`, `docker-compose.yml` (full read — confirms no third env var is
  needed beyond `PORT`/`API_BASE_URL`)

### Task 3 Context
- Spec: BEH-5 ("its own dedicated fixture that starts `mcp-server` alone... rather than the
  shared dual-server fixture"), Error Cases table (`E2E_SERVER_START_TIMEOUT` row)
- Source files (from Task 2, full read): `tests_e2e/servers.py::start_mcp_server`
- `tests_e2e/conftest.py` (full read — fixture-scope conventions: `server` is session-scoped
  shared, `ui_board_server` is function-scoped isolated for a documented reason; this task's
  `mcp_server_unreachable` follows the latter pattern)

### Task 4 Context
- Spec: Preconditions ("A real MCP client... connects to the live `mcp-server` process over that
  real transport. No test in this suite calls a tool function... directly")
- `mcp/client/streamable_http.py`, `mcp/client/session.py` (signatures read during planning —
  `streamable_http_client(url, *, http_client=None, terminate_on_close=True)`,
  `ClientSession(read_stream, write_stream, ...)`, `initialize()`, `list_tools()`, `call_tool()`)
- Source files (from Task 2, full read): `tests_e2e/servers.py::start_mcp_server` (for the
  fixture this helper connects to in its own test)

### Task 5 Context
- Spec: BEH-1 ("all 7 registered tools with their correct names and input schemas")
- Charter: Capability Map (7 `validated` tool capabilities), Interface Contracts → Exposed APIs
  table (the 7 tool names)
- `mcp_server/tools/issues.py`, `mcp_server/tools/projects.py` (full read — confirms tool names
  and required/optional parameters for schema assertions)
- Source files (from Task 2/4, full read): `tests_e2e/servers.py::start_mcp_server`,
  `tests_e2e/mcp_client.py::connect`

### Task 6 Context
- Spec: BEH-2 ("structured result matches what a direct real HTTP call to `issue-tracker-api`
  shows for the same data")
- `app/routers/projects.py`, `app/models.py` (full read — exact `GET /projects`/`POST /projects`
  response shapes to cross-verify against)
- `tests_e2e/test_project_crud_e2e.py` (full read — the existing direct-HTTP e2e convention for
  project CRUD, mirrored here at the MCP-tool layer)
- Source files (from Task 2/4, full read): `tests_e2e/conftest.py::mcp_dual_server`,
  `tests_e2e/mcp_client.py::connect`

### Task 7 Context
- Spec: BEH-3 ("the real CRUD operation happens — cross-verified by a direct real HTTP call...
  after each mutating call")
- `app/routers/issues.py` (if present) or equivalent issue routes, `app/models.py` (full read —
  exact issue CRUD shapes)
- `tests_e2e/test_issue_lifecycle_e2e.py` (full read — the existing direct-HTTP full-lifecycle
  e2e convention, mirrored here at the MCP-tool layer for all 5 issue tools)
- Source files (from Task 6, full read — extending the same file conventions):
  `tests_e2e/test_mcp_project_tools_e2e.py` (style reference only, not extended)

### Task 8 Context
- Spec: BEH-4, BEH-5, Error Cases table (all three rows)
- `tests/mcp_server/test_issue_tools.py` (full read — exact existing schema-invalid-input
  assertions, e.g. `test_get_issue_tool_missing_issue_id_errors_before_http_request`, mirrored
  here over the real transport)
- `mcp_server/client.py` (full read — exact `UpstreamUnreachableError` message text asserted
  verbatim for BEH-5)
- Source files (from Task 3/4, full read): `tests_e2e/conftest.py::mcp_server_unreachable`,
  `tests_e2e/mcp_client.py::connect`

---

## Parallelization

- Group A (independent): Task 1
- Group B (sequential): Task 2 → Task 3 → Task 4
- Group C (sequential): Task 5 → Task 6 → Task 7 → Task 8

Task 1 (`requirements-e2e.txt`) touches no file any other task depends on for imports — the `mcp`
package it wires in is only actually imported starting at Task 4 — so it can run independently of
Group B, though in practice it should land first since Task 4's test will fail on
`ModuleNotFoundError: No module named 'mcp'` in a fresh environment without it. Group B is
strictly sequential: Task 3's `mcp_server_unreachable` fixture reuses Task 2's `start_mcp_server`
helper, and Task 4's `mcp_client.py` is exercised in its own test against Task 2's fixture. Group
C cannot start until Group B lands (every BEH test needs both the fixtures and the client helper)
and is itself sequential — Tasks 5 through 8 do not share files with each other but do share the
growing set of assertions/conventions each subsequent task's tests build on, and running them out
of order risks a later task's test asserting on tool behavior a not-yet-verified earlier task was
meant to establish confidence in first (tool discovery before calling tools; project tools before
the larger issue-tool surface; happy paths before error paths).

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Wire mcp e2e test dependencies | small | unit | — | 1 create, 1 modify |
| 2 | Dual-server e2e fixture | medium | unit | Task 1 | 0 create, 2 modify; 1 test create |
| 3 | mcp-server-only e2e fixture (BEH-5) | small | unit | Task 2 | 0 create, 1 modify; 1 test create |
| 4 | Real MCP client helper | medium | unit | Task 2 | 1 create; 1 test create |
| 5 | Tool-discovery e2e test | small | unit | Task 4 | 1 test create |
| 6 | Project-tools e2e tests | small | unit | Task 5 | 1 test create |
| 7 | Issue-tools e2e tests | medium | unit | Task 6 | 1 test create |
| 8 | Error-path e2e tests | small | unit | Task 3, Task 7 | 1 test create |

All eight tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in the
spec's frontmatter, no `test_strategies` entries in `manifest.yaml`, and none of this plan's file
paths match `lib/test-strategies/detection.mjs`'s auto-detection globs — e.g. `mcp_client.py`
deliberately avoids the `*-client.*` hyphenated filename pattern that would auto-detect
`integration`). This matches the sibling `api-e2e.plan.md`'s precedent, where the same
`tests_e2e/` real-process suite also resolved to `unit` by fallback. Per Step 5, the Strategy
Summary section is omitted (all `unit`). No `infra_requirements:` is declared on the spec, and
every "external system" this suite touches (`issue-tracker-api`, `mcp-server`) is a real process
this same suite starts and binds to `127.0.0.1` itself — not a pre-provisioned external
dependency — so the Test Infrastructure Requirements section is also omitted, matching
`api-e2e.plan.md`'s precedent for the same style of suite.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). Tasks 1 through 4 are foundation tasks not tied to a single spec
behavior and each gets its own dedicated suite, created once (mirroring how `project-tools.plan.md`
gave its own foundation tasks dedicated suites). Tasks 5 through 8 each create the one new suite
for their behavior (BEH-1 through BEH-5); none of these suites previously existed, so every one is
"create," never "extend."

---

## Task Structure

### Task 1: Wire mcp e2e test dependencies [specialist: none]

**Charter capability:** End-to-end MCP test suite (foundation — every later task in this plan
imports the `mcp` SDK)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `requirements-e2e.txt`
- Test: `tests/test_requirements_files.py`

**Tests:** `tests/test_requirements_files.py` (create — first task to touch this behavior)

**Context to load:**
- `requirements-mcp.txt`, current `requirements-e2e.txt`
- `tests/test_docker_deploy.py` (raw-content-assertion convention)

- [ ] **Write failing test**

```python
# tests/test_requirements_files.py
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_requirements_e2e_includes_mcp_sdk_via_requirements_mcp():
    content = (REPO_ROOT / "requirements-e2e.txt").read_text()
    assert "-r requirements-mcp.txt" in content, (
        "mcp e2e tests need the mcp SDK/httpx/anyio pinned in requirements-mcp.txt; "
        "include it rather than re-pinning them separately"
    )


def test_requirements_e2e_still_includes_playwright():
    content = (REPO_ROOT / "requirements-e2e.txt").read_text()
    assert "playwright" in content
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests/test_requirements_files.py`
Expected: FAIL — `assert "-r requirements-mcp.txt" in content` fails (current
`requirements-e2e.txt` has only `playwright`).

- [ ] **Implement**

```text
# requirements-e2e.txt
-r requirements-mcp.txt
playwright
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests/test_requirements_files.py`
Expected: PASS

- [ ] **Commit**

Branch (create if not already created): `feat/mcp-server/mcp-e2e`

```bash
git add requirements-e2e.txt tests/test_requirements_files.py
git commit -m "test(mcp-e2e): wire mcp SDK deps into requirements-e2e.txt via requirements-mcp.txt"
```

---

### Task 2: Dual-server e2e fixture [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `tests_e2e/servers.py`
- Modify: `tests_e2e/conftest.py`
- Test: `tests_e2e/test_mcp_server_fixture.py`

**Tests:** `tests_e2e/test_mcp_server_fixture.py` (create — first task to touch this behavior)

**Context to load:**
- Spec Preconditions (real `mcp-server` process configured via `API_BASE_URL`/`PORT`)
- `tests_e2e/servers.py::start_issue_tracker_api` (pattern to mirror exactly)
- `mcp_server/server.py`, `mcp_server/config.py`

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_server_fixture.py
import socket

import pytest

from tests_e2e.servers import E2EServerStartTimeout, start_issue_tracker_api, start_mcp_server


def test_start_mcp_server_yields_reachable_base_url(tmp_path):
    with start_issue_tracker_api(tmp_path) as api_base_url:
        with start_mcp_server(api_base_url) as mcp_base_url:
            host, port = mcp_base_url.replace("http://", "").split(":")
            with socket.create_connection((host, int(port)), timeout=2):
                pass  # connection accepted — process is up


def test_start_mcp_server_tears_down_process_on_exit(tmp_path):
    with start_issue_tracker_api(tmp_path) as api_base_url:
        with start_mcp_server(api_base_url) as mcp_base_url:
            pass
        host, port = mcp_base_url.replace("http://", "").split(":")
        with pytest.raises(OSError):
            with socket.create_connection((host, int(port)), timeout=1):
                pass  # pragma: no cover - should never be reached


def test_start_mcp_server_raises_e2e_server_start_timeout_on_bad_command(monkeypatch, tmp_path):
    # Deliberate misuse: point PORT selection at a port that's already bound, so the
    # subprocess exits immediately with an "address already in use" error, exercising the
    # "process exited early" branch of E2E_SERVER_START_TIMEOUT.
    with start_issue_tracker_api(tmp_path) as api_base_url:
        blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        busy_port = blocker.getsockname()[1]
        monkeypatch.setattr("tests_e2e.servers._free_port", lambda: busy_port)
        try:
            with pytest.raises(E2EServerStartTimeout) as exc_info, start_mcp_server(api_base_url):
                pass  # pragma: no cover - should never be reached
        finally:
            blocker.close()
        message = str(exc_info.value)
        assert "startup timeout" in message
        assert "Last output" in message
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_server_fixture.py`
Expected: FAIL — `ImportError: cannot import name 'start_mcp_server' from 'tests_e2e.servers'`
(the function does not exist yet).

- [ ] **Implement**

```python
# tests_e2e/servers.py — append below start_issue_tracker_api

@contextlib.contextmanager
def start_mcp_server(api_base_url: str) -> Iterator[str]:
    """Start the real mcp-server process as a subprocess; yield its base_url.

    Args:
        api_base_url: value to set API_BASE_URL to — a live issue-tracker-api's base_url in the
            normal (dual-server) topology, or a deliberately unreachable URL for the mcp-e2e
            spec's BEH-5 scenario (a dedicated caller uses this same helper for that; see
            mcp_server_unreachable in tests_e2e/conftest.py).

    Yields:
        mcp-server's own base URL (e.g. "http://127.0.0.1:54232"). This is NOT the MCP endpoint
        URL — callers append the SDK's default streamable-http path themselves
        (see tests_e2e/mcp_client.py::connect).

    Raises:
        E2EServerStartTimeout: the process's port never accepted a TCP connection within the
            startup timeout (E2E_SERVER_START_TIMEOUT in mcp-e2e.spec.md). This is a coarse
            "is anything listening" check, not a full MCP handshake, so this fixture stays
            agnostic of BEH-5's own scenario (a dead API_BASE_URL) — mcp-server itself must
            still start up cleanly even when its upstream is unreachable; only its tool calls
            fail in that case.
    """
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "PORT": str(port), "API_BASE_URL": api_base_url}
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                last_output = proc.stdout.read() if proc.stdout else ""
                raise E2EServerStartTimeout(
                    f"mcp-server process exited early (code {proc.returncode}) before "
                    f"accepting connections on {base_url} within the "
                    f"{_STARTUP_TIMEOUT_SECONDS}s startup timeout. Last output:\n{last_output}"
                )
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    break
            except OSError:
                pass
            time.sleep(_POLL_INTERVAL_SECONDS)
        else:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            last_output = proc.stdout.read() if proc.stdout else ""
            raise E2EServerStartTimeout(
                f"mcp-server did not accept connections on {base_url} within the "
                f"{_STARTUP_TIMEOUT_SECONDS}s startup timeout. Last output:\n{last_output}"
            )
        yield base_url
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
```

```python
# tests_e2e/conftest.py — add below the existing `server` fixture
from tests_e2e.servers import start_mcp_server


@pytest.fixture(scope="session")
def mcp_dual_server(tmp_path_factory) -> tuple[str, str]:
    """Session-scoped real issue-tracker-api + real mcp-server pair, wired via API_BASE_URL.

    Shared across BEH-1 through BEH-4 (all tests that need a live, reachable upstream). Tests
    use unique project/issue keys per test to avoid cross-test collisions in the shared
    database, matching the existing `server` fixture's convention. NOT used by BEH-5, which
    needs mcp-server running with no reachable upstream at all — see mcp_server_unreachable.

    Yields:
        (api_base_url, mcp_base_url)
    """
    tmp_path = tmp_path_factory.mktemp("mcp-e2e-dual-server")
    with start_issue_tracker_api(tmp_path) as api_base_url:
        with start_mcp_server(api_base_url) as mcp_base_url:
            yield api_base_url, mcp_base_url
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_server_fixture.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/servers.py tests_e2e/conftest.py tests_e2e/test_mcp_server_fixture.py
git commit -m "test(mcp-e2e): add real mcp-server subprocess fixture and dual-server pairing"
```

---

### Task 3: mcp-server-only e2e fixture (BEH-5) [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `tests_e2e/conftest.py`
- Test: `tests_e2e/test_mcp_server_unreachable_fixture.py`

**Tests:** `tests_e2e/test_mcp_server_unreachable_fixture.py` (create — first task to touch this
behavior)

**Context to load:**
- Spec BEH-5 (dedicated fixture, no `issue-tracker-api` process at all)
- `tests_e2e/conftest.py::ui_board_server` (function-scoped isolated-fixture convention)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_server_unreachable_fixture.py
import socket


def test_mcp_server_unreachable_starts_only_mcp_server(mcp_server_unreachable):
    host, port = mcp_server_unreachable.replace("http://", "").split(":")
    with socket.create_connection((host, int(port)), timeout=2):
        pass  # mcp-server itself is up, even though its upstream is dead


def test_mcp_server_unreachable_points_at_a_dead_port():
    # A sibling assertion (not fixture-dependent) that the fixture's chosen dead port really
    # is unreachable, documenting the topology's intent — see the fixture's own docstring.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
    with pytest.raises(OSError):
        with socket.create_connection(("127.0.0.1", dead_port), timeout=1):
            pass  # pragma: no cover - should never be reached
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_server_unreachable_fixture.py`
Expected: FAIL — `fixture 'mcp_server_unreachable' not found` (also `NameError: name 'pytest' is
not defined` — add the missing `import pytest` when writing the real file).

- [ ] **Implement**

```python
# tests_e2e/conftest.py — add below mcp_dual_server
import socket


@pytest.fixture
def mcp_server_unreachable(tmp_path) -> str:
    """Function-scoped: real mcp-server alone, API_BASE_URL pointed at a port nothing listens on.

    Deliberately NOT mcp_dual_server (per BEH-5's own dedicated-fixture requirement — no
    issue-tracker-api process is started at all here). Function-scoped since only the error-path
    tests need this topology; no shared-database concerns apply since no upstream API exists to
    hold state.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
    dead_api_base_url = f"http://127.0.0.1:{dead_port}"
    with start_mcp_server(dead_api_base_url) as mcp_base_url:
        yield mcp_base_url
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_server_unreachable_fixture.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/conftest.py tests_e2e/test_mcp_server_unreachable_fixture.py
git commit -m "test(mcp-e2e): add BEH-5's dedicated mcp-server-only unreachable-upstream fixture"
```

---

### Task 4: Real MCP client helper [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Create: `tests_e2e/mcp_client.py`
- Test: `tests_e2e/test_mcp_client_helper.py`

**Tests:** `tests_e2e/test_mcp_client_helper.py` (create — first task to touch this behavior)

**Context to load:**
- Spec Preconditions ("A real MCP client... connects to the live `mcp-server` process over that
  real transport")
- `mcp.client.streamable_http.streamable_http_client`, `mcp.ClientSession` (signatures confirmed
  during planning against the installed 2.1.1 SDK)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_client_helper.py
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_connect_yields_an_initialized_session(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.list_tools()
        names = {tool.name for tool in result.tools}
        assert "list_projects" in names  # session is usable — initialize() already ran
```

`tests_e2e/conftest.py` needs a session-scoped `anyio_backend` fixture for this to collect (per
the `@pytest.mark.anyio` convention already used in `tests/mcp_server/conftest.py`); add it
alongside the other fixtures in this task's implementation step.

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_client_helper.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests_e2e.mcp_client'`.

- [ ] **Implement**

```python
# tests_e2e/mcp_client.py
"""Real MCP client helper, reused across this repo's mcp-e2e suite.

Every test in tests_e2e/test_mcp_*_e2e.py connects to a live mcp-server process through this
helper — never by calling a tool function in mcp_server/tools/*.py directly — so every assertion
is made against what a real MCP client received over the real streamable-http transport, per
mcp-e2e.spec.md's Preconditions/Postconditions.
"""
import contextlib
from collections.abc import AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

_MCP_PATH = "/mcp"  # mcp SDK's default streamable_http_path (MCPServer.run_streamable_http_async)


@contextlib.asynccontextmanager
async def connect(mcp_base_url: str) -> AsyncIterator[ClientSession]:
    """Connect a real MCP client to a live mcp-server process; yield an initialized session.

    Args:
        mcp_base_url: the base URL start_mcp_server yielded (e.g. "http://127.0.0.1:54232") —
            NOT including the SDK's /mcp path suffix; this helper appends it.

    Yields:
        An initialized mcp.ClientSession, ready for list_tools()/call_tool().
    """
    url = mcp_base_url.rstrip("/") + _MCP_PATH
    async with streamable_http_client(url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session
```

```python
# tests_e2e/conftest.py — add near the top, alongside other fixtures
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_client_helper.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/mcp_client.py tests_e2e/test_mcp_client_helper.py tests_e2e/conftest.py
git commit -m "test(mcp-e2e): add real MCP client helper over the streamable-http transport"
```

---

### Task 5: Tool-discovery e2e test (BEH-1) [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Test: `tests_e2e/test_mcp_tool_discovery_e2e.py`

**Tests:** `tests_e2e/test_mcp_tool_discovery_e2e.py` (create — first task to touch BEH-1)

**Context to load:**
- Spec BEH-1
- Charter Interface Contracts → Exposed APIs table (the 7 tool names)
- `mcp_server/tools/issues.py`, `mcp_server/tools/projects.py` (required parameter names, for
  representative schema assertions)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_tool_discovery_e2e.py
import pytest

from tests_e2e.mcp_client import connect

_EXPECTED_TOOL_NAMES = {
    "list_projects",
    "create_project",
    "list_issues",
    "get_issue",
    "create_issue",
    "update_issue",
    "delete_issue",
}


@pytest.mark.anyio
async def test_real_client_discovers_all_seven_tools_with_correct_schemas(mcp_dual_server):
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.list_tools()

    names = {tool.name for tool in result.tools}
    assert names == _EXPECTED_TOOL_NAMES

    by_name = {tool.name: tool for tool in result.tools}
    assert set(by_name["create_project"].inputSchema["required"]) == {"key", "name"}
    assert set(by_name["get_issue"].inputSchema["required"]) == {"issue_id"}
    assert set(by_name["create_issue"].inputSchema["required"]) >= {
        "project_id", "summary", "issue_type", "priority",
    }
    assert "issue_id" not in by_name.get("list_issues").inputSchema.get("required", [])
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_tool_discovery_e2e.py`
Expected: FAIL — collection error or fixture error if any prior task's file is missing; once
Tasks 1-4 exist, this test should already pass against the already-`validated` `mcp_server/`
tools, since this task adds no new production code — run once more to confirm it starts GREEN
without any implementation step. If it starts green, treat "Verify test fails" as satisfied by
temporarily asserting a deliberately wrong tool-name set first (e.g. add a bogus 8th name),
confirm that variant fails, then correct it to the real 7 before "Verify test passes" — this is a
pure-test task; there is no production code to implement, per the spec's Preconditions ("Both
mcp-server specs... are implemented").

- [ ] **Implement**

No production code changes — `mcp_server/`'s 7 tools are already `validated`. This step is the
red→green swap described above (temporarily wrong assertion, confirm RED, restore the correct
assertion above, confirm GREEN).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_tool_discovery_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_tool_discovery_e2e.py
git commit -m "test(mcp-e2e): real-client tool discovery over streamable-http (BEH-1)"
```

---

### Task 6: Project-tools e2e tests (BEH-2) [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 5
**Files:**
- Test: `tests_e2e/test_mcp_project_tools_e2e.py`

**Tests:** `tests_e2e/test_mcp_project_tools_e2e.py` (create — first task to touch BEH-2)

**Context to load:**
- Spec BEH-2
- `app/routers/projects.py`, `app/models.py` (exact response shapes)
- `tests_e2e/test_project_crud_e2e.py` (existing direct-HTTP convention, mirrored here)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_project_tools_e2e.py
import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_create_and_list_projects_match_real_http_state(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        create_result = await session.call_tool(
            "create_project", {"key": "MCPE2E", "name": "MCP E2E Project"}
        )
        assert create_result.is_error is False
        created = create_result.structured_content
        assert created["key"] == "MCPE2E"

        list_result = await session.call_tool("list_projects", {})
        assert list_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        http_projects = http_client.get("/projects").json()

    mcp_projects = list_result.structured_content["result"]
    assert any(p["key"] == "MCPE2E" for p in mcp_projects)
    assert {p["id"] for p in mcp_projects} == {p["id"] for p in http_projects}
    assert any(p["id"] == created["id"] for p in http_projects)
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_project_tools_e2e.py`
Expected: FAIL only if any earlier task's file is missing (`ModuleNotFoundError`/fixture error);
otherwise this is a pure-test task against already-`validated` production code (same "confirm
RED with a deliberately wrong assertion" approach as Task 5 applies if the suite is already
green).

- [ ] **Implement**

No production code changes — confirms the already-implemented `list_projects`/`create_project`
tools' real-transport behavior matches direct HTTP state.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_project_tools_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_project_tools_e2e.py
git commit -m "test(mcp-e2e): real-client project tools cross-verified via real HTTP (BEH-2)"
```

---

### Task 7: Issue-tools e2e tests (BEH-3) [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 6
**Files:**
- Test: `tests_e2e/test_mcp_issue_tools_e2e.py`

**Tests:** `tests_e2e/test_mcp_issue_tools_e2e.py` (create — first task to touch BEH-3)

**Context to load:**
- Spec BEH-3
- `app/models.py`, issue routes (exact CRUD shapes)
- `tests_e2e/test_issue_lifecycle_e2e.py` (existing direct-HTTP full-lifecycle convention,
  mirrored here across all 5 issue tools)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_issue_tools_e2e.py
import httpx
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_full_issue_lifecycle_over_real_mcp_protocol_cross_verified(mcp_dual_server):
    api_base_url, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        project_result = await session.call_tool(
            "create_project", {"key": "MCPE2EI", "name": "MCP E2E Issue Project"}
        )
        project_id = project_result.structured_content["id"]

        created_result = await session.call_tool(
            "create_issue",
            {
                "project_id": project_id, "summary": "mcp e2e issue",
                "issue_type": "task", "priority": "medium",
            },
        )
        assert created_result.is_error is False
        issue_id = created_result.structured_content["id"]

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        assert http_client.get(f"/issues/{issue_id}").status_code == 200

    async with connect(mcp_base_url) as session:
        list_result = await session.call_tool("list_issues", {"project_id": project_id})
        assert any(i["id"] == issue_id for i in list_result.structured_content["result"])

        get_result = await session.call_tool("get_issue", {"issue_id": issue_id})
        assert get_result.structured_content["id"] == issue_id

        update_result = await session.call_tool(
            "update_issue", {"issue_id": issue_id, "status": "in_progress"}
        )
        assert update_result.structured_content["status"] == "in_progress"

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        assert http_client.get(f"/issues/{issue_id}").json()["status"] == "in_progress"

    async with connect(mcp_base_url) as session:
        delete_result = await session.call_tool("delete_issue", {"issue_id": issue_id})
        assert delete_result.is_error is False

    with httpx.Client(base_url=api_base_url, timeout=5) as http_client:
        gone_resp = http_client.get(f"/issues/{issue_id}")
        assert gone_resp.status_code == 404
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_issue_tools_e2e.py`
Expected: FAIL only if any earlier task's file is missing; otherwise the same pure-test
RED-via-deliberately-wrong-assertion approach as Tasks 5/6 applies against already-`validated`
production code.

- [ ] **Implement**

No production code changes — confirms all 5 already-implemented issue tools' real-transport
behavior, cross-verified via direct HTTP after each mutating call.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_issue_tools_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_issue_tools_e2e.py
git commit -m "test(mcp-e2e): real-client full issue lifecycle cross-verified via real HTTP (BEH-3)"
```

---

### Task 8: Error-path e2e tests (BEH-4, BEH-5) [specialist: none]

**Charter capability:** End-to-end MCP test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 3, Task 7
**Files:**
- Test: `tests_e2e/test_mcp_error_paths_e2e.py`

**Tests:** `tests_e2e/test_mcp_error_paths_e2e.py` (create — first task to touch BEH-4/BEH-5)

**Context to load:**
- Spec BEH-4, BEH-5, Error Cases table (all three rows)
- `tests/mcp_server/test_issue_tools.py::test_get_issue_tool_missing_issue_id_errors_before_http_request`
  (exact existing schema-invalid-input assertion, mirrored here over the real transport)
- `mcp_server/client.py` (exact `UpstreamUnreachableError` message text)

- [ ] **Write failing test**

```python
# tests_e2e/test_mcp_error_paths_e2e.py
import pytest

from tests_e2e.mcp_client import connect


@pytest.mark.anyio
async def test_schema_invalid_tool_input_surfaces_protocol_level_error(mcp_dual_server):  # BEH-4
    _, mcp_base_url = mcp_dual_server

    async with connect(mcp_base_url) as session:
        result = await session.call_tool("get_issue", {})  # missing required "issue_id"

    assert result.is_error is True
    assert result.content  # a message is present for the model to see


@pytest.mark.anyio
async def test_unreachable_upstream_surfaces_protocol_level_connection_error(  # BEH-5
    mcp_server_unreachable,
):
    async with connect(mcp_server_unreachable) as session:
        result = await session.call_tool("list_projects", {})

    assert result.is_error is True
    assert "Could not reach issue-tracker-api" in result.content[0].text
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_error_paths_e2e.py`
Expected: FAIL until Task 3's `mcp_server_unreachable` fixture exists (`fixture
'mcp_server_unreachable' not found`); once Tasks 1-7 all exist, this is a pure-test task against
already-`validated` production code — same RED-via-deliberately-wrong-assertion approach applies
if the suite is already green (e.g. temporarily assert `is_error is False` first, confirm that
fails, then restore the correct assertions above).

- [ ] **Implement**

No production code changes — confirms the already-implemented schema-validation and
`UpstreamUnreachableError`→`ToolError` mapping behave correctly over the real transport, using
BEH-5's dedicated single-process fixture from Task 3.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_error_paths_e2e.py`
Expected: PASS

Then run the full new suite together to confirm no cross-test interference from the shared
`mcp_dual_server` fixture:

Run: `.venv/bin/python3 -m pytest -q -- tests_e2e/test_mcp_server_fixture.py tests_e2e/test_mcp_server_unreachable_fixture.py tests_e2e/test_mcp_client_helper.py tests_e2e/test_mcp_tool_discovery_e2e.py tests_e2e/test_mcp_project_tools_e2e.py tests_e2e/test_mcp_issue_tools_e2e.py tests_e2e/test_mcp_error_paths_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_mcp_error_paths_e2e.py
git commit -m "test(mcp-e2e): real-client error paths for schema-invalid input and dead upstream (BEH-4, BEH-5)"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:
- Tests pass: `.venv/bin/python3 -m pytest -q` (unit/core suite, `testpaths = tests`)
- E2E smoke: `.venv/bin/python3 -m pytest -q tests_e2e/` (`e2e-smoke` gate — `tier: e2e`,
  `required: false`, `severity: warning`; this plan's new tests run here)
- Lint passes: `ruff check .`
- All acceptance criteria from `mcp-e2e.spec.md` satisfied (BEH-1 through BEH-5, all real-client
  over real transport, cross-verified via real HTTP where the spec calls for it)
