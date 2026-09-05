---
last-reviewed-revision: 1
file-sha: 7adf49bb125061905869eb2f62f47adbd12f2f16bae3148576749d22bcecbd82
rigor-tier: quick
---

# Architecture Review: issue-lifecycle

> **Date:** 2026-09-04
> **Spec:** .context-index/specs/features/issue-tracker-api/issue-lifecycle.spec.md
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Verdict:** PASS_WITH_NOTES

## Rigor Tier

Resolved: **quick** (source: risk policy — `risk_level: medium` frontmatter maps to
`policies.medium.review_mode: quick` in `.context-index/governance/risk-policies.yaml`; no
explicit `--tier` or routing override was supplied). Per the graduated-rigor-tiers contract,
`quick` still runs the full gate — a single synthesized reviewer stands in for the three
specialist passes.

## Reviewers Dispatched

| ID | Name | Mode | Profile | Prompt/Skill |
|----|------|------|---------|--------------|
| quick-synthesized-reviewer | Quick Synthesized Reviewer | subagent | reviewer-capable | plugin:review-specs/quick-synthesized-reviewer-prompt.md |

## Disabled Reviewers

Not applicable to this run's dispatch decision (quick tier bypasses the reviewer registry's
per-reviewer dispatch loop entirely), but the project's materialized `governance/review.yaml`
disables all three bundled full-tier specialists, each with no stated reason
(`DISABLED_WITHOUT_REASON` advisory from `adev governance reviewers --json`):

| ID | Reason |
|----|--------|
| structural-architect | no reason given |
| security-reviewer | no reason given |
| consistency-analyzer | no reason given |

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

- **SA-1** — *warning* — Location: Behaviors (BEH-7) / Postconditions. BEH-7 says PATCH accepts
  "one or more mutable fields" but never states whether `project_id` is among them. The charter's
  key invariant ties an Issue's key to `<project.key>-<sequence>`, and this spec's Postconditions
  state "An Issue's key never changes once assigned." If `project_id` were patchable, an Issue's
  key would silently no longer match its owning project's key prefix — an unresolved conflict
  between "mutable fields" and the key-immutability invariant. If `project_id` is not patchable,
  the spec should say so explicitly rather than leaving it implicit. Recommendation: add an
  explicit statement (behavior or error case) that `project_id` (and `key`) are immutable via
  PATCH — e.g., "PATCH /issues/{id} attempting to change project_id or key -> rejected" or
  "project_id is not a mutable field; PATCH ignores/rejects it."
- **SA-2** — *suggestion* — Location: Behaviors (BEH-8) vs. Error Cases table. The Error Cases
  table generalizes 422 to "Invalid status, issue_type, or priority value on create/patch," but
  the Behaviors section only enumerates the status case for PATCH (BEH-8); there is no explicit
  BEH for an invalid `issue_type`/`priority` on PATCH, creating a minor asymmetry between the
  behavior list and the error table (and the Acceptance Criteria, which only checks BEH-8).
  Recommendation: either add a BEH covering invalid `issue_type`/`priority` on PATCH, or note in
  BEH-8 that the same rejection applies to all three enum fields.

Not flagged (reviewed, no issue): the endpoint set stays within charter scope (full Issue CRUD);
the per-project key-sequence derivation is unambiguous about starting value and increment
direction; error-code naming (`ISSUE_PROJECT_NOT_FOUND`, `ISSUE_NOT_FOUND`, `VALIDATION_ERROR`,
`MALFORMED_JSON`) mirrors the sibling `project-management` spec's `PROJECT_*` convention; no
auth is in scope per charter, consistent with the sibling spec's precondition; enum/required-
field validation is specified for all mutating endpoints; no injection-relevant free-text field
is treated as executable; the free-form kanban status transition rule (no enforced workflow
ordering) is respected; the dependency on the already-implemented and validated
`project-management` spec's endpoints is correctly stated as a precondition.

---

## Summary

**Total findings:** 2 (0 blockers, 1 warning, 1 suggestion)
**Action required:** No blockers — the spec is ready for planning. Consider folding SA-1 (and
optionally SA-2) into a spec revision before or during implementation to close the
`project_id`-mutability ambiguity, but neither is required to unblock `/adev:plan`.

**Governance note:** `.context-index/governance/gates.yaml` `transitions` is empty — no
`spec-to-plan` `approver_role` is configured, so no human-approval footer applies here.
