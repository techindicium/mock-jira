---
last-reviewed-revision: 1
file-sha: ba40f3e6ba0cf9de50a064a978a09c5d2284c3400a87b1ced912bf800533b856
---

# Architecture Review: sprints

> **Date:** 2026-09-09
> **Spec:** .context-index/specs/cross-cutting/sprints.spec.md
> **Charter:** .context-index/specs/cross-cutting/sprints/charter.md
> **Verdict:** PASS_WITH_NOTES
> **Tier:** full (manually dispatched — this project's governance/review.yaml has all three
> bundled full-tier reviewers disabled with no reason given, which would have meant **zero**
> reviewers under a literal `--tier full` invocation. Given this spec's `risk_level: high`, all
> three lenses (structural-architect, security-reviewer, consistency-analyzer) were dispatched
> manually using the bundled prompt files, then a consolidated confirmation pass verified fixes.)

## Reviewers Dispatched

| ID | Name | Mode | Profile | Prompt/Skill |
|----|------|------|---------|--------------|
| structural-architect | Structural Architect | subagent | general-purpose (read-only instructed) | plugin:review-specs/structural-architect-prompt.md |
| security-reviewer | Security Reviewer | subagent | general-purpose (read-only instructed) | plugin:review-specs/security-reviewer-prompt.md |
| consistency-analyzer | Consistency Analyzer | subagent | general-purpose (read-only instructed) | plugin:review-specs/consistency-analyzer-prompt.md |
| (confirmation) | Confirmation re-review | subagent | general-purpose (read-only instructed) | ad hoc — verified all fixes against real file content |

## Disabled Reviewers

| ID | Reason |
|----|--------|
| structural-architect | no reason given (project governance/review.yaml) — manually dispatched anyway for this high-risk spec |
| security-reviewer | no reason given (project governance/review.yaml) — manually dispatched anyway |
| consistency-analyzer | no reason given (project governance/review.yaml) — manually dispatched anyway |

## Structural Architect (structural-architect)

**Verdict:** PASS_WITH_NOTES

- SA-1 (warning) — kanban-ui missing as a named consumer of `GET /projects/{id}/sprints`. **Fixed**: Integration Points now names it explicitly.
- SA-2 (warning) — incomplete Sprint response/request shape; creation-time `start_date`/`end_date` unstated. **Fixed**: BEH-1 now states the full shape and creation-time field set.
- SA-3 (suggestion) — validation check ordering unstated. **Fixed**: BEH-7 now states existence → project-match → status order.
- SA-4 (suggestion) — closed-sprint check should be a shared helper. **Fixed**: noted in Actionable Task Map.

## Security Reviewer (security-reviewer)

**Verdict:** PASS_WITH_NOTES

- SEC-1 (warning, the important one) — `POST /issues` never addressed whether it accepts `sprint_id`, a potential bypass of the cross-Project invariant. **Fixed**: new BEH-13 explicitly rejects/ignores it; reflected in Invariants and Acceptance Criteria.
- SEC-2 (informational) — Sprint's immutable `project_id` correctly closes a re-homing vector. No action needed.
- SEC-3 (suggestion) — `GET /projects/{id}/sprints` missing 404 parity. **Fixed**: added to Error Cases.
- SEC-4 (suggestion) — no date format/ordering validation specified. **Fixed**: BEH-1 and Error Cases now require ISO-8601 and `end_date >= start_date`.

## Consistency Analyzer (consistency-analyzer)

**Verdict:** PASS_WITH_NOTES

- CON-1 (warning) — error codes didn't follow the project's referencing-entity-prefix convention. **Fixed**: renamed to `SPRINT_PROJECT_NOT_FOUND`/`ISSUE_SPRINT_NOT_FOUND`, bare `SPRINT_NOT_FOUND` reserved for the direct lookup only.
- CON-2 (warning) — sibling module charters (issue-tracker-api, kanban-ui, mcp-server) not synced, unlike the `issue-comments` precedent. **Fixed**: all three synced (Domain Model/Capability Map/Interface Contracts), including a gap the confirmation pass caught (mcp-server's Exposed APIs table was initially missed and has since been added).
- CON-3 (warning) — kanban-ui charter/`app-navigation.spec.md` hardcode "three nav items," conflicting with the new Sprint nav item. **Fixed**: explicit acknowledgment added (this is a second extension of the same staleness `backlog-view` already introduced); kanban-ui charter's Scope wording updated to stop compounding it. `app-navigation.spec.md`'s own behavioral contract is left as a noted follow-up, out of this spec's scope.
- CON-4 (suggestion) — stray `#backlog` banner reference. **Fixed**: now cites only `#board-error`.

---

## Summary

**Total findings:** 12 across three lenses (0 blockers, 8 warnings, 4 suggestions), all addressed. A confirmation pass caught one incomplete fix (mcp-server's Exposed APIs table) which was then also fixed.
**Action required:** None — ready for `/adev:plan`. Given `risk_level: high` and the recorded constitutional exception for `Issue.sprint_id`, recommend the implementation plan gets the same full-rigor review treatment (this project's disabled full-tier registry means manual dispatch, as done here).
