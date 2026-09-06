---
last-validated-revision: 1
---

# Validation Report: Visual design refresh — dispatch-board identity

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/visual-design-refresh.plan.md
> **Rigor Tier:** quick (resolved via risk policy: risk_level `low` -> `validate_mode: quick`)
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS
- Tests (`.venv/bin/python3 -m pytest -q`): PASS — 107 passed
- Lint (`.venv/bin/ruff check .`): PASS — all checks passed
- JS unit tests (`node --test tests_js/**/*.test.js`): PASS — 65 passed (includes all 8 new
  visual-refresh suites plus every pre-existing board-view/issue-crud-forms suite unmodified)
- E2E smoke (`.venv/bin/python3 -m pytest -q tests_e2e/`, severity: warning): PASS — 31 passed,
  including all 7 real-browser `tests_e2e/test_ui_*.py` tests against the restyled markup,
  unmodified (no locator fix was needed)

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify --spec <path>`: PASS — manifest matches (sha 470d4a0)
- All 12 manifested files confirmed committed to git (`git log --oneline -1 -- <file>` each
  returns exactly one commit)

## Check 1.6: Code-Side Drift — PASS
- `adev verify spec --check-drift`: `{"drifted":false}` — no drift

## Quick-Tier Synthesized Compliance Check (Spec + Constitution) — PASS

Verified by reading the actual files in this worktree (not the plan's checkboxes):
`static/css/board.css`, `static/index.html`, `static/js/board-logic.js`, `static/js/board.js`.

**Acceptance Criteria (12/12 satisfied):**

- [x] Page/board background renders `--ink`; columns render as `--rail` panels with a brass rule
  under each header (BEH-1, BEH-4). `board.css:3-4` declares `--ink: #16261f` / `--rail: #2f4a3e`;
  `board.css` `body{background:var(--ink)}`; `.column{background:var(--rail)}`;
  `.column-header{border-bottom:2px solid var(--stamp-gold-dim)}` (line 154).
- [x] Issue cards render on `--paper` with a left priority stripe colored by priority, a hard
  offset shadow, and sharp/near-sharp corners (BEH-2). `board.css` `.card{background:var(--paper);
  border-radius:2px; box-shadow:2px 2px 0 rgba(0,0,0,.35)}` plus
  `.card[data-priority="high"|"medium"|"low"|"unknown"]` border-left-color rules (lines 199-213).
  `board-logic.js`'s `priorityStripeAttr()` maps unknown/missing priority to `"unknown"` —
  verified by `tests_js/visual-refresh-beh-2-priority-stripe.test.js` (3 tests, all pass).
- [x] Cards show the issue key in mono, summary, sentence-case type+priority meta, and assignee
  (BEH-3). `board-logic.js`'s `buildCardHtml` renders `<p class="card-key">${escapeHtml(issue.key
  || "")}</p>` before the `<h3>` — verified by `tests_js/visual-refresh-beh-3-issue-key.test.js`
  (3 tests: key rendered, missing key renders empty not "undefined", key is escaped).
- [x] Column headers show sentence-case status names with a mono issue-count badge (BEH-4).
  `index.html`'s three columns now read "To do"/"In progress"/"Done" with a
  `<span class="col-count" id="count-todo">` sibling; `board.js`'s `renderColumns()` writes
  `BoardLogic.columnCounts(grouped)` into each badge — verified by
  `tests_js/visual-refresh-beh-4-column-count.test.js` (2 tests).
- [x] Project switcher is styled as a plate/tab control while remaining the same
  `<select id="project-switcher">` (BEH-5). `index.html` wraps the unchanged `<select>` in
  `<div class="switcher-plate">`; verified by `tests_js/visual-refresh-beh-5-switcher-plate.test.js`
  and, more importantly, by the real-browser `tests_e2e/test_ui_project_switcher_e2e.py` passing
  unmodified (the switcher's `change` contract is untouched).
- [x] All three forms restyled to the palette with sharp corners and `--ink-line` borders, no
  field id/name/required-attribute change (BEH-6). Verified by
  `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` (4 tests) and by
  `tests_e2e/test_ui_issue_forms_e2e.py` passing unmodified.
- [x] Keyboard focus remains visible via a deliberate `:focus-visible` style (BEH-7). `board.css`
  declares `:focus-visible{outline:2px solid var(--stamp-gold);outline-offset:2px}` — verified by
  `tests_js/visual-refresh-beh-7-8-accessibility-css.test.js`.
- [x] `prefers-reduced-motion: reduce` disables/reduces every added transition (BEH-8). `board.css`
  declares `@media (prefers-reduced-motion: reduce){*{transition:none!important;animation:none
  !important}}` — same test file as above.
- [x] No existing `board-view`/`issue-crud-forms`/`ui-e2e` DOM hooks broken. `tests_js/` (65
  passed, including every pre-existing suite unmodified) and `tests_e2e/test_ui_*.py` (7/7 passed
  unmodified, no locator fix required) confirm this directly.
- [x] No CDN font or other external network request introduced. `board.css`'s only font-family
  declarations are system-stack chains ending in `sans-serif`/`monospace`; verified by
  `tests_js/visual-refresh-no-cdn-fonts.test.js` (3 tests).
- [x] Paper-on-ink and ink-on-paper text contrast meets WCAG AA. Hand-computed relative luminance
  (WCAG formula) for every new text/surface pairing this refresh introduces: `--paper` text on
  `--rail` (header labels) = 8.18:1; `--ink`-on-`--stamp-gold` (count badge) = 5.06:1;
  `--ink-line` text on `--paper` (card meta/key) = 7.48:1; `--ink-text-on-paper` on `--paper`
  (card titles, form labels) = 14.58:1. All comfortably clear the 4.5:1 AA threshold for normal
  text — the reviewer's SA-1 concern (rail-surface contrast, specifically the count badge) is the
  tightest pairing at 5.06:1 and still passes with margin.
- [x] All quality gates pass — see Check 1 above.
- [x] No constitutional violations introduced (see Constitution section below).

**Constitution Compliance:**
- "Fixture-backed, offline only" — no `<link>` to any external stylesheet/font host, no remote
  `@font-face`, verified by `tests_js/visual-refresh-no-cdn-fonts.test.js` and by direct
  inspection of `index.html`'s `<head>` (only `/static/css/board.css` and same-origin scripts).
- "No inbound dependencies" — no new dependency of any kind added; `package.json`/`requirements*`
  untouched by this refresh.
- No build step introduced — `static/` remains plain HTML/CSS/vanilla JS; no bundler, framework,
  or CSS preprocessor file was added (confirmed: no new config file, no `package.json` changes).
- Architecture boundaries: this refresh touches only kanban-ui's own static assets and tests —
  `issue-tracker-api` (`app/`) and `mcp-server` are untouched, matching the charter's scope
  ("kanban-ui... never touches the database directly").

## Check 11: Visual Verification — SKIPPED-DISABLED
- `governance/validate.yaml`'s `validate.check-11-visual-verification` entry carries
  `enabled: false` project-wide (stale comment notwithstanding: "no UI — mock-jira is a headless
  HTTP API"). Per the registry's disabled-check handling, this check does not run and does not
  contribute to the aggregate verdict.
- Independent of the formal check: Playwright screenshots were taken during implementation
  (board view, create-issue form, edit-issue form) and reviewed for self-critique against the
  spec's Visual Expectations — see the implementation's final commit message for the summary.
  This was a self-review, not a substitute for a dispatched Check 11 subagent.

## Checks 2, 4, 8, 9 — SKIPPED (quick tier)
- Per the resolved `quick` rigor tier, the separate Check 2 (Spec Compliance) and Check 4
  (Constitution Compliance) subagent dispatches are replaced by the single synthesized compliance
  check above. Checks 8 (Boundary Compliance) and 9 (Transition Gates) are skipped per the quick
  tier's execution strategy.

---

**Summary:** 4 checks passed (Check 1, Check 1.5, Check 1.6, synthesized compliance), 1 disabled
(Check 11), 4 skipped per quick tier (Checks 2, 4, 8, 9 — superseded by the synthesized check
where applicable). 0 failed.

---

> **Note for users comparing with historic reports:** This project resolves `validate_mode: quick`
> for `risk_level: low` specs (`.context-index/governance/risk-policies.yaml`). See
> `.context-index/specs/cross-cutting/graduated-rigor-tiers.spec.md` for the tier contract.
