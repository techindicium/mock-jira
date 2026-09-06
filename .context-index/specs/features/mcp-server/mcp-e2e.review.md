---
last-reviewed-revision: 1
file-sha: cc2228f3b90b182f61aa7e3374341e51a66b4d191e821411cdcfc10d405d821e
rigor-tier: quick
---

# Architecture Review: mcp-e2e

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/mcp-server/mcp-e2e.spec.md
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

- **SA-1** — *warning* — Location: Behaviors (BEH-5) / Actionable Task Map (Dual-server e2e
  fixture). BEH-5 requires an `mcp-server` instance configured with `API_BASE_URL` pointing at a
  port with nothing listening — a materially different process topology than the one described
  in the "Dual-server e2e fixture" task, which wires `mcp-server` to a live `issue-tracker-api`
  instance. Neither the fixture task nor the Postconditions ("Both server processes are torn
  down after the test session") explicitly account for this third/divergent server
  configuration, its teardown, or whether it reuses the same fixture with a monkey-patched base
  URL versus a separate fixture instance. Recommendation: clarify in Preconditions or the Task
  Map how the BEH-5 scenario obtains its `mcp-server` process (variant of the standard fixture
  vs. a separate one) and confirm it is torn down alongside — or independently of — the standard
  pair.
- **CON-1** — *warning* — Location: System Constitution Reference / Preconditions
  (streamable-http transport). This spec's Preconditions rely on "the streamable-http transport
  added by `docker-packaging`," a validated cross-cutting spec. The parent charter's Dependencies
  table (revision 10, matching this spec's `charter-revision: 10`) lists only `issue-tracker-api`
  as a dependency — `docker-packaging` is absent, even though the mcp-server feature now
  structurally depends on it for its transport layer. Recommendation: flag for a charter update
  to add `docker-packaging` to the Dependencies table (outside this spec's own authority to fix,
  but worth surfacing before/alongside planning).
- **SA-2** — *suggestion* — Location: Error Cases table. This suite introduces new `E2E_*` error
  codes (`E2E_MCP_INPUT_INVALID`, `E2E_MCP_UPSTREAM_UNREACHABLE`, `E2E_SERVER_START_TIMEOUT`)
  distinct from the sibling specs' `MCP_*` codes for what are conceptually the same underlying
  failures (BEH-4/BEH-5 mirror project-tools/issue-tools error cases). This is defensible as
  test-assertion-level naming rather than protocol-level codes, but the relationship isn't
  stated. Recommendation: add a one-line note clarifying these codes label test
  assertions/expectations rather than values asserted verbatim against protocol output, to
  preempt confusion with the sibling specs' `MCP_*` codes.

Not flagged (reviewed, no issue): no structural gaps in tool-count coverage (BEH-1's "7 tools"
and BEH-3's "five issue tools" both reconcile correctly against the charter's Interface
Contracts); no auth/trust-boundary issues (constitution reference correctly reiterates
localhost-only binding); no contradictions with the validated `project-tools`/`issue-tools`
sibling specs' behaviors or error semantics.

---

## Summary

**Total findings:** 3 (0 blockers, 2 warnings, 1 suggestion)
**Action required:** No blockers — the spec is ready for planning. Consider folding SA-1, CON-1,
and SA-2 into a spec/charter revision before or during implementation to close the fixture-
topology, dependency-table, and error-code-naming gaps, but none is required to unblock
`/adev:plan`.

**Governance note:** `.context-index/governance/gates.yaml` `transitions` is empty — no
`spec-to-plan` `approver_role` is configured, so no human-approval footer applies here.

**Registry warnings (from `adev governance reviewers --json`):** `DISABLED_WITHOUT_REASON` x3
(structural-architect, security-reviewer, consistency-analyzer); `CONTEXT_PACK_OVERRIDE` (base
pack overrides bundled default); `BROADEN_TOOL` x2 and `BROADEN_NETWORK` (profile
`browser-review` broadens tool/network posture) — none of these affect this quick-tier dispatch,
surfaced here per Step 3 of the review-specs skill.
