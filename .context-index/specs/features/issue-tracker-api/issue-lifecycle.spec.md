---
partial_schema: implement@1
charter: issue-tracker-api
status: validated
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-05
kind: behavioral
source-manifest:
  sha: "4c492e5"
  files:
    - app/db.py
    - app/errors.py
    - app/main.py
    - app/models.py
    - app/routers/issues.py
    - tests/test_db.py
    - tests/test_issues.py
  computed-at: "2026-09-06T17:45:47.331Z"
---

# Live Spec: Issue lifecycle CRUD

<!-- Live Spec within the issue-tracker-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/issue-tracker-api/charter.md -->

## Behavioral Contract

### Preconditions

- The `project-management` spec's endpoints exist — Issues cannot be created without a Project
  to attach to.
- The API process is running and its SQLite database is available.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /issues` request is sent with a valid `project_id`, `summary`,
  `issue_type`, and `priority`, **then** the API creates the Issue with a server-assigned `key`
  of the form `<project.key>-<sequence>` (sequence increments per project, starting at 1),
  `status` defaulting to `todo`, and responds `201` with the full representation.
- **BEH-2** — **When** a `POST /issues` request names a `project_id` that does not exist,
  **then** the API responds `404` naming the missing project, and creates no Issue.
- **BEH-3** — **When** a `POST /issues` request is missing a required field (`project_id`,
  `summary`, `issue_type`, or `priority`), **then** the API responds `422` naming the missing
  field, and creates no Issue.
- **BEH-4** — **When** a `GET /issues` request is sent, optionally with `project_id` and/or
  `status` query parameters, **then** the API responds `200` with the matching Issues as a JSON
  array — unfiltered when no query parameters are given, narrowed to exactly the given
  project/status when they are.
- **BEH-5** — **When** a `GET /issues/{id}` request is sent for an id that exists, **then** the
  API responds `200` with that Issue's full representation.
- **BEH-6** — **When** a `GET /issues/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-7** — **When** a `PATCH /issues/{id}` request is sent with one or more mutable fields
  (`summary`, `description`, `issue_type`, `priority`, `assignee`, `reporter`, or `status` — the
  kanban drag action), **then** the API updates exactly those fields, bumps `updated_at`, and
  responds `200` with the full updated representation. `id`, `key`, and `project_id` are not
  mutable fields and are silently ignored if present in the request body — an Issue's project
  and key never change after creation (see Postconditions).
- **BEH-8** — **When** a `PATCH /issues/{id}` request sets `status` to a value outside the fixed
  set (`todo`, `in_progress`, `done`), **then** the API responds `422` and persists no change.
- **BEH-9** — **When** a `DELETE /issues/{id}` request is sent for an id that exists, **then**
  the API deletes it and responds `204` with an empty body.

### Postconditions

- Every Issue created via `POST /issues` is immediately retrievable via `GET /issues`,
  `GET /issues?project_id=...`, and `GET /issues/{id}` — no eventual consistency window.
- A deleted Issue no longer appears in any subsequent `GET /issues` or `GET /issues/{id}` call
  for that id (the id is not reused for a future Issue).
- An Issue's `key` and `project_id` never change once assigned, including across `PATCH`
  updates — there is no move-issue-to-another-project operation in this milestone.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Unknown `project_id` on create | `404 Not Found`, JSON body naming the missing project | `ISSUE_PROJECT_NOT_FOUND` |
| Missing required field on create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Unknown issue `id` on get/patch/delete | `404 Not Found`, JSON body naming the missing id | `ISSUE_NOT_FOUND` |
| Invalid `status`, `issue_type`, or `priority` value on create/patch | `422 Unprocessable Entity`, JSON body naming the invalid field and its allowed values | `VALIDATION_ERROR` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines the full Issue CRUD surface, the part of the contract both consuming tracks
  (`portwell-assist`/SDLC, `portwell-analytics`/DDLC) will exercise most.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because
  `PATCH /issues/{id}` (the status-transition endpoint) is the single most consumer-visible
  behavior in the whole module; its field/status semantics are the baseline every later change
  must be coordinated against.
- **Principle:** "Fixture-backed, offline only." — Applies because all Issue persistence is
  local SQLite; nothing in this spec reaches outside the process.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define the Issue table and key-sequence logic | SQLite table with a `project_id` foreign key; a per-project sequence counter for key derivation | medium |
| Implement `POST /issues` | Validation, project-existence check, key assignment, insert, default `status: todo` | medium |
| Implement `GET /issues` with filters | Query builder supporting optional `project_id`/`status` params | small |
| Implement `GET /issues/{id}` | Query by id, 404 if missing | small |
| Implement `PATCH /issues/{id}` | Partial update, status-value validation, `updated_at` bump | medium |
| Implement `DELETE /issues/{id}` | Delete by id, 404 if missing, 204 on success | small |

## Acceptance Criteria

- [x] `POST /issues` creates an Issue with a server-assigned key and `todo` default status,
      returns 201 (BEH-1)
- [x] `POST /issues` with an unknown `project_id` returns 404 and creates nothing (BEH-2)
- [x] `POST /issues` with a missing required field returns 422 (BEH-3)
- [x] `GET /issues` supports `project_id` and `status` filters, unfiltered when omitted (BEH-4)
- [x] `GET /issues/{id}` returns 200 for a valid id (BEH-5)
- [x] `GET /issues/{id}` returns 404 for an unknown id (BEH-6)
- [x] `PATCH /issues/{id}` updates the given fields (including status) and returns 200 (BEH-7)
- [x] `PATCH /issues/{id}` with an invalid status returns 422 and persists no change (BEH-8)
- [x] `DELETE /issues/{id}` deletes an existing Issue and returns 204 (BEH-9)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
