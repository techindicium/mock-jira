# Implementation Plan: App navigation shell (sidebar)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/app-navigation.spec.md
> **Review:** PASS (2026-09-07, all bundled reviewers disabled by project governance)
> **Platform:** vanilla JS / HTML / CSS (no build step), served as static assets by issue-tracker-api (FastAPI, Python 3.11)

**Goal:** Add a persistent left-hand sidebar (Board / Users / Projects) that toggles client-side view containers, with the existing board becoming the "Board" view's unchanged content.

**Architecture:** `static/index.html` gains an `.app-shell` wrapper: a `<nav class="sidebar">` of three `<button>` nav items, and an `.app-main` holding three `<section class="view">` containers (`#view-board` — wraps every existing board element unchanged, `#view-users`, `#view-projects` — initially empty, populated by the next two specs). `board.js` gains a small `showView(name)`/`onNavClick` pair that toggles `hidden` and an `active` class; no router library, no new dependency. Styling reuses existing tokens only (`--rail`, `--rail-light`, `--stamp-gold`).

---

## File Structure

**Create:**
- `tests_js/navigation-beh-1-sidebar-markup.test.js` — markup assertions (sidebar exists, sentence case, existing DOM hooks preserved, new view containers exist hidden)
- `tests_e2e/test_ui_navigation_e2e.py` — real-browser tests for default view, tab switching, state preservation, keyboard focus

**Modify:**
- `static/index.html` — wrap existing board markup in `#view-board`; add `.sidebar` nav and empty `#view-users`/`#view-projects` containers
- `static/js/board.js` — add `showView`, `onNavClick`, nav click listeners
- `static/css/board.css` — add `.app-shell`, `.sidebar`, `.nav-item`(`.active`), `.app-main`, `.view h1` rules; move body padding into `.app-main` (background stays on `body`)

**Reference (read, do not modify):**
- `.context-index/specs/features/kanban-ui/board-view.spec.md`, `issue-crud-forms.spec.md`, `user-picker.spec.md`, `visual-design-refresh.spec.md` — existing DOM hooks this shell must preserve verbatim
- `tests_e2e/test_ui_project_switcher_e2e.py`, `test_ui_issue_forms_e2e.py` — existing suites that must keep passing unmodified against the relocated (not renamed) markup

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Wrap existing board markup in view containers + add sidebar | medium | unit | — | 1 modify (index.html) |
| 2 | Sidebar/shell CSS | small | unit | Task 1 | 1 modify (board.css) |
| 3 | Tab-switch JS (`showView`/`onNavClick`) | small | unit | Task 1 | 1 modify (board.js) |
| 4 | Markup unit tests | small | unit | Task 1 | 1 create |
| 5 | Real-browser e2e coverage | medium | e2e | Tasks 1-3 | 1 create |
| 6 | Full regression pass (existing tests_js/tests_e2e unmodified) | small | unit+e2e | Tasks 1-5 | 0 create/modify |

---

## Task Structure

### Task 1: Wrap existing board markup in view containers + add sidebar

Add `<div class="app-shell"><nav class="sidebar">...3 nav buttons...</nav><div class="app-main">` wrapping the existing `<header>`...`<datalist>` block (now inside `<section id="view-board" class="view">`), plus two new empty `<section id="view-users" class="view" hidden>`/`<section id="view-projects" class="view" hidden>` siblings. No existing id/class/data-attribute is renamed or removed — only relocated one level deeper.

**Verify:** `node --test tests_js/**/*.test.js` — all existing suites (`visual-refresh-*`, `user-picker-*`, `beh-*`, `issue-crud-*`) still pass unmodified, since they only regex-match substrings, never assert DOM nesting.

### Task 2: Sidebar/shell CSS

`.app-shell` (flex row), `.sidebar` (fixed-width, `--rail` background, border-right `--ink-line`), `.nav-item`/`.nav-item.active` (left accent `--stamp-gold`, background `--rail-light`), `.app-main` (carries the padding `body` used to have). `body`'s own `background: var(--ink)` declaration is left untouched (required by `visual-refresh-beh-1-design-tokens.test.js`).

**Verify:** `node --test tests_js/visual-refresh-beh-1-design-tokens.test.js` still passes (body still declares `background: var(--ink)`).

### Task 3: Tab-switch JS

```javascript
const NAV_VIEWS = ["board", "users", "projects"];

function showView(name) {
  for (const view of NAV_VIEWS) {
    const section = document.getElementById(`view-${view}`);
    if (section) section.hidden = view !== name;
    const navBtn = document.getElementById(`nav-${view}`);
    if (navBtn) {
      navBtn.classList.toggle("active", view === name);
      if (view === name) navBtn.setAttribute("aria-current", "page");
      else navBtn.removeAttribute("aria-current");
    }
  }
}

function onNavClick(event) {
  const view = event.currentTarget.dataset.view;
  if (!NAV_VIEWS.includes(view)) return; // UI_NAV_VIEW_NOT_FOUND: defensive no-op
  showView(view);
  if (view === "users") loadUsersView();
  if (view === "projects") loadProjectsView();
}
```

`loadUsersView`/`loadProjectsView` are stubs at this point in the sequence (populated by the dependent specs); calling them defensively is harmless once those specs land, and this spec's own e2e suite does not depend on them existing.

**Verify:** e2e suite (Task 5).

### Task 5: Real-browser e2e coverage

`tests_e2e/test_ui_navigation_e2e.py` — default view, tab switch hides others, returning to Board issues no `/issues` refetch, nav items keyboard-focusable.

**Verify:** `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_navigation_e2e.py` — PASS.

### Task 6: Full regression pass

Run every gate (`pytest -q`, `ruff check .`, `node --test tests_js/**/*.test.js`, `pytest -q tests_e2e/`) and confirm the full pre-existing suite (46 tests) plus this spec's new coverage all pass, with zero locator changes needed (markup was relocated, not renamed).

---

## Quality Gates

- Test Suite: `.venv/bin/python3 -m pytest -q` (required)
- Linter: `.venv/bin/ruff check .` (required)
- JS Unit Tests: `node --test tests_js/**/*.test.js` (required)
- E2E Suite: `.venv/bin/python3 -m pytest -q tests_e2e/` (warning-tier, run to full regression per established practice)
- All acceptance criteria from `app-navigation.spec.md` satisfied
