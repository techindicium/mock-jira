---
status: approved
kind: feature
revision: 2
updated: 2026-09-04
---

# Feature Charter: issue-tracker-api

<!-- Feature Charter for the issue-tracker-api module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

issue-tracker-api provides a JIRA-shaped issue-tracking domain (projects, issues, kanban
statuses) backed by a local SQLite database, exposed over an HTTP CRUD API. It exists so the
adev-course tracks that need a realistic upstream issue tracker — `portwell-assist` (SDLC) and
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
- SQLite persistence, a single local file, created fresh on first run.
- Seed fixture data whose account/identifier references reconcile with
  `../course-shared/canon/identifiers.md` where an overlap exists.
- An OpenAPI-documented HTTP contract (auto-generated from the implementation, not hand-maintained).

### Out of Scope

- Authentication/authorization — there is no real user model; `assignee`/`reporter` are free-text
  labels, not accounts with credentials.
- Comments, attachments, activity history, webhooks, notifications.
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
| Issue | A single trackable unit of work | `id`, `key` (derived, e.g. `SDLC-1`), `project_id`, `summary`, `description`, `issue_type` (`bug`\|`task`\|`story`), `status` (`todo`\|`in_progress`\|`done`), `priority` (`low`\|`medium`\|`high`), `assignee`, `reporter`, `created_at`, `updated_at` |

### Relationships

- Every Issue belongs to exactly one Project (`Issue.project_id` → `Project.id`). A Project has
  zero or more Issues.

### Invariants

- An Issue's `key` is unique across the whole instance and is derived as
  `<project.key>-<sequence>`, where `<sequence>` increments per project starting at 1.
- An Issue's `status` is always one of the three fixed values; the API rejects any other value.
- A Project's `key` is unique, immutable once created, and used only to derive Issue keys — it is
  never renumbered (mirrors the identifier-stability rule other course repos already follow for
  the shared canon).

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| Create/list/get Project | Create a Project, list all Projects, fetch one by id | must-have | mvp | specified |
| Create Issue | Create an Issue under a Project, server assigns `key` | must-have | mvp | specified |
| List/get Issue | List Issues (filterable by `project_id` and `status`), fetch one by id | must-have | mvp | specified |
| Update Issue | Update any mutable Issue field, including `status` (the kanban drag action) | must-have | mvp | specified |
| Delete Issue | Delete a single Issue | must-have | mvp | specified |
| Seed fixture data | Populate the database with realistic starting Projects/Issues on first run, reconciled with `course-shared/canon` identifiers | must-have | mvp | specified |
| OpenAPI contract | Auto-generated, browsable API documentation | should-have | mvp | specified |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| Comments on Issues | Not needed by either consuming track yet | v2 | — |
| Configurable workflow rules | Fixed 3-status model is sufficient for course exercises | v2 | — |
| Delete Project | Deferred until a real cascade/conflict rule is needed — no consumer requires it yet | v2 | — |

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
| `GET /openapi.json` | REST endpoint | Auto-generated OpenAPI contract document |

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
