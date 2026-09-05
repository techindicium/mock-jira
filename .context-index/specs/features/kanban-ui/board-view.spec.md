---
partial_schema: spec@1
charter: kanban-ui
status: review-passed
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-04
kind: behavioral
---

# Live Spec: Kanban board view, project switcher, and project creation

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

### Preconditions

- `issue-tracker-api`'s `project-management` and `issue-lifecycle` specs are implemented and
  reachable — kanban-ui is served by that same process, so its API calls are same-origin
  relative requests (`/projects`, `/issues`), no base URL configuration needed.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the board page loads, **then** it fetches `GET /projects`, selects a
  Project by default (the first returned, or the last one the viewer selected, tracked
  client-side only), and fetches `GET /issues?project_id=<selected>` to render the board.
- **BEH-2** — **When** Issues are fetched for the selected Project, **then** the board renders
  the three fixed columns (`todo`, `in_progress`, `done`) with each Issue's card placed in the
  column matching its `status`, showing `summary`, `issue_type`, `priority`, and `assignee`.
- **BEH-3** — **When** the viewer picks a different Project from the switcher, **then** the
  board re-fetches Issues for that Project and fully replaces what is shown — it never merges
  two Projects' Issues on screen at once.
- **BEH-4** — **When** the viewer submits the create-project form with a non-empty `key` and
  `name`, **then** the UI calls `POST /projects`, adds the new Project to the switcher, and
  selects it.
- **BEH-5** — **When** any API request in this spec fails (network error or non-2xx response),
  **then** the UI shows a visible message naming what failed — it never fails silently or shows
  a blank screen.
- **BEH-6** — **When** `GET /projects` returns zero Projects, **then** the board shows an empty
  state prompting Project creation, not an error and not a blank screen.

### Postconditions

- The board's visible state always matches the currently selected Project — there is no stale
  render left over from a previous selection after a switch completes.
- A Project created through the create-project form is immediately selectable and immediately
  shows an empty board (zero Issues) until Issues are added under it.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any API request fails (network error or 5xx) | Visible error message naming the failed action | `UI_FETCH_FAILED` |
| Create-project form submits a duplicate `key` (API returns 409) | Form shows the error inline; input is not cleared | `UI_PROJECT_KEY_DUPLICATE` |
| Create-project form submitted with an empty `key` or `name` | Client-side validation blocks the request before it is sent | `UI_VALIDATION_ERROR` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary. Consuming tracks integrate through the
  documented API only, never by importing this repo's internals directly." — Applies because
  this spec is itself an API consumer, subject to the exact same rule as any other track: every
  read/write goes through `issue-tracker-api`'s documented endpoints, never a direct database
  call.
- **Principle:** "Fixture-backed, offline only. No network call to a real endpoint." — Applies
  because every request this spec makes stays on the same local origin.
- **Principle:** "No inbound dependencies." — Applies because kanban-ui depends on
  issue-tracker-api, never the reverse; this spec introduces no new dependency direction.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Static board page shell | HTML/CSS layout: three columns, project switcher, create-project control | medium |
| Fetch and render | JS to call `GET /projects`/`GET /issues` and render cards into columns | medium |
| Project switcher wiring | Selecting a Project re-fetches and fully replaces the board | small |
| Create-project form | Form + `POST /projects` call + inline error handling | small |
| Empty-state handling | Render a prompt-to-create state when there are zero Projects | small |

## Acceptance Criteria

- [ ] Board load fetches Projects, selects a default, fetches and renders that Project's Issues (BEH-1)
- [ ] Issues render into the correct one of three fixed columns with the right card fields (BEH-2)
- [ ] Switching Projects fully replaces the board, never merges two Projects' Issues (BEH-3)
- [ ] Create-project form creates and selects the new Project (BEH-4)
- [ ] Any API failure shows a visible message, never a silent failure or blank screen (BEH-5)
- [ ] Zero Projects shows an empty state, not an error (BEH-6)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
