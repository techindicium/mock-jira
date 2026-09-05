<!-- partial_schema: plan@1 -->

# Implementation Plan: Docker packaging and run instructions

> **Methodology:** adev
> **Charter:** .context-index/specs/cross-cutting/deployment/charter.md
> **Spec:** .context-index/specs/cross-cutting/docker-packaging.spec.md
> **Review:** PASS (2026-09-05) — 3 advisory suggestions (SA-1, SEC-1, CON-1), no blockers/warnings
> **Platform:** FastAPI + `mcp` SDK 2.1.1, Python 3.12 (`.venv` is 3.12.13 — `platform-context.yaml`
> still says `3.11`/`framework: none`, which is stale; this plan targets the actual interpreter
> version, and base images are pinned to match), SQLite, Docker Compose

**Goal:** Package `issue-tracker-api` (which also serves `kanban-ui`'s static assets) and
`mcp-server` into two Dockerfiles plus a `docker-compose.yml`, wired with a named volume for the
SQLite file and a `PORT`/`API_BASE_URL`/`DATABASE_PATH` env-var convention, with run instructions
in the README/CLAUDE.md — so `docker compose up` from a clean checkout brings up the whole stack
with no manual step.

**Architecture:** Both Dockerfiles pin `python:3.12-slim` (matching this repo's actual `.venv`
version, not a floating tag — per review suggestion SEC-1). `issue-tracker-api`'s Dockerfile is a
**single stage**, not multi-stage: `static/` is plain HTML/CSS/vanilla JS with no bundler, so
"bundling kanban-ui's build output" is a plain `COPY static/ ./static/` at build time, with no
separate build stage to isolate. Two supporting code tasks (Tasks 1-2) land first so the
Dockerfiles and compose file have real env-var behavior to wire against, rather than writing
container config against env vars the code doesn't yet read: `app/main.py` currently hardcodes
`DB_PATH = "mock_jira.db"` and has no startup-failure message naming the path
(`DEPLOY_VOLUME_NOT_WRITABLE`), and `mcp_server/server.py` currently always runs `mcp.run()` with
the default `stdio` transport, which cannot serve a long-running containerized process with no
attached stdin. `mcp_server/config.py`'s `get_api_base_url()` and
`mcp_server/client.py`'s per-request `UpstreamUnreachableError` handling already satisfy
`DEPLOY_UPSTREAM_UNREACHABLE` (it's read and validated lazily per-tool-call, not eagerly at
import/registration time, so a missing/unreachable API never crash-loops the process) — confirmed
by reading `mcp_server/tools/{issues,projects}.py` and the existing
`tests/mcp_server/test_client.py::test_list_projects_unreachable_api_raises_upstream_unreachable_error`
test; **no new code is needed for that error case**, only Task 2's transport change.

Dockerfiles live under `docker/<module>/Dockerfile` (not root-level `Dockerfile.<module>` names)
so each is discoverable as a literal `Dockerfile` basename — this also matches this project's
`test-strategies` auto-detection heuristic (`lib/test-strategies/detection.mjs`), which flags
`policy` strategy (medium confidence) on any file literally named `Dockerfile` anywhere in the
tree. Both Dockerfiles' `context:` in `docker-compose.yml` is the repo root (`.`), since each
needs to `COPY` from `app/`, `static/`, or `mcp_server/` at the repo root, not from inside their
own `docker/<module>/` directory.

**Design decision — two host-override variables, one in-container convention.** The charter's
`PORT` convention means each module independently reads its own listen port from a `PORT`
environment variable inside its own container (so neither module's code hardcodes a port) — it
does **not** mean both containers share one host-level override knob, which would make them
collide on the same published `localhost` port. `docker-compose.yml` therefore exposes two
distinct **host**-level substitution variables — `PORT` (issue-tracker-api's published port,
default `8000`) and `MCP_PORT` (mcp-server's published port, default `8001`) — while each
container's own `environment:` block still sets its internal env var literally named `PORT`,
satisfying BEH-4 ("no code change in either module") without a host port collision. This is
called out again at Task 5, where it's implemented, for reviewer visibility.

**Constitution Validation (Step 3):** Checked every task against `Architecture Boundaries`. No
task adds a dependency on another repo in the workspace — `python:3.12-slim` is a public base
image from a public registry, which the spec's own "System Constitution Reference" section
already confirms is not an inbound repo dependency. No task changes the public HTTP API contract
(no route paths, request/response shapes, or fixture-data identifiers change) or exposes a port
beyond `127.0.0.1` by default. `governance/boundaries.yaml` has `boundaries: []` — no file-pattern
rules to check tasks against. No task in this plan is marked `[REQUIRES HUMAN APPROVAL]`.

**Review notes addressed (PASS, advisory suggestions only):**
- **SEC-1** (suggestion) — addressed: both Dockerfiles pin `python:3.12-slim` explicitly (Tasks
  3-4), matching the actual `.venv` Python version rather than a floating `latest`/`3-slim` tag.
- **SA-1** (suggestion, healthcheck params unspecified) — addressed by judgment call: `interval:
  10s`, `timeout: 3s`, `start_period: 5s`, `retries: 5` (Task 5) — generous enough that a cold
  SQLite-schema-creation-and-seed startup won't flap, without leaving `mcp-server` waiting
  indefinitely on a wedged API.
- **CON-1** (suggestion, new error codes not checked against a prior taxonomy) — no action
  needed; the reviewer already noted this is fine since the codes are new to this spec and no
  prior error-code taxonomy exists to check against. `DEPLOY_VOLUME_NOT_WRITABLE` is implemented
  as a startup-time `RuntimeError` message (Task 1); `DEPLOY_UPSTREAM_UNREACHABLE` was already
  satisfied by existing `mcp_server` code (see Architecture above) and needed no new task.

---

## File Structure

**Create:**
- `docker/issue-tracker-api/Dockerfile` — single-stage `python:3.12-slim` image; installs
  `requirements.txt`; copies `app/` and `static/`; reads `PORT`/`DATABASE_PATH`; `HEALTHCHECK`
  against `/`
- `docker/mcp-server/Dockerfile` — single-stage `python:3.12-slim` image; installs
  `requirements-mcp.txt`; copies `mcp_server/`; reads `PORT`/`API_BASE_URL`
- `docker-compose.yml` — wires both services, named volume for the SQLite file, `depends_on`
  gated on issue-tracker-api's healthcheck, localhost-only port publishing
- `tests/test_docker_deploy.py` — static/config-level coverage for BEH-1 through BEH-4 and the
  localhost-only postcondition (created failing at Task 3, extended through Task 6)
- `tests/test_main_env.py` — `DATABASE_PATH`/`PORT` env-var behavior and the
  `DEPLOY_VOLUME_NOT_WRITABLE` startup error for `issue-tracker-api`
- `tests/mcp_server/test_transport.py` — `PORT`-driven transport selection for `mcp-server`

**Modify:**
- `app/main.py` — `DB_PATH` reads `DATABASE_PATH` env var (falls back to `"mock_jira.db"` for
  existing local/test usage); `on_startup()` wraps schema creation to raise a clear
  `DEPLOY_VOLUME_NOT_WRITABLE` error naming the path on failure
- `mcp_server/server.py` — `main()` selects `streamable-http` transport bound to `0.0.0.0:$PORT`
  when `PORT` is set (containerized run), otherwise keeps the existing `stdio` default (local
  dev / direct invocation unchanged)
- `README.md` — replace the stale "Not yet scoped" framing with `docker compose up` run
  instructions, exposed ports, and how to confirm the stack is healthy
- `.context-index/constitution.md` — add Docker run instructions to `## Quality Gates`, alongside
  the existing `pytest`/`ruff` commands; `CLAUDE.md` is then regenerated from it via `/adev:sync`
  (never hand-edited — see Task 6)

**Reference (read, do not modify):**
- `mcp_server/config.py` — `get_api_base_url()`, already reads `API_BASE_URL` and raises clearly
  when unset; unchanged
- `mcp_server/client.py` — `IssueTrackerClient._request()`, already raises
  `UpstreamUnreachableError` per-request on connection failure; unchanged
- `app/db.py` — `get_connection()` / `create_schema()`, the calls Task 1 wraps for the clearer
  startup error
- `tests/conftest.py` — existing `client` fixture pattern (monkeypatches `main_module.DB_PATH`
  directly); Task 1's new tests follow the same monkeypatch style but exercise the
  `DATABASE_PATH`-driven default instead
- `.context-index/specs/cross-cutting/deployment/charter.md` — Affected Modules, Interface
  Contracts (`PORT`/`API_BASE_URL`/`DATABASE_PATH` conventions), Quality Attributes
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands (`test`, `lint`);
  the `integration-test` gate stays unwired (`command: ""`) — see Quality Gates below

---

## Context Packets

> No `source-manifest.files[]` exists on this spec (it's a new cross-cutting spec, not a
> code-extraction one). Context packets fall back to charter + spec + constitution + the existing
> `app/`/`mcp_server/` implementations read as pattern references, per Step 2's "no
> source-manifest" fallback. No ADRs, samples, or `orientation/architecture.md` exist yet for this
> module. `.context-index/governance/boundaries.yaml` is empty (no rules to apply). No heuristics
> are available (`adev heuristics retrieve --module deployment` returned `__NONE__`).

### Task 1 Context
- Spec: `docker-packaging.spec.md` — Error Cases table (`DEPLOY_VOLUME_NOT_WRITABLE`); Module
  Impact Map row for `issue-tracker-api` ("reads `DATABASE_PATH` and `PORT` from env")
- Charter: `deployment/charter.md` — Interface Contracts → `DATABASE_PATH env var convention`
  ("issue-tracker-api reads its SQLite file path from this variable so compose can bind it to a
  named volume")
- Source files: `app/main.py` (full read — the `DB_PATH` constant and `on_startup()` to modify),
  `app/db.py` (full read — `get_connection()`/`create_schema()`, whose failure mode Task 1 wraps)
- Reference: `tests/conftest.py` (existing `client` fixture's monkeypatch pattern)

### Task 2 Context
- Spec: `docker-packaging.spec.md` — Error Cases table (`DEPLOY_UPSTREAM_UNREACHABLE`, already
  satisfied — see Architecture note); Module Impact Map row for `mcp-server` ("reads
  `API_BASE_URL` and `PORT` from env")
- Charter: `deployment/charter.md` — Interface Contracts → `PORT env var convention`
- Source files: `mcp_server/server.py` (full read — the `main()` function to modify),
  `mcp_server/config.py` (full read — already-satisfied `API_BASE_URL` handling, do not modify),
  `mcp_server/client.py` (full read — already-satisfied `UpstreamUnreachableError` handling, do
  not modify)
- Reference: `tests/mcp_server/test_config.py`, `tests/mcp_server/test_client.py` (existing
  coverage confirming Task 2 doesn't need to touch these behaviors)

### Task 3 Context
- Spec: `docker-packaging.spec.md` — BEH-1 (build produces exactly two images); Actionable Task
  Map row "`issue-tracker-api` Dockerfile"; System Constitution Reference (public base image is
  not an inbound dependency)
- Charter: `deployment/charter.md` — Affected Modules row for `issue-tracker-api`; Scope → "no
  separate build step" framing for `kanban-ui`'s static assets
- Source files: `requirements.txt` (full read — what gets installed), `static/` directory listing
  (full read — what gets copied; plain HTML/CSS/JS, confirms no bundler/build stage needed),
  `app/main.py` (post-Task-1 state — confirms `DATABASE_PATH`/root-route liveness are ready to
  wire against)
- Review: SEC-1 (pin base image version, not `latest`)

### Task 4 Context
- Spec: `docker-packaging.spec.md` — BEH-1; Actionable Task Map row "`mcp-server` Dockerfile"
- Charter: `deployment/charter.md` — Affected Modules row for `mcp-server`
- Source files: `requirements-mcp.txt` (full read), `mcp_server/server.py` (post-Task-2 state —
  confirms the `PORT`-driven transport switch is ready to wire against)
- Review: SEC-1 (pin base image version, not `latest`)

### Task 5 Context
- Spec: `docker-packaging.spec.md` — BEH-2 (startup order/health-gated dependency), BEH-3 (volume
  persistence), BEH-4 (PORT remap), Postconditions (localhost-only by default); Integration
  Points 1-2; Actionable Task Map row "`docker-compose.yml`"
- Charter: `deployment/charter.md` — Interface Contracts (all three env var conventions);
  Consumed APIs (healthcheck backing `depends_on`); Quality Attributes (Security: localhost-only;
  Availability: dependency-ordered startup)
- Source files: `docker/issue-tracker-api/Dockerfile` and `docker/mcp-server/Dockerfile` (from
  Tasks 3-4, full read — the `build.dockerfile` paths and `ENV`/`EXPOSE` values compose must
  match)
- Review: SA-1 (healthcheck param judgment call, documented in Architecture above)

### Task 6 Context
- Spec: `docker-packaging.spec.md` — Actionable Task Map row "Run instructions"; Postconditions
  ("no manual step beyond `docker compose up`"); Acceptance Criteria checklist (all six behaviors
  plus the two quality-gate/constitution items)
- Charter: `deployment/charter.md` — Business Intent (one-command local runtime)
- Source files: `README.md` (full read — current stale "Not yet scoped" text to replace),
  `.context-index/constitution.md` (full read — existing `## Quality Gates` section to extend);
  `CLAUDE.md` (read-only — regenerated by `/adev:sync`, never hand-edited)

## Parallelization

- Group A (sequential): Task 1 → Task 3
- Group B (sequential): Task 2 → Task 4
- Group C (sequential): Task 5 → Task 6

Groups A and B touch disjoint files (`app/main.py` vs. `mcp_server/server.py`) and can run in
parallel. Group C cannot start until both finish — Task 5 depends on the Dockerfiles produced by
both Task 3 (Group A) and Task 4 (Group B).

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | `issue-tracker-api` reads `DATABASE_PATH`/`PORT`, clear startup error | small | unit | — | 1 create, 1 modify |
| 2 | `mcp-server` reads `PORT`, adds `streamable-http` transport | small | unit | — | 1 create, 1 modify |
| 3 | `issue-tracker-api` Dockerfile | medium | policy | Task 1 | 2 create |
| 4 | `mcp-server` Dockerfile | small | policy | Task 2 | 1 create |
| 5 | `docker-compose.yml` | medium | policy | Task 3, Task 4 | 1 create |
| 6 | Run instructions (README/CLAUDE.md) | small | policy | Task 5 | 0 create, 2 modify |

---

## Strategy Summary

| Strategy | Tasks | Source |
|----------|-------|--------|
| unit | 2 | fallback |
| policy | 4 | detected, medium confidence |

⚠ Low confidence note: `policy` strategy auto-detects on any file literally named `Dockerfile`
anywhere in the tree (`lib/test-strategies/detection.mjs`) and is normally aimed at
conftest/OPA-style policy-as-code checks. No `policy` command is registered in this project's
`manifest.yaml` `test_strategies` (none are declared — everything defaults through the fallback
chain). Tasks 3-6 are verified instead by static/config assertions in
`tests/test_docker_deploy.py`, which runs under the ordinary `test` gate
(`python -m pytest -q`) alongside every other suite — no new gate or command is needed. This
plan does not attempt full `docker compose build`/`up` execution inside the fast test loop (slow,
and this repo's `test_depth: minimal` / `quick` posture for `risk_level: low` doesn't call for
it); full end-to-end verification is a documented manual step in Task 6.

## Test Infrastructure Requirements

> Emitted because Tasks 3-6 carry a non-`unit` strategy (`policy`). The automated `test` gate
> itself needs nothing beyond the checked-in Python toolchain — `tests/test_docker_deploy.py`
> only reads `Dockerfile`/`docker-compose.yml` off disk with `pytest`/`pyyaml`, no daemon
> involved. Docker Engine is only exercised by the optional manual verification checklist in
> Quality Gates, never by the automated gate.

### External Systems

| System | Required By | Strategy |
|--------|-------------|----------|
| Docker Engine + Compose CLI | Manual verification checklist (Quality Gates), not the automated `test` gate | policy (Tasks 3-6, advisory only) |

### Credentials / Environment Variables

None. Docker Engine runs locally with no credentials. `PORT`, `MCP_PORT`, `API_BASE_URL`, and
`DATABASE_PATH` are non-secret runtime configuration, not credentials — no value for any of them
is recorded in this plan, only the variable names per the spec's own convention.

### Pre-Provisioned State

- [ ] Docker Engine and Docker Compose CLI installed locally (already present in this dev
  environment — confirmed via `docker --version` / `docker-compose --version` during planning)

### CI Configuration

No CI pipeline exists for this project ("CI/CD pipeline automation" is explicitly out of scope
per `deployment/charter.md`). The automated `test` gate (`python -m pytest -q`) requires no
Docker daemon. Full `docker compose build`/`up` execution stays a manual step — see the
checklist in Quality Gates below.

### Unresolved Requirements

None.

## Task Structure

### Task 1: `issue-tracker-api` reads `DATABASE_PATH`/`PORT`, clear startup error [specialist: none]

**Charter capability:** Interface Contracts → `DATABASE_PATH env var convention` (`deployment/charter.md`)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/main.py:15` (the `DB_PATH` constant), `app/main.py:31-34` (`on_startup()`)
- Test: `tests/test_main_env.py`

**Tests:** `tests/test_main_env.py` (new — create)

- [ ] **Write failing test**

```python
import sqlite3

import pytest

import app.main as main_module


def test_db_path_defaults_to_env_var_database_path(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/tmp/from-env.db")
    # DB_PATH is resolved at import time; re-derive via the same helper the
    # module uses so the test exercises real resolution logic, not a literal.
    assert main_module.resolve_db_path() == "/tmp/from-env.db"


def test_db_path_falls_back_to_default_when_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    assert main_module.resolve_db_path() == "mock_jira.db"


def test_startup_raises_clear_error_naming_the_path_when_unwritable(monkeypatch, tmp_path):
    unwritable_dir = tmp_path / "no-such-parent" / "db.sqlite"
    monkeypatch.setattr(main_module, "DB_PATH", str(unwritable_dir))
    with pytest.raises(RuntimeError, match=str(unwritable_dir)):
        main_module.on_startup()
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_main_env.py`
Expected: FAIL — `AttributeError: module 'app.main' has no attribute 'resolve_db_path'` (and
`on_startup()` currently raises a bare `sqlite3.OperationalError`, not a `RuntimeError` naming the
path)

- [ ] **Implement**

```python
# app/main.py
import os

def resolve_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "mock_jira.db")


DB_PATH = resolve_db_path()

...

@app.on_event("startup")
def on_startup() -> None:
    try:
        conn = get_connection(DB_PATH)
        create_schema(conn)
    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            f"DATABASE_PATH '{DB_PATH}' is not writable: {exc}"
        ) from exc
    seed_if_empty(conn, DB_PATH)
    app.state.db_conn = conn
```

Import `sqlite3` at the top of `app/main.py` (needed for the `except sqlite3.OperationalError`
clause). `tests/conftest.py`'s existing `client` fixture still works unchanged — it monkeypatches
`main_module.DB_PATH` directly after import, which `on_startup()` still reads.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_main_env.py`
Expected: PASS

Also run the full suite to confirm no regression: `python -m pytest -q`

- [ ] **Commit**

Branch: `feat/docker-packaging/env-var-config`

```bash
git add app/main.py tests/test_main_env.py
git commit -m "feat(issue-tracker-api): read DATABASE_PATH env var, clear startup error on unwritable path"
```

---

### Task 2: `mcp-server` reads `PORT`, adds `streamable-http` transport [specialist: none]

**Charter capability:** Interface Contracts → `PORT env var convention` (`deployment/charter.md`)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `mcp_server/server.py:5-11` (the `main()` function)
- Test: `tests/mcp_server/test_transport.py`

**Tests:** `tests/mcp_server/test_transport.py` (new — create)

- [ ] **Write failing test**

```python
import os

import mcp_server.server as server_module


def test_main_runs_stdio_by_default(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    calls = []
    monkeypatch.setattr(server_module.mcp, "run", lambda *a, **kw: calls.append((a, kw)))
    server_module.main()
    assert calls == [((), {})]


def test_main_runs_streamable_http_when_port_is_set(monkeypatch):
    monkeypatch.setenv("PORT", "8001")
    calls = []
    monkeypatch.setattr(server_module.mcp, "run", lambda *a, **kw: calls.append((a, kw)))
    server_module.main()
    assert calls == [((), {"transport": "streamable-http", "host": "0.0.0.0", "port": 8001})]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/mcp_server/test_transport.py`
Expected: FAIL — `main()` always calls `mcp.run()` with no args regardless of `PORT`

- [ ] **Implement**

```python
# mcp_server/server.py
import os

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("mock-jira-mcp")


def main() -> None:
    import mcp_server.tools.issues
    import mcp_server.tools.projects  # noqa: F401  (import registers the tools as a side effect)

    port = os.environ.get("PORT")
    if port:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/mcp_server/test_transport.py`
Expected: PASS

Also run the full suite: `python -m pytest -q` (confirms `tests/mcp_server/test_config.py` and
`tests/mcp_server/test_client.py` are untouched and still pass — no code change was needed for
`DEPLOY_UPSTREAM_UNREACHABLE`).

- [ ] **Commit**

```bash
git add mcp_server/server.py tests/mcp_server/test_transport.py
git commit -m "feat(mcp-server): read PORT env var, run streamable-http transport when set"
```

---

### Task 3: `issue-tracker-api` Dockerfile [specialist: none]

**Charter capability:** Affected Modules → `issue-tracker-api` (`deployment/charter.md`)
**Depends on:** Task 1
**Strategy:** policy (source: detected, confidence: medium — see Strategy Summary)
**Files:**
- Create: `docker/issue-tracker-api/Dockerfile`
- Test: `tests/test_docker_deploy.py` (created here, extended by Tasks 4-6)

**Tests:** `tests/test_docker_deploy.py` (new — create)

- [ ] **Write failing test**

```python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_issue_tracker_api_dockerfile_pins_python_3_12_slim():
    dockerfile = REPO_ROOT / "docker" / "issue-tracker-api" / "Dockerfile"
    assert dockerfile.exists(), "docker/issue-tracker-api/Dockerfile is missing"
    content = dockerfile.read_text()
    assert "FROM python:3.12-slim" in content
    assert "latest" not in content.lower()


def test_issue_tracker_api_dockerfile_declares_healthcheck_and_reads_env():
    content = (REPO_ROOT / "docker" / "issue-tracker-api" / "Dockerfile").read_text()
    assert "HEALTHCHECK" in content
    assert "DATABASE_PATH" in content
    assert "PORT" in content
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: FAIL — `docker/issue-tracker-api/Dockerfile is missing`

- [ ] **Implement**

```dockerfile
# docker/issue-tracker-api/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY static/ ./static/

ENV PORT=8000
ENV DATABASE_PATH=/data/mock_jira.db

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
  CMD python3 -c "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/', timeout=2)"

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
```

No separate build stage: `static/` is plain HTML/CSS/vanilla JS (`static/index.html`,
`static/css/board.css`, `static/js/board.js`, `static/js/board-logic.js`) with no bundler, so
"bundling kanban-ui's build output" is exactly the `COPY static/ ./static/` line above.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: PASS (both Task 3 assertions)

- [ ] **Commit**

```bash
git add docker/issue-tracker-api/Dockerfile tests/test_docker_deploy.py
git commit -m "feat(deploy): add issue-tracker-api Dockerfile"
```

---

### Task 4: `mcp-server` Dockerfile [specialist: none]

**Charter capability:** Affected Modules → `mcp-server` (`deployment/charter.md`)
**Depends on:** Task 2
**Strategy:** policy (source: detected, confidence: medium — see Strategy Summary)
**Files:**
- Create: `docker/mcp-server/Dockerfile`
- Test: `tests/test_docker_deploy.py` (extend)

**Tests:** `tests/test_docker_deploy.py` (extend — add assertions below)

- [ ] **Write failing test**

```python
def test_mcp_server_dockerfile_pins_python_3_12_slim():
    dockerfile = REPO_ROOT / "docker" / "mcp-server" / "Dockerfile"
    assert dockerfile.exists(), "docker/mcp-server/Dockerfile is missing"
    content = dockerfile.read_text()
    assert "FROM python:3.12-slim" in content
    assert "latest" not in content.lower()


def test_mcp_server_dockerfile_reads_env():
    content = (REPO_ROOT / "docker" / "mcp-server" / "Dockerfile").read_text()
    assert "API_BASE_URL" in content
    assert "PORT" in content
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: FAIL — `docker/mcp-server/Dockerfile is missing`

- [ ] **Implement**

```dockerfile
# docker/mcp-server/Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements-mcp.txt .
RUN pip install --no-cache-dir -r requirements-mcp.txt

COPY mcp_server/ ./mcp_server/

ENV PORT=8001
ENV API_BASE_URL=http://issue-tracker-api:8000

EXPOSE 8001

CMD ["python3", "-m", "mcp_server.server"]
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: PASS (all four Dockerfile assertions from Tasks 3-4)

- [ ] **Commit**

```bash
git add docker/mcp-server/Dockerfile tests/test_docker_deploy.py
git commit -m "feat(deploy): add mcp-server Dockerfile"
```

---

### Task 5: `docker-compose.yml` [specialist: none]

**Charter capability:** Interface Contracts (all three env-var conventions); Consumed APIs
(healthcheck backing `depends_on`) (`deployment/charter.md`)
**Depends on:** Task 3, Task 4
**Strategy:** policy (source: detected, confidence: medium — see Strategy Summary)
**Files:**
- Create: `docker-compose.yml`
- Test: `tests/test_docker_deploy.py` (extend)

**Tests:** `tests/test_docker_deploy.py` (extend — add assertions below)

- [ ] **Write failing test**

```python
import yaml


def _load_compose():
    return yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())


def test_compose_builds_exactly_two_services_from_dockerfiles():  # BEH-1
    compose = _load_compose()
    services = compose["services"]
    assert set(services) == {"issue-tracker-api", "mcp-server"}
    for svc in services.values():
        assert "build" in svc, "each service must build its own image, not pull one"


def test_mcp_server_depends_on_issue_tracker_api_healthy():  # BEH-2
    compose = _load_compose()
    depends_on = compose["services"]["mcp-server"]["depends_on"]
    assert depends_on["issue-tracker-api"]["condition"] == "service_healthy"
    assert "healthcheck" in compose["services"]["issue-tracker-api"]


def test_named_volume_backs_the_sqlite_path():  # BEH-3
    compose = _load_compose()
    assert "mock_jira_db" in compose.get("volumes", {})
    api_volumes = compose["services"]["issue-tracker-api"]["volumes"]
    assert any(v.startswith("mock_jira_db:") for v in api_volumes)


def test_ports_are_env_var_driven_not_hardcoded():  # BEH-4
    compose = _load_compose()
    api_ports = compose["services"]["issue-tracker-api"]["ports"]
    mcp_ports = compose["services"]["mcp-server"]["ports"]
    assert any("${PORT" in p for p in api_ports)
    assert any("${MCP_PORT" in p for p in mcp_ports)


def test_no_port_exposed_beyond_localhost():  # postcondition
    compose = _load_compose()
    for svc in compose["services"].values():
        for mapping in svc.get("ports", []):
            assert mapping.startswith("127.0.0.1:"), f"{mapping} is not localhost-scoped"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: FAIL — `docker-compose.yml` does not exist yet (`FileNotFoundError`)

- [ ] **Implement**

```yaml
# docker-compose.yml
services:
  issue-tracker-api:
    build:
      context: .
      dockerfile: docker/issue-tracker-api/Dockerfile
    ports:
      - "127.0.0.1:${PORT:-8000}:${PORT:-8000}"
    environment:
      PORT: ${PORT:-8000}
      DATABASE_PATH: /data/mock_jira.db
    volumes:
      - mock_jira_db:/data
    healthcheck:
      test: ["CMD", "python3", "-c", "import os, urllib.request; urllib.request.urlopen('http://localhost:' + os.environ.get('PORT', '8000') + '/', timeout=2)"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 5s

  mcp-server:
    build:
      context: .
      dockerfile: docker/mcp-server/Dockerfile
    ports:
      - "127.0.0.1:${MCP_PORT:-8001}:${MCP_PORT:-8001}"
    environment:
      # Same PORT convention as issue-tracker-api, but a separate host-level
      # override variable (MCP_PORT) so remapping one service's published
      # port never collides with the other's. See plan Architecture note.
      PORT: ${MCP_PORT:-8001}
      API_BASE_URL: http://issue-tracker-api:${PORT:-8000}
    depends_on:
      issue-tracker-api:
        condition: service_healthy

volumes:
  mock_jira_db:
```

`pyyaml` is needed by the test but is not currently in `requirements.txt` — add it (`RUN pip
install pyyaml` is not needed in the Docker images themselves, only for running this test suite
locally/in CI; add `pyyaml` to `requirements.txt` since that's what `python -m pytest -q` installs
from).

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: PASS (all BEH-1 through BEH-4 plus the localhost postcondition assertions)

Optional manual confirmation (not part of the fast test loop, but worth doing once before
considering this task done): `docker compose config --quiet` — validates the file is
well-formed and resolvable by the real Compose CLI, not just parseable YAML.

- [ ] **Commit**

```bash
git add docker-compose.yml requirements.txt tests/test_docker_deploy.py
git commit -m "feat(deploy): add docker-compose.yml wiring issue-tracker-api and mcp-server"
```

---

### Task 6: Run instructions (README.md / CLAUDE.md) [specialist: none]

**Charter capability:** Business Intent — "one-command local runtime" (`deployment/charter.md`)
**Depends on:** Task 5
**Strategy:** policy (source: detected, confidence: medium — see Strategy Summary; this task is
doc-only, the `policy` label just reflects it extends the same Dockerfile-adjacent suite)
**Files:**
- Modify: `README.md`, `.context-index/constitution.md` (`## Quality Gates` section)
- Regenerate: `CLAUDE.md` (via `/adev:sync` — **do not hand-edit**; its own header comment reads
  "Synced from `.context-index/constitution.md` by adev. Do not edit above the User Additions
  line," and its `## Commands` section is generated from constitution.md's `## Quality Gates`
  section, not a 1:1 copy — confirmed by diffing the two files)
- Test: `tests/test_docker_deploy.py` (extend)

**Tests:** `tests/test_docker_deploy.py` (extend — add assertion below)

- [ ] **Write failing test**

```python
def test_readme_documents_docker_compose_up():
    content = (REPO_ROOT / "README.md").read_text()
    assert "docker compose up" in content


def test_constitution_documents_docker_commands():
    content = (REPO_ROOT / ".context-index" / "constitution.md").read_text()
    assert "docker compose up" in content


def test_claude_md_documents_docker_commands():
    # CLAUDE.md is regenerated by `/adev:sync` from constitution.md — this
    # assertion catches a forgotten sync step just as much as forgotten content.
    content = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "docker compose up" in content
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: FAIL — neither `README.md` nor `.context-index/constitution.md`/`CLAUDE.md` currently
mentions `docker compose up`

- [ ] **Implement**

Replace `README.md`'s stale "Not yet scoped" paragraph with:

~~~markdown
## Running with Docker

```bash
docker compose up
```

This builds two images (`issue-tracker-api`, which also serves `kanban-ui`'s static assets, and
`mcp-server`) and starts them in dependency order — `issue-tracker-api` first, `mcp-server` once
the API reports healthy.

- `issue-tracker-api` is published at `http://localhost:8000` (override with `PORT=<port>`)
- `mcp-server` is published at `http://localhost:8001` (override with `MCP_PORT=<port>`)
- Neither port is exposed beyond `localhost` by default
- The SQLite database lives in a named volume (`mock_jira_db`) and survives `docker compose down`
  (without `-v`)
- Confirm the stack is healthy: `docker compose ps` (both services should show `healthy`/`running`)
  or `curl http://localhost:8000/`
- View combined logs from both containers: `docker compose logs -f`
- Tear down (keeping data): `docker compose down`; tear down and wipe data: `docker compose down -v`
~~~

Add the same content, condensed to a `docker compose up` bullet list, to
`.context-index/constitution.md`'s existing `## Quality Gates` section (right after the existing
`python3 -m pytest -q` / `ruff check .` code block — that section is literally titled "Commands
that must pass before any implementation is considered complete," which is a slight mismatch for
run instructions, but it's this repo's existing single home for "how to run this project" prose,
and splitting it into a new top-level section is unnecessary scope for a small addition). Then
run `/adev:sync` to regenerate `CLAUDE.md` from the updated constitution — **do not hand-edit
`CLAUDE.md`**.

```bash
adev sync
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_docker_deploy.py`
Expected: PASS (all three assertions, including the regenerated `CLAUDE.md`)

- [ ] **Commit**

```bash
git add README.md .context-index/constitution.md CLAUDE.md tests/test_docker_deploy.py
git commit -m "docs(deploy): document docker compose run instructions"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` exists and is used in place of the constitution's generic gate list:

- **Test Suite** (`test`, deterministic, required, severity error): `python -m pytest -q` — this
  now includes `tests/test_main_env.py`, `tests/mcp_server/test_transport.py`, and
  `tests/test_docker_deploy.py`
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .`
- **Integration Tests** (`integration-test`, deterministic, required): command is unwired
  (`command: ""` in `gates.yaml`). This gate stays **skipped** for this plan — the static
  config-level coverage in `tests/test_docker_deploy.py` runs under the ordinary `test` gate
  instead (see Strategy Summary above for why full `docker compose build`/`up` execution is left
  to manual verification rather than a wired integration-test command).
- All acceptance criteria from `docker-packaging.spec.md` satisfied: BEH-1 through BEH-5,
  both Postconditions, and both Error Cases (`DEPLOY_VOLUME_NOT_WRITABLE`,
  `DEPLOY_UPSTREAM_UNREACHABLE`).

**Manual verification checklist (not part of the automated gate suite, but recommended once
before considering this plan fully done — BEH-3 and BEH-5 in particular require an actual running
stack, which the static tests above cannot exercise):**

- [ ] `docker compose build` — confirm exactly two images are produced (BEH-1)
- [ ] `docker compose up` — confirm `issue-tracker-api` becomes healthy before `mcp-server` starts
  (BEH-2); `docker compose ps` shows both running
- [ ] Create an Issue via the UI or API, then `docker compose down` (no `-v`) followed by
  `docker compose up` again — confirm the Issue is still present (BEH-3)
- [ ] `PORT=9000 MCP_PORT=9001 docker compose up` — confirm both services remap without any code
  change (BEH-4)
- [ ] `docker compose logs` — confirm both containers' output appears in one combined stream
  (BEH-5)
- [ ] `docker compose down -v` at the end, to leave no dangling volume from manual testing
