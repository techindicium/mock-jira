---
partial_schema: implement@1
charter: kanban-ui
status: validated
risk_level: low
milestone: v1.3
revision: 1
charter-revision: 18
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
source-manifest:
  sha: "aea3f85"
  files:
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_e2e/test_ui_user_picker_e2e.py
    - tests_js/user-picker-beh-2-3-datalist-markup.test.js
    - tests_js/user-picker-beh-2-3-user-options.test.js
    - tests_js/user-picker-beh-6-graceful-degradation.test.js
    - tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js
  computed-at: "2026-09-07T11:25:46.866Z"
---

# Live Spec: User picker in issue forms

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

<!-- This spec is a client-side convenience only: it fetches issue-tracker-api's User
     directory and lets a person pick a name into the existing free-text assignee field.
     It is purely additive — Issue.assignee stays a free-text string, exactly as
     issue-crud-forms already specifies it. No foreign key, no new required field, no
     validation that assignee must match a known User. -->

### Preconditions

- The `issue-crud-forms` spec is implemented and validated — the create-issue and edit-issue
  forms already have a free-text `assignee` input (`#issue-assignee`, `#edit-issue-assignee`)
  with no `required` attribute, exactly as that spec's Preconditions describe.
- `issue-tracker-api`'s `user-directory` spec is implemented and reachable at the same origin
  (`GET /users`), same-origin relative request, no separate server or CORS configuration.
- This spec introduces no change to the `Issue` schema, the `Issue.assignee` field, or any
  existing `issue-crud-forms`/`ui-e2e` behavior — it only adds a suggestion source on top of
  the field that already exists.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the board finishes loading, **then** the UI fetches `GET /users` exactly
  once and caches the result in memory for the rest of that page load — no polling, no re-fetch
  when a create/edit-issue form is subsequently opened, and no re-fetch if a User is renamed or
  removed server-side afterward (the suggestion list simply reflects the load-time snapshot
  until the next full board load).
- **BEH-2** — **When** the create-issue form opens, **then** the `#issue-assignee` input offers
  each cached User's name as a suggestion via a `<datalist>`-backed `list` attribute, while
  remaining the same free-text `<input id="issue-assignee" name="assignee">` issue-crud-forms
  already defines — no `id`, `name`, or `required` attribute changes.
- **BEH-3** — **When** the edit-issue form opens for an existing issue, **then**
  `#edit-issue-assignee` offers the same cached suggestions, and the field is still pre-filled
  with the issue's current `assignee` value exactly as `issue-crud-forms` BEH-2's edit-open
  behavior already does, even when that value does not match any User's name.
- **BEH-4** — **When** the viewer picks a suggested name from the assignee suggestion list,
  **then** the input's value is set to that exact name — no request is sent at pick time; the
  value is only submitted when the surrounding create/edit-issue form is submitted, per
  `issue-crud-forms` BEH-1/BEH-2 unaffected.
- **BEH-5** — **When** the viewer types a name that is not present in the User directory (or
  leaves the field blank), **then** the create/edit-issue form still accepts and submits that
  free-text value exactly as before this spec — no client-side validation requires `assignee`
  to match a known User, and `issue-crud-forms` BEH-6's required-field rule is unaffected
  (`assignee` was never required and stays that way).
- **BEH-6** — **When** `GET /users` fails (network error or non-2xx response) at board load,
  **then** both assignee inputs remain fully functional plain free-text fields with no
  suggestions offered, no board-error banner is shown, and board rendering and issue
  create/edit are not blocked or delayed. This is a deliberate, scoped narrowing of the
  charter's Observability quality attribute ("API errors surface to the user as a visible
  message naming what failed"): that attribute governs the primary Project/Issue CRUD flows,
  where a failure means the viewer's data did not load or save. `GET /users` backs a
  best-have, should-have convenience suggestion list layered on a field that already works
  without it — surfacing an error banner for a missing autocomplete source would be a false
  alarm out of proportion to what actually failed, so this spec intentionally lets it degrade
  silently to the pre-existing free-text-only behavior instead.

### Postconditions

- `#issue-assignee` and `#edit-issue-assignee` keep the exact `id`, `name`, and (absent)
  `required` attribute `issue-crud-forms` already gives them; the only additive markup is a
  `list` attribute on each input plus one shared `<datalist>` element populated from the User
  directory.
- A create or edit-issue form submission's `assignee` value is always whatever text currently
  sits in the input — picked from the suggestion list or typed free-hand — with no additional
  client-side rule beyond what `issue-crud-forms` already enforces.
- Every existing `issue-crud-forms` and `ui-e2e` behavior (form open/submit/cancel/delete,
  validation, error/revert handling) continues to pass unmodified when this suite runs.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `GET /users` fails (network error or non-2xx response) | Assignee inputs degrade to plain free-text fields with no suggestions; no error banner, no blocked board load or form submission (see BEH-6's rationale for this deliberate scoping of the charter's Observability attribute) | `UI_USER_DIRECTORY_UNAVAILABLE` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because the picker fetches
  `issue-tracker-api`'s documented `GET /users` endpoint only, never a direct database read.
- **Principle:** "Fixture-backed, offline only." — Applies because `GET /users` stays a
  same-origin relative request, same as every other kanban-ui API call.
- **Principle:** "No inbound dependencies." — Applies because this spec adds no dependency on
  any other repo; it only consumes an issue-tracker-api endpoint that already exists within
  this same repo.
- **Existing kanban-ui convention (no build step):** kanban-ui ships as static assets with no
  bundler/framework/preprocessor. Applies because the picker is implemented with a native
  `<datalist>` element and vanilla JS — no new dependency, no component framework.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Datalist markup | Add one shared `<datalist id="user-directory-options">` to `index.html`; add a `list="user-directory-options"` attribute to `#issue-assignee` and `#edit-issue-assignee` | small |
| Fetch + cache User directory | `board.js`: fetch `GET /users` once during `init()`, cache in memory, degrade gracefully (no board-error banner) on failure | small |
| Populate datalist options | `board-logic.js`: pure function building `<option>` HTML from a Users array; `board.js` calls it once to populate the shared datalist | small |
| Test coverage | JS unit tests for the pure option-builder function and the unchanged assignee-field attributes; a real-browser e2e test exercising picking a suggested name into the create-issue form | small |

## Acceptance Criteria

- [ ] `GET /users` is fetched at most once per board load and cached for reuse (BEH-1)
- [ ] Create-issue form's assignee input offers User-directory suggestions via `<datalist>` while remaining the same free-text field (BEH-2)
- [ ] Edit-issue form's assignee input offers the same suggestions and still pre-fills the issue's current assignee value (BEH-3)
- [ ] Picking a suggested name fills the input with no network request at pick time (BEH-4)
- [ ] An arbitrary or blank free-text assignee value is still accepted and submitted — no validation requires a User match (BEH-5)
- [ ] A `GET /users` failure degrades gracefully — plain free-text fields, no error banner, no blocked board or form (BEH-6)
- [ ] No `id`/`name`/`required` attribute change to `#issue-assignee` or `#edit-issue-assignee`
- [ ] All existing `issue-crud-forms` and `ui-e2e` behaviors pass unmodified
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
