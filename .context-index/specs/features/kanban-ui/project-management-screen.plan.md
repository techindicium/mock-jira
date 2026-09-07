# Implementation Plan: Projects management screen

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/project-management-screen.spec.md
> **Review:** PASS (2026-09-07, all bundled reviewers disabled by project governance)
> **Platform:** vanilla JS / HTML / CSS (no build step), served as static assets by issue-tracker-api (FastAPI, Python 3.11)

**Goal:** Populate the `#view-projects` container (from `app-navigation`) with a styled list of all Projects and a simple add-project form calling `POST /projects` — a second, independent entry point onto the same endpoint `board-view`'s switcher-adjacent create-project form already uses. Neither replaces the other.

**Architecture:** Same split as `user-management-screen`: pure functions in `board-logic.js`, fetch/DOM wiring in `board.js`. Maximizes reuse of existing `board-view` logic — `validateProjectForm(key, name)` and `extractProjectSubmitError(status, body)` are reused as-is (identical semantics), with only a new `buildProjectCreatePayload(fields)` added for the optional `description` field this screen's form has that the original create-project form does not.

---

## File Structure

**Create:**
- `tests_js/project-mgmt-beh-1-list-render.test.js` — `buildProjectListHtml`/`buildProjectCreatePayload` unit tests
- `tests_e2e/test_ui_project_management_e2e.py` — real-browser tests for list render, add-project success, empty/whitespace-key block, real duplicate-key error, switcher-visibility-after-reload, fetch-failure error

**Modify:**
- `static/index.html` — populate `#view-projects` (from `app-navigation`) with the ledger panel + add-project form (distinct ids from `board-view`'s own create-project form: `mgmt-project-key`, `mgmt-project-name`, `mgmt-project-description`, `mgmt-create-project-form`, `mgmt-create-project-error`)
- `static/js/board-logic.js` — add `buildProjectListHtml`, `buildProjectCreatePayload` (reuses existing `validateProjectForm`/`extractProjectSubmitError`)
- `static/js/board.js` — add `loadProjectsView`, `renderProjectsList`, `onMgmtCreateProjectSubmit`, wired to `#nav-projects`'s click and `#mgmt-create-project-form`'s submit
- `static/css/board.css` — extend error-banner/panel/form/submit-button selector lists to include the new `#projects-view-error`, `#mgmt-create-project`, `#mgmt-create-project-error` ids

**Reference (read, do not modify):**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` — the existing project switcher/create-project form this screen must not alter
- `app/seed.py`'s `SEED_PROJECT` (`ASSIST`) — used by e2e assertions and the real duplicate-key test
- `tests_e2e/test_ui_project_switcher_e2e.py` — existing suite that must keep passing unmodified, proving the switcher/create-project form are untouched

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Add `buildProjectListHtml`/`buildProjectCreatePayload` to `board-logic.js` | small | unit | app-navigation | 1 modify |
| 2 | Add ledger panel + add-project form markup (distinct ids) | small | unit | app-navigation | 1 modify |
| 3 | CSS for new form/error ids | small | unit | Task 2 | 1 modify |
| 4 | Wire fetch/render/submit into `board.js` | medium | unit (e2e-verified) | Tasks 1-2 | 1 modify |
| 5 | JS unit tests for Task 1's pure functions | small | unit | Task 1 | 1 create |
| 6 | Real-browser e2e coverage, incl. switcher-coexistence regression | medium | e2e | Tasks 1-4 | 1 create |

---

## Task Structure

### Task 1: Pure functions

```javascript
function buildProjectListHtml(projects) { /* ledger-row HTML: key (mono), name, description, escaped */ }
function buildProjectCreatePayload(fields) { /* key+name always, description only when non-blank */ }
```

`validateProjectForm`/`extractProjectSubmitError` (already in `board-logic.js` from `board-view`) are reused unchanged — same 409/422 semantics, same field-blank rule.

### Task 2: Markup

Inside `#view-projects`: `<h1>Projects</h1>`, `#projects-view-error` alert, `.ledger-panel` wrapping `#projects-list`/`#projects-empty`, and `#mgmt-create-project` section with `#mgmt-create-project-form` (`#mgmt-project-key`, `#mgmt-project-name` required, `#mgmt-project-description` optional textarea, submit button, `#mgmt-create-project-error`). Deliberately distinct ids from `board-view`'s `#create-project-form`/`#project-key`/`#project-name`/`#create-project-error` — both forms coexist and independently POST to `/projects`.

### Task 4: `board.js` wiring

Mirrors `user-management-screen`'s Task 4 pattern exactly, calling `BoardLogic.validateProjectForm`/`extractProjectSubmitError`/`buildProjectCreatePayload` instead of the User-specific equivalents. Called from `onNavClick` (`if (view === "projects") loadProjectsView();`).

**Verify:** e2e suite (Task 6).

### Task 6: Real-browser e2e coverage

`tests_e2e/test_ui_project_management_e2e.py` — list renders the seeded `ASSIST` Project with key/name/description; add-project success refreshes list and clears form; whitespace-only key blocks submit client-side (no POST sent); a real duplicate-key `409` against `ASSIST` shows the API's own message inline with input retained; a Project created here is visible in `board-view`'s switcher after a reload (proving the two entry points share state, never conflict); an aborted `/projects` request shows a visible view-level error while the add-project form stays usable.

**Verify:** `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_project_management_e2e.py tests_e2e/test_ui_project_switcher_e2e.py` — all PASS (the second file, unmodified, proves the existing switcher/create-project form are unaffected).

---

## Quality Gates

- Test Suite: `.venv/bin/python3 -m pytest -q` (required)
- Linter: `.venv/bin/ruff check .` (required)
- JS Unit Tests: `node --test tests_js/**/*.test.js` (required)
- E2E Suite: `.venv/bin/python3 -m pytest -q tests_e2e/` (warning-tier, run to full regression per established practice)
- All acceptance criteria from `project-management-screen.spec.md` satisfied
