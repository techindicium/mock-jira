---
partial_schema: implement@1
charter: kanban-ui
status: validated
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-05
kind: behavioral
source-manifest:
  sha: "a987602"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_js/issue-crud-beh-1-create-issue.test.js
    - tests_js/issue-crud-beh-2-edit-issue.test.js
    - tests_js/issue-crud-beh-3-column-move.test.js
    - tests_js/issue-crud-beh-4-delete-issue.test.js
    - tests_js/issue-crud-beh-5-error-handling.test.js
    - tests_js/issue-crud-beh-6-create-validation.test.js
  computed-at: "2026-09-05T12:06:33.669Z"
---

# Live Spec: Issue create, edit, delete, and column move

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

### Preconditions

- The `board-view` spec is implemented — a board is already rendered with a selected Project
  before any of these actions can be triggered.
- `issue-tracker-api`'s `issue-lifecycle` spec is implemented and reachable at the same origin.
- The create-issue form's required fields are exactly those `issue-lifecycle`'s `POST /issues`
  requires: `summary`, `issue_type`, and `priority` (`project_id` is supplied implicitly from
  the currently selected board, not a form field). The edit-issue form has no required fields —
  any subset of mutable fields may be submitted (see `issue-lifecycle` BEH-7).
- A newly created Issue's `status` defaults to `todo` server-side (per `issue-lifecycle` BEH-1);
  the create-issue form does not offer a status field.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the viewer submits the create-issue form with all required fields filled,
  **then** the UI calls `POST /issues` under the currently selected Project, closes the form, and
  the new card appears in the `todo` column.
- **BEH-2** — **When** the viewer submits the edit-issue form with one or more changed non-status
  fields, **then** the UI calls `PATCH /issues/{id}` with just the changed fields, closes the
  form, and the card updates in place to reflect the server's response.
- **BEH-3** — **When** the viewer moves a card to a different column (drag-and-drop or an
  equivalent explicit control), **then** the UI calls `PATCH /issues/{id}` with the new status,
  and the card's final resting column reflects the server's confirmed response, not merely an
  unreconciled optimistic move.
- **BEH-4** — **When** the viewer deletes a card and confirms the deletion, **then** the UI
  calls `DELETE /issues/{id}` and removes the card from the board once the server confirms
  success.
- **BEH-5** — **When** any API call in this spec fails (network error or non-2xx response),
  **then** the UI reverts any optimistic change (e.g. a dragged card returns to its original
  column) and shows a visible error message naming what failed.
- **BEH-6** — **When** the create-issue form is submitted with `summary`, `issue_type`, or
  `priority` missing, **then** client-side validation blocks the request before it is sent. The
  edit-issue form has no required fields and is never blocked by this rule.

### Postconditions

- The board never shows a card in a column that does not match the server's last-confirmed
  `status` for that Issue — an optimistic move that fails is always reverted, never left stuck.
- A deleted Issue's card never reappears on a subsequent board refresh.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Create/edit form submitted with a missing required field | Client-side validation blocks the request before it is sent | `UI_VALIDATION_ERROR` |
| `PATCH`/`DELETE` targets an id the API no longer has (404) | Card is removed from the board; a message notes it was already gone. This is the one exception to BEH-5's generic revert rule: a 404 means the card is already gone server-side, so removing it (not reverting to a stale local state) is the correct recovery. | `UI_ISSUE_NOT_FOUND` |
| Any request fails (network error or 5xx) | Optimistic change reverted; visible error message | `UI_FETCH_FAILED` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because every mutation in this
  spec goes through `issue-tracker-api`'s documented endpoints, never a direct database write.
- **Principle:** "Fixture-backed, offline only." — Applies because every request stays on the
  same local origin.
- **Principle:** "No inbound dependencies." — Applies because kanban-ui depends on
  issue-tracker-api, never the reverse.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Create-issue form | Modal/form + `POST /issues` wiring + client-side validation | medium |
| Edit-issue form | Modal/form + `PATCH /issues/{id}` wiring for non-status fields | medium |
| Column-move interaction | Drag-and-drop (or equivalent control) + `PATCH /issues/{id}` status update + optimistic-then-reconcile | medium |
| Delete confirmation | Confirm step + `DELETE /issues/{id}` wiring | small |
| Shared error/revert handling | Common path for reverting optimistic changes and surfacing errors across all four actions | small |

## Acceptance Criteria

- [x] Create-issue form creates a card in the `todo` column on success (BEH-1)
- [x] Edit-issue form updates only the changed fields, reflecting the server's response (BEH-2)
- [x] Column move calls the status-update endpoint and settles on the server-confirmed column (BEH-3)
- [x] Delete removes the card from the board once confirmed by the server (BEH-4)
- [x] Any failed call reverts its optimistic change and shows a visible error (BEH-5)
- [x] Missing required fields block submission client-side (BEH-6)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
