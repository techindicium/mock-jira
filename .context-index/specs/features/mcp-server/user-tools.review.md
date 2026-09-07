---
last-reviewed-revision: 2
file-sha: 0996f4badaeb3b82663cb845b412921f1256f8a856e78dd0b35222cc5385a1b6
rigor-tier: quick
---

# Architecture Review: user-tools

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/features/mcp-server/user-tools.spec.md
> **Charter:** .context-index/specs/features/mcp-server/charter.md
> **Verdict:** PASS_WITH_NOTES

## Rigor Tier

Resolved: **quick** (source: risk policy — `risk_level: low` frontmatter maps to
`policies.low.review_mode: quick` in `.context-index/governance/risk-policies.yaml`; no
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

This is revision 2, re-reviewed after revision 1's BLOCK. All three findings from the
revision-1 review are confirmed addressed:

- **CON-1 (was blocker, now resolved)** — The Actionable Task Map now carries an explicit
  "Update `mcp-e2e.spec.md` tool count" task, and the Acceptance Criteria list a matching
  criterion (BEH-1 count 7 → 9, plus the `tests_e2e/test_mcp_tool_discovery_e2e.py` assertion
  and source-manifest re-stamp). The cross-spec touch on the validated `mcp-e2e` sibling is now
  tracked rather than silent.
- **SEC-1 (was warning, now resolved)** — BEH-2 now states explicitly that `role` is delegated
  verbatim to `issue-tracker-api`'s validation with no tool-boundary enum, and that an invalid
  value surfaces via the existing `422` `MCP_UPSTREAM_ERROR` row rather than a new code.
- **SA-1 (was warning, now resolved)** — Preconditions now cite `user-directory`'s BEH-2/BEH-4
  email-uniqueness guarantee by name, giving BEH-3's `409` passthrough a named upstream contract
  to rest on.
- **SA-2 (was suggestion, now resolved)** — BEH-1 now states `list_users` takes no filter/
  pagination parameters this milestone, matching `list_projects`.
- **CON-2 (was suggestion, no change needed)** — the `get_user` deferral note remains consistent
  with the charter's Deferred Capabilities table.

**New observation (warning, not a blocker):** the Actionable Task Map's new "Update
`mcp-e2e.spec.md` tool count" task and its Acceptance Criterion correctly describe the required
change but do not themselves update `mcp-e2e.spec.md` — that remains an implementation-time task
(tracked, per the plan/implement steps) rather than something this spec-authoring pass performs.
This is expected (a spec describes work, it does not perform it) and is noted only so
`/adev:plan` carries this task through explicitly and `/adev:implement` does not silently skip
the sibling-spec update.

Not flagged (reviewed, no issue): the spec stays within charter scope (list_users/create_user
only); no ADR conflicts (`.context-index/adrs/` is empty in this repository); no auth gap beyond
the charter's stated "no real auth" posture; `API_BASE_URL` precondition matches the
cross-cutting `docker-packaging.spec.md`'s integration point for mcp-server reaching
issue-tracker-api; the `user-directory` upstream spec's `422`/`409` error codes align with this
spec's Error Cases table.

---

## Summary

**Total findings:** 1 (0 blockers, 1 warning, 0 suggestions)
**Action required:** None blocking. Proceed to `/adev:plan`. Ensure the plan carries the
`mcp-e2e.spec.md` tool-count update task through to implementation (see warning above).

**Governance note:** `.context-index/governance/gates.yaml` `transitions` is empty — no
`spec-to-plan` `approver_role` is configured, so no human-approval footer applies here.

**Registry warnings (from `adev governance reviewers --json`):** `DISABLED_WITHOUT_REASON` x3
(structural-architect, security-reviewer, consistency-analyzer) — none of these affect this
quick-tier dispatch, surfaced here per Step 3 of the review-specs skill.

**Heuristics:** No related prior lessons found for the `mcp-server` module (`__NONE__`).
