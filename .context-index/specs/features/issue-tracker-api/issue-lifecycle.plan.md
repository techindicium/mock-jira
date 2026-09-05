<!-- partial_schema: plan@1 -->

# Implementation Plan: Issue lifecycle CRUD

> **Methodology:** adev
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Spec:** .context-index/specs/features/issue-tracker-api/issue-lifecycle.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-04)
> **Platform:** FastAPI 0.x (per existing `app/` scaffold), Python 3.11, SQLite, Pydantic

**Goal:** Implement the full Issue CRUD HTTP surface (`POST /issues`, `GET /issues`,
`GET /issues/{id}`, `PATCH /issues/{id}`, `DELETE /issues/{id}`) with server-assigned,
per-project sequential keys, extending the existing FastAPI scaffold shipped by the
`project-management` spec on this branch.

**Architecture:** This plan extends the existing `app/` layout — it does not re-scaffold. A new
`issues` table (with a companion `project_issue_sequences` counter table for durable per-project
key sequencing) is added via `app/db.py`'s existing `create_schema()`. New Pydantic models
(`IssueCreate`, `IssueRead`, `IssuePatch`) go in `app/models.py` alongside the existing Project
models, using `Literal[...]` types for `issue_type`/`priority`/`status` so enum validation is
Pydantic-native. A new `app/routers/issues.py` mirrors the structure and error-envelope
conventions already established by `app/routers/projects.py` (raise
`HTTPException(status_code=..., detail={"message": ..., "code": ...})`, consumed by the existing
`app/errors.py` handlers). `app/main.py` is modified only to mount the new router;
`app/routers/projects.py` and `tests/test_projects.py` are untouched.

`app/errors.py`'s `StarletteHTTPException` handler needs no change — it already unwraps any
dict-shaped `detail` generically. Its `RequestValidationError` handler, however, **does** need a
small addition (Task 2, below): today it unconditionally reports every validation error as
`"{field} is required"`, which is correct for a genuinely missing field but factually wrong for
an out-of-set `Literal` value (e.g. `{"status": "blocked"}` would incorrectly say "status is
required") and doesn't satisfy the spec's Error Cases requirement that an invalid
`status`/`issue_type`/`priority` value name "the invalid field and its allowed values." Task 2
adds a branch for Pydantic's `literal_error` type that reports the field and its allowed values
instead, reusable by every future `Literal`-typed field (create and patch alike, closing SA-2's
asymmetry in code, not just for Issues).

**Constitution Validation (Step 3):** Checked every task's files/behavior against
`Architecture Boundaries`. No task adds a workspace-repo dependency, touches auth, or breaks an
already-shipped contract — `/issues` is a net-new endpoint family, and the Project surface
(`app/routers/projects.py`) is untouched. `governance/boundaries.yaml` has no rules configured
(`boundaries: []`), so no file-pattern flags apply. No task in this plan is marked
`[REQUIRES HUMAN APPROVAL]`. No new pip dependencies are required — `requirements.txt` already
carries `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `httpx`, `ruff` from the
`project-management` plan.

**Review notes carried forward (PASS_WITH_NOTES):**
- **SA-1** (warning, already fixed in the reviewed spec text) — BEH-7 explicitly states `id`,
  `key`, and `project_id` are not mutable fields and are silently ignored if present in a
  `PATCH /issues/{id}` request body. Task 5 below implements this by constructing the `UPDATE`
  statement only from the `IssuePatch` fields that are mutable, never reading `project_id`/`key`/`id`
  out of the incoming payload for the SQL update — those three simply have no corresponding
  column-write path, so "ignored" is enforced structurally, not by a runtime check that could
  regress.
- **SA-2** (suggestion, advisory) — the Error Cases table generalizes 422 to "Invalid `status`,
  `issue_type`, or `priority` value on create/patch," but the Behaviors section only has an
  explicit BEH for the `status` case on PATCH (BEH-8); there's no dedicated BEH for invalid
  `issue_type`/`priority` on PATCH. Per the review's own note, this is fine to cover through the
  same validation code path as create rather than a separate behavior — Task 5 below reuses
  Task 2's `issue_type`/`priority` enum-validation helper for `PATCH` so the two endpoints can
  never drift on what counts as a valid value, closing the asymmetry in code even though the spec
  text itself doesn't enumerate a separate BEH for it.

---

## File Structure

**Create:**
- `app/routers/issues.py` — `POST /issues`, `GET /issues`, `GET /issues/{id}`,
  `PATCH /issues/{id}`, `DELETE /issues/{id}`
- `tests/test_issues.py` — BEH-1 through BEH-9 coverage

**Modify:**
- `app/db.py` — extend `create_schema()` to also create the `issues` and
  `project_issue_sequences` tables; add a `allocate_issue_key()` helper for per-project
  sequential key derivation
- `app/models.py` — add `IssueCreate`, `IssueRead`, `IssuePatch` Pydantic models
- `app/main.py` — include the new `issues` router (`app.include_router(issues_router)`); no
  change to the existing exception-handler registration, which already applies generically
- `app/errors.py` — add a `literal_error`-specific branch to `validation_exception_handler` so
  an invalid `Literal` value (out-of-set `status`/`issue_type`/`priority`) is reported as "field
  must be one of: ..." instead of the generic (and here incorrect) "field is required" message —
  see Task 2

**Reference (read, do not modify):**
- `app/routers/projects.py` — follow this file's pattern for router structure, connection
  access via `request.app.state.db_conn`, and `HTTPException(detail={"message", "code"})` shape
- `tests/conftest.py` — reuse the existing `client` fixture (isolated temp SQLite file +
  `TestClient` per test) unchanged
- `tests/conftest.py` — reuse the existing `client` fixture (isolated temp SQLite file +
  `TestClient` per test) unchanged
- `.context-index/specs/features/issue-tracker-api/charter.md` — Capability Map, Domain Model,
  Invariants
- `CLAUDE.md` — constitution: "HTTP contract is the boundary", "breaking API changes are
  coordinated"
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands

---

## Context Packets

> No `source-manifest.files[]` exists on this spec yet. This module has no ADRs, no samples, and
> no `orientation/architecture.md`. Context packets fall back to charter + spec + constitution +
> the sibling `project-management` implementation (already-shipped source, read as a pattern
> reference), per Step 2's "no source-manifest" fallback.

### Task 1 Context
- Spec: `issue-lifecycle.spec.md` (Preconditions; Postconditions: "key and project_id never
  change once assigned"; Invariants inherited from charter: key derivation `<project.key>-<sequence>`)
- Charter: `charter.md` (capability: Create Issue — foundation; Domain Model → Issue entity full
  field list; Invariants: "sequence increments per project starting at 1")
- Source files: `app/db.py` (full read — existing `create_schema()` to extend), `app/models.py`
  (full read — existing `ProjectCreate`/`ProjectRead` for naming-convention consistency)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty, no rules to apply
- Heuristics: none available for module `issue-tracker-api`

### Task 2 Context
- Spec: BEH-1, BEH-2, BEH-3; Error Cases table (`ISSUE_PROJECT_NOT_FOUND`, `VALIDATION_ERROR` —
  including its "naming the invalid field and its allowed values" clause for enum fields)
- Charter: capability "Create Issue"; Invariants: key derivation and per-project sequencing
- Review notes: plan-reviewer finding (fixed here) — `app/errors.py`'s existing
  `validation_exception_handler` reports every validation error as "field is required," which
  is wrong for an out-of-set `Literal` value; this task adds a `literal_error` branch
- Source files: `app/routers/projects.py` (full read — pattern for validation + error envelope),
  `app/errors.py` (full read — existing handler being extended), `app/db.py` and `app/models.py`
  (from Task 1, full read)

### Task 3 Context
- Spec: BEH-4; Postconditions: "immediately retrievable via `GET /issues`,
  `GET /issues?project_id=...`"
- Charter: capability "List/get Issue"
- Source files: `app/routers/issues.py` (from Task 2, full read — extending, not replacing)

### Task 4 Context
- Spec: BEH-5, BEH-6; Error Cases table (`ISSUE_NOT_FOUND`)
- Charter: capability "List/get Issue"
- Source files: `app/routers/issues.py` (from Task 2/3, full read — extending)

### Task 5 Context
- Spec: BEH-7, BEH-8; Postconditions: "key and project_id never change once assigned"; Error
  Cases table (`VALIDATION_ERROR` for invalid enum values on patch)
- Charter: capability "Update Issue"
- Review notes: **SA-1** (id/key/project_id immutability — enforced structurally, see plan
  header), **SA-2** (issue_type/priority validation reuses Task 2's validation path)
- Source files: `app/routers/issues.py` (from Task 2-4, full read — extending)

### Task 6 Context
- Spec: BEH-9
- Charter: capability "Delete Issue"
- Source files: `app/routers/issues.py` (from Task 2-5, full read — extending)

---

## Heuristics

No heuristics available for module `issue-tracker-api` (`adev heuristics retrieve` returned
`__NONE__`). Section omitted from further reference per Step 2.

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6

All six tasks are sequential: Task 1 is the schema/model foundation every later task imports
from, and Tasks 2-6 all extend the same two files (`app/routers/issues.py`,
`tests/test_issues.py`), so no independent group exists in this plan.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Define Issue table, sequence counter, and Pydantic models | medium | unit | — | 0 create, 2 modify |
| 2 | Implement `POST /issues` | medium | unit | Task 1 | 2 create, 1 modify |
| 3 | Implement `GET /issues` with filters | small | unit | Task 2 | 0 create, 2 modify |
| 4 | Implement `GET /issues/{id}` | small | unit | Task 3 | 0 create, 2 modify |
| 5 | Implement `PATCH /issues/{id}` | medium | unit | Task 4 | 0 create, 2 modify |
| 6 | Implement `DELETE /issues/{id}` | small | unit | Task 5 | 0 create, 2 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no `test_strategies` entries in `manifest.yaml` matching these paths). Per Step 5,
the Strategy Summary section is omitted since every task is `unit`.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). `tests/test_db.py` is extended once (Task 1, covering the new
schema/sequencing precondition). `tests/test_issues.py` is created once (Task 2, covering
BEH-1/2/3) and extended four times (Task 3 for BEH-4, Task 4 for BEH-5/6, Task 5 for BEH-7/8,
Task 6 for BEH-9).

---

## Task Structure

### Task 1: Define Issue table, sequence counter, and Pydantic models [specialist: none]

**Charter capability:** Create Issue (foundation)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/db.py` — extend `create_schema()`; add `allocate_issue_key()`
- Modify: `app/models.py` — add `IssueCreate`, `IssueRead`, `IssuePatch`
- Test: `tests/test_db.py`

**Tests:** `tests/test_db.py` (extend — schema/sequencing precondition; suite already exists
from the `project-management` plan)

**Context to load:**
- Spec Preconditions: "The API process is running and its SQLite database is available."
- Charter Domain Model: Issue entity (`id`, `key`, `project_id`, `summary`, `description`,
  `issue_type`, `status`, `priority`, `assignee`, `reporter`, `created_at`, `updated_at`);
  Invariants: "key derived as `<project.key>-<sequence>`, sequence increments per project
  starting at 1"

- [ ] **Write failing test**

```python
# tests/test_db.py (append)
def test_create_schema_creates_issues_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='issues'"
    )
    assert cursor.fetchone() is not None


def test_allocate_issue_key_increments_per_project_starting_at_one(tmp_path):
    from app.db import allocate_issue_key

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('SDLC', 'SDLC', '')")
    project_id = conn.execute("SELECT id FROM projects WHERE key='SDLC'").fetchone()["id"]

    assert allocate_issue_key(conn, project_id, "SDLC") == "SDLC-1"
    assert allocate_issue_key(conn, project_id, "SDLC") == "SDLC-2"


def test_allocate_issue_key_sequences_are_independent_per_project(tmp_path):
    from app.db import allocate_issue_key

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('SDLC', 'SDLC', '')")
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('DDLC', 'DDLC', '')")
    sdlc_id = conn.execute("SELECT id FROM projects WHERE key='SDLC'").fetchone()["id"]
    ddlc_id = conn.execute("SELECT id FROM projects WHERE key='DDLC'").fetchone()["id"]

    assert allocate_issue_key(conn, sdlc_id, "SDLC") == "SDLC-1"
    assert allocate_issue_key(conn, ddlc_id, "DDLC") == "DDLC-1"
    assert allocate_issue_key(conn, sdlc_id, "SDLC") == "SDLC-2"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_db.py`
Expected: FAIL — `sqlite3.OperationalError: no such table: issues` and
`ImportError: cannot import name 'allocate_issue_key'`, since neither exists yet.

- [ ] **Implement**

```python
# app/db.py (extend create_schema; add allocate_issue_key)
def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects ( ... unchanged ... )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            summary TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            issue_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL,
            assignee TEXT NOT NULL DEFAULT '',
            reporter TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_issue_sequences (
            project_id INTEGER PRIMARY KEY REFERENCES projects(id),
            next_seq INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()


def allocate_issue_key(conn: sqlite3.Connection, project_id: int, project_key: str) -> str:
    """Durable per-project sequence: never decrements or reuses a number, even across deletes."""
    row = conn.execute(
        "SELECT next_seq FROM project_issue_sequences WHERE project_id = ?", (project_id,)
    ).fetchone()
    seq = row["next_seq"] if row else 1
    conn.execute(
        """
        INSERT INTO project_issue_sequences (project_id, next_seq) VALUES (?, ?)
        ON CONFLICT(project_id) DO UPDATE SET next_seq = excluded.next_seq
        """,
        (project_id, seq + 1),
    )
    conn.commit()
    return f"{project_key}-{seq}"
```

```python
# app/models.py (append)
from typing import Literal

ISSUE_TYPES = ("bug", "task", "story")
ISSUE_STATUSES = ("todo", "in_progress", "done")
ISSUE_PRIORITIES = ("low", "medium", "high")


class IssueCreate(BaseModel):
    project_id: int
    summary: str
    issue_type: Literal["bug", "task", "story"]
    priority: Literal["low", "medium", "high"]
    description: str | None = None
    assignee: str | None = None
    reporter: str | None = None


class IssueRead(BaseModel):
    id: int
    key: str
    project_id: int
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: str
    reporter: str
    created_at: str
    updated_at: str


class IssuePatch(BaseModel):
    summary: str | None = None
    description: str | None = None
    issue_type: Literal["bug", "task", "story"] | None = None
    priority: Literal["low", "medium", "high"] | None = None
    assignee: str | None = None
    reporter: str | None = None
    status: Literal["todo", "in_progress", "done"] | None = None
```

Note: `IssuePatch` deliberately has no `id`, `key`, or `project_id` field at all — this is the
structural enforcement of SA-1 (see plan header): even if a client sends those keys in the JSON
body, Pydantic drops them silently (no such field to populate), so Task 5's `UPDATE` statement
can never reach them.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_db.py`
Expected: PASS

- [ ] **Commit**

Branch: `feat/issue-tracker-api/issue-lifecycle`

```bash
git add app/db.py app/models.py tests/test_db.py
git commit -m "feat(issue-tracker-api): add Issue schema, per-project key sequencing, and Issue Pydantic models"
```

---

### Task 2: Implement `POST /issues` [specialist: none]

**Charter capability:** Create Issue
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `app/routers/issues.py`
- Modify: `app/main.py` — include the issues router
- Modify: `app/errors.py` — add a `literal_error` branch to `validation_exception_handler`
- Test: `tests/test_issues.py`

**Tests:** `tests/test_issues.py` (create — first task to touch this behavior; covers BEH-1,
BEH-2, BEH-3)

**Context to load:**
- Spec BEH-1, BEH-2, BEH-3 and Error Cases table (`ISSUE_PROJECT_NOT_FOUND`, `VALIDATION_ERROR` —
  "naming the invalid field and its allowed values" for enum fields)
- Charter Invariants: key derivation, per-project sequencing starting at 1
- `app/routers/projects.py` — pattern reference for `HTTPException(detail={"message", "code"})`
  and `request.app.state.db_conn` access
- `app/errors.py` — existing `validation_exception_handler` being extended (full read)

- [ ] **Write failing test**

```python
# tests/test_issues.py
def _create_project(client, key="SDLC", name="SDLC Track"):
    return client.post("/projects", json={"key": key, "name": name}).json()


def test_create_issue_returns_201_with_server_assigned_key_and_todo_status(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={
            "project_id": project["id"],
            "summary": "Fix login bug",
            "issue_type": "bug",
            "priority": "high",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"] == "SDLC-1"
    assert body["status"] == "todo"
    assert body["project_id"] == project["id"]
    assert body["summary"] == "Fix login bug"


def test_create_second_issue_in_same_project_increments_sequence(client):
    project = _create_project(client)
    client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "A", "issue_type": "task", "priority": "low"},
    )
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "B", "issue_type": "task", "priority": "low"},
    )
    assert resp.json()["key"] == "SDLC-2"


def test_create_issue_unknown_project_returns_404(client):
    resp = client.post(
        "/issues",
        json={"project_id": 999999, "summary": "X", "issue_type": "bug", "priority": "low"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "ISSUE_PROJECT_NOT_FOUND"
    assert "999999" in body["message"]


def test_create_issue_missing_summary_returns_422(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "issue_type": "bug", "priority": "low"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "summary" in body["message"]


def test_create_issue_invalid_issue_type_returns_422(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "X", "issue_type": "epic", "priority": "low"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "issue_type" in body["message"]
    # Error Cases table requires naming the allowed values, not just "field is required"
    assert "bug" in body["message"] and "task" in body["message"] and "story" in body["message"]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_issues.py`
Expected: FAIL — `404 Not Found` (no `/issues` route registered yet) or
`ModuleNotFoundError: No module named 'app.routers.issues'`. Once the route exists but before
`app/errors.py` is patched, `test_create_issue_invalid_issue_type_returns_422` fails specifically
on the allowed-values assertion — the existing handler would report "issue_type is required",
which contains none of `bug`/`task`/`story`, confirming this assertion is meaningful.

- [ ] **Implement**

```python
# app/routers/issues.py
from fastapi import APIRouter, HTTPException, Request

from app.models import IssueCreate, IssueRead
from app.db import allocate_issue_key

router = APIRouter()


def _row_to_issue_read(row) -> IssueRead:
    return IssueRead(
        id=row["id"], key=row["key"], project_id=row["project_id"], summary=row["summary"],
        description=row["description"], issue_type=row["issue_type"], status=row["status"],
        priority=row["priority"], assignee=row["assignee"], reporter=row["reporter"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


@router.post("/issues", response_model=IssueRead, status_code=201)
def create_issue(payload: IssueCreate, request: Request):
    conn = request.app.state.db_conn
    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (payload.project_id,)
    ).fetchone()
    if project is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Project {payload.project_id} not found",
                "code": "ISSUE_PROJECT_NOT_FOUND",
            },
        )

    key = allocate_issue_key(conn, project["id"], project["key"])
    cursor = conn.execute(
        """
        INSERT INTO issues
            (key, project_id, summary, description, issue_type, status, priority, assignee, reporter)
        VALUES (?, ?, ?, ?, ?, 'todo', ?, ?, ?)
        """,
        (
            key, project["id"], payload.summary, payload.description or "", payload.issue_type,
            payload.priority, payload.assignee or "", payload.reporter or "",
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_issue_read(row)
```

`issue_type`/`priority` enum validation is handled entirely by Pydantic's `Literal[...]` types on
`IssueCreate` (Task 1) — FastAPI raises `RequestValidationError` for an out-of-set value. Today
`app/errors.py`'s handler converts every `RequestValidationError` into the generic
`"{field} is required"` message, which is wrong for this case (the field wasn't missing, it was
invalid) and doesn't name the allowed values the spec's Error Cases table requires. Add a
`literal_error` branch:

```python
# app/errors.py (modify validation_exception_handler)
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
    if first.get("type") == "literal_error":
        allowed = first.get("ctx", {}).get("expected", "")
        return JSONResponse(
            status_code=422,
            content={
                "message": f"{field} must be one of: {allowed}",
                "code": "VALIDATION_ERROR",
            },
        )
    return JSONResponse(
        status_code=422,
        content={"message": f"{field} is required", "code": "VALIDATION_ERROR"},
    )
```

Pydantic v2 populates `ctx.expected` on a `literal_error` with a human-readable list of the
allowed values (e.g. `"'bug', 'task' or 'story'"`), so `f"{field} must be one of: {allowed}"`
satisfies "naming the invalid field and its allowed values" without hardcoding the enum members
in `errors.py` itself — this branch is generic across every current and future `Literal`-typed
field (`issue_type`, `priority`, `status` on both `IssueCreate` and `IssuePatch`), not
Issue-specific. No manual
`if` check is needed in the router for this, unlike `projects.py`'s hand-rolled empty-string
checks (those predate the `Literal` pattern this task introduces).

Wire the router in `app/main.py`:

```python
# app/main.py (modify)
from app.routers.issues import router as issues_router

app.include_router(issues_router)
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_issues.py tests/test_projects.py`
Expected: PASS for both files — `tests/test_projects.py` is included deliberately since
`app/errors.py` is a shared, cross-router file: this confirms the new `literal_error` branch is
purely additive and doesn't change behavior for `test_create_project_missing_name_returns_422_with_error_envelope`
or any other existing Project validation test (none of `ProjectCreate`'s fields are `Literal`
type, so they only ever hit the unchanged fallback branch).

- [ ] **Commit**

```bash
git add app/routers/issues.py app/main.py app/errors.py tests/test_issues.py
git commit -m "feat(issue-tracker-api): implement POST /issues with per-project sequential keys and enum-aware validation messages"
```

---

### Task 3: Implement `GET /issues` with filters [specialist: none]

**Charter capability:** List/get Issue
**Depends on:** Task 2
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/issues.py` — add list endpoint
- Modify: `tests/test_issues.py` — extend
- Test: `tests/test_issues.py`

**Tests:** `tests/test_issues.py` (extend — BEH-4's unfiltered and `project_id`-filter cases;
suite already created by Task 2). The `status`-filter half of BEH-4 is covered in Task 5, once
`PATCH /issues/{id}` exists to actually change an Issue's status away from its `todo` default.

**Context to load:**
- Spec BEH-4 and Postconditions: "immediately retrievable via `GET /issues`,
  `GET /issues?project_id=...`"

- [ ] **Write failing test**

```python
# tests/test_issues.py (append)
def test_list_issues_unfiltered_returns_all(client):
    project = _create_project(client)
    client.post("/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"})
    client.post("/issues", json={"project_id": project["id"], "summary": "B", "issue_type": "task", "priority": "low"})
    resp = client.get("/issues")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_issues_filtered_by_project_id(client):
    p1 = _create_project(client, key="SDLC", name="SDLC")
    p2 = _create_project(client, key="DDLC", name="DDLC")
    client.post("/issues", json={"project_id": p1["id"], "summary": "A", "issue_type": "bug", "priority": "low"})
    client.post("/issues", json={"project_id": p2["id"], "summary": "B", "issue_type": "bug", "priority": "low"})
    resp = client.get(f"/issues?project_id={p1['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["project_id"] == p1["id"]
```

The `status` filter half of BEH-4 is deliberately deferred to Task 5's test file, not written
here: proving it requires setting an Issue to a non-`todo` status, which requires
`PATCH /issues/{id}` — an endpoint this task does not yet implement. Writing that assertion now
would leave a red test with no corresponding "implement" step in this task, violating this plan's
own per-task TDD contract (write failing test -> implement -> verify pass, all within the same
task). See Task 5's `test_list_issues_filtered_by_status`.

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_issues.py::test_list_issues_unfiltered_returns_all tests/test_issues.py::test_list_issues_filtered_by_project_id`
Expected: FAIL — `405 Method Not Allowed` (no `GET /issues` route yet).

- [ ] **Implement**

```python
# app/routers/issues.py (append)
from typing import List


@router.get("/issues", response_model=List[IssueRead])
def list_issues(request: Request, project_id: int | None = None, status: str | None = None):
    conn = request.app.state.db_conn
    query = "SELECT * FROM issues WHERE 1=1"
    params: list = []
    if project_id is not None:
        query += " AND project_id = ?"
        params.append(project_id)
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_issue_read(r) for r in rows]
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_issues.py::test_list_issues_unfiltered_returns_all tests/test_issues.py::test_list_issues_filtered_by_project_id`
Expected: PASS.

- [ ] **Commit**

```bash
git add app/routers/issues.py tests/test_issues.py
git commit -m "feat(issue-tracker-api): implement GET /issues with project_id/status filters"
```

---

### Task 4: Implement `GET /issues/{id}` [specialist: none]

**Charter capability:** List/get Issue
**Depends on:** Task 3
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/issues.py` — add get-by-id endpoint
- Modify: `tests/test_issues.py` — extend
- Test: `tests/test_issues.py`

**Tests:** `tests/test_issues.py` (extend — BEH-5, BEH-6; suite already created by Task 2)

**Context to load:**
- Spec BEH-5, BEH-6 and Error Cases table (`ISSUE_NOT_FOUND`)

- [ ] **Write failing test**

```python
# tests/test_issues.py (append)
def test_get_issue_by_id_returns_200(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.get(f"/issues/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["key"] == "SDLC-1"


def test_get_issue_unknown_id_returns_404(client):
    resp = client.get("/issues/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "ISSUE_NOT_FOUND"
    assert "999999" in body["message"]
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_issues.py::test_get_issue_by_id_returns_200`
Expected: FAIL — `404 Not Found` from FastAPI's default route-not-found (no `GET /issues/{id}`
route yet).

- [ ] **Implement**

```python
# app/routers/issues.py (append)
@router.get("/issues/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    return _row_to_issue_read(row)
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_issues.py::test_get_issue_by_id_returns_200 tests/test_issues.py::test_get_issue_unknown_id_returns_404`
Expected: PASS

- [ ] **Commit**

```bash
git add app/routers/issues.py tests/test_issues.py
git commit -m "feat(issue-tracker-api): implement GET /issues/{id} with 404 handling"
```

---

### Task 5: Implement `PATCH /issues/{id}` [specialist: none]

**Charter capability:** Update Issue
**Depends on:** Task 4
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/issues.py` — add partial-update endpoint
- Modify: `tests/test_issues.py` — extend
- Test: `tests/test_issues.py`

**Tests:** `tests/test_issues.py` (extend — BEH-7, BEH-8, plus the `status`-filter half of BEH-4
deferred from Task 3; suite already created by Task 2)

**Context to load:**
- Spec BEH-7, BEH-8; Postconditions: "key and project_id never change once assigned"
- Spec BEH-4 (`status`-filter half, deferred from Task 3 — see Task 3's test note): now that
  `PATCH` exists, an Issue can actually be moved off its `todo` default so the filter has
  something non-trivial to select.
- Review notes: **SA-1** — `id`/`key`/`project_id` are structurally excluded from `IssuePatch`
  (Task 1), so this task's `UPDATE` statement has no path to write them regardless of request
  body content. **SA-2** — reuse `IssuePatch`'s `Literal[...]` fields for `issue_type`/`priority`
  so PATCH rejects invalid enum values through the identical Pydantic validation path as create
  (Task 2), even though the spec's Behaviors section only names `status` explicitly (BEH-8).

- [ ] **Write failing test**

```python
# tests/test_issues.py (append)
def test_patch_issue_updates_given_fields_and_returns_200(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(
        f"/issues/{created['id']}",
        json={"summary": "Updated summary", "status": "in_progress", "assignee": "dana"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == "Updated summary"
    assert body["status"] == "in_progress"
    assert body["assignee"] == "dana"
    assert body["updated_at"] != created["updated_at"]


def test_patch_issue_ignores_id_key_and_project_id_in_body(client):
    p1 = _create_project(client, key="SDLC", name="SDLC")
    p2 = _create_project(client, key="DDLC", name="DDLC")
    created = client.post(
        "/issues", json={"project_id": p1["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(
        f"/issues/{created['id']}",
        json={"id": 999, "key": "DDLC-1", "project_id": p2["id"], "summary": "still SDLC"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["key"] == created["key"]
    assert body["project_id"] == p1["id"]
    assert body["summary"] == "still SDLC"


def test_patch_issue_invalid_status_returns_422_and_persists_no_change(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(f"/issues/{created['id']}", json={"status": "blocked"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    # Error Cases table requires naming the invalid field and its allowed values (Task 2's
    # literal_error branch in app/errors.py, reused here unchanged for the status field)
    assert "status" in body["message"]
    assert "todo" in body["message"] and "in_progress" in body["message"] and "done" in body["message"]
    unchanged = client.get(f"/issues/{created['id']}").json()
    assert unchanged["status"] == "todo"


def test_patch_issue_invalid_issue_type_returns_422(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(f"/issues/{created['id']}", json={"issue_type": "epic"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "issue_type" in body["message"]


def test_patch_issue_unknown_id_returns_404(client):
    resp = client.patch("/issues/999999", json={"summary": "x"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"


def test_list_issues_filtered_by_status(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    client.patch(f"/issues/{created['id']}", json={"status": "in_progress"})
    resp = client.get("/issues?status=in_progress")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "in_progress"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_issues.py::test_patch_issue_updates_given_fields_and_returns_200 tests/test_issues.py::test_list_issues_filtered_by_status`
Expected: FAIL — `405 Method Not Allowed` (no `PATCH /issues/{id}` route yet), so
`test_list_issues_filtered_by_status` also fails: it can't move the Issue off `todo` to give the
`status` filter something non-default to select.

- [ ] **Implement**

```python
# app/routers/issues.py (append)
from app.models import IssuePatch

_PATCHABLE_FIELDS = ("summary", "description", "issue_type", "priority", "assignee", "reporter", "status")


@router.patch("/issues/{issue_id}", response_model=IssueRead)
def patch_issue(issue_id: int, payload: IssuePatch, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )

    updates = payload.model_dump(exclude_unset=True)
    set_clauses = [f"{field} = ?" for field in _PATCHABLE_FIELDS if field in updates]
    values = [updates[field] for field in _PATCHABLE_FIELDS if field in updates]
    if set_clauses:
        set_clauses.append("updated_at = datetime('now')")
        conn.execute(
            f"UPDATE issues SET {', '.join(set_clauses)} WHERE id = ?",
            (*values, issue_id),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return _row_to_issue_read(row)
```

`IssuePatch` (Task 1) has no `id`/`key`/`project_id` field, so `payload.model_dump(exclude_unset=True)`
can never contain those keys even if the raw request JSON does — FastAPI/Pydantic drops unknown
extra fields on a `BaseModel` by default. `_PATCHABLE_FIELDS` is a second, redundant guard: even
if a future edit to `IssuePatch` accidentally added one of those three fields, the `UPDATE`'s
`SET` clause is still built only from this fixed allow-list, so this task satisfies BEH-7's
immutability clause via two independent structural layers, not a single point of failure.
`status`/`issue_type`/`priority` enum validation is enforced by `IssuePatch`'s `Literal[...]`
types (Task 1) — an invalid value raises `RequestValidationError` before this handler body ever
runs, so no row is read or written (satisfies BEH-8's "persists no change"). No further change to
`app/errors.py` is needed here: Task 2's `literal_error` branch is already generic across every
`Literal`-typed field, so `PATCH`'s invalid-status/issue_type/priority messages get the same
"field must be one of: ..." treatment for free — this is the SA-2 fix in code (see plan header).

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_issues.py`
Expected: PASS

- [ ] **Commit**

```bash
git add app/routers/issues.py tests/test_issues.py
git commit -m "feat(issue-tracker-api): implement PATCH /issues/{id} with structural id/key/project_id immutability"
```

---

### Task 6: Implement `DELETE /issues/{id}` [specialist: none]

**Charter capability:** Delete Issue
**Depends on:** Task 5
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/routers/issues.py` — add delete endpoint
- Modify: `tests/test_issues.py` — extend
- Test: `tests/test_issues.py`

**Tests:** `tests/test_issues.py` (extend — BEH-9; suite already created by Task 2)

**Context to load:**
- Spec BEH-9; Postconditions: "A deleted Issue no longer appears in any subsequent `GET /issues`
  or `GET /issues/{id}` call for that id (the id is not reused for a future Issue)."

- [ ] **Write failing test**

```python
# tests/test_issues.py (append)
def test_delete_issue_returns_204_and_removes_it(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.delete(f"/issues/{created['id']}")
    assert resp.status_code == 204
    assert resp.content == b""

    follow_up = client.get(f"/issues/{created['id']}")
    assert follow_up.status_code == 404

    listing = client.get("/issues")
    assert created["id"] not in [i["id"] for i in listing.json()]


def test_delete_issue_unknown_id_returns_404(client):
    resp = client.delete("/issues/999999")
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_issues.py::test_delete_issue_returns_204_and_removes_it`
Expected: FAIL — `405 Method Not Allowed` (no `DELETE /issues/{id}` route yet).

- [ ] **Implement**

```python
# app/routers/issues.py (append)
@router.delete("/issues/{issue_id}", status_code=204)
def delete_issue(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    conn.commit()
```

`id` is an `AUTOINCREMENT` primary key, so SQLite never reassigns a deleted row's id to a later
insert — satisfying "the id is not reused for a future Issue" without any extra bookkeeping. The
`project_issue_sequences` counter from Task 1 is untouched by delete, so a deleted Issue's `key`
is likewise never reissued to a different Issue.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_issues.py`
Expected: PASS

- [ ] **Commit**

```bash
git add app/routers/issues.py tests/test_issues.py
git commit -m "feat(issue-tracker-api): implement DELETE /issues/{id}"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` exists and is used in place of the constitution's generic gate list:

- **Test Suite** (`test`, deterministic, required, severity error): `python -m pytest -q`
- **Linter** (`lint`, deterministic, required, severity error): `ruff check .`
- **Integration Tests** (`integration-test`, deterministic, required): command is unwired
  (`command: ""` in `gates.yaml`). This gate is **skipped** for this plan; nothing in this plan's
  task list requires an integration suite beyond the unit-level `TestClient` coverage above.
- All acceptance criteria from `issue-lifecycle.spec.md` satisfied (BEH-1 through BEH-9).
