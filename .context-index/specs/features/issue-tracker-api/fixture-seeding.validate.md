---
spec: .context-index/specs/features/issue-tracker-api/fixture-seeding.spec.md
plan: .context-index/specs/features/issue-tracker-api/fixture-seeding.plan.md
date: 2026-09-04
overall_status: PASS_WITH_NOTES
rigor_tier: full
---

# Validation Report: Fixture seed data

> **Date:** 2026-09-04
> **Spec:** .context-index/specs/features/issue-tracker-api/fixture-seeding.spec.md
> **Plan:** .context-index/specs/features/issue-tracker-api/fixture-seeding.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

Advisory: running repo-scoped inside workspace — cross-repo validation skipped (no cross-repo depends-on references).

## Check 1: Quality Gates — PASS

**Check 1a (fast tier):**
- `test` (`python3 -m pytest -q`) — PASS: 39 passed, 4 warnings, 0.45s
- `lint` (`ruff check .`) — PASS: All checks passed!

**Check 1b (integration tier):** SKIP — "integration tier — no gates configured, skipped." (`integration-test` gate declares no `command` field and was dropped by the loader as `INVALID_GATE`.)

**Check 1c (e2e tier):** SKIP — "e2e tier — no gates configured, skipped."

gate_outcomes: `[{"id":"test","verdict":"pass","tier":"fast"},{"id":"lint","verdict":"pass","tier":"fast"}]`

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify` → `Check 1.5: PASS — source manifest matches (sha: a163164)`
- Git-tracked check: all 3 manifest files have commits —
  - `app/main.py`, `app/seed.py` → `48a25cb feat(issue-tracker-api): seed one Project and six Issues on empty-database startup`
  - `tests/test_seed.py` → `ff94030 test(issue-tracker-api): confirm seeding is idempotent across process restarts`

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)
- `adev verify spec --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}` for this spec.
- Note: sibling specs in this module (`issue-lifecycle.spec.md`, `project-management.spec.md`) do show `drift_detected:true` per the implement-step summary, but that is out of scope for this spec's validation run — those specs carry their own drift flags to be addressed separately (see `/adev:reconcile`).

## Check 2: Spec Compliance — SKIPPED-DISABLED
Governance posture (`governance/validate.yaml`): `enabled: false` — "subagent-review — dropped for lightweight validation." Per this repo's constitution ("Validation ... only deterministic checks run; both subagent-review checks and visual-verification are disabled"), this check does not dispatch.

## Check 4: Constitution Compliance — SKIPPED-DISABLED
Same governance posture as Check 2 — `enabled: false` in `governance/validate.yaml`.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","findings":[],"disabled":[],"warnings":[],"summary":{"errors":0,"warnings":0,"infos":0,"files_checked":1}}`
- SKIP means no boundary rules are declared for this project — not that boundaries held.

## Check 9: Transition Gates — SKIP
- Transition: `implement-to-validate`
- `adev gate transitions --transition implement-to-validate --json` → `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions configured","gates":{}}`

## Check 11: Visual Verification — SKIPPED-DISABLED
`enabled: false` in `governance/validate.yaml` — "no UI — mock-jira is a headless HTTP API." Also structurally N/A: no UI files in this spec's implementation diff.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json` → 4 warnings, 0 errors:
  - `gate-doctor/gate-set-divergence`: raw `gates.yaml` declares `integration-test` but it is absent from the domain-merged set every consumer reads.
  - `gate-doctor/ci-config-missing`: no CI configuration found.
  - `gate-doctor/runner-unknown` (gate `lint`): no known test runner identified in `ruff check .`, so test collection cannot be verified for that gate.
  - `gate-doctor/empty-command` (gate `integration-test`): declares no command.
- Runners resolved: `test` → `pytest` (source: gates.yaml); `lint` → runner unknown.
- All findings are `severity: warning`; none block the aggregate verdict.

---

**Summary:** 5 checks ran (1, 1.5, 1.6, 8, 9, 14 — 6 total including the observational 1.6), all PASS or SKIP, plus one PASS_WITH_NOTES (Check 14). 3 checks skipped due to governance configuration (2, 4, 11 — disabled per this repo's lightweight validation posture; not a run failure). No FAILs.

**Notes carried forward from the implement step (non-blocking, out of scope for this validate run):**
- A known epic-close CLI bug was already reported separately.
- `issue-lifecycle.spec.md` and `project-management.spec.md` both show `drift_detected: true` because this and prior plans touched shared files (`app/main.py`, `app/db.py`). This is deferred housekeeping — recommend `/adev:reconcile` or a follow-up `/adev:validate` pass on those two specs.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> Historic `.validate.md` reports continue to use the pre-restructure numbering; the gaps in the surviving inventory (Checks 1, 1.5, 1.6, 2, 4, optionally 8 and 9) are intentional to preserve report readability.
