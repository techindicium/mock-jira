---
last-reviewed-revision: 1
file-sha: 909d1d1b666c8bb256ef636f8094b5bd4db82122788daa7afd772d99bc36506b
---

# Architecture Review: issue-crud-forms

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Rigor Tier:** quick (resolved from `risk_level: medium` via `.context-index/governance/risk-policies.yaml` → `policies.medium.review_mode: quick`)

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

> Note: these three bundled reviewers are disabled project-wide in `.context-index/governance/review.yaml`
> ("all three bundled reviewers off — as lightweight as review gets"). Because the resolved rigor
> tier for this spec is `quick`, they were not the dispatch candidates in this run regardless —
> the quick tier dispatches the single synthesized reviewer below instead of the three specialists.
> `adev governance reviewers --json` additionally raised a `DISABLED_WITHOUT_REASON` warning for
> each of the three entries (see Warnings below).

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

**Structural lens:**
- **SA-1** — Severity: warning. Location: Behaviors (BEH-6) / Error Cases. BEH-6 and the
  "missing required field" error case reference "required fields" for the create/edit forms, but
  neither this spec nor the parent charter enumerates which Issue fields are required, making the
  validation unverifiable and implementation-dependent as written. Recommendation: enumerate the
  required fields here, or add an explicit precondition cross-referencing `issue-tracker-api`'s
  `issue-lifecycle` spec as the source of truth for required-field definitions.
- **SA-2** — Severity: suggestion. Location: BEH-1. BEH-1 assumes newly created issues always
  land in `todo`, implying the API defaults new issues to that status — an assumption not stated
  as a precondition and not confirmed against the (not-included-in-this-pack) `issue-lifecycle`
  spec. Recommendation: state explicitly as a precondition that `issue-tracker-api` defaults new
  Issues to `status=todo`, or have the UI place the card by reading the server's returned `status`
  rather than assuming `todo`.

**Security lens:**
- **SEC-1** — No findings. Auth is explicitly out of scope per charter ("No real auth...
  localhost only"); DELETE/PATCH calls go through documented same-origin endpoints only,
  consistent with the "HTTP contract is the boundary" principle. No trust-boundary or injection
  concerns introduced by this spec's client-side behaviors.

**Consistency lens:**
- **CON-1** — No findings. Terminology, error-code naming (`UI_*`), status values
  (`todo`/`in_progress`/`done`), and endpoint usage (`PATCH /issues/{id}` for both edits and
  status moves) are all consistent with the charter's Interface Contracts and the sibling
  `board-view.spec.md`. `risk_level: medium` correctly maps to the `quick` review/no-HITL policy
  under which this review is running. No ADRs exist to conflict with (directory empty).
- **CON-2** — Severity: suggestion. Location: Error Cases table. The 404 case
  (`UI_ISSUE_NOT_FOUND`) removes the card rather than "reverting" it — a reasonable special case
  of BEH-5's general revert rule, but not explicitly called out as an exception to BEH-5's
  wording. Recommendation: add a one-line note clarifying that 404 is handled by removal (per the
  error table), not the generic revert-and-error path in BEH-5, to avoid ambiguity for
  implementers.

No blockers identified. The spec is well-scoped, stays within charter boundaries, and does not
conflict with sibling specs, ADRs, or risk/gate policy for its medium risk tier.

---

## Warnings (registry-level, informational)

- `DISABLED_WITHOUT_REASON` (x3): `structural-architect`, `security-reviewer`, and
  `consistency-analyzer` are disabled in `.context-index/governance/review.yaml` with no
  `disabled_reason` field. Recommend adding a reason (e.g., "training-course fixture, low risk")
  so future reports can distinguish an intentional opt-out from an undeclared entry.
- `BROADEN_TOOL` / `BROADEN_NETWORK` (profile `browser-review`): not exercised by this run (quick
  tier used a different profile) — carried through from `adev governance reviewers --json` for
  completeness.
- `CONTEXT_PACK_OVERRIDE`: project overrides the bundled `base` context pack with an empty
  `include: []`. Not applicable to the quick-tier dispatch, which does not use the registry's
  context packs.

## Summary

**Total findings:** 3 (0 blockers, 1 warning, 2 suggestions)
**Action required:** None blocking. Recommend enumerating required Issue fields (SA-1) before or
during planning; the spec is ready for `/adev:plan` as-is.
