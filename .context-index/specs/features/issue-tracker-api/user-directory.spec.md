---
partial_schema: implement@1
charter: issue-tracker-api
status: validated
risk_level: low
milestone: v1.2
revision: 1
charter-revision: 11
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
source-manifest:
  sha: "6d65b3b"
  files:
    - app/db.py
    - app/main.py
    - app/models.py
    - app/routers/users.py
    - app/seed.py
    - tests/test_db.py
    - tests/test_seed.py
    - tests/test_users.py
    - tests_e2e/test_user_directory_e2e.py
  computed-at: "2026-09-06T23:15:14.154Z"
---

# Live Spec: User directory (create/list/get)

<!-- Live Spec within the issue-tracker-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/issue-tracker-api/charter.md -->

## Behavioral Contract

### Preconditions

- The API process is running and its SQLite database file exists (created fresh on first run
  if absent — schema creation is idempotent).
- No authentication is required to reach any endpoint (per charter: no real auth in scope). The
  User entity introduced by this spec is a structured directory record, never an account — it
  carries no password, token, session, or permissions semantics.
- This spec is purely additive: it introduces no change to the existing `Project` or `Issue`
  schema or endpoints. `Issue.assignee`/`Issue.reporter` remain free-text strings, not foreign
  keys to `User.id` (see parent charter's Out of Scope and Domain Model sections).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a `POST /users` request is sent with a non-empty `name` (and optionally
  `email`/`role`), **then** the API creates a new User row and responds `201` with the created
  User's `id`, `name`, `email`, and `role`.
- **BEH-2** — **When** a `POST /users` request is sent with an `email` that already exists on
  another User (case-sensitive comparison — `a@x.com` and `A@x.com` are treated as distinct),
  **then** the API responds `409` and does not create a duplicate row.
- **BEH-3** — **When** a `POST /users` request is sent with a missing or empty `name`, **then**
  the API responds `422` naming the missing field, and no row is created.
- **BEH-4** — **When** a `POST /users` request is sent with no `email` at all, **then** the API
  creates the User successfully — `email` is optional and an absent email never collides with
  any other User, including another User also created without an email.
- **BEH-5** — **When** two `POST /users` requests are sent with the same `name` but different
  (or absent) `email` values, **then** both Users are created successfully — `name` is not
  required to be unique, only `email` is (when present).
- **BEH-6** — **When** a `GET /users` request is sent, **then** the API responds `200` with
  every existing User as a JSON array, ordered by creation time.
- **BEH-7** — **When** a `GET /users/{id}` request is sent for an id that exists, **then** the
  API responds `200` with that User's full representation.
- **BEH-8** — **When** a `GET /users/{id}` request is sent for an id that does not exist,
  **then** the API responds `404` naming the missing id.
- **BEH-9** — **When** the API starts against an empty User directory (no User rows exist),
  **then** it seeds a handful of realistic Users (name/email/role, no placeholder text) drawn
  from the same "Assist engineering" roster already used as Issue `assignee`/`reporter`
  (`course-shared/canon/company.md`'s Named People table) — independently of whether any
  Project/Issue seeding has run, via its own emptiness check (`seed_users_if_empty`), never
  folded into the `fixture-seeding` spec's existing Project/Issue seeding transaction.

### Postconditions

- Every User created via `POST /users` is immediately retrievable via both `GET /users` and
  `GET /users/{id}` — no eventual consistency window.
- Creating, listing, or fetching Users never reads or writes any `Issue` or `Project` row —
  the User directory is fully independent of the existing Issue/Project schema.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Duplicate `email` on create (when email provided) | `409 Conflict`, JSON body naming the colliding email | `USER_EMAIL_DUPLICATE` |
| Missing or empty `name` on create | `422 Unprocessable Entity`, JSON body naming the missing field | `VALIDATION_ERROR` |
| Unknown `id` on `GET /users/{id}` | `404 Not Found`, JSON body naming the missing id | `USER_NOT_FOUND` |
| Malformed JSON request body | `400 Bad Request` | `MALFORMED_JSON` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec defines a new slice of that same contract (User create/list/get), discoverable the
  same way as every other endpoint, via `GET /openapi.json`.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies in reverse here:
  this spec is deliberately non-breaking. It adds new endpoints and a new table; it changes
  nothing about the already-validated `Project`/`Issue` contract, request/response shapes, or
  schema. `Issue.assignee`/`Issue.reporter` stay exactly as `project-management`/`issue-lifecycle`
  already specify them.
- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint, no real
  credentials." — Applies because User persistence is local SQLite only, and because the User
  entity itself carries no credentials of any kind — it is a directory record, not an account.
- **Charter note:** This spec is the scoped, additive exception the parent charter's Out of
  Scope section now names explicitly: a real, structured User entity without authentication.
  It does not reintroduce auth — there is still no login, password, token, or session anywhere
  in this API.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define the User table | SQLite table with `id`, `name` (NOT NULL), `email` (nullable, UNIQUE), `role` (nullable), `created_at`; created on startup alongside the existing schema | small |
| Implement `POST /users` | Pydantic request model validation (`name` required; `email`/`role` optional), unique-email enforcement at the DB layer, insert row, return 201 | small |
| Implement `GET /users` | Query all users ordered by creation time, return as a JSON array | small |
| Implement `GET /users/{id}` | Query by id, 404 with `USER_NOT_FOUND` if missing | small |
| Seed a handful of realistic Users | Reuse the existing "Assist engineering" roster already referenced as Issue assignee/reporter (Mei Tan, Kofi Adjei, Priya Nair, Joao Pinto), sourced from `course-shared/canon/company.md`'s Named People table, same sourcing rule the `fixture-seeding` spec's BEH-3 already established | small |
| Confirm OpenAPI wiring | Verify FastAPI's auto-generated `/openapi.json` reflects the new `/users` routes with proper Pydantic response/request models | small |

## Acceptance Criteria

- [x] `POST /users` creates a User and returns 201 with its id/name/email/role (BEH-1)
- [x] `POST /users` with a duplicate email returns 409 and creates no row (BEH-2)
- [x] `POST /users` with a missing or empty name returns 422 (BEH-3)
- [x] `POST /users` with no email succeeds, and never collides with another emailless User (BEH-4)
- [x] `POST /users` allows two Users to share the same name (BEH-5)
- [x] `GET /users` returns all Users as a JSON array, ordered by creation time (BEH-6)
- [x] `GET /users/{id}` returns 200 with the User for a valid id (BEH-7)
- [x] `GET /users/{id}` returns 404 for an unknown id (BEH-8)
- [x] A fresh (empty) database seeds a handful of real, non-placeholder Users on startup, via its
      own independent emptiness check (BEH-9)
- [x] `GET /openapi.json` lists `/users` and `/users/{id}`
- [x] No change to any existing `Project`/`Issue` endpoint, schema, or response shape
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
