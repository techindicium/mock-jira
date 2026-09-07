---
last-validated-revision: 1
---

# Validation Report: App navigation shell (sidebar)

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/features/kanban-ui/app-navigation.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/app-navigation.plan.md
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS
- Test: `.venv/bin/python3 -m pytest -q` — PASS (135 passed)
- Lint: `.venv/bin/ruff check .` — PASS (clean)
- JS Unit Tests: `node --test tests_js/**/*.test.js` — PASS (95 passed, was 74)
- E2E Smoke Suite: `.venv/bin/python3 -m pytest -q tests_e2e/` — PASS (62 passed, was 46; warning-tier, non-blocking)

## Check 1.5: Source Manifest Verification — PASS
`adev source-manifest verify --spec app-navigation.spec.md` → PASS (sha: d6332ea). Also re-stamped
and re-verified PASS on all four sibling specs sharing the touched shared files
(board-view, issue-crud-forms, visual-design-refresh, user-picker) — all clean, no drift.

## Check 2: Spec Compliance — SKIPPED-DISABLED
Disabled by this project's governance (`governance/validate.yaml`: `validate.check-2-spec-compliance`
`enabled: false` — "subagent-review — dropped for lightweight validation"). Equivalent coverage:
`/adev:review-specs` (trivial PASS, all bundled reviewers disabled) plus the manual acceptance-criteria
walkthrough below.

Manual acceptance-criteria walkthrough (self-attested, since Check 2 is disabled):
- Sidebar renders three nav items, "Board" active by default (BEH-1) — `static/index.html` lines
  11-15 (`<nav class="sidebar">`...`nav-board` with class `active`); e2e
  `test_board_is_active_view_by_default` PASS.
- Clicking Users/Projects shows that view, hides others, no reload (BEH-2) — `static/js/board.js`
  `showView`/`onNavClick`; e2e `test_clicking_users_nav_shows_users_view_and_hides_board`,
  `test_clicking_projects_nav_shows_projects_view_and_hides_others` PASS.
- Returning to Board shows unchanged prior state, no refetch (BEH-3) — e2e
  `test_returning_to_board_shows_prior_state_without_refetch` PASS (asserts zero `/issues` requests).
- Active nav item visually distinguished via existing tokens only (BEH-4) — `static/css/board.css`
  `.nav-item.active` uses `--rail-light`/`--stamp-gold` only; visually confirmed via screenshot.
- Nav items keyboard-focusable with visible focus (BEH-5) — native `<button>` elements, global
  `:focus-visible` rule already covers them; e2e `test_nav_items_are_keyboard_focusable` PASS.
- `prefers-reduced-motion` guard (BEH-6) — pre-existing global `@media (prefers-reduced-motion: reduce)`
  rule in `board.css` applies to the new `.nav-item` transition (universal selector).
- All existing DOM hooks preserved, relocated not renamed — `tests_js/navigation-beh-1-sidebar-markup.test.js`
  PASS; every pre-existing `tests_js/`/`tests_e2e/test_ui_*.py` suite passes unmodified.

## Check 4: Constitution Compliance — SKIPPED-DISABLED
Disabled by governance (`validate.check-4-constitution` `enabled: false`). No new dependency, no
network call beyond same-origin, no build step introduced — consistent with the constitution's
"No inbound dependencies" and "Fixture-backed, offline only" principles.

## Check 8: Boundary Compliance — SKIP
`adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared"}`.

## Check 9: Transition Gates — SKIP
`adev gate transitions --transition implement-to-validate --spec app-navigation.spec.md --json` →
`{"verdict":"SKIP","reason":"no transitions configured"}`.

## Check 11: Visual Verification — SKIPPED-DISABLED
Disabled by governance (`validate.check-11-visual-verification` `enabled: false`). Informal manual
visual verification performed anyway via a real headless-Chromium screenshot pass (Board/Users/Projects
views) confirming the dispatch-board palette, ledger-panel treatment, and active-nav accent render as
specified; no layout breakage observed.

---

**Summary:** 4 checks ran (1, 1.5, 8, 9) — all PASS/SKIP-as-expected. 3 checks SKIPPED-DISABLED
per project governance (2, 4, 11), with equivalent coverage noted above.
