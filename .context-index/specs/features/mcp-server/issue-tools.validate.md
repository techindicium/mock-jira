---
partial_schema: validate@1
spec: .context-index/specs/features/mcp-server/issue-tools.spec.md
plan: .context-index/specs/features/mcp-server/issue-tools.plan.md
date: 2026-09-05
overall_status: PASS_WITH_NOTES
---

# Validation Report: Issue MCP tools (list/get/create/update/delete)

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/mcp-server/issue-tools.spec.md
> **Plan:** .context-index/specs/features/mcp-server/issue-tools.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Governance Configuration Note

This repo's `governance/validate.yaml` enables only deterministic checks (Check 1 quality
gates, Check 1.5 source-manifest, Check 1.6 code-drift, Check 8 boundaries, Check 9 transition
gates, Check 14 gate executability). Both subagent-review checks (Check 2 spec compliance,
Check 4 constitution compliance) and Check 11 (visual verification) are `enabled: false`,
respected as-is per this project's intentionally lightweight training-course governance
posture — no subagent was dispatched for this run.

## Check 1: Quality Gates — PASS
- Tier: fast (integration and e2e tiers have no gates configured; `integration-test` gate is
  an unwired sentinel with empty `command`, excluded from the resolved set — `INVALID_GATE`
  warning surfaced by `adev domain load-gates`)
- **Test Suite (`test`, `[.venv/bin/python3, -m, pytest, -q]`): PASS.**
  `86 passed, 3 warnings in 0.98s` (warnings are pre-existing `DeprecationWarning`s in
  `app/main.py` / fastapi/starlette, unrelated to this spec).
  command_sha: `864cd8c369fc558cf6a8235d2514a26c14a6e2c1de08efd0629c4f69d1843587`
- **Linter (`lint`, `[.venv/bin/ruff, check, .]`): PASS.** `All checks passed!`
  command_sha: `2ea305ec5813b091e1464bd56985f9caafca6483b6a08963281eaa2f0f5b3fb0`
- **JS Unit Tests (`test-js`, `[node, --test, "tests_js/**/*.test.js"]`): PASS.**
  `44 pass, 0 fail` (all 12 `tests_js/*.test.js` suites collected and run).
  command_sha: `4d4e3bbfdf575dc83338694f6da0b95a44b8490751148497dfe931c5af571c77`

All fast-tier gates green. No integration or e2e tier gates configured (skipped with note).
`gate_outcomes` attested via `adev report --type validator` (manifest sha `d2ef81d`).

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify`: PASS — source manifest matches (sha: `d2ef81d`)
- Git-tracked check: all 5 manifest files verified committed via `git log --oneline -1 -- <file>`:
  `mcp_server/client.py` (commit `bf25d72`), `mcp_server/server.py` (commit `1ad47ae`),
  `mcp_server/tools/issues.py` (commit `5af2019`), `tests/mcp_server/test_client.py`
  (commit `bf25d72`), `tests/mcp_server/test_issue_tools.py` (commit `26caf45`).

## Check 1.6: Code-Side Drift — PASS
- `adev verify spec --check-drift`: `{"drifted":false,"drift_source":null,"drift_at":null}` — no
  drift detected for this spec.
- Note (non-blocking, not this run's concern): the sibling `project-tools.spec.md` in this same
  charter shows `drift_detected:true` because `tests/mcp_server/test_client.py` (a file shared
  between both specs) was extended during this spec's TDD cycle. Deferred housekeeping per
  `/adev:hygiene`; does not affect this spec's own drift status, which reads clean.

## Check 2 / Check 4 / Check 11 — SKIPPED-DISABLED
Disabled in `governance/validate.yaml` per this project's lightweight governance posture
(subagent-review checks and visual verification off; mock-jira is a headless HTTP-API-adjacent
MCP server with no UI).

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `verdict: SKIP`, reason: `no boundary rules declared`.
  (No rules configured project-wide — nothing was read, so nothing held.)

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec <spec> --json` →
  `verdict: SKIP`, reason: `no transitions configured`. (`gates.yaml`'s `transitions: {}` is
  intentionally empty per its own scaffold comment.)

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
`adev gate doctor --json` → 8 findings (3 error, 5 warning), exit code 2. Identical, pre-existing
repo-wide gate-configuration findings already surfaced and accepted in the prior
`project-tools.validate.md` run (same `gates.yaml`, unchanged by this spec):
- `gate-doctor/gate-set-divergence` (warning): `integration-test` declared but excluded from the
  merged set (empty command).
- `gate-doctor/ci-config-missing` (warning): no CI configuration found in the repo.
- `gate-doctor/path-gitignored` **(error)** ×2: `test` (`.venv/bin/python3`) and `lint`
  (`.venv/bin/ruff`) both start by entering a gitignored path — works locally, not in CI or on a
  fresh clone. Real, not-yet-closed portability gap tracked as a follow-up; does not block this
  validation (Check 14's registry severity is `warning`).
- `gate-doctor/runner-unknown` (warning) ×2: `lint` and `test-js` have no identifiable
  collect-only mode for verifying test collection.
- `gate-doctor/glob-under-expansion` **(error)**: `test-js`'s glob degrades under a
  `sh`-mediated shell invocation. Verified non-issue as actually run: the quality-gate runner
  uses `execFile` with `shell: false`, so Node's own glob resolution expands it correctly
  (44/44 tests collected and passed, confirmed above).
- `gate-doctor/empty-command` (warning): `integration-test` declares no command (documented
  unwired sentinel).

None of these findings are new or specific to this spec's implementation — all pre-date it and
were already accepted as non-blocking follow-ups in the prior validate run for this module.

---

**Summary:** 5 checks produced a verdict (1, 1.5, 1.6, 8, 9 all PASS; 14 PASS_WITH_NOTES), 0
failed, 3 skipped by governance (2, 4, 11 disabled). **Overall: PASS_WITH_NOTES** — all quality
gates green (86 pytest + 44 node tests, ruff clean), source manifest verified and git-tracked,
no drift, no boundary or transition-gate configuration to enforce. Check 14's pre-existing
gate-portability findings (gitignored `.venv` paths, glob-under-shell-expansion) are carried
over unchanged from the prior module validation and remain non-blocking follow-ups, not new
regressions introduced by this spec.

This is the last spec of the mcp-server module — both `project-tools` and `issue-tools` are now
implemented and validated.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly
>   Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
