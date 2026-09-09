---
last-reviewed-revision: 1
file-sha: 855246acf7a9b9138a39d7248a0dcc6a06cbf7e1b470815269252b2d80600246
---

# Architecture Review: backlog-view

> **Date:** 2026-09-09
> **Spec:** .context-index/specs/features/kanban-ui/backlog-view.spec.md
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Tier:** quick (routing signal: low blast-radius, additive-only, no API contract change)

## Reviewers Dispatched

| ID | Name | Mode | Profile | Prompt/Skill |
|----|------|------|---------|--------------|
| quick-synthesized-reviewer | Quick Synthesized Reviewer | subagent | general-purpose (read-only instructed) | plugin:review-specs/quick-synthesized-reviewer-prompt.md |

## Disabled Reviewers

(Not applicable — quick tier bypasses the full-tier registry, which has all three bundled reviewers disabled by this project's own governance/review.yaml.)

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

### Structural

**SA-1** — Severity: `suggestion`
Location: Behaviors, BEH-3
Finding: BEH-3 refers to "the filter bar" as if already established, but no behavior explicitly states where/when the filter bar itself appears (persistently visible across both Board and Backlog views, vs. rendered per-view).
Recommendation: Add a short behavior or precondition clause establishing the filter bar's placement/visibility scope before BEH-3 references it.

### Security

No findings. The spec is explicitly read-only/client-side (no new endpoint, no query params, no write path), filter inputs are constrained `<select>` values rather than free text, and no auth/credential surface is touched — consistent with the charter's "no real auth, localhost-only" posture and the constitution's fixture-only/offline principle.

### Consistency

**CON-1** — Severity: `warning`
Location: BEH-3/BEH-4/BEH-6 vs. board-view.spec.md
Finding: This spec asserts filtering applies to "both the Backlog view and the Board view" (BEH-3) and that the zero-match state applies to "the affected view" including Board (BEH-6), meaning Board's rendering behavior changes. But board-view.spec.md is `status: validated` with a locked source-manifest, and its own Behavioral Contract makes no mention of filters — its stated contract is now incomplete relative to what the shipped Board view will actually do.
Recommendation: Either add a forward-reference/amendment note in board-view.spec.md acknowledging the filter bar affects its rendering, or scope this spec's task map to touch board-view.spec.md alongside implementation so the two specs don't diverge from shipped behavior.

**CON-2** — Severity: `suggestion`
Location: Charter Out of Scope vs. Capability Map (both revision 38)
Finding: The charter's Out-of-Scope list still reads "Complex search/filter beyond 'which project' (no JQL-style query builder)," while the same revision's Capability Map now includes an assignee/type/priority filter bar. Not truly contradictory, but the Out-of-Scope wording wasn't refreshed to draw that line explicitly.
Recommendation: When convenient, clarify the Out-of-Scope entry to distinguish simple field-equality filters (in scope) from query-builder-style search (out of scope).

---

## Summary

**Total findings:** 3 (0 blockers, 1 warning, 2 suggestions)
**Action required:** None blocking. Recommended before/during implementation: note the filter bar's placement in a precondition (SA-1), and add a forward-reference in board-view.spec.md so its contract doesn't silently drift out of sync with the shipped filtering behavior (CON-1). CON-2 is optional polish.
