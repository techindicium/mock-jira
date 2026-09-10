---
last-reviewed-revision: 1
file-sha: 991dea825ccdff6061549288766f9c673e56d8e993f39f382d176d3ac37e3e2e
---

# Architecture Review: issue-comments

> **Date:** 2026-09-09
> **Spec:** .context-index/specs/cross-cutting/issue-comments.spec.md
> **Charter:** .context-index/specs/cross-cutting/issue-comments/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Tier:** quick (routing signal: purely additive, no existing-endpoint contract change)

## Reviewers Dispatched

| ID | Name | Mode | Profile | Prompt/Skill |
|----|------|------|---------|--------------|
| quick-synthesized-reviewer | Quick Synthesized Reviewer | subagent | general-purpose (read-only instructed) | plugin:review-specs/quick-synthesized-reviewer-prompt.md |

## Disabled Reviewers

(Not applicable — quick tier bypasses the full-tier registry, which has all three bundled reviewers disabled by this project's own governance/review.yaml.)

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

**SA-1** — Severity: `warning` — **Addressed.**
Location: Behaviors, BEH-1/BEH-2
Finding: Neither behavior stated the HTTP response status code, unlike sibling spec `issue-lifecycle.spec.md`.
Resolution: BEH-1 now states `201`, BEH-2 now states `200`.

**SA-2** — Severity: `warning` — **Addressed.**
Location: Error Cases, kanban-ui row
Finding: "network or non-2xx" was undifferentiated; `issue-crud-forms.spec.md` treats 404-on-stale-Issue specially.
Resolution: Split into two rows — a `404` (`UI_ISSUE_NOT_FOUND`, closes the form and refreshes) and a generic failure (`UI_FETCH_FAILED`), matching the `issue-crud-forms.spec.md` precedent.

**CON-1** — Severity: `warning` — **Addressed.**
Location: Error Cases table structure
Finding: Table lacked an Error Code column, unlike every sibling spec in the three affected modules.
Resolution: Added an Error Code column with `VALIDATION_ERROR`, `ISSUE_NOT_FOUND`, `UI_ISSUE_NOT_FOUND`, `UI_FETCH_FAILED`, `MCP_UPSTREAM_ERROR`.

**CON-2** — Severity: `warning` — **Addressed.**
Location: Module Impact Map vs. kanban-ui/mcp-server charters
Finding: issue-tracker-api's charter was fully updated with the Comment entity/endpoints, but kanban-ui's and mcp-server's charters had zero mention of the new capability, despite both being named as affected modules.
Resolution: Added a Capability Map row + two Interface Contract rows to `kanban-ui/charter.md` (revision → 40) and `mcp-server/charter.md` (revision → 21), each referencing this cross-cutting charter as the owner.

No structural blockers, no ADR conflicts, no security gaps beyond what the charter already scopes (no auth, plain-text body, HTML-escape-on-render, consistent with every other free-text field in this project).

---

## Summary

**Total findings:** 4 (0 blockers, 4 warnings, 0 suggestions)
**Action required:** None — all four warnings were addressed directly in the spec and the two affected module charters before finalizing this review.
