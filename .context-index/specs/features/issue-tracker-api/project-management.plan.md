<!-- partial_schema: plan@1 -->

# Implementation Plan: Project management and OpenAPI contract

> **Methodology:** adev
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Spec:** .context-index/specs/features/issue-tracker-api/project-management.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-04)
> **Platform:** FastAPI (spec-designated), Python 3.11, SQLite, Pydantic

**Goal:** Implement the Project management HTTP surface (`POST /projects`, `GET /projects`,
`GET /projects/{id}`) backed by a local SQLite schema, and confirm the auto-generated
`GET /openapi.json` contract — the first live slice of the mock-jira HTTP API.

**Architecture:** This is the first code in the repository (no `app/`, `tests/`, or dependency
manifest exist yet), so this plan also establishes the base layout the sibling `issue-lifecycle`
and `fixture-seeding` specs will build on. A FastAPI app (`app/main.py`) runs an idempotent
SQLite schema-creation step on startup (`app/db.py`), exposes a thin router
(`app/routers/projects.py`) backed by Pydantic request/response models (`app/models.py`), and
relies entirely on FastAPI's built-in `/openapi.json` generation — never a hand-authored OpenAPI
document — per the charter's "the HTTP contract is the boundary" principle.

`platform-context.yaml` currently lists `framework: none` ("not yet chosen"), but the spec's own
Actionable Task Map designates FastAPI + Pydantic + SQLite explicitly (`POST /projects` task:
"Pydantic request model validation"; OpenAPI task: "FastAPI's auto-generated `/openapi.json`").
This plan treats that as the spec's binding framework decision and builds accordingly; a
follow-up to `platform-context.yaml` to record `framework: fastapi` is a reasonable hygiene
cleanup but is not a gating concern for this plan.

**Constitution Validation (Step 3):** Checked every task's files/behavior against
`Architecture Boundaries`. None of these tasks add a workspace-repo dependency, touch auth, or
break an already-shipped contract (this is the first version of these endpoints). Adding
`fastapi`/`uvicorn`/`pydantic`/`pytest`/`ruff` as pip dependencies is consistent with the
constitution's own documented `Commands` section (`pip install -r requirements.txt`,
`ruff check .`) and needs no separate human approval. `governance/boundaries.yaml` has no rules
configured (`boundaries: []`), so no file-pattern flags apply. No task in this plan is marked
`[REQUIRES HUMAN APPROVAL]`.

**Review notes carried forward (PASS_WITH_NOTES):**
- **SA-1** (suggestion) — the spec doesn't state whether `description` is required on
  `POST /projects` input. This plan treats it as **optional, defaulting to an empty string when
  omitted** (see Task 2). Recommend folding this into a `project-management.spec.md` revision
  separately from this plan.
- **CON-1** (warning) — the spec is silent on how runtime-created Project ids/keys avoid
  colliding with `course-shared/canon/identifiers.md`'s reserved prefixes
  (`ACCOUNT-`, `TICKET-`, `ARTICLE-`, `PROPOSAL-`, `INCIDENT-`, `POLICY-`, `OPPORTUNITY-`,
  `EXPERIMENT-`, `P-`, `INTERACTION-`). This is advisory, not a spec requirement, so it is
  **not** added as a required acceptance check in Task 2 (adding an unrequested validation rule
  as a hard requirement would silently expand the reviewed contract). Task 2 carries a note
  flagging this as a candidate defensive addition for a future spec revision, consistent with
  the review's own recommendation to "fold CON-1 into a spec revision" rather than block on it.

---

## File Structure

**Create:**
- `requirements.txt` — deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `httpx` (needed by FastAPI's `TestClient`), `ruff`
- `app/__init__.py` — package marker
- `app/db.py` — SQLite connection helper + idempotent `create_schema()`
- `app/models.py` — Pydantic models: `ProjectCreate`, `ProjectRead`
- `app/main.py` — `FastAPI()` app instance; startup hook calls `create_schema()`; mounts the projects router
- `app/routers/__init__.py` — package marker
- `app/routers/projects.py` — `POST /projects`, `GET /projects`, `GET /projects/{id}`
- `tests/__init__.py` — package marker
- `tests/conftest.py` — pytest fixture: isolated temp SQLite file + `TestClient` per test (no cross-test pollution)
- `tests/test_db.py` — schema-creation idempotency coverage (Precondition)
- `tests/test_projects.py` — BEH-1 through BEH-6 coverage
- `tests/test_openapi.py` — BEH-7 coverage

**Modify:** none — this is the first implementation work in the repository.

**Reference (read, do not modify):**
- `.context-index/specs/features/issue-tracker-api/charter.md` — Capability Map, Domain Model, Invariants
- `CLAUDE.md` — constitution: "HTTP contract is the boundary", "breaking API changes are coordinated", "identifiers reconcile with the shared canon"
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands (used instead of constitution generic gates, per Step 5 Quality Gates rule)

---

## Context Packets

> No `source-manifest.files[]` exists on this spec yet (greenfield — first implementation), and
> the sibling specs (`issue-lifecycle`, `fixture-seeding`) are `review-pending` with no
> source-manifest of their own either. No `orientation/architecture.md`, ADRs, or samples exist
> in this repo yet. Context packets below fall back to charter + spec + constitution only, per
> Step 2's "no source-manifest" fallback.

### Task 1 Context
- Spec: `.context-index/specs/features/issue-tracker-api/project-management.spec.md` (Preconditions: "SQLite database file exists ... schema creation is idempotent")
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: Create/list/get Project; Domain Model → Project entity: `id`, `key`, `name`, `description`)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty, no rules to apply
- Heuristics: none available for module `issue-tracker-api`

### Task 2 Context
- Spec: `.context-index/specs/features/issue-tracker-api/project-management.spec.md` (BEH-1, BEH-2, BEH-3; Error Cases table: `PROJECT_KEY_DUPLICATE`, `VALIDATION_ERROR`, `MALFORMED_JSON`)
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: Create/list/get Project; Invariants: "A Project's `key` is unique, immutable once created")
- Review notes: SA-1 (description optionality), CON-1 (canon reserved-prefix advisory — see plan header)
- Source files: `app/db.py`, `app/models.py` (from Task 1, full read)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty, no rules to apply

### Task 3 Context
- Spec: `.context-index/specs/features/issue-tracker-api/project-management.spec.md` (BEH-4; Postconditions: "immediately retrievable ... no eventual consistency window")
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: Create/list/get Project)
- Source files: `app/routers/projects.py` (from Task 2, full read — extending, not replacing)

### Task 4 Context
- Spec: `.context-index/specs/features/issue-tracker-api/project-management.spec.md` (BEH-5, BEH-6; Error Cases table: `PROJECT_NOT_FOUND`)
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: Create/list/get Project)
- Source files: `app/routers/projects.py` (from Task 2/3, full read — extending, not replacing)

### Task 5 Context
- Spec: `.context-index/specs/features/issue-tracker-api/project-management.spec.md` (BEH-7; Postconditions: "always reflects the currently mounted routes ... regenerated per request, never cached stale")
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: OpenAPI contract; Deferred Capabilities — none relevant)
- Source files: `app/main.py` (from Task 1, full read — verifying router mount only, no modification expected)

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5

All five tasks are sequential: Task 1 is the foundation every later task imports from, and
Tasks 2-4 all extend the same two files (`app/routers/projects.py`, `tests/test_projects.py`),
so no independent group exists in this plan. Task 5 depends on Tasks 2-4 having mounted every
route it verifies.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Stand up FastAPI app and SQLite schema | medium | unit | — | 8 create, 0 modify |
| 2 | Implement `POST /projects` | small | unit | Task 1 | 1 create, 2 modify |
| 3 | Implement `GET /projects` | small | unit | Task 2 | 0 create, 2 modify |
| 4 | Implement `GET /projects/{id}` | small | unit | Task 3 | 0 create, 2 modify |
| 5 | Confirm OpenAPI wiring | small | unit | Task 2, Task 3, Task 4 | 1 create, 0 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no `test_strategies` entries in `manifest.yaml` matching these paths). Per Step 5,
the Strategy Summary section is omitted since every task is `unit`.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). `tests/test_projects.py` is created once (Task 2, covering
BEH-1/2/3) and extended twice (Task 3 for BEH-4, Task 4 for BEH-5/6); `tests/test_db.py` and
`tests/test_openapi.py` are each created once, by Task 1 and Task 5 respectively, since no other
task shares their behavior.

---

## Task Structure

### Task 1: Stand up FastAPI app and SQLite schema [specialist: none]

**Charter capability:** Create/list/get Project (foundation)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `requirements.txt`
- Create: `app/__init__.py`
- Create: `app/db.py`
- Create: `app/models.py`
- Create: `app/main.py`
- Create: `app/routers/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Test: `tests/test_db.py`

**Tests:** `tests/test_db.py` (create — first task to touch this behavior)

**Context to load:**
- Spec Preconditions: "The API process is running and its SQLite database file exists (created
  fresh on first run if absent — schema creation is idempotent)."
- Charter Domain Model: Project entity fields (`id`, `key`, `name`, `description`)

- [ ] **Write failing test**

```python
# tests/test_db.py
import sqlite3
from app.db import create_schema, get_connection

def test_create_schema_creates_projects_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
    )
    assert cursor.fetchone() is not None

def test_create_schema_is_idempotent(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    create_schema(conn)  # second call must not raise or duplicate the table
    cursor = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='projects'"
    )
    assert cursor.fetchone()[0] == 1
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_db.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'` (or `ImportError: cannot import
name 'create_schema'`), since `app/db.py` does not exist yet.

- [ ] **Implement**

```python
# app/db.py
import sqlite3

def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
```

```python
# app/models.py
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    key: str
    name: str
    description: str | None = None  # optional per review note SA-1; defaults to "" on create

class ProjectRead(BaseModel):
    id: int
    key: str
    name: str
    description: str
```

```python
# app/main.py
from fastapi import FastAPI
from app.db import get_connection, create_schema

DB_PATH = "mock_jira.db"

app = FastAPI(title="mock-jira", version="0.1.0")

@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection(DB_PATH)
    create_schema(conn)
    conn.close()
```

`app/routers/__init__.py`, `app/__init__.py`, `tests/__init__.py` are empty package markers.
`tests/conftest.py` provides an isolated per-test `TestClient` bound to a temp DB file (see
Task 2 for its first consumer — written here so Task 2 can use it immediately):

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
import app.main as main_module

@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(main_module, "DB_PATH", str(db_path))
    with TestClient(main_module.app) as c:
        yield c
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_db.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/issue-tracker-api/project-management-foundation`

```bash
git add requirements.txt app/__init__.py app/db.py app/models.py app/main.py app/routers/__init__.py tests/__init__.py tests/conftest.py tests/test_db.py
git commit -m "feat(issue-tracker-api): stand up FastAPI app and idempotent SQLite schema"
```

---

### Task 2: Implement `POST /projects` [specialist: none]

**Charter capability:** Create/list/get Project
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `app/routers/projects.py`
- Create: `app/errors.py` — shared exception handlers normalizing every error response to `{"message": ..., "code": ...}`
- Modify: `app/main.py` — include the projects router; register the two exception handlers from `app/errors.py`
- Test: `tests/test_projects.py`

**Tests:** `tests/test_projects.py` (create — first task to touch this behavior; covers BEH-1, BEH-2, BEH-3, plus the Error Cases table's `MALFORMED_JSON` case)

**Context to load:**
- Spec BEH-1, BEH-2, BEH-3 and the full Error Cases table (`PROJECT_KEY_DUPLICATE`, `VALIDATION_ERROR`, `MALFORMED_JSON`) — **all four rows of that table are in scope for this task**, not just the three named behaviors.
- Charter Invariants: "A Project's `key` is unique, immutable once created"
- Review note SA-1: `description` is optional on input, defaults to `""` when omitted (already reflected in `ProjectCreate` from Task 1)
- Review note CON-1 (non-blocking): the spec does not require rejecting Project keys that
  collide with `course-shared/canon/identifiers.md` reserved prefixes (`ACCOUNT-`, `TICKET-`,
  `ARTICLE-`, `PROPOSAL-`, `INCIDENT-`, `POLICY-`, `OPPORTUNITY-`, `EXPERIMENT-`, `P-`,
  `INTERACTION-`). **Out of scope for this task** — implementing an unrequested validation rule
  as a hard requirement would silently expand the reviewed contract. If desired, raise a
  `project-management.spec.md` revision adding this as an explicit behavior/error case first.
- **Plan-reviewer finding (fixed here):** the first pass of this plan left `MALFORMED_JSON`
  unimplemented entirely, and its `VALIDATION_ERROR` envelope diverged between manually-raised
  checks (empty string) and Pydantic's own missing-field errors (which FastAPI returns as
  `{"detail": [...]}` by default, with no `code` field). `app/errors.py` below fixes both:
  a `RequestValidationError` handler distinguishes "malformed JSON body" from "missing/invalid
  field" and emits the correct status + envelope for each, and an `HTTPException` handler
  unwraps this task's dict-shaped `detail` so every error path (`404`, `409`, `422`, `400`)
  returns the identical flat `{"message": ..., "code": ...}` shape at the top level — never
  nested under `"detail"`.

- [ ] **Write failing test**

```python
# tests/test_projects.py
def test_create_project_returns_201_with_full_representation(client):
    resp = client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"] == "SDLC"
    assert body["name"] == "SDLC Track"
    assert body["description"] == ""
    assert "id" in body

def test_create_project_duplicate_key_returns_409(client):
    client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    resp = client.post("/projects", json={"key": "SDLC", "name": "Another"})
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "PROJECT_KEY_DUPLICATE"
    assert "SDLC" in body["message"]

def test_create_project_missing_name_returns_422_with_error_envelope(client):
    # Field entirely absent from the body -> Pydantic/FastAPI raises RequestValidationError,
    # not our manual check. Must still surface the same VALIDATION_ERROR envelope.
    resp = client.post("/projects", json={"key": "SDLC"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "name" in body["message"]

def test_create_project_empty_key_returns_422_with_error_envelope(client):
    resp = client.post("/projects", json={"key": "", "name": "SDLC Track"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "key" in body["message"]

def test_create_project_malformed_json_returns_400(client):
    resp = client.post(
        "/projects",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "MALFORMED_JSON"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_projects.py`
Expected: FAIL — `404 Not Found` (no `/projects` route registered yet) or
`ModuleNotFoundError: No module named 'app.routers.projects'`. Once the route exists but before
`app/errors.py` is wired, the envelope/malformed-JSON tests fail on assertion (default FastAPI
error shape has no top-level `code`, and malformed JSON yields `422` not `400`) — confirming
those specific assertions are meaningful, not vacuous.

- [ ] **Implement**

```python
# app/errors.py
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    for error in errors:
        if error.get("type") == "json_invalid":
            return JSONResponse(
                status_code=400,
                content={"message": "Request body is not valid JSON", "code": "MALFORMED_JSON"},
            )
    first = errors[0] if errors else {}
    field = first.get("loc", ["field"])[-1]
    return JSONResponse(
        status_code=422,
        content={"message": f"{field} is required", "code": "VALIDATION_ERROR"},
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})
```

```python
# app/routers/projects.py
import sqlite3
from fastapi import APIRouter, HTTPException, Request
from app.models import ProjectCreate, ProjectRead

router = APIRouter()

@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, request: Request):
    if not payload.key or not payload.key.strip():
        raise HTTPException(status_code=422, detail={"message": "key is required", "code": "VALIDATION_ERROR"})
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=422, detail={"message": "name is required", "code": "VALIDATION_ERROR"})

    conn = request.app.state.db_conn
    try:
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description) VALUES (?, ?, ?)",
            (payload.key, payload.name, payload.description or ""),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={"message": f"Project key '{payload.key}' already exists", "code": "PROJECT_KEY_DUPLICATE"},
        )

    row = conn.execute("SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return ProjectRead(id=row["id"], key=row["key"], name=row["name"], description=row["description"])
```

Wire the router and both exception handlers in `app/main.py`. This **replaces** Task 1's
`on_startup` body with the one below (do not add a second `@app.on_event("startup")` handler —
edit the existing function in place):

```python
# app/main.py (modify)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.routers.projects import router as projects_router
from app.errors import validation_exception_handler, http_exception_handler

app.include_router(projects_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

@app.on_event("startup")  # replaces Task 1's on_startup body, same function, not a second handler
def on_startup() -> None:
    conn = get_connection(DB_PATH)
    create_schema(conn)
    app.state.db_conn = conn  # kept open for the process lifetime; sqlite3 handles serialization
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_projects.py`
Expected: PASS

- [ ] **Commit**

Branch (continue): `feat/issue-tracker-api/project-management-foundation`

```bash
git add app/routers/projects.py app/errors.py app/main.py tests/test_projects.py
git commit -m "feat(issue-tracker-api): implement POST /projects with a normalized error envelope covering duplicate-key, validation, and malformed-JSON cases"
```

---

### Task 3: Implement `GET /projects` [specialist: none]

**Charter capability:** Create/list/get Project
**Depends on:** Task 2
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/projects.py` — add list endpoint
- Modify: `tests/test_projects.py` — extend
- Test: `tests/test_projects.py`

**Tests:** `tests/test_projects.py` (extend — BEH-4; suite already created by Task 2)

**Context to load:**
- Spec BEH-4 and Postconditions: "immediately retrievable ... ordered by creation time"

- [ ] **Write failing test**

```python
# tests/test_projects.py (append)
def test_list_projects_returns_all_ordered_by_creation(client):
    client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    client.post("/projects", json={"key": "DDLC", "name": "DDLC Track"})
    resp = client.get("/projects")
    assert resp.status_code == 200
    keys = [p["key"] for p in resp.json()]
    assert keys == ["SDLC", "DDLC"]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_projects.py::test_list_projects_returns_all_ordered_by_creation`
Expected: FAIL — `405 Method Not Allowed` or `404 Not Found` (no `GET /projects` route yet).

- [ ] **Implement**

```python
# app/routers/projects.py (append)
from typing import List

@router.get("/projects", response_model=List[ProjectRead])
def list_projects(request: Request):
    conn = request.app.state.db_conn
    rows = conn.execute("SELECT * FROM projects ORDER BY id ASC").fetchall()
    return [
        ProjectRead(id=r["id"], key=r["key"], name=r["name"], description=r["description"])
        for r in rows
    ]
```

`ORDER BY id ASC` is equivalent to creation-time order given `id` is an `AUTOINCREMENT` primary
key assigned strictly in insertion order (Task 1's schema).

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_projects.py`
Expected: PASS

- [ ] **Commit**

```bash
git add app/routers/projects.py tests/test_projects.py
git commit -m "feat(issue-tracker-api): implement GET /projects ordered by creation time"
```

---

### Task 4: Implement `GET /projects/{id}` [specialist: none]

**Charter capability:** Create/list/get Project
**Depends on:** Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/projects.py` — add get-by-id endpoint
- Modify: `tests/test_projects.py` — extend
- Test: `tests/test_projects.py`

**Tests:** `tests/test_projects.py` (extend — BEH-5, BEH-6; suite already created by Task 2)

**Context to load:**
- Spec BEH-5, BEH-6 and Error Cases table (`PROJECT_NOT_FOUND`)

- [ ] **Write failing test**

```python
# tests/test_projects.py (append)
def test_get_project_by_id_returns_200(client):
    created = client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"}).json()
    resp = client.get(f"/projects/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["key"] == "SDLC"

def test_get_project_unknown_id_returns_404(client):
    resp = client.get("/projects/999999")
    assert resp.status_code == 404
    assert "999999" in resp.json()["message"]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_projects.py::test_get_project_by_id_returns_200`
Expected: FAIL — `404 Not Found` from FastAPI's default route-not-found (indistinguishable from
the intended 404 until the route exists — confirm by checking the response body carries no
`PROJECT_NOT_FOUND` code yet).

- [ ] **Implement**

```python
# app/routers/projects.py (append)
@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Project {project_id} not found", "code": "PROJECT_NOT_FOUND"},
        )
    return ProjectRead(id=row["id"], key=row["key"], name=row["name"], description=row["description"])
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_projects.py`
Expected: PASS

- [ ] **Commit**

```bash
git add app/routers/projects.py tests/test_projects.py
git commit -m "feat(issue-tracker-api): implement GET /projects/{id} with 404 handling"
```

---

### Task 5: Confirm OpenAPI wiring [specialist: none]

**Charter capability:** OpenAPI contract
**Depends on:** Task 2, Task 3, Task 4
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Test: `tests/test_openapi.py`

**Tests:** `tests/test_openapi.py` (create — first task to touch this behavior; covers BEH-7)

**Context to load:**
- Spec BEH-7 and Postconditions: "always reflects the currently mounted routes ... regenerated
  per request, never cached stale across a code change"
- Charter: "An OpenAPI-documented HTTP contract (auto-generated from the implementation, not
  hand-maintained)"

- [ ] **Write failing test**

```python
# tests/test_openapi.py
def test_openapi_json_lists_project_routes(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    doc = resp.json()
    assert "/projects" in doc["paths"]
    assert "post" in doc["paths"]["/projects"]
    assert "get" in doc["paths"]["/projects"]
    assert "/projects/{project_id}" in doc["paths"]
    assert "get" in doc["paths"]["/projects/{project_id}"]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_openapi.py`
Expected: FAIL if run in isolation before Tasks 2-4 land (no `/projects` routes mounted yet); in
this plan's execution order Tasks 2-4 are already complete, so this step confirms FastAPI's
built-in generator picks up the mounted routes without any hand-authored OpenAPI file — no
production code change is expected here. If the test unexpectedly fails after Tasks 2-4, that
signals a router-mounting gap in `app/main.py`, not a missing OpenAPI feature.

- [ ] **Implement**

No implementation step is expected: FastAPI auto-generates `/openapi.json` from the routes and
Pydantic models already registered in Tasks 1-4. If the test in fact fails, the fix belongs in
`app/main.py`'s router registration (Task 2's `include_router` call), not in a new
hand-maintained OpenAPI document — hand-authoring `/openapi.json` would violate the charter's
"auto-generated from the implementation, never hand-maintained" requirement.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_openapi.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests/test_openapi.py
git commit -m "test(issue-tracker-api): confirm auto-generated OpenAPI contract covers Project routes"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` exists and is used in place of the constitution's generic gate list:

- **Test Suite** (`test`, deterministic, required, severity error): `python -m pytest -q`
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .`
- **Integration Tests** (`integration-test`, deterministic, required): command is unwired
  (`command: ""` in `gates.yaml` — "no integration-test suite yet; seed once one exists"). This
  gate is **skipped** for this plan; nothing in this plan's task list requires an integration
  suite beyond the unit-level `TestClient` coverage above.
- All acceptance criteria from `project-management.spec.md` satisfied (BEH-1 through BEH-7).
