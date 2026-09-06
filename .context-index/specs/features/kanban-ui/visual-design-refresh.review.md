---
last-reviewed-revision: 1
file-sha: b5877c8d1db2ee727d78d87a566907fc6935980aec0cad9105ae6499f7d87492
---

# Architecture Review: visual-design-refresh (kanban-ui)

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Rigor Tier:** quick (resolved via risk policy: risk_level `low` → `review_mode: quick`)

## Reviewers Dispatched

| ID | Name | Mode | Profile | Prompt/Skill |
|----|------|------|---------|--------------|
| quick-synthesized-reviewer | Quick Synthesized Reviewer | subagent | reviewer-capable | plugin:review-specs/quick-synthesized-reviewer-prompt.md |

## Disabled Reviewers

| ID | Reason |
|----|--------|
| structural-architect | no reason given |
| security-reviewer | no reason given |
| consistency-analyzer | no reason given |

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

**Verification note:** Cross-checked the spec's DOM-hook claims against actual code
(`static/index.html`, `static/js/board-logic.js`, `tests_js/`, `tests_e2e/`). All hooks the spec
lists (`#board`, `#board-error`, `#project-switcher`, `.column[data-status]`, `.cards`,
`.card[data-issue-id]`, `#create-issue`, `#edit-issue`, `#create-issue-form`, `#edit-issue-form`,
`#delete-issue`, `draggable`) exist verbatim and match what `tests_e2e/test_ui_*.py` and
`tests_js/` locators use. The "no DOM hooks change" claim is credible.

- **SA-1** (warning) — Location: Postconditions ("Body text against its surface...") / Acceptance
  Criteria (contrast bullet). BEH-1 introduces a third distinct surface, `--rail` (#2F4A3E,
  mid-tone), which holds the column header label and the new mono count badge (BEH-4/Visual
  Expectations). The contrast postcondition and its matching acceptance-criteria bullet only cover
  "ink-on-page chrome" and "ink/dark text on paper cards and forms" — text/badge contrast on the
  `--rail` surface is never required or tested, and is exactly where an AA failure is most
  plausible since `--ink` and `--rail` are both dark tones. Recommendation: add an explicit AA
  contrast requirement for text/badge color against `--rail`, alongside the existing ink/paper
  pairs. **Disposition: accepted as implementation guidance** — column header text and the count
  badge will be verified against `--rail` for WCAG AA during implementation/validation, in
  addition to the ink/paper pairs the spec already names.
- **SEC-1** (warning) — Location: Actionable Task Map ("Card restyle + key" / "Column count
  badge"). `board-logic.js` currently escapes all interpolated card fields via a shared
  `escapeHtml()` helper before `innerHTML` insertion. The spec directs adding the issue key to
  `buildCardHtml` and a count badge to the render path but never states that new interpolated
  content must go through the existing `escapeHtml()` convention; an implementer who inlines the
  key without escaping would reopen an innerHTML injection point the codebase has otherwise
  closed. **Disposition: accepted as implementation guidance** — the issue key and any other new
  interpolated card/badge content will be passed through the existing `escapeHtml()` helper,
  consistent with `summary`/`issue_type`/`priority`/`assignee` today.
- **SA-2** (suggestion) — Location: Error Cases table. Unlike sibling specs, where "Error Cases"
  means real failure/API-error handling, this table's three rows are defensive CSS/rendering
  fallbacks (unknown priority, text overflow, reduced-motion), not errors. **Disposition:
  acknowledged** — these are deliberately defensive/CSS-only fallback conditions for a
  presentation-only spec, not API/network failures; the table is retained as-is for consistency
  with the shared spec template's section name.
- **CON-1** (suggestion) — Location: Preconditions vs. BEH-4/Visual Expectations. Current markup
  renders column headers in title case ("To Do"); BEH-4 requires sentence case ("To do"). No test
  asserts on this exact casing, so no break risk, but the "presentation-only, no DOM/content
  change" framing in Preconditions is imprecise since visible text content does change where a
  behavior calls for it. **Disposition: acknowledged** — Preconditions describes structural DOM
  hooks (ids/classes/data-attributes), not visible text content; visible text/casing changes
  (BEH-4's sentence case) are an intended, in-scope part of this spec.

No blockers. The spec stays within charter scope (kanban-ui, v1.2 milestone, "Visual design
refresh" capability), introduces no new dependency or endpoint, and does not conflict with any
sibling spec, ADR, or the constitution. Risk level (`low`) and rigor tier (`quick`) match the
low-blast-radius nature of a CSS/vanilla-JS-only restyle of already-validated UI specs.

---

## Summary

**Total findings:** 4 (0 blockers, 2 warnings, 2 suggestions)
**Action required:** None blocking. Both warnings (SA-1: rail-surface contrast, SEC-1: escape new
interpolated content) are carried forward as explicit implementation requirements — see the
"Disposition" notes above — and will be checked during `/adev:implement` and `/adev:validate`.

**Governance note:** All three bundled reviewers (structural-architect, security-reviewer,
consistency-analyzer) are disabled project-wide per `governance/review.yaml`, per this repo's
deliberately lightweight governance posture. No `spec-to-plan` transition `approver_role` is
defined in `governance/gates.yaml` (`transitions: {}`).
