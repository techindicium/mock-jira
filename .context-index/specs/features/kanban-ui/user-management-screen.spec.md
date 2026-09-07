---
charter: kanban-ui
status: implemented
risk_level: low
milestone: v1.4
revision: 1
charter-revision: 24
created: 2026-09-07
updated: 2026-09-07
kind: behavioral
source-manifest:
  sha: "1ef19b4"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_e2e/test_ui_user_management_e2e.py
    - tests_js/user-mgmt-beh-1-list-render.test.js
    - tests_js/user-mgmt-beh-4-5-validate-and-errors.test.js
  computed-at: "2026-09-07T11:26:17.475Z"
---

# Live Spec: Users management screen

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

<!-- This spec populates the "Users" view container the app-navigation spec defines. It is a
     primary CRUD-style read/create view over issue-tracker-api's User directory — distinct
     from user-picker.spec.md, which is a convenience assignee-suggestion source layered on
     the issue forms. The two specs consume the same GET /users endpoint independently; this
     spec additionally uses POST /users, which user-picker never calls. -->

### Preconditions

- The `app-navigation` spec is implemented — a "Users" nav item and an (initially empty)
  `#view-users` container already exist and become visible/hidden per that spec's BEH-2.
- `issue-tracker-api`'s `user-directory` spec is implemented and reachable at the same origin
  (`GET /users`, `POST /users`), same-origin relative requests, no separate server or CORS
  configuration.
- This spec introduces no change to `user-picker.spec.md`'s cached-datalist behavior (BEH-1's
  "fetch `GET /users` at most once per board load" guarantee is unaffected) — this screen's own
  `GET /users` calls are independent and do not share that cache.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the viewer switches to the Users view, **then** the UI fetches
  `GET /users` and renders each returned User's `name`, `email`, and `role` in a styled list
  (ledger-row treatment with `--ink-line` hairline dividers, not a generic HTML table).
- **BEH-2** — **When** `GET /users` returns zero Users, **then** the list area shows an
  empty-state message inviting the viewer to add one, not a blank area and not an error.
- **BEH-3** — **When** the viewer submits the add-user form with a non-empty `name` (`email`
  and `role` left blank or filled), **then** the UI calls `POST /users` and, on success, clears
  the form and refreshes the visible list to include the new User.
- **BEH-4** — **When** the add-user form is submitted with an empty or whitespace-only `name`,
  **then** client-side validation blocks the request before it is sent.
- **BEH-5** — **When** `POST /users` fails with a duplicate-email `409` or a validation `422`,
  **then** the form shows the API's own response message text inline (never a generic
  "something went wrong"), and the form's input values are not cleared.
- **BEH-6** — **When** `GET /users` fails (network error or non-2xx response) while loading the
  Users view, **then** the view shows a visible error message naming what failed; the add-user
  form remains present and usable regardless of the list-fetch outcome.
- **BEH-7** — **When** a User is successfully created through this screen, **then**
  `user-picker.spec.md`'s cached assignee-suggestion datalist is **not** required to update
  immediately — that spec's load-time-snapshot semantics (BEH-1) are explicitly unaffected; the
  new User appears in the assignee suggestion list only after the next full board load.

### Postconditions

- The Users list always reflects the most recently successful `GET /users` fetch for the
  current view visit; a failed `POST /users` never partially or optimistically updates the
  list.
- No change to `Issue.assignee`, `user-picker.spec.md`'s datalist-caching behavior, or any
  `board-view`/`issue-crud-forms` behavior.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `GET /users` fails (network error or non-2xx) while loading the Users view | Visible error message naming the failure; add-user form remains usable | `UI_USERS_FETCH_FAILED` |
| Add-user form submitted with an empty/whitespace `name` | Client-side validation blocks the request before it is sent | `UI_VALIDATION_ERROR` |
| `POST /users` returns `409` (duplicate email) | Inline error showing the API's own message; input values retained | `UI_USER_EMAIL_DUPLICATE` |
| `POST /users` returns `422` (validation) | Inline error showing the API's own message; input values retained | `UI_VALIDATION_ERROR` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because this screen reads and
  writes `issue-tracker-api`'s documented `GET`/`POST /users` endpoints only, never a direct
  database access.
- **Principle:** "Fixture-backed, offline only." — Applies because every request stays a
  same-origin relative call, same as the rest of kanban-ui.
- **Principle:** "No inbound dependencies." — Applies because this spec adds no dependency on
  any other repo; it only consumes an issue-tracker-api endpoint that already exists in this
  same repo.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Users view markup + CSS | List container + add-user form inside `#view-users`, styled as ledger rows with `--ink-line` dividers, consistent with the dispatch-board aesthetic | medium |
| Fetch + render list | `board.js`: fetch `GET /users` on each Users-view visit; `board-logic.js`: pure function building ledger-row HTML from a Users array | medium |
| Add-user form wiring | Client-side validation (`name` required), `POST /users`, list refresh on success, inline error display using the API's real message on failure | small |
| Test coverage | JS unit tests for the pure render/validate functions; a real-browser e2e test for list render, empty state, add-user success, and a real duplicate-email `409` error surfaced inline | small |

## Acceptance Criteria

- [ ] Switching to Users fetches `GET /users` and renders name/email/role as a styled ledger list (BEH-1)
- [ ] Zero Users shows an empty-state prompt, not a blank area or error (BEH-2)
- [ ] Add-user form creates a User and refreshes the list on success (BEH-3)
- [ ] Empty/whitespace `name` blocks submission client-side (BEH-4)
- [ ] A real `409`/`422` failure shows the API's own message inline, without clearing inputs (BEH-5)
- [ ] A `GET /users` failure shows a visible error while keeping the add-user form usable (BEH-6)
- [ ] `user-picker.spec.md`'s cached-datalist semantics are unaffected by this screen (BEH-7)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
