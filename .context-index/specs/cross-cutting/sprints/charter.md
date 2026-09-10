---
status: approved
kind: cross-cutting
revision: 2
updated: 2026-09-09
---

# Cross-Cutting Charter: sprints

<!-- Cross-Cutting Charter for the sprints concern. Cross-cutting charters describe a concern
     that touches multiple modules. They live under specs/cross-cutting/, NOT specs/features/. -->

## Business Intent

sprints gives `mock-jira` the one capability that most distinguishes a real Jira board from a
plain kanban tool: time-boxed iterations that group a subset of a Project's Issues, so a team can
plan and work "this sprint" instead of everything at once. It is additive across all three
existing modules: `issue-tracker-api` gains a new Sprint entity, sprint CRUD endpoints, and an
optional `sprint_id` field on Issue (backward-compatible — existing clients that ignore unknown
response fields are unaffected); `kanban-ui` gains a sprint board view and sprint-management
controls; `mcp-server` gains matching MCP tools. No existing endpoint's *required* fields or
status codes change — `sprint_id` is purely additive on Issue's existing shape.

This is a genuinely higher-blast-radius addition than `backlog-view` or `issue-comments`: it adds
a schema field to the existing Issue entity (not just a new independent entity) and introduces
real workflow semantics (a sprint's lifecycle). It should go through full-rigor review and
planning, not the quick tier used for the more contained additions.

**Governance note (constitutional exception, explicitly human-approved):** `Issue.sprint_id` and
the extension of `PATCH /issues/{id}` to accept it modify an *existing* endpoint's
request/response shape — read literally, the constitution's "Requires Human Approval" bucket
("Breaking changes to the public HTTP API contract: endpoint paths, request/response shapes")
covers this, not the "Autonomous" bucket (which covers *new* endpoints only). The project
operator explicitly reviewed and approved this addition on 2026-09-09, judging the field
genuinely additive/nullable and this a course fixture with no real external consumer to protect
(unlike a production API), so the formal `portwell-portal`/`portwell-analytics`-flagging
procedure in constitution principle #5 was deliberately not invoked for this change. This
approval covers `Issue.sprint_id` and the `PATCH /issues/{id}` extension specifically — it is not
a blanket precedent for future breaking-shaped changes.

## Scope

### In Scope

- A Sprint entity (`id`, `project_id`, `name`, `start_date`, `end_date`, `status`) owned by
  `issue-tracker-api` — a time-boxed container scoped to exactly one Project.
- Sprint lifecycle: `planned` → `active` → `closed`, one-directional (no reopening a closed
  sprint), enforced server-side. `POST /projects/{id}/sprints` always creates a Sprint in
  `planned` status — `status` is not settable at creation, only via `PATCH /sprints/{id}`'s
  transition. This means the one-active-sprint invariant below only needs enforcing at the
  `PATCH .../status: active` transition, never at creation.
- At most one `active` sprint per Project at a time — transitioning a Sprint to `active` while
  another of that Project's Sprints is already `active` is rejected (matching how a real team
  runs one sprint at a time).
- Assigning an Issue to a `closed` Sprint via `PATCH /issues/{id}` (`sprint_id: <closed sprint's
  id>`) is rejected — a closed sprint accepts no new membership. Assigning to a `planned` or
  `active` Sprint is allowed.
- `Issue.sprint_id` — an optional, nullable field added to the existing Issue entity. An Issue
  with `sprint_id: null` is in the Backlog (unsprinted); assigning it a Sprint's id moves it into
  that sprint. This field is additive to Issue's existing response shape.
- `POST`/`GET /projects/{id}/sprints` and `PATCH /sprints/{id}` (name/dates/status transitions)
  on `issue-tracker-api`.
- `PATCH /issues/{id}` (already exists) additionally accepts an optional `sprint_id` field —
  reuses the existing update endpoint rather than adding a separate assignment endpoint, matching
  how `status`/`priority` updates already flow through that one endpoint.
- kanban-ui: a "Sprint" nav view showing a kanban board (same three status columns as the
  existing Board view) scoped to the Project's active Sprint's Issues only, plus simple
  start-sprint/close-sprint controls and a way to assign a Backlog issue into the active sprint
  (extends the `backlog-view` capability's list view with a per-row "Add to sprint" action).
- mcp-server: `create_sprint`, `list_sprints`, `update_sprint` tools mirroring the new endpoints;
  the existing `update_issue` tool gains `sprint_id` as an optional parameter.

### Out of Scope

- Sprint velocity, burndown charts, or any reporting/analytics on sprint history.
- Multiple simultaneous active sprints per Project (real Jira supports this in some
  configurations; this course fixture does not).
- Reopening a closed sprint, or moving a closed sprint's incomplete Issues automatically into a
  new sprint ("sprint rollover") — closing a sprint simply stops it; any remaining
  non-`done` Issues stay `sprint_id`-tagged to the closed sprint until manually reassigned.
- Sprint goals/descriptions, capacity planning, or story-point estimation fields on Issue.
- Backlog *ranking/ordering* within a sprint (drag-to-reorder) — Issues in a sprint render in the
  same fixed column-by-status grouping the existing Board view already uses, not a ranked list.

## Affected Modules

| Module | Impact (high / medium / low) | Changes Required |
|---|---|---|
| issue-tracker-api | high | New Sprint table/entity; three new/extended endpoints; `Issue.sprint_id` column (nullable, additive); one-active-sprint-per-Project invariant enforced on the `active` transition; closed-sprint assignment rejected. No `DELETE /sprints/{id}` endpoint exists in this charter's scope (Sprint deletion is deferred, matching how Project deletion was already deferred in issue-tracker-api's own charter) — `DELETE /issues/{id}` is unaffected by this charter, it already cascades to that Issue's Comments (see `issue-comments` charter) and now also simply removes the Issue's `sprint_id` reference along with the Issue itself. |
| kanban-ui | medium | New "Sprint" nav view (board scoped to the active sprint); start/close-sprint controls; an "Add to sprint" action on `backlog-view`'s table rows. Depends on `backlog-view` being implemented first (the assignment action lives there). |
| mcp-server | low | Three new MCP tools, following the existing tool-per-endpoint pattern; `update_issue` tool's schema gains one optional field. |

## Interface Contracts

### Exposed APIs

None — this is a cross-cutting concern wiring three existing modules together; the concrete new
endpoints are exposed by `issue-tracker-api` and the concrete new MCP tools are exposed by
`mcp-server` (each module's own Interface Contracts section is the source of truth once updated).

### Consumed APIs

| Interface | Source Module | Description |
|-----------|---------------|--------------|
| `POST /projects/{id}/sprints` | issue-tracker-api | Create a Sprint; backing call for mcp-server's `create_sprint` tool |
| `GET /projects/{id}/sprints` | issue-tracker-api | List a Project's Sprints; backing call for `list_sprints` |
| `PATCH /sprints/{id}` | issue-tracker-api | Update a Sprint (name/dates/status); backing call for `update_sprint` |
| `PATCH /issues/{id}` (extended) | issue-tracker-api | Assign/unassign an Issue's `sprint_id`; kanban-ui's Backlog "Add to sprint" action and mcp-server's extended `update_issue` tool both use this |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Not a concern at course-fixture volume; no explicit latency target. |
| Availability | No availability requirement beyond the three modules' own — this concern adds no new process. |
| Security | No real auth, matching every other capability in this project. |
| Observability | Sprint-state-transition errors (e.g. starting a second active sprint) surface a clear message naming the conflicting sprint, matching issue-tracker-api's existing validation-error shape. |
