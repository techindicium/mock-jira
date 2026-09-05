---
last-reviewed-revision: 1
file-sha: b45c86735f71b19b9a3bfb1912ddcf32507aed05988605513caaff240e244e05
rigor-tier: quick
---

# Architecture Review: issue-tools

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/mcp-server/issue-tools.spec.md
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

- **SA-1** — *warning* — Location: Behaviors (BEH-4) / Error Cases table. The depended-on
  `issue-lifecycle.spec.md` defines BEH-2 (`POST /issues` with an unknown `project_id` →
  `404` naming the missing project, `ISSUE_PROJECT_NOT_FOUND`), but this spec's Error Cases
  table scopes its `404` row to "unknown issue id" only, with no row or behavior covering an
  unknown `project_id` on `create_issue`. An implementer could reasonably treat that create-time
  `404` as something other than verbatim passthrough. Recommendation: broaden the `404` error
  row to cover "unknown issue id *or* unknown `project_id` on create", or add a behavior
  mirroring upstream BEH-2.
- **SA-2** — *warning* — Location: Behaviors (BEH-5) / update_issue input schema. Upstream
  `issue-lifecycle` BEH-7 declares `id`, `key`, and `project_id` immutable and silently ignored
  if present in the PATCH body. BEH-5 here says only "one or more fields (including `status`)"
  without stating whether `update_issue`'s input schema excludes those three fields outright
  (schema-level rejection → `MCP_INPUT_INVALID`) or accepts-and-forwards them to be ignored
  upstream. Both are defensible, but one path is in tension with the charter invariant that
  schema validation gates every HTTP call. Recommendation: state explicitly which behavior the
  tool's input schema implements for `id`/`key`/`project_id` on `update_issue`.
- **SA-3** — *warning* — Location: Behaviors (BEH-6) / Postconditions. `delete_issue` "returns a
  success confirmation" is the only tool output in this spec not defined by passthrough of the
  upstream response; `DELETE /issues/{id}` responds `204` with an empty body, so the MCP layer
  must synthesize a result, but its shape is unspecified — in tension with the sibling
  `project-tools.spec.md`'s "returns the result unmodified" convention. Recommendation: specify
  the confirmation's shape (e.g. a structured `{deleted: true, id}` or a fixed text result) so
  BEH-6's acceptance criterion is testable.
- **CON-1** — *warning* — Location: Frontmatter. `charter-revision: 2` is stamped against the
  parent `mcp-server` charter, which is now at `revision: 4`. The sibling `project-tools.spec.md`
  carries the same stale value, so this looks inherited rather than deliberate. Recommendation:
  re-stamp `charter-revision: 4` after confirming nothing in charter revisions 3–4 changed the
  Issue capability rows this spec covers.
- **CON-2** — *suggestion* — Location: Preconditions. The sibling `project-tools.spec.md` names
  its configuration precondition explicitly ("configured with the API's base URL via
  `API_BASE_URL`"); this spec omits it. The cross-cutting `docker-packaging.spec.md` also assigns
  mcp-server a `PORT` env var that appears in no mcp-server spec. Recommendation: add the
  `API_BASE_URL` precondition here for parity with the sibling spec, and leave `PORT` owned by
  `docker-packaging` (or cross-reference it) so the env surface is discoverable from either side.
- **SEC-1** — *suggestion* — Location: Error Cases (verbatim passthrough). Verbatim upstream
  error passthrough is a charter invariant and is correct here — the API is fixture-backed,
  offline, and unauthenticated, so there is no credential or tenant data an error string could
  leak. No auth/authorization gap is introduced by this spec; it inherits the charter's explicit
  no-auth stance. Recommendation: none required now — revisit passthrough only if mcp-server is
  ever pointed at a non-fixture backend, which belongs to a future spec.

Not flagged (reviewed, no issue): the spec stays within charter scope (all five must-have Issue
capabilities, no scope creep into resources/prompts/auth); `list_issues`'/`get_issue`'s
passthrough behavior is unambiguous; no ADR conflicts (no ADRs are adopted yet — only the
unfilled `.template.md` scaffold exists).

**Awareness-only note (not actionable in this spec):** the depended-on
`issue-lifecycle.spec.md` carries `drift_detected: true` on the `issue-tracker-api` side —
behaviors here are written against its stated contract, which may itself have drifted from
code. This is a concern for the `issue-tracker-api` charter, not something this spec can fix.

---

## Summary

**Total findings:** 6 (0 blockers, 4 warnings, 2 suggestions)
**Action required:** No blockers — the spec is ready for planning. Consider folding SA-1, SA-2,
SA-3, and CON-1 into a spec revision before or during implementation to close the error-table,
schema-behavior, and delete-confirmation-shape gaps, but none is required to unblock
`/adev:plan`.

**Governance note:** `.context-index/governance/gates.yaml` `transitions` is empty — no
`spec-to-plan` `approver_role` is configured, so no human-approval footer applies here.

**Registry warnings (from `adev governance reviewers --json`):** `DISABLED_WITHOUT_REASON` x3
(structural-architect, security-reviewer, consistency-analyzer); `CONTEXT_PACK_OVERRIDE` (base
pack overrides bundled default); `BROADEN_TOOL` x2 and `BROADEN_NETWORK` (profile
`browser-review` broadens tool/network posture) — none of these affect this quick-tier dispatch,
surfaced here per Step 3 of the review-specs skill.
