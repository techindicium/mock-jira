<!-- partial_schema: plan@1 -->

# Implementation Plan: User directory (create/list/get)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Spec:** .context-index/specs/features/issue-tracker-api/user-directory.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-06)
> **Platform:** FastAPI, Python 3.11, SQLite, Pydantic (established pattern from
> `project-management`/`issue-lifecycle`)

**Goal:** Implement the User directory HTTP surface (`POST /users`, `GET /users`,
`GET /users/{id}`), a new independent SQLite table, and startup seeding — an additive slice of
the issue-tracker-api contract with no change to any existing Project/Issue endpoint, schema, or
response shape.

**Architecture:** This spec extends the existing, already-validated Project/Issue codebase
rather than establishing a new layout. It follows `app/routers/projects.py`'s exact pattern:
Pydantic request/response models in `app/models.py`, a thin router in
`app/routers/users.py`, schema creation in `app/db.py`'s existing idempotent `create_schema()`,
router registration in `app/main.py`. Seeding is deliberately **not** folded into the existing
`seed_if_empty` (which governs `fixture-seeding.spec.md`'s Project/Issue transaction) — a new
`seed_users_if_empty()` in `app/seed.py` runs its own independent emptiness check, consistent
with the charter's "additive, not a hard relational dependency" framing for the User entity.

**Constitution Validation:** No task adds a workspace-repo dependency, touches auth, or breaks an
already-shipped contract. `Issue.assignee`/`Issue.reporter` are untouched. Reusing the existing
`fastapi`/`pydantic`/`pytest`/`ruff` dependencies needs no new `requirements.txt` entry. No task
is `[REQUIRES HUMAN APPROVAL]`.

**Review notes carried forward (PASS_WITH_NOTES, both addressed directly in the spec before this
plan was authored — see `user-directory.review.md`):**
- **SA-1** (warning) — added BEH-9 (independent User-seeding behavior) and its own acceptance
  criterion, so the spec is self-contained and does not require touching the already-validated
  `fixture-seeding.spec.md`.
- **SA-2** (suggestion) — BEH-2 now states email-uniqueness comparison is case-sensitive,
  matching SQLite's default `TEXT UNIQUE` collation (no `COLLATE NOCASE`).

---

## File Structure

**Create:**
- `app/routers/users.py` — `POST /users`, `GET /users`, `GET /users/{id}`
- `tests/test_users.py` — BEH-1 through BEH-9 coverage (router-level)
- `tests_e2e/test_user_directory_e2e.py` — real-HTTP coverage of the same surface, following the
  `api-e2e.spec.md` pattern (real server subprocess + httpx, never in-process `TestClient`)

**Modify:**
- `app/models.py` — add `UserCreate`, `UserRead`
- `app/db.py` — add `users` table to `create_schema()`
- `app/main.py` — register `users_router`; call `seed_users_if_empty()` alongside the existing
  `seed_if_empty()`
- `app/seed.py` — add `SEED_USERS` (4 realistic Users drawn from the same "Assist engineering"
  roster already used as Issue assignee/reporter) and `seed_users_if_empty()`
- `tests/test_db.py` — add users-table creation + multiple-NULL-email coverage
- `tests/test_seed.py` — add `SEED_USERS` canon-name and independence/idempotency coverage

**Reference (read, do not modify):**
- `.context-index/specs/features/issue-tracker-api/charter.md` (rev 11 at spec-authoring time) —
  Domain Model User entity, Capability Map row, Interface Contracts, Out of Scope
- `app/routers/projects.py` — the exact create/list/get pattern this mirrors
- `.context-index/governance/gates.yaml` — authoritative quality-gate commands

---

## Context Packets

### Task 1 Context
- Spec: `user-directory.spec.md` Preconditions (purely additive; no existing schema change)
- Charter: Domain Model → User entity fields; Invariants (`email` unique when present, `name`
  required)
- Source files: `app/db.py`, `app/models.py` (full read, extending in place)

### Task 2 Context
- Spec: BEH-1 through BEH-5; Error Cases table (`USER_EMAIL_DUPLICATE`, `VALIDATION_ERROR`,
  `MALFORMED_JSON`)
- Source files: `app/routers/projects.py` (pattern reference), `app/errors.py` (existing shared
  handlers — no change needed, already generic over `{"message", "code"}`)

### Task 3 Context
- Spec: BEH-6, BEH-7, BEH-8; Error Cases table (`USER_NOT_FOUND`)

### Task 4 Context
- Spec: BEH-9 (seed-on-startup); charter note on `course-shared/canon/company.md` Named People
  sourcing (same rule `fixture-seeding.spec.md` BEH-3 established for Issue assignee/reporter)

### Task 5 Context
- Spec: Acceptance Criteria "no change to any existing Project/Issue endpoint, schema, or
  response shape"; `api-e2e.spec.md` real-HTTP pattern

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5

Task 1 (models/schema) is the foundation; Tasks 2-3 extend the same new router file; Task 4
(seeding) depends on the table existing; Task 5 (e2e) depends on every endpoint being mounted.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Define User Pydantic models and SQLite schema | small | unit | — | 0 create, 2 modify |
| 2 | Implement `POST /users` | small | unit | Task 1 | 1 create, 1 modify |
| 3 | Implement `GET /users` and `GET /users/{id}` | small | unit | Task 2 | 0 create, 1 modify |
| 4 | Seed User directory on startup (BEH-9) | small | unit | Task 1 | 0 create, 2 modify |
| 5 | Real-HTTP e2e coverage | small | unit | Task 2, Task 3 | 1 create, 0 modify |

All tasks resolve to the `unit` strategy (fallback — no `test_strategy` in spec frontmatter, no
matching `test_strategies` entries in `manifest.yaml`).

**Granularity:** `per-behavior` (source: manifest `test_policy.granularity`). `tests/test_users.py`
is created once (Task 2, BEH-1/2/3/4/5) and extended twice (Task 3 for BEH-6/7/8, Task 4 for
BEH-9).

---

## Task Structure

### Task 1: Define User Pydantic models and SQLite schema [specialist: none]

**Charter capability:** User directory (create/list/get)
**Files:** Modify `app/models.py`, `app/db.py`
**Tests:** `tests/test_db.py` (extend)

- [x] Added `UserCreate` (`name`, optional `email`/`role`) and `UserRead` (`id`, `name`, `email`,
      `role`) to `app/models.py`.
- [x] Added a `users` table (`id`, `name NOT NULL`, `email UNIQUE` nullable, `role` nullable,
      `created_at`) to `create_schema()` in `app/db.py`. SQLite's default `UNIQUE` behavior
      treats multiple `NULL` values as distinct, satisfying BEH-4 (multiple emailless Users)
      without any extra application-level logic.
- [x] `tests/test_db.py`: `test_create_schema_creates_users_table`,
      `test_users_table_allows_multiple_null_emails`.

### Task 2: Implement `POST /users` [specialist: none]

**Depends on:** Task 1
**Files:** Create `app/routers/users.py`, modify `app/main.py`
**Tests:** `tests/test_users.py` (create)

- [x] `app/routers/users.py::create_user` — validates non-empty `name` (422
      `VALIDATION_ERROR`), inserts, catches `sqlite3.IntegrityError` on the `email` unique
      constraint (409 `USER_EMAIL_DUPLICATE`), returns 201 with the full representation.
      Malformed JSON is already handled by the existing shared `validation_exception_handler`
      (400 `MALFORMED_JSON`) — no new code needed.
- [x] `app/main.py`: registered `users_router` via `app.include_router(users_router)`.
- [x] Tests: `test_create_user_returns_201_with_full_representation`,
      `test_create_user_duplicate_email_returns_409`,
      `test_create_user_missing_name_returns_422_with_error_envelope`,
      `test_create_user_empty_name_returns_422_with_error_envelope`,
      `test_create_user_without_email_succeeds_and_never_collides`,
      `test_create_user_allows_duplicate_names`.

### Task 3: Implement `GET /users` and `GET /users/{id}` [specialist: none]

**Depends on:** Task 2
**Files:** Modify `app/routers/users.py`
**Tests:** `tests/test_users.py` (extend)

- [x] `list_users` — `SELECT * FROM users ORDER BY id ASC` (creation order, matching the
      Project/Issue precedent).
- [x] `get_user` — 404 `USER_NOT_FOUND` naming the missing id when not found.
- [x] Tests: `test_list_users_returns_all_ordered_by_creation`,
      `test_get_user_by_id_returns_200`, `test_get_user_unknown_id_returns_404`.

### Task 4: Seed User directory on startup (BEH-9) [specialist: none]

**Depends on:** Task 1
**Files:** Modify `app/seed.py`, `app/main.py`
**Tests:** `tests/test_seed.py`, `tests/test_users.py` (extend)

- [x] `app/seed.py`: added `SEED_USERS` (Mei Tan / Head of Engineering, Kofi Adjei / Staff
      Engineer Assist service, Priya Nair / Solution Consultant escalations, Joao Pinto /
      Support Engineer pilot participant — the same 4 names already used as Issue
      assignee/reporter, per `course-shared/canon/company.md`) and `seed_users_if_empty()`
      (independent `COUNT(*) FROM users` emptiness check, never touching the Project/Issue
      seeding transaction).
- [x] `app/main.py`: calls `seed_users_if_empty(conn, DB_PATH)` alongside the existing
      `seed_if_empty(conn, DB_PATH)` in the startup hook.
- [x] Tests: `test_seed_users_use_real_canon_names`,
      `test_seed_users_if_empty_is_independent_of_project_seeding`,
      `test_seed_users_if_empty_is_idempotent`, `test_fresh_startup_seeds_real_users`.

### Task 5: Real-HTTP e2e coverage [specialist: none]

**Depends on:** Task 2, Task 3
**Files:** Create `tests_e2e/test_user_directory_e2e.py`
**Tests:** new file

- [x] Mirrors `test_project_crud_e2e.py`/`test_error_paths_e2e.py`/`test_openapi_and_seed_e2e.py`'s
      pattern: real `uvicorn` subprocess + `httpx.Client`, never in-process `TestClient`.
- [x] Tests: `test_created_user_is_visible_over_real_http`,
      `test_duplicate_user_email_returns_409_over_real_http`,
      `test_unknown_user_id_returns_404_over_real_http`,
      `test_openapi_json_lists_user_routes_over_real_http`,
      `test_seed_users_visible_on_fresh_server_start`.

---

## Quality Gates

- **Test Suite** (`test`, `.venv/bin/python3 -m pytest -q`): 122 passed (unit/integration suite
  under `tests/`, per `pytest.ini`'s `testpaths = tests`).
- **Linter** (`lint`, `.venv/bin/ruff check .`): all checks passed.
- **E2E smoke** (`e2e-smoke`, not part of the required `tests/` gate set but run manually):
  `tests_e2e/test_user_directory_e2e.py` (5 passed) plus the full non-UI/non-MCP e2e subset (18
  passed) — no regression in existing Project/Issue e2e coverage.
- All acceptance criteria from `user-directory.spec.md` satisfied (BEH-1 through BEH-9).
