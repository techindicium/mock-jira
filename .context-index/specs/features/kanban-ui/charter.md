---
status: approved
kind: feature
revision: 45
updated: 2026-09-09
---

# Feature Charter: kanban-ui

<!-- Feature Charter for the kanban-ui module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

kanban-ui gives `mock-jira` a JIRA-like kanban board web interface — issues rendered as cards
in status columns, full CRUD via forms, and column-to-column moves — so the mock reads and feels
like a real issue tracker to anyone browsing it, not just to a program calling its API. It is a
pure client of `issue-tracker-api`: it owns no persisted data and never touches the database
directly. It ships as static assets (HTML/CSS/JS) served by `issue-tracker-api`'s own HTTP
process — same origin, same container — so its API calls are same-origin relative requests with
no separate server, no CORS configuration, and no runtime base-URL configuration to wire up.

## Scope and Boundaries

### In Scope

- A kanban board view with the three fixed status columns (`todo`, `in_progress`, `done`).
- Issue cards showing summary, type, priority, and assignee.
- Moving an issue between columns (drag-and-drop, or an equivalent explicit control), which calls
  the API's status-update endpoint.
- Create/edit/delete Issue via a form or modal.
- A project switcher listing all Projects and filtering the board to the selected one.
- Basic project creation via a simple form (the API already supports it).
- A persistent left-hand navigation sidebar (Board / Users / Projects, extended by later
  capabilities to Backlog and Sprint — see Capability Map; the nav item set is not fixed at
  exactly these three) that switches between
  view containers client-side; the existing board (columns, switcher, issue forms) becomes the
  "Board" view's content, unchanged in behavior.
- A Users management screen: list all Users (name, email, role) and a simple add-user form
  (`POST /users`) — no edit/delete, since the API does not support them yet.
- A Projects management screen: list all Projects (key, name, description) and a simple
  add-project form (`POST /projects`) — distinct from, and coexisting with, the in-board project
  switcher. No edit/delete, since the API does not support them yet.

### Out of Scope

- Authentication/login — there is no user model to log into.
- Real-time multi-user sync (websockets/live push). A page reload or simple polling is enough.
- Custom board configuration — swimlanes, custom columns, or reordering columns.
- Complex search/filter beyond "which project" (no JQL-style query builder).
- Mobile-responsive polish — a desktop-width browser is the target.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| issue-tracker-api | internal module | Sole source of data, and the process that serves this module's static assets. All reads and writes go through its HTTP API; this module never opens the SQLite file directly. |

## Domain Model

<!-- This module owns no persisted entities — it renders issue-tracker-api's Project and Issue
     one-for-one. The one concept below is a pure view-side grouping, never persisted. -->

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| BoardColumn | A fixed, client-side rendering grouping — not persisted, not an API resource | `status_value` (`todo`\|`in_progress`\|`done`), `display_label`, `ordinal` |

### Relationships

- A BoardColumn groups zero or more of issue-tracker-api's Issue records by their `status` field.

### Invariants

- The three BoardColumns are fixed and always rendered in the same order (`todo`, `in_progress`,
  `done`) — the UI never invents a status value the API does not recognize.
- Every Issue shown on the board belongs to the currently selected Project; switching Projects
  fully replaces the visible set, never merges two Projects' issues on screen at once.

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| Render kanban board | Fetch Issues for the selected Project, group into the three columns | must-have | mvp | validated |
| Move issue between columns | Change an Issue's status via the board (drag-and-drop or equivalent control) | must-have | mvp | validated |
| Create issue | Form/modal that calls the API's create-issue endpoint | must-have | mvp | validated |
| Edit issue | Form/modal that calls the API's update-issue endpoint for non-status fields | must-have | mvp | validated |
| Delete issue | Remove an Issue via the board | must-have | mvp | validated |
| Project switcher | List Projects, select one to filter the board | should-have | mvp | validated |
| Create project | Retired 2026-09-07 — the board tab's own, narrower create-project form (key/name only) was removed as a redundant duplicate of the "Projects management screen" capability's superset add-project form (key/name/description); see `board-view.spec.md`'s `retired-behavior-ids: BEH-4` | should-have | mvp | retired |
| End-to-end UI test suite | Real browser automation (a real rendering engine, real clicks/drags/form fills) driving the actual served page — the same interface a person uses, never calling board-logic.js's functions directly | must-have | v1.1 | validated |
| Visual design refresh | Distinctive ticket/dispatch-board visual identity — cards read as ticket stubs on a rail-mounted board, not a generic SaaS dashboard; no functional/behavioral change to any existing capability | should-have | v1.2 | validated |
| User picker in issue forms | Auto-fills the assignee field in the create/edit-issue forms by picking a name from issue-tracker-api's User directory (`GET /users`); the field stays free-text — no schema change, no foreign key, no requirement that assignee match a User | should-have | v1.3 | validated |
| App navigation shell (sidebar) | A persistent left-hand nav rail (Board / Users / Projects) that toggles client-side view containers; Board is the default/active view and wraps the existing board unchanged | should-have | v1.4 | validated |
| Users management screen | List all Users and a simple add-user form (`POST /users`); no edit/delete (API does not support them) | should-have | v1.4 | validated |
| Projects management screen | List all Projects and a simple add-project form (`POST /projects`), distinct from and coexisting with the in-board project switcher; no edit/delete (API does not support them) | should-have | v1.4 | validated |
| Backlog list view and filters | A list/table view of the selected Project's Issues (alternative to the board), plus an assignee/type/priority filter bar shared by both the Backlog and Board views; purely client-side, no new API surface | should-have | v1.5 | validated |
| Sprint view and Backlog sprint assignment | A "Sprint" nav view (board scoped to the Project's active Sprint), start/close-sprint controls, and an "Add to sprint" action on the Backlog view's rows; owned by the `sprints` cross-cutting charter (`.context-index/specs/cross-cutting/sprints/charter.md`) | should-have | v1.6 | validated |
| Comment thread panel in edit-issue form | A chronological Comment list plus an add-comment control inside the existing edit-issue form; owned by the `issue-comments` cross-cutting charter (`.context-index/specs/cross-cutting/issue-comments/charter.md`) | should-have | v1.6 | validated |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| Real-time multi-viewer sync | No multi-user requirement yet; polling/reload suffices | v2 | — |
| Custom board configuration | Fixed 3-column model matches issue-tracker-api's fixed status set | v2 | issue-tracker-api workflow customization (deferred there too) |

## Interface Contracts

### Exposed APIs

None — this module is consumed directly by a human through a browser, not programmatically by
other modules.

### Consumed APIs

| Interface | Source Module | Description |
|-----------|-------------|-------------|
| `GET /projects` | issue-tracker-api | Populate the project switcher |
| `POST /projects` | issue-tracker-api | Create-project form |
| `GET /issues` | issue-tracker-api | Populate the board for the selected project |
| `POST /issues` | issue-tracker-api | Create-issue form |
| `GET /issues/{id}` | issue-tracker-api | Load full detail for the edit form |
| `PATCH /issues/{id}` | issue-tracker-api | Save edits and column-move status changes |
| `DELETE /issues/{id}` | issue-tracker-api | Delete-issue action |
| `GET /users` | issue-tracker-api | Populate the assignee picker's suggestion list in the create/edit-issue forms, and the Users management screen's list |
| `GET /issues/{id}/comments` | issue-tracker-api | Populate the comment-thread panel in the edit-issue form (see `issue-comments` cross-cutting charter) |
| `POST /projects/{id}/sprints` | issue-tracker-api | Create a Sprint (see `sprints` cross-cutting charter) |
| `GET /projects/{id}/sprints` | issue-tracker-api | Populate the Sprint view and the Backlog's "Add to sprint" action with the Project's active Sprint |
| `PATCH /sprints/{id}` | issue-tracker-api | Start/close a Sprint |
| `POST /issues/{id}/comments` | issue-tracker-api | Submit a new Comment from the edit-issue form's add-comment control |
| `POST /users` | issue-tracker-api | Users management screen's add-user form |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Board of a few dozen issues renders with no perceptible lag on a local connection. |
| Availability | No process of its own — availability is entirely issue-tracker-api's, since that is what serves these static assets. Restarting that process is an acceptable recovery path. |
| Security | No real auth. Bound to localhost only by default — never exposed to a real network. |
| Observability | API errors surface to the user as a visible message naming what failed; no structured logging required. |
