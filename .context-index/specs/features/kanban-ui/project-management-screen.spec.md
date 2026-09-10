---
charter: kanban-ui
status: validated
risk_level: low
milestone: v1.4
revision: 2
charter-revision: 24
created: 2026-09-07
updated: 2026-09-07
kind: behavioral
source-manifest:
  sha: "4ee1393"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_e2e/test_ui_project_management_e2e.py
    - tests_js/project-mgmt-beh-1-list-render.test.js
    - tests_js/project-mgmt-beh-4-5-validate-and-errors.test.js
  computed-at: "2026-09-07T12:34:56.929Z"
drift_detected: true
---

# Live Spec: Projects management screen

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

<!-- This spec populates the "Projects" view container the app-navigation spec defines. It is a
     management view distinct from board-view.spec.md's in-board project switcher: the switcher
     (BEH-1/BEH-3 there) selects which Project's board is visible; this screen lists all
     Projects and is now the sole UI entry point for creating one (board-view.spec.md's own,
     narrower create-project form — key/name only, no description — has been retired as of
     board-view revision 2; see that spec's retired-behavior-ids: BEH-4). No update/delete UI
     is added, matching the Project API/charter, which does not support them yet. -->

### Preconditions

- The `app-navigation` spec is implemented — a "Projects" nav item and an (initially empty)
  `#view-projects` container already exist and become visible/hidden per that spec's BEH-2.
- `issue-tracker-api`'s `project-management` spec already backs `GET`/`POST /projects` — the
  same endpoints `board-view`'s switcher already calls (for `GET /projects`) and this screen's
  own add-project form calls (for both `GET` and `POST /projects`).
- This spec does not alter `board-view.spec.md`'s project switcher in any way — it keeps
  functioning exactly as that spec defines. (`board-view.spec.md`'s own create-project form has
  been retired; this screen's add-project form is now the only `POST /projects` entry point in
  the UI.)

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the viewer switches to the Projects view, **then** the UI fetches
  `GET /projects` and renders each returned Project's `key`, `name`, and `description` in a
  styled list (ledger-row treatment with `--ink-line` hairline dividers, not a generic HTML
  table).
- **BEH-2** — **When** `GET /projects` returns zero Projects, **then** the list area shows an
  empty-state message inviting the viewer to add one, not a blank area and not an error.
- **BEH-3** — **When** the viewer submits this screen's add-project form with non-empty `key`
  and `name` (`description` optional), **then** the UI calls `POST /projects` and, on success,
  clears the form and refreshes the visible list to include the new Project.
- **BEH-4** — **When** this screen's add-project form is submitted with an empty `key` or
  `name`, **then** client-side validation blocks the request before it is sent.
- **BEH-5** — **When** `POST /projects` fails with a duplicate-key `409` or a validation `422`,
  **then** the form shows the API's own response message text inline (never a generic
  "something went wrong"), and the form's input values are not cleared.
- **BEH-6** — **When** `GET /projects` fails (network error or non-2xx response) while loading
  the Projects view, **then** the view shows a visible error message naming what failed; the
  add-project form remains present and usable regardless of the list-fetch outcome.
- **BEH-7** — **When** a Project is created through this screen's add-project form, **then** it
  becomes available in `board-view`'s in-board project switcher the next time the board data is
  loaded or refreshed — this screen is the UI's sole `POST /projects` entry point (`board-view`'s
  own create-project form has been retired; see that spec's `retired-behavior-ids`).

### Postconditions

- The Projects list always reflects the most recently successful `GET /projects` fetch for the
  current view visit; a failed `POST /projects` never partially or optimistically updates the
  list.
- No change to `board-view`'s project switcher or its `change` event contract; this screen's
  `POST /projects` calls create the exact same kind of Project record the switcher already
  displays.
- No edit/delete UI or affordance is added for Projects, matching the Project API's own
  deliberately-deferred scope.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `GET /projects` fails (network error or non-2xx) while loading the Projects view | Visible error message naming the failure; add-project form remains usable | `UI_PROJECTS_FETCH_FAILED` |
| Add-project form submitted with an empty `key` or `name` | Client-side validation blocks the request before it is sent | `UI_VALIDATION_ERROR` |
| `POST /projects` returns `409` (duplicate key) | Inline error showing the API's own message; input values retained | `UI_PROJECT_KEY_DUPLICATE` |
| `POST /projects` returns `422` (validation) | Inline error showing the API's own message; input values retained | `UI_VALIDATION_ERROR` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because this screen reads and
  writes `issue-tracker-api`'s documented `GET`/`POST /projects` endpoints only, never a direct
  database access.
- **Principle:** "Fixture-backed, offline only." — Applies because every request stays a
  same-origin relative call, same as the rest of kanban-ui.
- **Principle:** "No inbound dependencies." — Applies because this spec adds no dependency on
  any other repo; it only consumes an issue-tracker-api endpoint that already exists in this
  same repo.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Projects view markup + CSS | List container + add-project form inside `#view-projects`, styled as ledger rows with `--ink-line` dividers, distinct DOM ids from `board-view`'s own create-project form | medium |
| Fetch + render list | `board.js`: fetch `GET /projects` on each Projects-view visit; `board-logic.js`: pure function building ledger-row HTML from a Projects array | medium |
| Add-project form wiring | Reuse `board-logic.js`'s existing `validateProjectForm`/`extractProjectSubmitError` (identical semantics to `board-view`'s create-project form) wired to this screen's own DOM ids; list refresh on success | small |
| Test coverage | JS unit tests for the pure render function; a real-browser e2e test for list render, empty state, add-project success, and a real duplicate-key `409` error surfaced inline; a regression check that `board-view`'s own switcher still functions unchanged (its own create-project form has since been retired) | small |

## Acceptance Criteria

- [ ] Switching to Projects fetches `GET /projects` and renders key/name/description as a styled ledger list (BEH-1)
- [ ] Zero Projects shows an empty-state prompt, not a blank area or error (BEH-2)
- [ ] Add-project form creates a Project and refreshes the list on success (BEH-3)
- [ ] Empty `key` or `name` blocks submission client-side (BEH-4)
- [ ] A real `409`/`422` failure shows the API's own message inline, without clearing inputs (BEH-5)
- [ ] A `GET /projects` failure shows a visible error while keeping the add-project form usable (BEH-6)
- [ ] A Project created here is selectable in the board-view project switcher on next load (BEH-7)
- [ ] `board-view`'s project switcher remains fully functional and unchanged (its own
      create-project form has been retired — see `board-view.spec.md`'s `retired-behavior-ids`)
- [ ] No update/delete UI is added for Projects
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
