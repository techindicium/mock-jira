---
last-reviewed-revision: 1
file-sha: 236db1af8ee6b4ceee443d073285cd844bf2ec8509aaa2c063549cd93b4591e2
rigor-tier: quick
---

# Architecture Review: fixture-seeding

> **Date:** 2026-09-04
> **Spec:** .context-index/specs/features/issue-tracker-api/fixture-seeding.spec.md
> **Charter:** .context-index/specs/features/issue-tracker-api/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Rigor tier:** quick (resolved via risk policy: `risk_level: low` → `review_mode: quick`; no `--tier` override, no routing signal)

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

> Note: `adev governance reviewers --json` also raised `DISABLED_WITHOUT_REASON` warnings for all
> three entries above (governance/review.yaml disables them with no `disabled_reason` field). This
> is orthogonal to the quick-tier dispatch above: the quick synthesized reviewer runs regardless of
> the bundled reviewers' enabled state, because rigor-tier resolution (risk policy → `quick`)
> bypasses the per-reviewer registry dispatch loop entirely for this spec.

## Quick Synthesized Reviewer (quick-synthesized-reviewer)

**Verdict:** PASS_WITH_NOTES

- **ID:** SA-1
  **Severity:** warning
  **Location:** Behavioral Contract → BEH-1
  **Finding:** The spec specifies that seeding creates one Project and six Issues but never states
  what `status` (`todo`/`in_progress`/`done`), `issue_type`, or `priority` values those six Issues
  receive. Seeding writes directly to the tables (per Preconditions), bypassing the `POST /issues`
  default-status behavior defined in the `issue-lifecycle` sibling spec, so nothing else in the
  reviewed context fills this gap. The parent charter frames seed data's purpose as giving
  consuming tracks — explicitly including `kanban-ui`, a client of this same charter — "realistic
  starting Projects/Issues." Six issues all defaulting to a single status would leave a
  three-column kanban board effectively empty in two of three columns, undermining that stated
  purpose.
  **Recommendation:** Add a behavior or acceptance-criterion line specifying that the six seed
  Issues cover a realistic spread across the three statuses (and ideally varied `issue_type`/
  `priority`), so the fixture actually exercises the kanban board it's meant to populate.

- **ID:** CON-1
  **Severity:** warning
  **Location:** Frontmatter (`charter-revision: 2`) vs. Parent Charter frontmatter (`revision: 7`)
  **Finding:** This spec (and both cited sibling specs) declare `charter-revision: 2`, but the
  parent charter is now at `revision: 7`. The specific capability row this spec implements ("Seed
  fixture data," status `specified`) does match the current charter text, so there's no visible
  contradiction in content — but the five-revision gap is unexplained, and nothing in the spec
  confirms it was re-checked against the charter's current state (e.g., current Domain Model,
  Deferred Capabilities, Dependencies table) rather than the state at revision 2.
  **Recommendation:** Bump `charter-revision` to the charter's current revision (7) once confirmed,
  or note in the spec why revision 2 is still the correct pin — so future readers don't have to
  guess whether charter drift since revision 2 was accounted for.

No blocker findings. Security lens: no findings — the module has no auth surface in scope (per
charter, out of scope) and seeding uses only hardcoded, authoring-time data with no runtime input,
so there is no injection or trust-boundary concern.

---

## Summary

**Total findings:** 2 (0 blockers, 2 warnings, 0 suggestions)
**Action required:** Optional. The spec is ready for planning as-is. Consider addressing SA-1
(unspecified status/type/priority distribution across the six seed Issues — meaningful because an
all-`todo` fixture underserves the kanban-ui consumer this charter names) and CON-1
(unexplained `charter-revision` gap) before or during `/adev:plan`; neither is a blocker.
