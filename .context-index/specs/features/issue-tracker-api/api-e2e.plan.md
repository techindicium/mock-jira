<!-- partial_schema: plan@1 -->

# Implementation Plan: End-to-end API test suite (real HTTP)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Spec:** .context-index/specs/features/issue-tracker-api/api-e2e.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-06)
> **Platform:** FastAPI (uvicorn), Python 3.11, sqlite3, httpx, pytest

**Goal:** Add a real-HTTP end-to-end test suite that starts `app.main:app` as its own OS process
(never in-process via `TestClient`) and drives every documented Project/Issue behavior — plus the
documented error paths, the OpenAPI contract, and startup seeding — over a live socket, the same
way a real consuming track's client would.

**Architecture:** A new `tests_e2e/` directory sits alongside the existing `tests/` (fast,
in-process `TestClient` suite) so the e2e suite is optional and separately gated rather than
slowing down the fast gate. Its core is a reusable `start_issue_tracker_api(tmp_path)` context
manager in `tests_e2e/servers.py` that launches `uvicorn app.main:app` via `subprocess.Popen` on
an ephemeral port with `DATABASE_PATH` pointed at a fresh temp file, polls `GET /` (the app's
existing root route — there is no dedicated `/health` endpoint, confirmed in review note SA-1 and
consistent with the `docker-compose.yml` healthcheck, which already polls the same route) until
healthy or a startup timeout is hit, yields the base URL, and tears the process down afterward.
This function is deliberately framework-light (a plain context manager taking any `Path`, not a
pytest fixture itself) so the two not-yet-planned sibling specs that will reuse it — `kanban-ui`'s
`ui-e2e` and `mcp-server`'s `mcp-e2e` — can import it directly without depending on this repo's
`tests_e2e/conftest.py` fixture wiring. `tests_e2e/conftest.py` wraps it in a session-scoped
`server` fixture for this repo's own tests. Because there is no existing `pytest.ini`, a bare
`python3 -m pytest -q` invocation (the `test` gate's command) would otherwise recurse into
`tests_e2e/` too and defeat the fast/e2e split — Task 6 closes that gap with a `testpaths = tests`
`pytest.ini`, proven by a test that asserts real exclusion once the e2e suite exists. Task 7 wires
the new `e2e-smoke` gate (`tier: e2e`, `.venv/bin/python3 -m pytest -q tests_e2e/`) into
`governance/gates.yaml`, kept at the e2e-tier default `severity: warning` since these are
first-generation e2e tests for a course-fixture repo.

---

## File Structure

**Create:**
- `tests_e2e/__init__.py` — empty; makes `tests_e2e` a package, matching the existing
  `tests/__init__.py` convention so `from tests_e2e.servers import start_issue_tracker_api` works
  the same way from sibling specs' own suites later.
- `tests_e2e/servers.py` — the reusable `start_issue_tracker_api(tmp_path)` context manager
  (subprocess launch, ephemeral port, health poll, teardown).
- `tests_e2e/conftest.py` — session-scoped `server` fixture wrapping `start_issue_tracker_api`
  with a `tmp_path_factory`-produced directory (a fresh DB file per test *session*, per spec
  Preconditions — `tmp_path` itself is function-scoped, so the session fixture uses
  `tmp_path_factory.mktemp(...)` rather than the `tmp_path` fixture directly).
- `tests_e2e/test_server_fixture.py` — direct test of the fixture contract itself (Preconditions:
  real OS process, ephemeral port, temp DB, polls `GET /`, yields a reachable base URL, tears down
  cleanly) and the `E2E_SERVER_START_TIMEOUT` error case.
- `tests_e2e/test_project_crud_e2e.py` — BEH-1.
- `tests_e2e/test_issue_lifecycle_e2e.py` — BEH-2.
- `tests_e2e/test_error_paths_e2e.py` — BEH-3 (404/409/422, including the invalid-enum → 422
  `VALIDATION_ERROR` case added to the spec's Error Cases table per review note SA-2).
- `tests_e2e/test_openapi_and_seed_e2e.py` — BEH-4 (`GET /openapi.json`) and BEH-5 (seed data
  visible on a truly fresh server — uses `start_issue_tracker_api` directly with its own fresh
  `tmp_path`, not the shared session `server` fixture, so no other test's writes contaminate the
  "fresh empty database" assertion).
- `pytest.ini` — `testpaths = tests`, so a bare `python3 -m pytest -q` (the existing `test` gate)
  keeps discovering only the fast in-process suite and never recurses into `tests_e2e/`.
- `tests/test_pytest_config.py` — proves the `pytest.ini` isolation is real (Task 6).
- `tests/test_gates_config.py` — proves the new `e2e-smoke` gate is defined correctly (Task 7).

**Modify:**
- `.context-index/governance/gates.yaml` — add the `e2e-smoke` gate entry (Task 7).

**Reference (read, do not modify):**
- `app/main.py` — `app` object, `resolve_db_path()`/`DATABASE_PATH` env var, root route `GET /`,
  startup seeding hook. This is exactly what the real server process runs.
- `app/routers/projects.py`, `app/routers/issues.py` — exact status codes and error `code` values
  (`PROJECT_NOT_FOUND`, `PROJECT_KEY_DUPLICATE`, `ISSUE_NOT_FOUND`, `ISSUE_PROJECT_NOT_FOUND`,
  `VALIDATION_ERROR`) that the e2e error-path tests must assert against.
- `app/models.py` — `ISSUE_TYPES`/`ISSUE_STATUSES`/`ISSUE_PRIORITIES` enum values, used to pick a
  deliberately-invalid enum value for the BEH-3 422 case.
- `app/seed.py` — `SEED_PROJECT`/`SEED_ISSUES` shape (1 project, `ASSIST` key, 6 issues) that
  BEH-5's fresh-server assertion checks against; mirrors `tests/test_seed.py`'s existing
  assertions for the in-process case.
- `tests/conftest.py`, `tests/test_seed.py`, `tests/test_openapi.py`, `tests/test_projects.py`,
  `tests/test_issues.py` — existing in-process equivalents; the e2e suite asserts the same
  contract, over a real socket instead of `TestClient`.
- `docker-compose.yml` — existing healthcheck (`GET /` via `urllib.request`) that the fixture's
  polling loop mirrors.
- `requirements.txt` — already lists `httpx` (used elsewhere, e.g. `tests/mcp_server/`); no new
  dependency needed.
- `governance/gates.yaml` — existing `test`/`lint`/`test-js`/`integration-test` gate shapes,
  followed for the new `e2e-smoke` entry (`.venv/bin/python3`, never ambient `python3`).

---

## Context Packets

No `source-manifest.files[]` exists yet on this spec (first implementation pass), so context
packets fall back to sibling specs' stamped source manifests (signatures only) plus the charter
Capability Map and constitution principles.

### Task 1 Context
- Spec: `api-e2e.spec.md` — Preconditions, Error Cases (`E2E_SERVER_START_TIMEOUT` row)
- Charter: `charter.md` (capability: "End-to-end API test suite")
- Source files: `app/main.py` (full read — `resolve_db_path()`, `DATABASE_PATH` env var, root
  route, `on_startup` hook); `docker-compose.yml` healthcheck block (full read, ~5 lines)
- Constitution: "Fixture-backed, offline only" (bind to `127.0.0.1` only)

### Task 2 Context
- Spec: `api-e2e.spec.md` — BEH-1
- Charter: `charter.md` (capability: "Create/list/get Project")
- Source files: `app/routers/projects.py` (`grep "^def\|^@router"` — signatures only),
  `app/models.py` (`ProjectCreate`/`ProjectRead` fields, full read — small file)
- Sibling test (signatures only): `tests/test_projects.py`

### Task 3 Context
- Spec: `api-e2e.spec.md` — BEH-2
- Charter: `charter.md` (capabilities: "Create Issue", "List/get Issue", "Update Issue",
  "Delete Issue")
- Source files: `app/routers/issues.py` (full read — status transition, patch, delete semantics),
  `app/models.py` (`IssueCreate`/`IssueRead`/`IssuePatch`, full read)
- Sibling test (signatures only): `tests/test_issues.py`

### Task 4 Context
- Spec: `api-e2e.spec.md` — BEH-3, Error Cases table (all four rows, including the
  invalid-enum-value row added per review note SA-2)
- Charter: `charter.md` (capability: "Create Issue" invariant: "status is always one of the three
  fixed values")
- Source files: `app/errors.py` (full read — `VALIDATION_ERROR`/`MALFORMED_JSON` shaping),
  `app/routers/projects.py` + `app/routers/issues.py` (`grep "HTTPException\|status_code"` —
  error-producing lines only)

### Task 5 Context
- Spec: `api-e2e.spec.md` — BEH-4, BEH-5
- Charter: `charter.md` (capabilities: "OpenAPI contract", "Seed fixture data")
- Source files: `app/seed.py` (`SEED_PROJECT`/`SEED_ISSUES`, full read — small, load-bearing for
  exact assertion values)
- Sibling tests (signatures only): `tests/test_openapi.py`, `tests/test_seed.py`

### Task 6 Context
- Spec: `api-e2e.spec.md` — Architecture rationale (fast-gate isolation, see plan header)
- Source files: none in `app/`; this task only touches `pytest.ini` and a new `tests/` config test
- Reference: `governance/gates.yaml` `test` gate command (`[.venv/bin/python3, -m, pytest, -q]`,
  no path argument — the reason discovery-scope matters)

### Task 7 Context
- Spec: `api-e2e.spec.md` — Actionable Task Map ("Wire the `e2e` gate tier")
- Reference: `governance/gates.yaml` (full read — gate schema comment block, `integration-test`
  gate as the nearest unwired-but-defined precedent)
- Boundary rules: `governance/boundaries.yaml` — empty (`boundaries: []`), no rules to check

---

## Parallelization

- Group A (sequential): Task 1 → Task 6 → Task 7
- Group B (independent): Task 2
- Group C (independent): Task 3
- Group D (independent): Task 4
- Group E (independent): Task 5

Groups B, C, D, and E each depend only on Task 1 (see each task's "Depends on" annotation below)
and can run in parallel with each other; none of them touches a file another group touches. Task 6
additionally depends on Tasks 2-5 having landed (it proves real exclusion of the e2e test files
those tasks create, not just the fixture from Task 1), and Task 7 depends on Task 6. Group A's
arrows represent that tail dependency chain, not a file-overlap constraint.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Real-server-process fixture | medium | unit | — | 4 create, 0 modify |
| 2 | Project CRUD e2e tests | small | unit | Task 1 | 1 create, 0 modify |
| 3 | Issue lifecycle e2e tests | medium | unit | Task 1 | 1 create, 0 modify |
| 4 | Error-path e2e tests | small | unit | Task 1 | 1 create, 0 modify |
| 5 | OpenAPI + seed-data e2e tests | small | unit | Task 1 | 1 create, 0 modify |
| 6 | Isolate `tests_e2e/` from the fast gate | small | unit | Task 2, Task 3, Task 4, Task 5 | 2 create, 0 modify |
| 7 | Wire the `e2e-smoke` gate | small | unit | Task 6 | 1 create, 1 modify |

All seven tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in the
spec's frontmatter, no matching `manifest.yaml` glob rule, and no file path matches any
auto-detection heuristic in `lib/test-strategies/detection.mjs`). Strategy Summary and Test
Infrastructure Requirements sections are omitted per the plan template (all-unit, no
`infra_requirements:` on the spec).

---

## Task Structure

> Task status lives in the spec's lifecycle event log (`plan_task` events), not in the `- [ ]`
> checkboxes below — those are authoring guides only.

### Task 1: Real-server-process fixture [specialist: none]

**Charter capability:** End-to-end API test suite
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `tests_e2e/__init__.py`
- Create: `tests_e2e/servers.py`
- Create: `tests_e2e/conftest.py`
- Test: `tests_e2e/test_server_fixture.py`

**Tests:** `tests_e2e/test_server_fixture.py` — new suite (per-behavior granularity: this covers
the Preconditions/Error-Cases contract of the reusable fixture itself, not one of BEH-1..5).

**Context to load:**
- `app/main.py` (root route, `DATABASE_PATH` env var, startup hook)
- `docker-compose.yml` healthcheck block (same `GET /` polling convention)

- [ ] **Write failing test**

```python
# tests_e2e/test_server_fixture.py
import httpx
import pytest

from tests_e2e.servers import E2EServerStartTimeout, start_issue_tracker_api


def test_start_issue_tracker_api_yields_reachable_base_url(tmp_path):
    with start_issue_tracker_api(tmp_path) as base_url:
        resp = httpx.get(base_url + "/", timeout=5)
        assert resp.status_code == 200


def test_start_issue_tracker_api_tears_down_process_on_exit(tmp_path):
    with start_issue_tracker_api(tmp_path) as base_url:
        pass
    with httpx.Client(timeout=1) as client:
        try:
            client.get(base_url + "/")
            assert False, "expected connection to be refused after teardown"
        except httpx.ConnectError:
            pass


def test_start_issue_tracker_api_raises_e2e_server_start_timeout_on_unhealthy_startup(tmp_path):
    # Deliberate misuse: pass a *file* where the fixture expects a directory to place
    # the DB under. `app.main`'s on_startup catches the resulting sqlite3.OperationalError
    # ("unable to open database file") and raises RuntimeError, which fails uvicorn's
    # startup event — so the subprocess exits almost immediately, exercising the
    # "process exited early" branch of E2E_SERVER_START_TIMEOUT without waiting out
    # the full startup timeout.
    not_a_dir = tmp_path / "not_a_directory"
    not_a_dir.write_text("this is a file, not a directory, so app startup fails fast")

    with pytest.raises(E2EServerStartTimeout) as exc_info:
        with start_issue_tracker_api(not_a_dir):
            pass  # pragma: no cover - should never be reached

    message = str(exc_info.value)
    assert "startup timeout" in message  # names the timeout
    assert "Last output" in message      # names the last-seen process output
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_server_fixture.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests_e2e.servers'` for all three tests
(the third test additionally exercises the `E2E_SERVER_START_TIMEOUT` error case from the spec's
Error Cases table, which the first two tests deliberately do not cover).

- [ ] **Implement**

```python
# tests_e2e/servers.py
"""Reusable real-server-process fixture for e2e suites.

Launches `uvicorn app.main:app` as its own OS process (never imported in-process),
on an ephemeral local port, with DATABASE_PATH pointed at a fresh temp file. Polls
GET / (the app's existing root route — there is no dedicated /health endpoint,
same convention as this repo's docker-compose.yml healthcheck) until it answers,
then yields the base URL. Terminates the process on exit.

Reused by this repo's own tests_e2e/conftest.py `server` fixture, and intended for
direct reuse (no pytest dependency) by kanban-ui's ui-e2e and mcp-server's mcp-e2e
sibling specs, which will start this same API as their upstream test dependency.
"""
import contextlib
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator

import httpx

_STARTUP_TIMEOUT_SECONDS = 10.0
_POLL_INTERVAL_SECONDS = 0.1


class E2EServerStartTimeout(RuntimeError):
    """Raised when the server subprocess doesn't answer GET / within the startup timeout."""


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def start_issue_tracker_api(tmp_path: Path) -> Iterator[str]:
    """Start the real issue-tracker-api server as a subprocess; yield its base_url.

    Args:
        tmp_path: a directory to place this run's SQLite DB file in. Callers control
            scope (function- or session-level) by choosing what Path they pass in
            (e.g. pytest's `tmp_path` vs. `tmp_path_factory.mktemp(...)`).

    Yields:
        The base URL (e.g. "http://127.0.0.1:54231") once the server answers GET /.

    Raises:
        E2EServerStartTimeout: the process didn't answer GET / within the startup
            timeout. The exception message names the timeout and the last-seen
            process output (E2E_SERVER_START_TIMEOUT in api-e2e.spec.md).
    """
    port = _free_port()
    db_path = Path(tmp_path) / "e2e.db"
    base_url = f"http://127.0.0.1:{port}"
    env = {"DATABASE_PATH": str(db_path)}
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(port),
        ],
        env={**__import__("os").environ, **env},
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
                    f"server process exited early (code {proc.returncode}) before "
                    f"answering GET {base_url}/ within the {_STARTUP_TIMEOUT_SECONDS}s "
                    f"startup timeout. Last output:\n{last_output}"
                )
            try:
                resp = httpx.get(base_url + "/", timeout=1)
                if resp.status_code == 200:
                    break
            except httpx.TransportError:
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
                f"server did not answer GET {base_url}/ within the "
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

Both raise sites now name the timeout budget (`_STARTUP_TIMEOUT_SECONDS`) and the last-seen
process output in every case — not just whichever branch happens to fire — satisfying the
spec's `E2E_SERVER_START_TIMEOUT` Error Case row ("naming the timeout and the last-seen process
output") regardless of which internal path (early exit vs. exhausted poll loop) is taken. The
`finally` block now guards `terminate()` behind a liveness check so it's a no-op (never an
exception) when the process already exited before the `finally` runs.

```python
# tests_e2e/conftest.py
import pytest

from tests_e2e.servers import start_issue_tracker_api


@pytest.fixture(scope="session")
def server(tmp_path_factory) -> str:
    """Session-scoped real server, shared across this repo's own e2e tests.

    Uses tmp_path_factory (not the function-scoped tmp_path fixture) so the DB
    file is fresh once per test session, per api-e2e.spec.md Preconditions.
    Tests that need a truly empty/fresh database (e.g. BEH-5 seed-on-startup)
    must NOT use this shared fixture — call start_issue_tracker_api directly
    with their own tmp_path instead.
    """
    tmp_path = tmp_path_factory.mktemp("issue-tracker-api-e2e")
    with start_issue_tracker_api(tmp_path) as base_url:
        yield base_url
```

`tests_e2e/__init__.py` is empty (package marker only).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_server_fixture.py`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/e2e-testing/core`

```bash
git add tests_e2e/__init__.py tests_e2e/servers.py tests_e2e/conftest.py tests_e2e/test_server_fixture.py
git commit -m "feat(issue-tracker-api): add reusable real-server-process e2e fixture"
```

### Task 2: Project CRUD e2e tests [specialist: none]

**Charter capability:** Create/list/get Project
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_project_crud_e2e.py`

**Tests:** `tests_e2e/test_project_crud_e2e.py` — new suite (BEH-1).

**Context to load:**
- `app/routers/projects.py` (signatures), `app/models.py` (`ProjectCreate`/`ProjectRead`)

- [ ] **Write failing test**

```python
# tests_e2e/test_project_crud_e2e.py
import httpx


def test_created_project_is_visible_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        create_resp = client.post(
            "/projects",
            json={"key": "E2ECRUD", "name": "E2E CRUD Project"},
        )
        assert create_resp.status_code == 201
        created = create_resp.json()

        list_resp = client.get("/projects")
        assert list_resp.status_code == 200
        keys = [p["key"] for p in list_resp.json()]
        assert "E2ECRUD" in keys
        assert any(p["id"] == created["id"] for p in list_resp.json())
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_project_crud_e2e.py`
Expected: FAIL — `fixture 'server' not found` until Task 1 lands, or a real assertion failure if
Task 1 already landed but the project router doesn't yet exist (it already does in this repo, so
this is the ordering check — the test must fail for the *right* reason before Task 1 is done).

- [ ] **Implement**

No production code changes — `POST /projects` and `GET /projects` already exist
(`app/routers/projects.py`). This task's "implement" step is the test file itself; it goes green
as soon as Task 1's fixture is in place.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_project_crud_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_project_crud_e2e.py
git commit -m "test(issue-tracker-api): add real-HTTP Project CRUD e2e coverage (BEH-1)"
```

### Task 3: Issue lifecycle e2e tests [specialist: none]

**Charter capability:** Create Issue, List/get Issue, Update Issue, Delete Issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_issue_lifecycle_e2e.py`

**Tests:** `tests_e2e/test_issue_lifecycle_e2e.py` — new suite (BEH-2).

**Context to load:**
- `app/routers/issues.py` (full — create/list/get/patch/delete), `app/models.py`
  (`IssueCreate`/`IssuePatch`)

- [ ] **Write failing test**

```python
# tests_e2e/test_issue_lifecycle_e2e.py
import httpx


def test_full_issue_lifecycle_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        project = client.post(
            "/projects", json={"key": "E2ELIFE", "name": "E2E Lifecycle Project"}
        ).json()

        created = client.post(
            "/issues",
            json={
                "project_id": project["id"], "summary": "e2e issue",
                "issue_type": "task", "priority": "medium",
            },
        ).json()
        issue_id = created["id"]
        assert created["status"] == "todo"

        listed = client.get("/issues", params={"project_id": project["id"]}).json()
        assert any(i["id"] == issue_id for i in listed)

        fetched = client.get(f"/issues/{issue_id}").json()
        assert fetched["id"] == issue_id

        patched = client.patch(f"/issues/{issue_id}", json={"status": "in_progress"}).json()
        assert patched["status"] == "in_progress"
        patched = client.patch(f"/issues/{issue_id}", json={"status": "done"}).json()
        assert patched["status"] == "done"

        delete_resp = client.delete(f"/issues/{issue_id}")
        assert delete_resp.status_code == 204

        gone_resp = client.get(f"/issues/{issue_id}")
        assert gone_resp.status_code == 404
        assert gone_resp.json()["code"] == "ISSUE_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_issue_lifecycle_e2e.py`
Expected: FAIL — `fixture 'server' not found` (before Task 1) or a specific assertion failure.

- [ ] **Implement**

No production code changes — the full Issue CRUD surface already exists
(`app/routers/issues.py`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_issue_lifecycle_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_issue_lifecycle_e2e.py
git commit -m "test(issue-tracker-api): add real-HTTP Issue lifecycle e2e coverage (BEH-2)"
```

### Task 4: Error-path e2e tests [specialist: none]

**Charter capability:** Create Issue (status enum invariant), Create/list/get Project
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_error_paths_e2e.py`

**Tests:** `tests_e2e/test_error_paths_e2e.py` — new suite (BEH-3; covers all four Error Cases
rows, including the invalid-enum-value row added to the spec per review note SA-2).

**Context to load:**
- `app/errors.py` (full), error-producing lines in `app/routers/projects.py` /
  `app/routers/issues.py`

- [ ] **Write failing test**

```python
# tests_e2e/test_error_paths_e2e.py
import httpx


def test_unknown_project_id_returns_404(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/projects/999999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "PROJECT_NOT_FOUND"


def test_unknown_issue_id_returns_404(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/issues/999999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "ISSUE_NOT_FOUND"


def test_duplicate_project_key_returns_409(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        client.post("/projects", json={"key": "E2EDUP", "name": "First"})
        resp = client.post("/projects", json={"key": "E2EDUP", "name": "Second"})
        assert resp.status_code == 409
        assert resp.json()["code"] == "PROJECT_KEY_DUPLICATE"


def test_invalid_issue_type_enum_returns_422(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        project = client.post(
            "/projects", json={"key": "E2EENUM", "name": "Enum Project"}
        ).json()
        resp = client.post(
            "/issues",
            json={
                "project_id": project["id"], "summary": "bad enum",
                "issue_type": "not-a-real-type", "priority": "medium",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_error_paths_e2e.py`
Expected: FAIL — `fixture 'server' not found` (before Task 1).

- [ ] **Implement**

No production code changes — all four error paths already exist (`app/routers/projects.py`,
`app/routers/issues.py`, `app/errors.py`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_error_paths_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_error_paths_e2e.py
git commit -m "test(issue-tracker-api): add real-HTTP error-path e2e coverage (BEH-3)"
```

### Task 5: OpenAPI + seed-data e2e tests [specialist: none]

**Charter capability:** OpenAPI contract, Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_openapi_and_seed_e2e.py`

**Tests:** `tests_e2e/test_openapi_and_seed_e2e.py` — new suite (BEH-4 and BEH-5; two distinct
spec behaviors covered by one task, per the spec's own Actionable Task Map grouping).

**Context to load:**
- `app/seed.py` (full — `SEED_PROJECT`/`SEED_ISSUES`), `tests/test_seed.py` (signatures, for the
  matching in-process assertions)

- [ ] **Write failing test**

```python
# tests_e2e/test_openapi_and_seed_e2e.py
import httpx

from tests_e2e.servers import start_issue_tracker_api


def test_openapi_json_lists_implemented_routes_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        doc = resp.json()
        assert "/projects" in doc["paths"]
        assert "/issues" in doc["paths"]
        assert "get" in doc["paths"]["/projects"]
        assert "post" in doc["paths"]["/issues"]


def test_seed_data_visible_on_fresh_server_start(tmp_path):
    # Deliberately NOT the shared `server` fixture: BEH-5 asserts a *fresh, empty*
    # database seeds exactly once, so this needs its own isolated server instance.
    with start_issue_tracker_api(tmp_path) as base_url:
        with httpx.Client(base_url=base_url, timeout=5) as client:
            projects = client.get("/projects").json()
            assert len(projects) == 1
            assert projects[0]["key"] == "ASSIST"

            issues = client.get("/issues", params={"project_id": projects[0]["id"]}).json()
            assert len(issues) == 6
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_openapi_and_seed_e2e.py`
Expected: FAIL — `fixture 'server' not found` / `ModuleNotFoundError` (before Task 1).

- [ ] **Implement**

No production code changes — OpenAPI generation and startup seeding already exist
(`app/main.py` `on_startup`, `app/seed.py`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_openapi_and_seed_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_openapi_and_seed_e2e.py
git commit -m "test(issue-tracker-api): add real-HTTP OpenAPI + seed-data e2e coverage (BEH-4, BEH-5)"
```

### Task 6: Isolate `tests_e2e/` from the fast test gate [specialist: none]

**Charter capability:** End-to-end API test suite (supports the "separately gated" design intent;
not itself one of BEH-1..5)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2, Task 3, Task 4, Task 5
**Files:**
- Create: `pytest.ini`
- Test: `tests/test_pytest_config.py`

**Tests:** `tests/test_pytest_config.py` — new suite, in the *fast* `tests/` tree (this checks
discovery configuration, not e2e behavior, so it belongs with the fast tests).

**Context to load:**
- `governance/gates.yaml` `test` gate command (no path argument today)

- [ ] **Write failing test**

```python
# tests/test_pytest_config.py
import subprocess
import sys


def test_bare_pytest_collection_excludes_tests_e2e():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only"],
        capture_output=True, text=True, cwd=".",
    )
    assert "tests_e2e" not in result.stdout
    assert "tests/test_projects.py" in result.stdout or "test_projects.py" in result.stdout
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests/test_pytest_config.py`
Expected: FAIL — with Tasks 2-5 already landed and no `pytest.ini` yet, the bare collection run's
stdout contains `tests_e2e` entries, so the `not in` assertion fails.

- [ ] **Implement**

```ini
# pytest.ini
[pytest]
testpaths = tests
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests/test_pytest_config.py`
Expected: PASS. Also re-run the full fast gate to confirm nothing in `tests/` was dropped:
`.venv/bin/python3 -m pytest -q` (should still collect/run every existing `tests/` suite,
including `tests/mcp_server/`, since `testpaths = tests` covers the whole subtree).

- [ ] **Commit**

```bash
git add pytest.ini tests/test_pytest_config.py
git commit -m "chore(issue-tracker-api): restrict bare pytest discovery to tests/, excluding tests_e2e/"
```

### Task 7: Wire the `e2e-smoke` gate [specialist: none]

**Charter capability:** End-to-end API test suite
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 6
**Files:**
- Modify: `.context-index/governance/gates.yaml` (append a new gate entry after `integration-test`)
- Test: `tests/test_gates_config.py`

**Tests:** `tests/test_gates_config.py` — new suite, in `tests/` (this checks a governance config
file, not e2e runtime behavior).

**Context to load:**
- `governance/gates.yaml` (full — gate schema comment block, `integration-test` as nearest
  unwired-but-defined precedent)

- [ ] **Write failing test**

```python
# tests/test_gates_config.py
from pathlib import Path

import yaml


def test_e2e_smoke_gate_is_defined_correctly():
    doc = yaml.safe_load(Path(".context-index/governance/gates.yaml").read_text())
    gates = {g["id"]: g for g in doc["gates"]}
    assert "e2e-smoke" in gates
    gate = gates["e2e-smoke"]
    assert gate["tier"] == "e2e"
    assert gate["command"] == [".venv/bin/python3", "-m", "pytest", "-q", "tests_e2e/"]
    assert gate.get("required") is False or gate.get("severity") == "warning"
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests/test_gates_config.py`
Expected: FAIL — `KeyError: 'e2e-smoke'` (gate not defined yet).

- [ ] **Implement**

Append to `.context-index/governance/gates.yaml`, after the existing `integration-test` entry:

```yaml
  - id: e2e-smoke
    name: E2E API Smoke Suite
    kind: deterministic
    tier: e2e
    command: [.venv/bin/python3, -m, pytest, -q, tests_e2e/]
    scope: project
    required: false          # e2e tier default: severity forced to warning (first-generation
                              # e2e coverage for a course-fixture repo; not yet a merge blocker)
    severity: warning
    triggers:
      - post-implement
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests/test_gates_config.py`
Expected: PASS

- [ ] **Commit**

```bash
git add .context-index/governance/gates.yaml tests/test_gates_config.py
git commit -m "feat(issue-tracker-api): wire e2e-smoke gate for tests_e2e/ (tier: e2e, warning)"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` defines the deterministic gates for this project — used here instead of
constitution Quality Gates, per plan template precedence:

| Gate | Tier | Command | Severity |
|------|------|---------|----------|
| `test` | fast | `.venv/bin/python3 -m pytest -q` | error |
| `lint` | fast | `.venv/bin/ruff check .` | error |
| `test-js` | fast | `node --test "tests_js/**/*.test.js"` | error |
| `integration-test` | integration | *(unwired — `command: ""`)* | error (skipped, no command) |
| `e2e-smoke` | e2e | `.venv/bin/python3 -m pytest -q tests_e2e/` | warning *(added by Task 7)* |

- The `test` gate must keep passing with `tests_e2e/` excluded from its bare-invocation discovery
  scope (Task 6) — this is the load-bearing invariant this plan protects.
- `e2e-smoke` is `severity: warning` / `required: false` per the e2e-tier default in
  `governance/gates.yaml`'s own schema comment, deliberately kept rather than escalated, since
  this is first-generation e2e coverage for a course-fixture repo.
- All eight acceptance criteria in `api-e2e.spec.md` must be satisfied: real out-of-process
  server startup (BEH-1 precondition), Project round-trip (BEH-1), full Issue lifecycle (BEH-2),
  404/409/422 error paths (BEH-3), valid OpenAPI document (BEH-4), seeded data visible on fresh
  start (BEH-5), all quality gates passing, no constitutional violations.

