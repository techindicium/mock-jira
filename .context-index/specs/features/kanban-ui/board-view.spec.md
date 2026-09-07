---
partial_schema: implement@1
charter: kanban-ui
status: validated
risk_level: medium
milestone: mvp
revision: 2
charter-revision: 2
created: 2026-09-04
updated: 2026-09-07
kind: behavioral
source-manifest:
  sha: "829e1aa"
  files:
    - .context-index/governance/gates.yaml
    - app/main.py
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests/test_static_assets.py
    - tests_js/beh-1-board-load.test.js
    - tests_js/beh-2-render-columns.test.js
    - tests_js/beh-3-project-switch.test.js
    - tests_js/beh-5-fetch-error.test.js
    - tests_js/beh-6-empty-state.test.js
  computed-at: "2026-09-07T12:34:45.868Z"
---

# Live Spec: Kanban board view and project switcher

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

### Preconditions

- `issue-tracker-api`'s `project-management` and `issue-lifecycle` specs are implemented and
  reachable — kanban-ui is served by that same process, so its API calls are same-origin
  relative requests (`/projects`, `/issues`), no base URL configuration needed.

### Behaviors

<!-- retired-behavior-ids: BEH-4 -->
<!-- BEH-4 (retired 2026-09-07) — When the viewer submitted the create-project form (fields:
     key, name) that lived next to the switcher, the UI called POST /projects, added the new
     Project to the switcher, and selected it. Retired because it was a redundant, narrower
     duplicate of the add-project form the Projects tab now owns (key, name, and description —
     see project-management-screen.spec.md's own BEH-3/BEH-4/BEH-5). Project creation from the
     board view is no longer part of this spec's scope; the switcher itself is unaffected and
     remains fully in scope (BEH-1/BEH-3 below). -->

- **BEH-1** — **When** the board page loads, **then** it fetches `GET /projects`, selects a
  Project by default (the first returned, or the last one the viewer selected, tracked
  client-side only), and fetches `GET /issues?project_id=<selected>` to render the board.
- **BEH-2** — **When** Issues are fetched for the selected Project, **then** the board renders
  the three fixed columns (`todo`, `in_progress`, `done`) with each Issue's card placed in the
  column matching its `status`, showing `summary`, `issue_type`, `priority`, and `assignee`.
- **BEH-3** — **When** the viewer picks a different Project from the switcher, **then** the
  board re-fetches Issues for that Project and fully replaces what is shown — it never merges
  two Projects' Issues on screen at once.
- **BEH-5** — **When** any API request in this spec fails (network error or non-2xx response),
  **then** the UI shows a visible message naming what failed — it never fails silently or shows
  a blank screen.
- **BEH-6** — **When** `GET /projects` returns zero Projects, **then** the board shows an empty
  state prompting Project creation — via the Projects tab's add-project form, see
  `project-management-screen.spec.md` — not an error and not a blank screen.

### Postconditions

- The board's visible state always matches the currently selected Project — there is no stale
  render left over from a previous selection after a switch completes.
- A Project created through the Projects tab's add-project form (see
  `project-management-screen.spec.md` BEH-3/BEH-7) is immediately selectable in this board's
  switcher the next time the board's Project list is loaded or refreshed, and immediately shows
  an empty board (zero Issues) until Issues are added under it.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Any API request fails (network error or 5xx) | Visible error message naming the failed action | `UI_FETCH_FAILED` |

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
| Static board page shell | HTML/CSS layout: three columns, project switcher | medium |
| Fetch and render | JS to call `GET /projects`/`GET /issues` and render cards into columns | medium |
| Project switcher wiring | Selecting a Project re-fetches and fully replaces the board | small |
| Empty-state handling | Render a prompt-to-create state when there are zero Projects | small |

## Acceptance Criteria

- [x] Board load fetches Projects, selects a default, fetches and renders that Project's Issues (BEH-1)
- [x] Issues render into the correct one of three fixed columns with the right card fields (BEH-2)
- [x] Switching Projects fully replaces the board, never merges two Projects' Issues (BEH-3)
- [x] Any API failure shows a visible message, never a silent failure or blank screen (BEH-5)
- [x] Zero Projects shows an empty state, not an error (BEH-6)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
- [x] (retired) BEH-4 create-project form removed from this spec's scope — see
      `retired-behavior-ids` above and `project-management-screen.spec.md` for the surviving
      add-project form
