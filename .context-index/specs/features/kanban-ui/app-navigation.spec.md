---
charter: kanban-ui
status: validated
risk_level: low
milestone: v1.4
revision: 1
charter-revision: 24
created: 2026-09-07
updated: 2026-09-07
kind: behavioral
source-manifest:
  sha: "d6332ea"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board.js
    - tests_e2e/test_ui_navigation_e2e.py
    - tests_js/navigation-beh-1-sidebar-markup.test.js
  computed-at: "2026-09-07T11:26:15.463Z"
---

# Live Spec: App navigation shell (sidebar)

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

<!-- This spec adds a persistent navigation shell around the existing board — it is a
     prerequisite for the user-management-screen and project-management-screen specs, which
     each render inside a view container this spec defines. It changes no existing board-view,
     issue-crud-forms, user-picker, or visual-design-refresh behavior; it only wraps that
     existing markup in a new container and adds two new (initially empty) view containers
     alongside it. -->

### Preconditions

- The `board-view`, `issue-crud-forms`, `visual-design-refresh`, and `user-picker` specs are
  implemented and validated — their existing markup (header, project switcher, columns,
  create/edit-issue forms, the datalist) becomes the content of this spec's "Board" view
  container, unchanged in behavior, id, class, or data attribute.
- The dispatch-board palette tokens (`--ink`, `--rail`, `--paper`, `--stamp-gold`, `--ink-line`,
  etc.) already exist in `board.css`'s `:root` (from `visual-design-refresh`) and are reused
  as-is for the sidebar — no new palette is introduced.
- No build step is introduced — `static/` stays plain HTML/CSS/vanilla JS, same as every prior
  kanban-ui capability.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the page loads, **then** a persistent left-hand sidebar renders with
  three nav items ("Board", "Users", "Projects" — sentence case, no icons required), the
  "Board" item is active by default, and the existing board content (header, switcher, columns,
  forms) renders inside the visible "Board" view container exactly as `board-view` and
  `issue-crud-forms` already specify it.
- **BEH-2** — **When** the viewer clicks the "Users" or "Projects" nav item, **then** that
  item's view container becomes visible, every other view container (including "Board") is
  hidden, and no page reload occurs.
- **BEH-3** — **When** the viewer clicks the "Board" nav item after visiting another view,
  **then** the Board view container becomes visible again showing exactly the state it held
  before the switch (selected Project, loaded Issues, any open form) — switching views never
  re-fetches or discards in-memory Board state on its own.
- **BEH-4** — **When** a nav item is the currently active view, **then** it is visually
  distinguished from the other two (e.g. a left accent bar and/or background shift) using only
  the existing palette tokens — never a new color.
- **BEH-5** — **When** any nav item receives keyboard focus, **then** a visible
  `:focus-visible` outline is shown, and every nav item is reachable and activatable via
  keyboard alone (native `<button>` semantics — Tab to focus, Enter/Space to activate).
- **BEH-6** — **When** the viewer's browser/OS reports `prefers-reduced-motion: reduce`,
  **then** any transition this shell adds to the active-item indicator or view switch is
  disabled or reduced to near-zero duration.

### Postconditions

- Exactly one view container is visible at any time; the other two always carry the `hidden`
  attribute.
- Every element id, class name, and data attribute that `board-view.spec.md`,
  `issue-crud-forms.spec.md`, `user-picker.spec.md`, `visual-design-refresh.spec.md`, and
  `ui-e2e.spec.md` depend on (`#board`, `#board-error`, `#project-switcher`,
  `.column[data-status]`, `.card[data-issue-id]`, `#create-issue`, `#edit-issue`,
  `#create-project-form`, etc.) is unchanged after this shell is added — those elements are
  relocated inside a new `#view-board` container, never renamed or removed.
- Switching away from and back to the Board view never triggers a network request by itself —
  only user actions already defined by `board-view`/`issue-crud-forms` (initial load, project
  switch, form submit) do.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| A nav item's target view container is missing from the DOM (defensive — should never happen with this spec's own markup) | The click is a no-op; the currently visible view stays visible; no uncaught exception reaches the console in a way that breaks the rest of the page | `UI_NAV_VIEW_NOT_FOUND` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because this shell adds no new
  network calls of its own; it is pure client-side show/hide over markup whose own API calls
  are already governed by `board-view`/`issue-crud-forms`.
- **Principle:** "Fixture-backed, offline only." — Applies because no new request, remote
  asset, or dependency is introduced.
- **Existing kanban-ui convention (no build step):** kanban-ui ships as static assets with no
  bundler/framework/preprocessor. Applies because the tab switch is implemented with a small
  vanilla-JS function over plain `<section>` containers — no router library.
- **Principle:** "No inbound dependencies." — Applies because this spec adds no dependency on
  any other repo; it only restructures this module's own static assets.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Sidebar markup + CSS | Add a `<nav class="sidebar">` with three nav buttons, styled from `--rail`/`--stamp-gold` tokens | small |
| View container wrapper | Wrap the existing board markup in `<section id="view-board" class="view">`; add empty `<section id="view-users" class="view" hidden>` and `<section id="view-projects" class="view" hidden>` containers for the next two specs to populate | medium |
| Tab-switch JS | A `showView(name)` function toggling `hidden` on the three view containers and the `active` class on the three nav buttons | small |
| Focus/motion accessibility | `:focus-visible` styling on nav items; guard any added transition under `prefers-reduced-motion` | small |

## Visual Expectations

- **Sidebar:** fixed-width left column, `--rail` background, matching the existing column-header
  treatment. Nav items in sentence case, no ALL-CAPS, no icons required.
- **Active indicator:** a left accent bar (e.g. `--stamp-gold`) and/or a background shift (e.g.
  `--rail-light`) on the active nav item — reusing existing tokens only.
- **Layout:** sidebar sits to the left of the existing board content; the board's own layout
  (columns, switcher, forms) is otherwise unchanged.
- **Focus:** the same visible 2px outline convention already established for buttons/inputs.
- **Motion:** any hover/active-state transition is disabled under `prefers-reduced-motion: reduce`.
- **Mobile (< 768px):** out of scope, per the parent charter's existing exclusion of
  mobile-responsive polish.

## Acceptance Criteria

- [ ] Sidebar renders three nav items; "Board" is active/visible by default (BEH-1)
- [ ] Clicking "Users"/"Projects" shows that view and hides all others, no reload (BEH-2)
- [ ] Returning to "Board" shows its unchanged prior state (BEH-3)
- [ ] The active nav item is visually distinguished using existing palette tokens only (BEH-4)
- [ ] Every nav item is keyboard-focusable and -activatable with a visible focus outline (BEH-5)
- [ ] `prefers-reduced-motion: reduce` disables/reduces any added transition (BEH-6)
- [ ] No existing `board-view`/`issue-crud-forms`/`user-picker`/`visual-design-refresh`/`ui-e2e` DOM hook (id, class, data attribute) is broken — `tests_js/` and `tests_e2e/test_ui_*.py` pass unmodified or with locator-only fixes, never a weakened assertion
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
