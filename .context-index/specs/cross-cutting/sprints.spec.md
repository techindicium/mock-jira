---
partial_schema: implement@1
mode: cross-cutting
affects: [issue-tracker-api, kanban-ui, mcp-server]
status: validated
revision: 1
created: 2026-09-09
updated: 2026-09-10
kind: behavioral
risk_level: high
source-manifest:
  sha: "1bccb88"
  files:
    - app/db.py
    - app/main.py
    - app/models.py
    - app/routers/issues.py
    - app/routers/sprints.py
    - mcp_server/client.py
    - mcp_server/server.py
    - mcp_server/tools/issues.py
    - mcp_server/tools/sprints.py
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests/mcp_server/test_client.py
    - tests/mcp_server/test_issue_tools.py
    - tests/mcp_server/test_sprint_tools.py
    - tests/test_issue_sprint_assignment.py
    - tests/test_sprints.py
    - tests_js/sprints-beh-1-nav-and-render.test.js
    - tests_js/sprints-beh-2-add-to-sprint.test.js
  computed-at: "2026-09-10T15:54:30.802Z"
drift_detected: true
---

# Live Spec: Sprints

<!-- Cross-cutting Live Spec. Parent Charter: .context-index/specs/cross-cutting/sprints/charter.md
     risk_level: high — this is the only spec in this session's batch that extends an EXISTING
     entity's (Issue) response/request shape rather than adding a wholly independent entity; see
     the charter's Governance note for the human-approval record. -->

## Behavioral Contract

### Preconditions

- issue-tracker-api's `issue-lifecycle` and `project-management` specs are implemented.
- kanban-ui's `backlog-view` spec is implemented (the "Add to sprint" action extends its table
  rows; charted as a sequencing dependency in the `sprints` charter's Affected Modules table).
- mcp-server's `issue-tools`/`project-tools` specs are implemented.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a client calls `POST /projects/{id}/sprints` with a `name` and optional
  ISO-8601 `start_date`/`end_date` **then** issue-tracker-api creates a Sprint in `planned`
  status under that Project and responds `201` with the created Sprint (`id`, `project_id`,
  `name`, `start_date`, `end_date`, `status`). `status` is not accepted as a create-time field —
  a Sprint is always born `planned`. `start_date`/`end_date` are optional; when both are given,
  `end_date` must not precede `start_date`.
- **BEH-2** — **When** a client calls `GET /projects/{id}/sprints` **then** issue-tracker-api
  responds `200` with that Project's Sprints, or `404` if the Project doesn't exist (matching
  `GET /projects/{id}`'s existing 404 behavior — parity across every `/projects/{id}/...` path).
- **BEH-13** — **When** a client calls `POST /issues` (the existing, unchanged endpoint) with a
  `sprint_id` field **then** issue-tracker-api ignores it — every newly created Issue starts
  unsprinted (`sprint_id: null`), regardless of what the request body contains. `sprint_id` is
  writable only via `PATCH /issues/{id}` (BEH-7/BEH-9), where the full cross-Project and
  closed-sprint validation applies. This closes the one gap that could otherwise let an Issue be
  born pre-assigned to another Project's Sprint, bypassing the invariant this spec exists to
  enforce.
- **BEH-3** — **When** a client calls `PATCH /sprints/{id}` with `name`/`start_date`/`end_date`
  **then** issue-tracker-api updates those fields and responds `200` with the updated Sprint.
- **BEH-4** — **When** a client calls `PATCH /sprints/{id}` with `status: active` and that
  Sprint's Project has no other `active` Sprint **then** the Sprint transitions to `active`.
- **BEH-5** — **When** a client calls `PATCH /sprints/{id}` with `status: active` and that
  Sprint's Project already has a different `active` Sprint **then** the request is rejected —
  the one-active-sprint-per-Project invariant holds.
- **BEH-6** — **When** a client calls `PATCH /sprints/{id}` with `status: closed`
  **then** the Sprint transitions to `closed` (from any prior status) and no further status
  transition is ever accepted for that Sprint (one-directional lifecycle).
- **BEH-7** — **When** a client calls `PATCH /issues/{id}` with a `sprint_id` naming a `planned`
  or `active` Sprint of that Issue's own Project **then** the Issue is assigned to that Sprint.
  Validation order when `sprint_id` is present: (1) the named Sprint must exist (else `404
  ISSUE_SPRINT_NOT_FOUND`), (2) it must belong to the Issue's own Project (else `422
  SPRINT_PROJECT_MISMATCH`), (3) it must not be `closed` (else `409 SPRINT_CLOSED`) — matching
  `patch_issue`'s existing existence-check-first pattern.
- **BEH-8** — **When** a client calls `PATCH /issues/{id}` with `sprint_id: null`
  **then** the Issue is unassigned from any Sprint (returns to the Backlog).
- **BEH-9** — **When** a client calls `PATCH /issues/{id}` with a `sprint_id` naming a `closed`
  Sprint **then** the request is rejected — a closed sprint accepts no new membership.
- **BEH-10** — **When** the user opens kanban-ui's "Sprint" nav view **then** it shows a kanban
  board (the same three status columns as the existing Board view) scoped to the selected
  Project's `active` Sprint's Issues only — or, if no Sprint is `active`, an explicit "No active
  sprint" message with a control to start one from the Backlog/Projects area.
- **BEH-11** — **When** the user clicks an "Add to sprint" action on a Backlog row (extending
  `backlog-view`'s table) **then** kanban-ui calls `PATCH /issues/{id}` with the Project's
  `active` Sprint's id, and the row updates to reflect its new Sprint membership without a full
  reload.
- **BEH-12** — **When** an MCP client calls `create_sprint`/`list_sprints`/`update_sprint`
  **then** mcp-server translates each to its backing endpoint and returns the result unchanged,
  exactly mirroring existing tools; `update_issue` additionally accepts an optional `sprint_id`
  parameter that maps to the same field on `PATCH /issues/{id}`.

### Postconditions

- At any time, at most one Sprint per Project has `status: active`.
- A Sprint's `status` only ever moves forward (`planned → active → closed`); no code path can
  set it backward.
- Every Issue's `sprint_id` either names a Sprint scoped to that Issue's own Project, or is
  `null` — never a Sprint belonging to a different Project (see Error Cases).
- No existing Issue/Project/User/Comment endpoint's response shape loses or renames a field —
  `Issue`'s response shape gains exactly one new field, `sprint_id` (nullable).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `POST /projects/{id}/sprints` with empty/missing `name`, or where `{id}` doesn't exist | `422` (empty name) or `404` (missing Project) | `VALIDATION_ERROR` / `SPRINT_PROJECT_NOT_FOUND` |
| `POST /projects/{id}/sprints` with `end_date` before `start_date`, or either malformed (not ISO-8601) | `422` | `VALIDATION_ERROR` |
| `GET /projects/{id}/sprints` where `{id}` doesn't exist | `404` (parity with `GET /projects/{id}`) | `SPRINT_PROJECT_NOT_FOUND` |
| `PATCH /sprints/{id}` where `{id}` doesn't exist | `404` | `SPRINT_NOT_FOUND` |
| `PATCH /sprints/{id}` with `status: active` while another Sprint in the same Project is already `active` | `409` naming the conflicting Sprint | `SPRINT_ALREADY_ACTIVE` |
| `PATCH /sprints/{id}` on an already-`closed` Sprint attempting any status change | `409` | `SPRINT_CLOSED` |
| `PATCH /issues/{id}` with a `sprint_id` naming a Sprint from a *different* Project than the Issue's own | `422` | `SPRINT_PROJECT_MISMATCH` |
| `PATCH /issues/{id}` with a `sprint_id` naming a `closed` Sprint | `409` | `SPRINT_CLOSED` |
| `PATCH /issues/{id}` with a `sprint_id` that doesn't exist | `404` | `ISSUE_SPRINT_NOT_FOUND` |
| kanban-ui's Sprint view/Add-to-sprint call fails | Same `#board-error` error-banner pattern the Board and Backlog views already reuse (no new error-handling path) | `UI_FETCH_FAILED` |
| mcp-server tool called against a non-existent Sprint/Issue | Same 404-translated error shape existing tools use | `MCP_UPSTREAM_ERROR` |

## System Constitution Reference

- Principle 5, "Breaking API changes are coordinated, not silent" — this spec's `Issue.sprint_id`
  field and `PATCH /issues/{id}` extension were explicitly reviewed and approved by the project
  operator on 2026-09-09 (recorded in the `sprints` cross-cutting charter's Governance note); the
  new Sprint-only endpoints (`POST`/`GET /projects/{id}/sprints`, `PATCH /sprints/{id}`) are
  ordinary autonomous additions under "Adding new mock endpoints that extend (not break) the
  existing contract."
- "Fixture-backed, offline only" — no new fixture data or network dependency; Sprints persist in
  the same local SQLite file.
- "Identifiers reconcile with the shared canon" — Sprint `id` is server-assigned and internal,
  matching how Project/Issue/Comment ids are already handled; no reconciliation needed.

## Module Impact Map

| Module | Impact | Changes Required |
|--------|--------|-------------------|
| issue-tracker-api | High | New Sprint table/entity; three new/extended endpoints; `Issue.sprint_id` column; one-active-sprint invariant; closed-sprint rejection; cross-Project assignment rejection |
| kanban-ui | Medium | New "Sprint" nav view (board scoped to active Sprint); start/close-sprint controls; "Add to sprint" action on `backlog-view`'s table |
| mcp-server | Low | Three new MCP tools; `update_issue` tool's schema gains one optional field |

## Integration Points

1. kanban-ui ↔ issue-tracker-api: the Sprint view and Backlog's "Add to sprint" action call the
   new/extended endpoints directly, same-origin, exactly like every other kanban-ui API call.
   kanban-ui is a direct consumer of `GET /projects/{id}/sprints` — it needs the Project's
   `active` Sprint's id both to render the Sprint view (BEH-10, including its "no active sprint"
   fallback) and to know which Sprint id the Backlog's "Add to sprint" action should send
   (BEH-11). This consumption is additive to the same kanban-ui module already listed in the
   sibling `issue-comments` cross-cutting charter's precedent structure.
2. mcp-server ↔ issue-tracker-api: `create_sprint`/`list_sprints`/`update_sprint` translate to
   the same three endpoints, following `mcp_server/tools/issues.py`'s existing pattern; the
   extended `update_issue` tool passes `sprint_id` through to the existing `PATCH /issues/{id}`
   call unchanged in structure.
3. **Nav scope acknowledgment:** `backlog-view.spec.md` already added a "Backlog" nav item to
   kanban-ui's sidebar as a `charter-extension` beyond `app-navigation.spec.md` BEH-1's literal
   "three nav items" wording and kanban-ui's charter Scope's "(Board / Users / Projects)"
   parenthetical (both now stale). This spec's "Sprint" nav item (BEH-10) is a second such
   extension on top of the same already-stale wording — not a new deviation this spec
   introduces. Updating `app-navigation.spec.md`'s BEH-1 to describe a non-fixed nav item count
   is out of scope for this spec (it is a different spec's behavioral contract); the kanban-ui
   charter's Scope/Capability Map wording is updated alongside this spec's review to stop
   compounding the staleness (see charter revision bump).
4. kanban-ui's Sprint view ↔ Board view: both render the same three-status-column layout and
   share `board-logic.js`'s existing `buildCardHtml`/`groupIssuesByStatus`/`columnCounts`
   functions — the Sprint view is Board's rendering logic applied to a different Issue subset
   (active-Sprint-scoped instead of all-of-Project-scoped), not a separate rendering path.

## Actionable Task Map

| Task | Description | Complexity |
|------|-------------|------------|
| Sprint table + model | SQLite table, Pydantic model, one-active-sprint/closed-sprint invariants in issue-tracker-api | Medium |
| Sprint endpoints | `POST`/`GET /projects/{id}/sprints`, `PATCH /sprints/{id}` | Medium |
| Issue.sprint_id extension | Add column; extend `PATCH /issues/{id}` and its response shape. The "closed sprint rejects new membership" check is needed on this write path only (not on `PATCH /sprints/{id}`, which enforces its own separate one-active-sprint invariant) — implement as one shared validation helper reused if any future write path needs it, not duplicated logic. | Medium |
| kanban-ui Sprint view | New nav view + board rendering scoped to active Sprint | Medium |
| kanban-ui Backlog integration | "Add to sprint" action on `backlog-view`'s rows | Small |
| Sprint MCP tools | `create_sprint`/`list_sprints`/`update_sprint`; extend `update_issue` | Small |
| Tests | Unit + e2e (API), unit + e2e (UI), unit (MCP tools) | Medium |

## Acceptance Criteria

- [ ] `POST /projects/{id}/sprints` creates a `planned` Sprint with optional dates, validated (BEH-1)
- [ ] `GET /projects/{id}/sprints` lists a Project's Sprints, 404s on a missing Project (BEH-2)
- [ ] `POST /issues` ignores any client-supplied `sprint_id` — new Issues always start unsprinted (BEH-13)
- [ ] `PATCH /sprints/{id}` updates name/dates (BEH-3) and transitions status forward-only (BEH-4, BEH-6)
- [ ] A second concurrent `active` Sprint per Project is rejected (BEH-5)
- [ ] `PATCH /issues/{id}` assigns/unassigns `sprint_id` (BEH-7, BEH-8), rejecting closed-sprint and cross-Project assignment (BEH-9, Error Cases)
- [ ] kanban-ui's Sprint view renders the active Sprint's Issues in the standard 3-column board (BEH-10)
- [ ] Backlog's "Add to sprint" action works end-to-end (BEH-11)
- [ ] All three new MCP tools and the extended `update_issue` tool work end-to-end (BEH-12)
- [ ] No existing endpoint's response shape loses or renames a field — only `Issue` gains `sprint_id`
- [ ] All quality gates pass (`pytest`, `ruff`, `tests_js`, e2e, MCP e2e)
- [ ] No constitutional violations beyond the explicitly-recorded, scoped exception for `Issue.sprint_id`
