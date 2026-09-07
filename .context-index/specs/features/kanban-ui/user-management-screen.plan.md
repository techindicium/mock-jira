# Implementation Plan: Users management screen

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/user-management-screen.spec.md
> **Review:** PASS (2026-09-07, all bundled reviewers disabled by project governance)
> **Platform:** vanilla JS / HTML / CSS (no build step), served as static assets by issue-tracker-api (FastAPI, Python 3.11)

**Goal:** Populate the `#view-users` container (from `app-navigation`) with a styled list of all Users and a simple add-user form calling `POST /users`, surfacing the API's real error messages.

**Architecture:** Same split as every other kanban-ui capability: pure render/validate/payload functions live in `board-logic.js` (unit-tested), fetch/DOM wiring lives in `board.js` (e2e-verified). The list reuses the `.ledger-panel`/`.ledger-row` treatment (paper surface, `--ink-line` hairline dividers) rather than a generic HTML table. `GET /users` is refetched every time the Users nav item is clicked — no caching layer, deliberately independent of `user-picker.spec.md`'s separate load-once-at-board-init cache.

---

## File Structure

**Create:**
- `tests_js/user-mgmt-beh-1-list-render.test.js` — `buildUserListHtml` unit tests
- `tests_js/user-mgmt-beh-4-5-validate-and-errors.test.js` — `validateUserForm`/`extractUserSubmitError`/`buildUserCreatePayload` unit tests
- `tests_e2e/test_ui_user_management_e2e.py` — real-browser tests for list render, add-user success, empty/whitespace-name block, real duplicate-email error, fetch-failure error

**Modify:**
- `static/index.html` — populate `#view-users` (from `app-navigation`) with the ledger panel + add-user form
- `static/js/board-logic.js` — add `buildUserListHtml`, `validateUserForm`, `extractUserSubmitError`, `buildUserCreatePayload`
- `static/js/board.js` — add `loadUsersView`, `renderUsersList`, `onCreateUserSubmit` and wire them to `#nav-users`'s click (via `app-navigation`'s `onNavClick`) and `#create-user-form`'s submit
- `static/css/board.css` — extend the existing error-banner/panel/form/submit-button selector lists to include the new `#users-view-error`, `#create-user`, `#create-user-error` ids

**Reference (read, do not modify):**
- `.context-index/specs/features/issue-tracker-api/user-directory.spec.md` — `GET`/`POST /users` shapes and error codes (`USER_EMAIL_DUPLICATE`, `VALIDATION_ERROR`)
- `static/js/board.js`'s existing `onCreateProjectSubmit`/`extractProjectSubmitError` — the pattern this form's handler mirrors
- `app/seed.py`'s `SEED_USERS` — 4 real seeded Users used by e2e assertions

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Add pure render/validate/payload functions to `board-logic.js` | medium | unit | app-navigation | 1 modify |
| 2 | Add ledger panel + add-user form markup | small | unit | app-navigation | 1 modify |
| 3 | CSS for ledger list + new form/error ids | small | unit | Task 2 | 1 modify |
| 4 | Wire fetch/render/submit into `board.js` | medium | unit (e2e-verified) | Tasks 1-2 | 1 modify |
| 5 | JS unit tests for Task 1's pure functions | small | unit | Task 1 | 2 create |
| 6 | Real-browser e2e coverage | medium | e2e | Tasks 1-4 | 1 create |

---

## Task Structure

### Task 1: Pure functions in `board-logic.js`

```javascript
function buildUserListHtml(users) { /* ledger-row HTML per User, escaped, "—" fallback */ }
function validateUserForm(name) { /* trims, requires non-blank name */ }
function extractUserSubmitError(status, body) { /* 409 -> email field, 422 -> form field */ }
function buildUserCreatePayload(fields) { /* name always, email/role only when non-blank */ }
```

Mirrors `buildCardHtml`/`validateProjectForm`/`extractProjectSubmitError`/`buildIssueCreatePayload`'s existing style exactly (escape via `escapeHtml`, optional-field omission via truthy+trim checks).

### Task 2: Markup

Inside `#view-users`: `<h1>Users</h1>`, `#users-view-error` alert, `.ledger-panel` wrapping `#users-list`/`#users-empty`, and `#create-user` section with `#create-user-form` (`#user-name` required, `#user-email`, `#user-role`, submit button, `#create-user-error`).

### Task 4: `board.js` wiring

```javascript
async function loadUsersView() {
  clearUsersViewError();
  let users;
  try { users = await fetchJson("/users"); }
  catch (err) { showUsersViewError(BoardLogic.formatFetchError("Loading users", err)); return; }
  renderUsersList(users);
}

async function onCreateUserSubmit(event) {
  event.preventDefault();
  const { valid, errors } = BoardLogic.validateUserForm(nameInput.value);
  if (!valid) { showUserFormError(Object.values(errors)[0]); return; }
  // POST /users via buildUserCreatePayload; 409/422 -> showUserFormError with body.message;
  // network error -> showUsersViewError; success -> clear inputs, loadUsersView()
}
```

Called from `app-navigation`'s `onNavClick` (`if (view === "users") loadUsersView();`) — no separate init-time fetch, satisfying BEH-1's "fetch on switch" contract without a caching layer.

**Verify:** e2e suite (Task 6).

### Task 6: Real-browser e2e coverage

`tests_e2e/test_ui_user_management_e2e.py` — list renders 4 seeded Users with name/email/role; add-user success refreshes list and clears form; whitespace-only name blocks submit client-side (no POST sent); a real duplicate-email `409` against a seeded user's email shows the API's own message inline with input retained; an aborted `/users` request shows a visible view-level error while the add-user form stays usable.

**Verify:** `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_user_management_e2e.py` — PASS.

---

## Quality Gates

- Test Suite: `.venv/bin/python3 -m pytest -q` (required)
- Linter: `.venv/bin/ruff check .` (required)
- JS Unit Tests: `node --test tests_js/**/*.test.js` (required)
- E2E Suite: `.venv/bin/python3 -m pytest -q tests_e2e/` (warning-tier, run to full regression per established practice)
- All acceptance criteria from `user-management-screen.spec.md` satisfied
