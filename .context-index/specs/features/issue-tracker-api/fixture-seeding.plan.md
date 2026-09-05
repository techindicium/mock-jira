<!-- partial_schema: plan@1 -->

# Implementation Plan: Fixture seed data

> **Methodology:** adev
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Spec:** .context-index/specs/features/issue-tracker-api/fixture-seeding.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-04)
> **Platform:** FastAPI 0.x (per existing `app/` scaffold), Python 3.11, SQLite, Pydantic

**Goal:** On a fresh database, seed exactly one Project (`ASSIST` / "Portwell Assist
Engineering") and six Issues spanning all three statuses, a mix of type and priority, with
real canon names and canon-reconciled identifiers — and never seed again once any Project row
exists.

**Architecture:** This plan extends the existing `app/` scaffold shipped by the
`project-management` and `issue-lifecycle` plans — it does not re-scaffold anything. A new
`app/seed.py` module carries the hardcoded seed data (`SEED_PROJECT`, `SEED_ISSUES`), a
`_validate_seed_data()` self-consistency check, and a `seed_if_empty(conn, db_path)` entry
point that runs once at startup, before the app begins serving traffic. `app/main.py`'s existing
`on_startup()` gains one line calling it, between the existing `create_schema()` call and the
`app.state.db_conn = conn` assignment. Seeded Issues get their keys through the existing
`allocate_issue_key()` helper (from the `issue-lifecycle` plan), so the per-project sequence
counter stays correct for the first real `POST /issues` call after startup (it continues at
`ASSIST-7`, not `ASSIST-1`).

**Reconciliation with `course-shared/canon` is a plan-authoring-time act, not a runtime one.**
Per this spec's own Preconditions, the seed data below is copied by value into `app/seed.py` —
assignee/reporter names from `course-shared/canon/company.md`'s Named People table ("Assist
engineering" appearances: Mei Tan, Kofi Adjei, Priya Nair, Joao Pinto), and narrative references
to `INCIDENT-01`/`INCIDENT-02`/`ACCOUNT-1001` from that same file's "What Assist did" section.
The running program never opens `../course-shared/*` — that would be an inbound dependency the
constitution forbids outright (Principle 1). The `ASSIST` project key and derived `ASSIST-<n>`
Issue keys are validated at seed time against the canon's reserved prefix list
(`course-shared/canon/identifiers.md`: `ACCOUNT-`, `TICKET-`, `ARTICLE-`, `PROPOSAL-`,
`INCIDENT-`, `POLICY-`, `OPPORTUNITY-`, `EXPERIMENT-`, `P-`), satisfying BEH-4 with an assertion
that runs on every startup, not just at authoring time.

**Constitution Validation (Step 3):** Checked every task's files/behavior against `Architecture
Boundaries`. No task adds a workspace-repo dependency, a new pip dependency, an auth flow, or a
breaking change to an already-shipped endpoint contract — `app/seed.py` is net-new and
`app/main.py`'s change is a single additive line. `governance/boundaries.yaml` has no rules
configured (`boundaries: []`), so no file-pattern flags apply. No task is marked
`[REQUIRES HUMAN APPROVAL]`.

**Review notes carried forward (PASS_WITH_NOTES):** BEH-1 now names an explicit status/type/
priority spread across the six seed Issues (2 `todo`, 2 `in_progress`, 2 `done`; a mix of
`bug`/`task`/`story` and `low`/`medium`/`high`). The seed data below (Task 1) is designed to that
exact spread — each of the three `issue_type` values and each of the three `priority` values
appears exactly twice, in addition to the required 2/2/2 status split — and `_validate_seed_data`
asserts the status split programmatically so a future edit to the fixture can't silently drift
back to "one column with six cards."

---

## File Structure

**Create:**
- `app/seed.py` — seed data constants, `SeedError`, `_validate_seed_data()`, `seed_if_empty()`
- `tests/test_seed.py` — BEH-1 through BEH-4, idempotency, and both Error Cases

**Modify:**
- `app/main.py` — call `seed_if_empty(conn, DB_PATH)` in `on_startup()`, after `create_schema()`
  and before `app.state.db_conn = conn`

**Reference (read, do not modify):**
- `app/db.py` — `get_connection()`, `create_schema()`, `allocate_issue_key()` (reused unchanged
  for seed Issue key derivation, so the sequence counter stays consistent for post-seed writes)
- `app/models.py` — `ISSUE_TYPES`, `ISSUE_STATUSES`, `ISSUE_PRIORITIES` tuples (reused for
  validation instead of re-declaring the enum sets in `app/seed.py`)
- `app/routers/projects.py`, `app/routers/issues.py` — insert statement shape and column order,
  for consistency with how the same tables are written elsewhere in this codebase
- `tests/conftest.py` — reuse the existing `client` fixture (isolated temp SQLite file +
  `TestClient` per test) unchanged
- `../course-shared/canon/company.md` — Named People table (Assist engineering names) and "What
  each process actually is" / pilot summary section (`INCIDENT-01`, `INCIDENT-02`, pilot
  narrative, `ACCOUNT-1001`) — source for seed data values, read once at plan-authoring time
- `../course-shared/canon/identifiers.md` — reserved prefix list, source for the collision check
- `.context-index/specs/features/issue-tracker-api/charter.md` — Capability Map, Domain Model
- `CLAUDE.md` — constitution: "no inbound dependencies," "identifiers reconcile with canon,"
  "fixture-backed, offline only"
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands

---

## Context Packets

> No `source-manifest.files[]` exists on this spec yet (first implementation). This module has
> no ADRs, no samples, and no `orientation/architecture.md`. Context packets fall back to
> charter + spec + constitution + the sibling `issue-lifecycle`/`project-management`
> implementations (already-shipped source, read as pattern references), per Step 2's
> "no source-manifest" fallback.

### Task 1 Context
- Spec: BEH-3 ("every `assignee` and `reporter` value is a real name drawn from
  `course-shared/canon/company.md`'s Named People table"), BEH-4 (key/prefix collision rule),
  Error Cases (`SEED_DATA_INVALID`)
- Charter: capability "Seed fixture data"; constitution reference block on canon reconciliation
- Source files: `app/models.py` (full read — `ISSUE_TYPES`/`ISSUE_STATUSES`/`ISSUE_PRIORITIES`
  to reuse, not redeclare)
- Canon: `../course-shared/canon/company.md` Named People table + pilot narrative section (full
  read); `../course-shared/canon/identifiers.md` Schemes table (full read — reserved prefixes)
- Boundary rules: `.context-index/governance/boundaries.yaml` — empty, no rules to apply
- Heuristics: none available for module `issue-tracker-api`

### Task 2 Context
- Spec: BEH-1 (exact seed contract: 1 Project, 6 Issues, 2/2/2 status split, mixed type/priority,
  no placeholder text), Error Cases (`SEED_DB_NOT_WRITABLE`), Postconditions (`GET /projects`
  returns exactly one Project, `GET /issues?project_id=...` returns exactly six)
- Charter: capability "Seed fixture data"; Invariants (Issue key derivation, per-project
  sequencing) — this task's use of `allocate_issue_key()` must not violate them
- Source files: `app/db.py` (full read — `get_connection`, `create_schema`, `allocate_issue_key`),
  `app/main.py` (full read — existing `on_startup()` being extended), `app/seed.py` (from Task 1,
  full read — extending, not replacing)
- Reference: `app/routers/issues.py`'s `create_issue` (insert statement shape/column order)

### Task 3 Context
- Spec: BEH-2 ("performs no seeding" when a Project already exists; "restarting the process any
  number of times never creates a second copy")
- Charter: capability "Seed fixture data"
- Source files: `app/seed.py`, `app/main.py` (from Task 2, full read — exercising the wired
  startup path, not changing it)
- Reference: `tests/conftest.py` (pattern for constructing an isolated temp-file `TestClient`;
  this task's test builds its own two-`TestClient` sequence rather than using the shared
  `client` fixture, since it needs the *same* db file across two separate startups)

---

## Heuristics

No heuristics available for module `issue-tracker-api` (`adev heuristics retrieve` returned
`__NONE__`). Section omitted from further reference per Step 2.

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3

All three tasks are sequential: Task 2's `seed_if_empty()` imports the data constants and
`SeedError` Task 1 defines, and Task 3's idempotency test exercises the startup wiring Task 2
adds. No independent group exists in this plan.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Define seed fixture data and validation | small | unit | — | 2 create, 0 modify |
| 2 | Implement `seed_if_empty()` and wire into startup | small | unit | Task 1 | 0 create, 2 modify |
| 3 | Idempotency test across restarts | small | unit | Task 2 | 0 create, 1 modify |

All tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in spec
frontmatter, no `test_strategies` entries in `manifest.yaml` matching these paths, and no
`infra_requirements:` declared). Per Step 5, the Strategy Summary and Test Infrastructure
Requirements sections are both omitted since every task is `unit` with no infra requirements.

**Granularity:** `per-behavior` (source: manifest — `test_policy.granularity: per-behavior` in
`.context-index/manifest.yaml`). `tests/test_seed.py` is created once (Task 1, covering BEH-3,
BEH-4, and `SEED_DATA_INVALID`) and extended twice (Task 2 for BEH-1 and `SEED_DB_NOT_WRITABLE`,
Task 3 for BEH-2).

---

## Task Structure

### Task 1: Define seed fixture data and validation [specialist: none]

**Charter capability:** Seed fixture data
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `app/seed.py` — `SEED_PROJECT`, `SEED_ISSUES`, `SeedError`, `_validate_seed_data()`
- Create: `tests/test_seed.py`
- Test: `tests/test_seed.py`

**Tests:** `tests/test_seed.py` (create — first task to touch this behavior; covers BEH-3,
BEH-4, `SEED_DATA_INVALID`)

**Context to load:**
- Spec BEH-3, BEH-4, Error Cases (`SEED_DATA_INVALID`)
- `../course-shared/canon/company.md` Named People table (Assist engineering names: Mei Tan,
  Kofi Adjei, Priya Nair, Joao Pinto) and pilot narrative (`INCIDENT-01`, `INCIDENT-02`,
  `ACCOUNT-1001`, "review queue as the new bottleneck")
- `../course-shared/canon/identifiers.md` Schemes table (reserved prefixes)
- `app/models.py`: `ISSUE_TYPES`, `ISSUE_STATUSES`, `ISSUE_PRIORITIES`

- [ ] **Write failing test**

```python
# tests/test_seed.py
import pytest

from app.seed import SEED_ISSUES, SEED_PROJECT, SeedError, _validate_seed_data

_CANON_ASSIST_NAMES = {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto"}


def test_seed_project_key_and_name_are_not_placeholder_text():
    assert SEED_PROJECT["key"] == "ASSIST"
    assert SEED_PROJECT["name"] == "Portwell Assist Engineering"
    assert "lorem" not in SEED_PROJECT["description"].lower()


def test_seed_issues_use_real_canon_names():
    for issue in SEED_ISSUES:
        assert issue["assignee"] in _CANON_ASSIST_NAMES
        assert issue["reporter"] in _CANON_ASSIST_NAMES


def test_validate_seed_data_passes_for_shipped_fixture():
    _validate_seed_data(SEED_PROJECT, SEED_ISSUES)  # must not raise


def test_validate_seed_data_rejects_canon_reserved_key_prefix():
    bad_project = {**SEED_PROJECT, "key": "ACCOUNT-1"}
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(bad_project, SEED_ISSUES)
    assert exc_info.value.code == "SEED_DATA_INVALID"


def test_validate_seed_data_rejects_invalid_status():
    bad_issues = [dict(SEED_ISSUES[0], status="blocked")] + SEED_ISSUES[1:]
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(SEED_PROJECT, bad_issues)
    assert exc_info.value.code == "SEED_DATA_INVALID"
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_seed.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.seed'`, since the module doesn't
exist yet.

- [ ] **Implement**

```python
# app/seed.py
from app.models import ISSUE_PRIORITIES, ISSUE_STATUSES, ISSUE_TYPES

# Reserved identifier prefixes from ../course-shared/canon/identifiers.md — read once, at
# plan-authoring time, and copied by value here. Never re-read at runtime: the constitution
# ("no inbound dependencies") forbids this repo from opening any file outside itself.
_CANON_RESERVED_PREFIXES = (
    "ACCOUNT-", "TICKET-", "ARTICLE-", "PROPOSAL-", "INCIDENT-",
    "POLICY-", "OPPORTUNITY-", "EXPERIMENT-", "P-",
)

SEED_PROJECT = {
    "key": "ASSIST",
    "name": "Portwell Assist Engineering",
    "description": (
        "Engineering tracker for Portwell Assist, the AI-assisted support-ticket triage pilot."
    ),
}

# 6 Issues: exactly 2 of each status (todo/in_progress/done), 2 of each issue_type
# (bug/task/story), 2 of each priority (low/medium/high) — per BEH-1 as tightened by review.
SEED_ISSUES = [
    {
        "summary": "Investigate INCIDENT-01: proposal quoted a superseded refund window",
        "description": (
            "A billing proposal cited an out-of-date refund-window policy instead of the "
            "current one. Trace which article version the retriever returned for ACCOUNT-1001 "
            "and confirm the index only serves published, current articles."
        ),
        "issue_type": "bug", "status": "todo", "priority": "high",
        "assignee": "Kofi Adjei", "reporter": "Joao Pinto",
    },
    {
        "summary": "Design review-queue triage rules for pilot expansion",
        "description": (
            "Support engineers flagged the review queue, not answer quality, as the pilot's "
            "real bottleneck. Propose a triage rule set so low-confidence proposals reach a "
            "reviewer faster without adding headcount."
        ),
        "issue_type": "story", "status": "todo", "priority": "medium",
        "assignee": "Mei Tan", "reporter": "Priya Nair",
    },
    {
        "summary": "Add webhook-retry safeguard after INCIDENT-02",
        "description": (
            "An integrations proposal told an account to disable a webhook retry its EDI feed "
            "depended on. Add a guard so the proposal generator never recommends disabling "
            "retries on a webhook flagged as EDI-critical."
        ),
        "issue_type": "task", "status": "in_progress", "priority": "low",
        "assignee": "Joao Pinto", "reporter": "Mei Tan",
    },
    {
        "summary": "Fix stale-article lookup in the proposal generator",
        "description": (
            "The retriever can still surface a superseded article version. Filter the article "
            "index to `status: published` only and drop anything a newer article's "
            "`supersedes` list names."
        ),
        "issue_type": "bug", "status": "in_progress", "priority": "medium",
        "assignee": "Priya Nair", "reporter": "Kofi Adjei",
    },
    {
        "summary": "Publish pilot-expansion readiness checklist",
        "description": (
            "One side wants to expand the pilot; the other wants review capacity solved "
            "first. Publish a checklist covering both positions so Product can decide with "
            "the tradeoffs visible."
        ),
        "issue_type": "story", "status": "done", "priority": "high",
        "assignee": "Kofi Adjei", "reporter": "Mei Tan",
    },
    {
        "summary": "Document review-capacity findings from the pilot",
        "description": (
            "Write up the pilot's review-queue bottleneck finding for the engineering team's "
            "retro, referencing the 22-minute median response time on proposal-sent tickets."
        ),
        "issue_type": "task", "status": "done", "priority": "low",
        "assignee": "Mei Tan", "reporter": "Joao Pinto",
    },
]


class SeedError(RuntimeError):
    """Raised when startup seeding cannot proceed. Carries a stable `code` for operators."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _validate_seed_data(project: dict, issues: list[dict]) -> None:
    if not project.get("key") or not project["key"].strip():
        raise SeedError("SEED_DATA_INVALID", "Seed project is missing a key")
    if any(project["key"].startswith(p) for p in _CANON_RESERVED_PREFIXES):
        raise SeedError(
            "SEED_DATA_INVALID",
            f"Seed project key '{project['key']}' collides with a canon-reserved prefix",
        )
    if not project.get("name") or not project["name"].strip():
        raise SeedError("SEED_DATA_INVALID", "Seed project is missing a name")

    if len(issues) != 6:
        raise SeedError("SEED_DATA_INVALID", f"Expected 6 seed issues, found {len(issues)}")

    for i, issue in enumerate(issues):
        if issue.get("issue_type") not in ISSUE_TYPES:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Seed issue {i} has invalid issue_type '{issue.get('issue_type')}'",
            )
        if issue.get("status") not in ISSUE_STATUSES:
            raise SeedError(
                "SEED_DATA_INVALID", f"Seed issue {i} has invalid status '{issue.get('status')}'"
            )
        if issue.get("priority") not in ISSUE_PRIORITIES:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Seed issue {i} has invalid priority '{issue.get('priority')}'",
            )
        if not issue.get("summary") or not issue["summary"].strip():
            raise SeedError("SEED_DATA_INVALID", f"Seed issue {i} is missing a summary")
        if not issue.get("assignee") or not issue.get("reporter"):
            raise SeedError("SEED_DATA_INVALID", f"Seed issue {i} is missing assignee or reporter")

    statuses = [issue["status"] for issue in issues]
    for status in ISSUE_STATUSES:
        count = statuses.count(status)
        if count != 2:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Expected exactly 2 seed issues with status '{status}', found {count}",
            )
```

Note: `_validate_seed_data` runs against the module's own hardcoded constants, so in normal
operation it can never fail — it exists as a structural guardrail (asserted every startup) so a
future edit to `SEED_PROJECT`/`SEED_ISSUES` that breaks BEH-1's spread or BEH-4's collision rule
fails loudly at startup (`SEED_DATA_INVALID`) instead of silently shipping a degraded fixture.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_seed.py`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/issue-tracker-api/fixture-seeding`

```bash
git add app/seed.py tests/test_seed.py
git commit -m "feat(issue-tracker-api): add seed fixture data and validation"
```

---

### Task 2: Implement `seed_if_empty()` and wire into startup [specialist: none]

**Charter capability:** Seed fixture data
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `app/seed.py` — add `seed_if_empty(conn, db_path)`
- Modify: `app/main.py` — call it from `on_startup()`
- Modify: `tests/test_seed.py` — extend
- Test: `tests/test_seed.py`

**Tests:** `tests/test_seed.py` (extend — BEH-1, `SEED_DB_NOT_WRITABLE`; suite already created
by Task 1)

**Context to load:**
- Spec BEH-1 (exact contract), Error Cases (`SEED_DB_NOT_WRITABLE`), Postconditions
- Charter Invariants: Issue key derivation (`<project.key>-<sequence>`), per-project sequencing
- Source files: `app/db.py` (full read — `get_connection`, `create_schema`, `allocate_issue_key`),
  `app/main.py` (full read — existing `on_startup()`)

- [ ] **Write failing test**

```python
# tests/test_seed.py (append)
def test_fresh_startup_seeds_one_project_and_six_issues(client):
    projects = client.get("/projects").json()
    assert len(projects) == 1
    project = projects[0]
    assert project["key"] == "ASSIST"
    assert project["name"] == "Portwell Assist Engineering"

    issues = client.get("/issues", params={"project_id": project["id"]}).json()
    assert len(issues) == 6

    statuses = [i["status"] for i in issues]
    assert statuses.count("todo") == 2
    assert statuses.count("in_progress") == 2
    assert statuses.count("done") == 2

    assert {i["issue_type"] for i in issues} == {"bug", "task", "story"}
    assert {i["priority"] for i in issues} == {"low", "medium", "high"}

    for issue in issues:
        assert issue["summary"].strip() != ""
        assert "lorem" not in issue["summary"].lower()
        assert "lorem" not in issue["description"].lower()
        assert not issue["key"].startswith((
            "ACCOUNT-", "TICKET-", "ARTICLE-", "PROPOSAL-", "INCIDENT-",
            "POLICY-", "OPPORTUNITY-", "EXPERIMENT-", "P-",
        ))


def test_seed_if_empty_raises_seed_db_not_writable_when_connection_is_read_only(tmp_path):
    from app.db import create_schema, get_connection
    from app.seed import seed_if_empty

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("PRAGMA query_only = ON")  # simulate an unwritable database, no chmod needed

    with pytest.raises(SeedError) as exc_info:
        seed_if_empty(conn, str(db_path))
    assert exc_info.value.code == "SEED_DB_NOT_WRITABLE"
    assert str(db_path) in str(exc_info.value)
```

Note: `create_schema`/`get_connection`/`seed_if_empty` are imported inside the test function
body, not at module level, matching the existing convention this repo already uses in
`tests/test_db.py` (`test_allocate_issue_key_increments_per_project_starting_at_one` imports
`allocate_issue_key` the same way). This is not a style nicety — it is required here: `ruff` (a
`post-task`, `severity: error` gate per `governance/gates.yaml`) flags any `import` statement
placed after existing top-level code in a file as `E402`, and `seed_if_empty` does not exist as
a name until this task, so a module-level import added at the top of `tests/test_seed.py` at
Task 1 time would itself fail as an unresolvable/unused import before this task lands. A
function-scoped import sidesteps both problems and is resolved fresh on each test call.

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_seed.py::test_fresh_startup_seeds_one_project_and_six_issues tests/test_seed.py::test_seed_if_empty_raises_seed_db_not_writable_when_connection_is_read_only`
Expected: FAIL — `test_fresh_startup_...` fails because `GET /projects` returns `[]` (nothing
seeds yet); `test_seed_if_empty_raises_...` fails with `ImportError: cannot import name
'seed_if_empty'`.

- [ ] **Implement**

```python
# app/seed.py (append)
def seed_if_empty(conn, db_path: str) -> None:
    """Seed one Project and six Issues on first run only. No-op if any Project already exists.

    Runs synchronously during app startup, before Uvicorn begins serving requests — no request
    can observe a partially-seeded state, and no concurrent writer can interleave with it.
    """
    existing = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()
    if existing["n"] > 0:
        return  # BEH-2: already seeded (or real data present) — never touch it

    _validate_seed_data(SEED_PROJECT, SEED_ISSUES)  # hardcoded data; a failure here is a code bug

    import sqlite3

    from app.db import allocate_issue_key

    try:
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description) VALUES (?, ?, ?)",
            (SEED_PROJECT["key"], SEED_PROJECT["name"], SEED_PROJECT["description"]),
        )
        project_id = cursor.lastrowid
        for issue in SEED_ISSUES:
            key = allocate_issue_key(conn, project_id, SEED_PROJECT["key"])
            conn.execute(
                """
                INSERT INTO issues
                    (key, project_id, summary, description, issue_type, status, priority,
                     assignee, reporter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key, project_id, issue["summary"], issue["description"], issue["issue_type"],
                    issue["status"], issue["priority"], issue["assignee"], issue["reporter"],
                ),
            )
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise SeedError(
            "SEED_DB_NOT_WRITABLE", f"Cannot write seed data to database at '{db_path}': {exc}"
        ) from exc
```

`allocate_issue_key()` (from the `issue-lifecycle` plan) is reused unchanged for each seed
Issue's key, so `project_issue_sequences` ends at `next_seq = 7` after seeding — the first real
`POST /issues` call gets `ASSIST-7`, not a duplicate `ASSIST-1`. `PRAGMA query_only = ON` in the
test forces the first `INSERT` to raise `sqlite3.OperationalError` deterministically and
portably (no filesystem permission bits, which behave inconsistently across OSes and under a
root test runner).

`import sqlite3` / `from app.db import allocate_issue_key` are placed inside `seed_if_empty`'s
body rather than at the top of `app/seed.py`, for the same `E402`/lint-gate reason as Task 1's
note above — `_validate_seed_data` (Task 1) is already the first top-level statement after the
module's original imports, so any new module-level `import` appended after it fails
`governance/gates.yaml`'s `post-task` lint gate. `conn` is deliberately left unannotated (no
`sqlite3.Connection` type hint) since annotations are evaluated at `def`-time and would force
`sqlite3` back to being a module-level name.

Wire it into startup:

```python
# app/main.py (modify)
from app.seed import seed_if_empty

@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection(DB_PATH)
    create_schema(conn)
    seed_if_empty(conn, DB_PATH)
    app.state.db_conn = conn
```

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_seed.py`
Expected: PASS

- [ ] **Commit**

```bash
git add app/seed.py app/main.py tests/test_seed.py
git commit -m "feat(issue-tracker-api): seed one Project and six Issues on empty-database startup"
```

---

### Task 3: Idempotency test across restarts [specialist: none]

**Charter capability:** Seed fixture data
**Depends on:** Task 2
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `tests/test_seed.py` — extend
- Test: `tests/test_seed.py`

**Tests:** `tests/test_seed.py` (extend — BEH-2; suite already created by Task 1)

**Context to load:**
- Spec BEH-2: "restarting the process any number of times never creates a second copy"
- `tests/conftest.py` — pattern reference only; this test builds its own `TestClient` sequence
  rather than using the shared `client` fixture, since it needs the same db file across two
  separate startups

- [ ] **Write failing test**

```python
# tests/test_seed.py (append)
def test_seeding_is_idempotent_across_restarts(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.main as main_module

    db_path = tmp_path / "restart.db"
    monkeypatch.setattr(main_module, "DB_PATH", str(db_path))

    with TestClient(main_module.app) as c1:
        first_projects = c1.get("/projects").json()

    with TestClient(main_module.app) as c2:
        second_projects = c2.get("/projects").json()
        issues = c2.get(
            "/issues", params={"project_id": second_projects[0]["id"]}
        ).json()

    assert len(first_projects) == 1
    assert len(second_projects) == 1
    assert first_projects[0]["id"] == second_projects[0]["id"]
    assert len(issues) == 6
```

- [ ] **Verify test fails**

Run: `python -m pytest -q -- tests/test_seed.py::test_seeding_is_idempotent_across_restarts`
Expected: FAIL if run in isolation before Task 2 lands (no seeding at all, so the two restarts
would each see zero Projects, not one). In this plan's execution order Task 2 is already
complete, so this step instead confirms `seed_if_empty()`'s empty-check holds across two
genuinely separate `TestClient`/connection lifecycles against the same db file — no production
code change is expected here. To positively confirm this test is meaningful (not vacuously
passing), temporarily comment out the `if existing["n"] > 0: return` guard in `app/seed.py`,
observe this test now fails (duplicate Project rows, mismatched ids between `c1`/`c2`), then
restore the guard before proceeding.

- [ ] **Implement**

No implementation step is expected: Task 2's `seed_if_empty()` empty-check (`if existing["n"] >
0: return`) already satisfies BEH-2. If the test in fact fails, the fix belongs in that guard,
not in a new code path — this task only adds the regression test above.

- [ ] **Verify test passes**

Run: `python -m pytest -q -- tests/test_seed.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests/test_seed.py
git commit -m "test(issue-tracker-api): confirm seeding is idempotent across process restarts"
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
- All acceptance criteria from `fixture-seeding.spec.md` satisfied (BEH-1 through BEH-4).
