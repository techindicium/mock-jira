---
status: approved
kind: feature
revision: 21
updated: 2026-09-09
---

# Feature Charter: issue-tracker-api

<!-- Feature Charter for the issue-tracker-api module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

issue-tracker-api provides a JIRA-shaped issue-tracking domain (projects, issues, kanban
statuses) backed by a local SQLite database, exposed over an HTTP CRUD API. It exists so the
adev-course tracks that need a realistic upstream issue tracker — `portwell-portal` (SDLC) and
`portwell-analytics` (DDLC) today — have something concrete and offline to integrate against,
without any real Atlassian service involved. This is the core module of `mock-jira`: the kanban
UI and MCP server modules are both clients of this API, never the other way around.

## Scope and Boundaries

### In Scope

- Project entity: a named grouping of issues, identified by a short key (e.g. `SDLC`).
- Issue entity: summary, description, type, status, priority, assignee, reporter, timestamps,
  belonging to exactly one project.
- Fixed kanban status set (`todo`, `in_progress`, `done`) with free-form transitions between them
  (no enforced workflow ordering — any status may move to any other status, matching how a
  simple kanban board behaves when a card is dragged).
- Full CRUD HTTP endpoints for Issue. Create/Read only for Project in this milestone — a
  Project's `key` is immutable once created (see Invariants), so Update has no mutable field to
  target yet, and Delete is deferred (see Deferred Capabilities) rather than chartering a
  cascade/conflict rule this milestone doesn't need.
- User entity: a structured directory record (`name`, optional `email`, optional free-text
  `role`) describing a person who may be referenced elsewhere in this API. Create/List/Get only
  — an additive directory, not a hard relational dependency of Issue (see Invariants and Out of
  Scope).
- SQLite persistence, a single local file, created fresh on first run.
- Seed fixture data whose account/identifier references reconcile with
  `../course-shared/canon/identifiers.md` where an overlap exists.
- An OpenAPI-documented HTTP contract (auto-generated from the implementation, not hand-maintained).

### Out of Scope

- Authentication/authorization/credentials/sessions — the User entity is a structured directory
  record only (name/email/role), never an account. There is no login, no password, no token, no
  session, and no permissions semantics anywhere in this API. This is an explicit, scoped
  exception to nothing in the constitution's "no real auth" posture — the constitution forbids
  real authentication, not a structured record of who's who; adding a User directory does not
  reintroduce auth by another name.
- A foreign-key relationship from Issue to User. `Issue.assignee` and `Issue.reporter` remain
  free-text strings exactly as before; the User directory is additive and independently queried,
  never joined against Issue at the schema level. This preserves the existing Issue contract
  unchanged (see "Breaking API changes are coordinated, not silent").
- Attachments, webhooks, notifications. (Comments and a per-Issue activity log were carved out
  of this exclusion 2026-09-09 — see the `issue-comments` cross-cutting charter, which adds a
  Comment entity and endpoints to this module additively, without changing any existing
  endpoint's request/response shape.)
- Configurable/custom workflows — the three-status kanban model is fixed.
- Full JQL-style search — filtering is limited to the fields capabilities below name.
- Multi-tenancy — one SQLite file serves the whole mock instance.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| `../course-shared/canon/identifiers.md` | shared reference (read-only) | Seed fixture identifiers must not collide with the canon's reserved ranges. Not a runtime/code dependency — this repo does not import or execute anything from `course-shared`. |

## Domain Model

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| Project | A named grouping of issues | `id`, `key` (short, unique, e.g. `SDLC`), `name`, `description` |
| Issue | A single trackable unit of work | `id`, `key` (derived, e.g. `SDLC-1`), `project_id`, `summary`, `description`, `issue_type` (`bug`\|`task`\|`story`), `status` (`todo`\|`in_progress`\|`done`), `priority` (`low`\|`medium`\|`high`), `assignee`, `reporter`, `sprint_id` (optional, nullable — see `sprints` cross-cutting charter), `created_at`, `updated_at` |
| User | A directory record describing a person, for reference only — not an account | `id`, `name` (required), `email` (optional, unique when present), `role` (optional free-text, descriptive only, no permissions semantics) |
| Comment | A timestamped note attached to exactly one Issue, forming that Issue's activity log | `id`, `issue_id`, `body` (required, free text), `author` (free-text, mirrors `Issue.assignee`/`reporter` — not a foreign key to User), `created_at` |
| Sprint | A time-boxed iteration scoped to exactly one Project; owned by the `sprints` cross-cutting charter (`.context-index/specs/cross-cutting/sprints/charter.md`) | `id`, `project_id`, `name`, `start_date` (optional), `end_date` (optional), `status` (`planned`\|`active`\|`closed`) |

### Relationships

- Every Issue belongs to exactly one Project (`Issue.project_id` → `Project.id`). A Project has
  zero or more Issues.
- User has no relationship to Project or Issue at the schema level. It is an independent,
  additive directory — `Issue.assignee`/`Issue.reporter` stay free-text strings, not foreign keys
  to `User.id` (see Out of Scope). A client may use the User list to auto-fill those free-text
  fields, but this API never enforces or joins that association.
- Every Comment belongs to exactly one Issue (`Comment.issue_id` → `Issue.id`). An Issue has zero
  or more Comments, ordered by `created_at`. Comment has no relationship to User (`author` is
  free-text, same pattern as `Issue.assignee`/`reporter` — see Out of Scope).
- Every Sprint belongs to exactly one Project (`Sprint.project_id` → `Project.id`). An Issue
  optionally belongs to at most one Sprint of its own Project (`Issue.sprint_id` → `Sprint.id`,
  nullable, and only ever set to a Sprint sharing the Issue's `project_id`).

### Invariants

- An Issue's `key` is unique across the whole instance and is derived as
  `<project.key>-<sequence>`, where `<sequence>` increments per project starting at 1.
- An Issue's `status` is always one of the three fixed values; the API rejects any other value.
- A Project's `key` is unique, immutable once created, and used only to derive Issue keys — it is
  never renumbered (mirrors the identifier-stability rule other course repos already follow for
  the shared canon).
- A User's `email`, when provided, is unique across all Users; a User's `name` is required and
  non-empty. A User's `id` is never reused once assigned.
- Every Comment belongs to exactly one Issue (`Comment.issue_id` → `Issue.id`); deleting an Issue
  deletes its Comments (no orphaned Comments). A Comment's `body` is required and non-empty. A
  Comment's `id` is never reused once assigned. Comments are append-only and immutable once
  created — no edit endpoint, matching an activity log's semantics (mirrors how Issue history
  would work if it existed; this Comment log is the only history this API keeps).
- A Sprint's `status` only ever moves forward (`planned → active → closed`); at most one Sprint
  per Project has `status: active` at a time; a `closed` Sprint accepts no new Issue membership.
  An Issue's `sprint_id`, when set, always names a Sprint of that Issue's own Project — never a
  different Project's Sprint. `POST /issues` never accepts a client-supplied `sprint_id` — every
  new Issue starts unsprinted.

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| Create/list/get Project | Create a Project, list all Projects, fetch one by id | must-have | mvp | validated |
| Create Issue | Create an Issue under a Project, server assigns `key` | must-have | mvp | validated |
| List/get Issue | List Issues (filterable by `project_id` and `status`), fetch one by id | must-have | mvp | validated |
| Update Issue | Update any mutable Issue field, including `status` (the kanban drag action) | must-have | mvp | validated |
| Delete Issue | Delete a single Issue | must-have | mvp | validated |
| Seed fixture data | Populate the database with realistic starting Projects/Issues on first run, reconciled with `course-shared/canon` identifiers | must-have | mvp | validated |
| OpenAPI contract | Auto-generated, browsable API documentation | should-have | mvp | validated |
| End-to-end API test suite | Real HTTP calls (over a real socket, against a real running server process) exercising the full Project/Issue CRUD surface — the same interface a consuming track's real client uses, never FastAPI's in-process TestClient | must-have | v1.1 | validated |
| User directory (create/list/get) | Create a User, list all Users, fetch one by id — an additive, structured directory of people (name/email/role), no authentication, no FK from Issue | must-have | v1.2 | validated |
| Comments on Issues (create/list) | Add a Comment to an Issue, list an Issue's Comments in order — an append-only activity log; no update/delete endpoint (see Invariants). Additive: no existing endpoint's request/response shape changes. | should-have | v1.3 | validated |
| Sprints (create/list/update, Issue assignment) | Sprint CRUD (minus delete) plus an optional `sprint_id` field on Issue; owned by the `sprints` cross-cutting charter. This is the one capability in this module with a recorded constitutional exception (extends an existing entity's response/request shape — see that charter's Governance note). | should-have | v1.4 | implemented |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| Update/delete Comment | Deferred until a consumer needs to correct or remove a Comment — append-only activity log is sufficient for now | v2 | — |
| Configurable workflow rules | Fixed 3-status model is sufficient for course exercises | v2 | — |
| Delete Project | Deferred until a real cascade/conflict rule is needed — no consumer requires it yet | v2 | — |
| Update/Delete User | Deferred until a consumer needs to edit or remove a directory entry — the initial directory is create/list/get only, mirroring how Project deferred Update/Delete until a real need appeared | v2 | — |
| Issue-to-User linkage (foreign key) | Deferred indefinitely per charter Out of Scope — `assignee`/`reporter` stay free-text; a future kanban-ui user picker only auto-fills those fields client-side | — | — |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|-----------|------|-------------|
| `GET /projects` | REST endpoint | List all Projects |
| `POST /projects` | REST endpoint | Create a Project |
| `GET /projects/{id}` | REST endpoint | Fetch one Project |
| `GET /issues` | REST endpoint | List Issues, optional `project_id`/`status` query filters |
| `POST /issues` | REST endpoint | Create an Issue under a Project |
| `GET /issues/{id}` | REST endpoint | Fetch one Issue |
| `PATCH /issues/{id}` | REST endpoint | Update one or more Issue fields, including `status` |
| `DELETE /issues/{id}` | REST endpoint | Delete one Issue |
| `GET /users` | REST endpoint | List all Users |
| `POST /users` | REST endpoint | Create a User |
| `GET /users/{id}` | REST endpoint | Fetch one User |
| `GET /openapi.json` | REST endpoint | Auto-generated OpenAPI contract document |
| `GET /issues/{id}/comments` | REST endpoint | List an Issue's Comments, ordered by `created_at` |
| `POST /issues/{id}/comments` | REST endpoint | Add a Comment to an Issue |
| `POST /projects/{id}/sprints` | REST endpoint | Create a Sprint (always `planned`) under a Project |
| `GET /projects/{id}/sprints` | REST endpoint | List a Project's Sprints |
| `PATCH /sprints/{id}` | REST endpoint | Update a Sprint's name/dates, or transition its status |

### Consumed APIs

None — this module has no inbound dependency on any other module or repo, per the project
constitution's first non-negotiable principle.

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Not a concern at course-fixture volume (dozens to low hundreds of issues); no explicit latency target. |
| Availability | Runs as a single local process; no HA requirement. Restarting it is an acceptable recovery path. |
| Security | No real auth. Bound to localhost only by default — never exposed to a real network. |
| Observability | Errors return JSON with a message naming what was rejected (e.g. invalid status value) and why. No structured logging required beyond what aids local debugging. |
