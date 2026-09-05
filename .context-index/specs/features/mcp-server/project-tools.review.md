---
last-reviewed-revision: 1
file-sha: 239ae95014db8bd9a19d5d35bde5fdd8ea1a5673eb05e04203eab1708d0d2166
rigor-tier: quick
---

# Architecture Review: project-tools

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/mcp-server/project-tools.spec.md
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

- **SA-1** — *warning* — Location: Behaviors (BEH-2, BEH-4) / Error Cases table. The actual
  `POST /projects` endpoint (`app/routers/projects.py`) returns `422` with `code:
  VALIDATION_ERROR` when `key` or `name` is present but blank/whitespace-only. The spec's Error
  Cases table only lists `MCP_INPUT_INVALID` (schema failure) and `MCP_UPSTREAM_ERROR` (409
  duplicate) — there is no row for a `422` passthrough, unlike the sibling `issue-tools.spec.md`,
  which explicitly lists a `422` → `MCP_UPSTREAM_ERROR` case. BEH-2's phrase "valid, non-empty
  key and name" implies the tool's input schema is expected to reject blank strings before the
  HTTP call, but BEH-4 only gives "missing key" as an example, not "empty-string key." If the
  input schema uses `required` without `minLength: 1`, a blank-string key/name would pass schema
  validation and hit the API's 422 — a case this spec doesn't account for. Recommendation:
  either (a) add a `422` → `MCP_UPSTREAM_ERROR` row to the Error Cases table mirroring the
  sibling spec, or (b) make explicit in BEH-4/Behavioral Contract that the input schema enforces
  `minLength: 1` on `key`/`name` so blank strings are rejected client-side and the API's 422 path
  is genuinely unreachable via this tool.
- **CON-1** — *suggestion* — Location: Error Cases table (cross-spec comparison with
  `issue-tools.spec.md`). The two sibling specs under the same charter diverge in error-table
  completeness (issue-tools covers input/404/422/unreachable; this spec covers only
  input/409/unreachable), without a stated reason tied to actual endpoint behavior differences.
  Recommendation: align the two specs' error-table conventions (or explicitly note why Project
  creation has no 422 case, once SA-1 is resolved) so a reader can trust error-table completeness
  as a pattern across mcp-server specs.

Not flagged (reviewed, no issue): the spec stays within charter scope (list_projects/create_project
only, `get_project` correctly deferred to v2); no security or blocking structural/consistency
issues found; correctly excludes auth per the charter's "no real auth" stance; the
`API_BASE_URL` precondition matches the cross-cutting `docker-packaging.spec.md`'s integration
point for mcp-server reaching issue-tracker-api; no ADR conflicts (no ADRs are adopted yet — only
the unfilled `.template.md` scaffold exists).

---

## Summary

**Total findings:** 2 (0 blockers, 1 warning, 1 suggestion)
**Action required:** No blockers — the spec is ready for planning. Consider folding SA-1 and
CON-1 into a spec revision before or during implementation to close the error-table gap, but
neither is required to unblock `/adev:plan`.

**Governance note:** `.context-index/governance/gates.yaml` `transitions` is empty — no
`spec-to-plan` `approver_role` is configured, so no human-approval footer applies here.

**Registry warnings (from `adev governance reviewers --json`):** `DISABLED_WITHOUT_REASON` x3
(structural-architect, security-reviewer, consistency-analyzer); `CONTEXT_PACK_OVERRIDE` (base
pack overrides bundled default); `BROADEN_TOOL` x2 and `BROADEN_NETWORK` (profile
`browser-review` broadens tool/network posture) — none of these affect this quick-tier dispatch,
surfaced here per Step 3 of the review-specs skill.
