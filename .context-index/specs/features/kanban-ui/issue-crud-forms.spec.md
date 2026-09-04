---
partial_schema: spec@1
charter: kanban-ui
status: review-pending
risk_level: medium
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-04
kind: behavioral
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
- **BEH-6** — **When** the create-issue or edit-issue form is submitted with a missing required
  field, **then** client-side validation blocks the request before it is sent.

### Postconditions

- The board never shows a card in a column that does not match the server's last-confirmed
  `status` for that Issue — an optimistic move that fails is always reverted, never left stuck.
- A deleted Issue's card never reappears on a subsequent board refresh.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Create/edit form submitted with a missing required field | Client-side validation blocks the request before it is sent | `UI_VALIDATION_ERROR` |
| `PATCH`/`DELETE` targets an id the API no longer has (404) | Card is removed from the board; a message notes it was already gone | `UI_ISSUE_NOT_FOUND` |
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

- [ ] Create-issue form creates a card in the `todo` column on success (BEH-1)
- [ ] Edit-issue form updates only the changed fields, reflecting the server's response (BEH-2)
- [ ] Column move calls the status-update endpoint and settles on the server-confirmed column (BEH-3)
- [ ] Delete removes the card from the board once confirmed by the server (BEH-4)
- [ ] Any failed call reverts its optimistic change and shows a visible error (BEH-5)
- [ ] Missing required fields block submission client-side (BEH-6)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
