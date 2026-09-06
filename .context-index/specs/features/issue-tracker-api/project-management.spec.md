---
partial_schema: implement@1
charter: issue-tracker-api
status: validated
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-04
kind: behavioral
source-manifest:
  sha: "1596ffd"
  files:
    - app/__init__.py
    - app/db.py
    - app/errors.py
    - app/main.py
    - app/models.py
    - app/routers/__init__.py
    - app/routers/projects.py
    - requirements.txt
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_db.py
    - tests/test_openapi.py
    - tests/test_projects.py
  computed-at: "2026-09-06T23:14:22.388Z"
---

# Live Spec: Project management and OpenAPI contract

<!-- Live Spec within the issue-tracker-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/issue-tracker-api/charter.md -->

## Behavioral Contract

### Preconditions

- The API process is running and its SQLite database file exists (created fresh on first run
  if absent — schema creation is idempotent).
- No authentication is required to reach any endpoint (per charter: no real auth in scope).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /projects` request is sent with a unique, non-empty `key` and a
  non-empty `name`, **then** the API creates a new Project row and responds `201` with the
  created Project's `id`, `key`, `name`, and `description`.
- **BEH-2** — **When** a `POST /projects` request is sent with a `key` that already exists,
  **then** the API responds `409` and does not create a duplicate row.
- **BEH-3** — **When** a `POST /projects` request is sent with a missing or empty `key` or
  `name`, **then** the API responds `422` naming the missing field, and no row is created.
- **BEH-4** — **When** a `GET /projects` request is sent, **then** the API responds `200` with
  every existing Project as a JSON array, ordered by creation time.
- **BEH-5** — **When** a `GET /projects/{id}` request is sent for an id that exists, **then**
  the API responds `200` with that Project's full representation.
- **BEH-6** — **When** a `GET /projects/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-7** — **When** a `GET /openapi.json` request is sent, **then** the API responds `200`
  with a valid OpenAPI document describing every route mounted at that time — the document is
  auto-generated from the implementation, never hand-maintained.

### Postconditions

- Every Project created via `POST /projects` is immediately retrievable via both
  `GET /projects` and `GET /projects/{id}` — no eventual consistency window.
- `GET /openapi.json` always reflects the currently mounted routes; it is regenerated per
  request, never cached stale across a code change.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Duplicate `key` on create | `409 Conflict`, JSON body naming the colliding key | `PROJECT_KEY_DUPLICATE` |
| Missing or empty `key`/`name` on create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Unknown `id` on `GET /projects/{id}` | `404 Not Found`, JSON body naming the missing id | `PROJECT_NOT_FOUND` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines the first slice of that exact contract (Project create/list/get plus the
  OpenAPI document that makes the contract discoverable).
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because these are
  the first live endpoints; their shapes become the baseline every later change must be
  coordinated against.
- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint, no real
  credentials." — Applies because Project persistence is local SQLite only; nothing in this
  spec reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Stand up the FastAPI app and SQLite schema | Initialize the FastAPI app; define the Project table; create the schema on startup if the database file is missing or the table doesn't exist yet | medium |
| Implement `POST /projects` | Pydantic request model validation (key/name required, key uniqueness enforced at the DB layer), insert row, return 201 | small |
| Implement `GET /projects` | Query all projects ordered by creation time, return as a JSON array | small |
| Implement `GET /projects/{id}` | Query by id, 404 with `PROJECT_NOT_FOUND` if missing | small |
| Confirm OpenAPI wiring | Verify FastAPI's auto-generated `/openapi.json` reflects these routes with proper Pydantic response/request models (no manual OpenAPI authoring) | small |

## Acceptance Criteria

- [x] `POST /projects` creates a Project and returns 201 with its id/key/name/description (BEH-1)
- [x] `POST /projects` with a duplicate key returns 409 and creates no row (BEH-2)
- [x] `POST /projects` with a missing key or name returns 422 (BEH-3)
- [x] `GET /projects` returns all Projects as a JSON array, ordered by creation time (BEH-4)
- [x] `GET /projects/{id}` returns 200 with the Project for a valid id (BEH-5)
- [x] `GET /projects/{id}` returns 404 for an unknown id (BEH-6)
- [x] `GET /openapi.json` returns a valid OpenAPI document listing `/projects` and `/projects/{id}` (BEH-7)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
