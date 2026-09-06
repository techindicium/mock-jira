---
spec: .context-index/specs/features/mcp-server/mcp-e2e.spec.md
plan: .context-index/specs/features/mcp-server/mcp-e2e.plan.md
date: 2026-09-06
overall_status: PASS_WITH_NOTES
---

# Validation Report: End-to-end MCP test suite (real client/transport)

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/mcp-server/mcp-e2e.spec.md
> **Plan:** .context-index/specs/features/mcp-server/mcp-e2e.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS

Resolved gate set (via `adev domain load-gates`): test, lint, test-js, e2e-smoke.
(`integration-test` was excluded from the resolved set — its `command` field is empty in
`governance/gates.yaml`; flagged by the loader as `INVALID_GATE` and skipped.)

**Check 1a (fast tier):**
- test (`.venv/bin/python3 -m pytest -q`): PASS — 107 passed, 3 warnings, 1.98s
- lint (`.venv/bin/ruff check .`): PASS — "All checks passed!"
- test-js (`node --test tests_js/**/*.test.js`): PASS — 44 passed, 0 failed, 99ms

**Check 1b (integration tier):** no gates configured, skipped.

**Check 1c (e2e tier):**
- e2e-smoke (`.venv/bin/python3 -m pytest -q tests_e2e/`), severity warning, group full: PASS — 31 passed, 17.66s

All 4 resolved gates pass. Gate outcomes attested via `adev report --type validator` with
`--gate-outcomes` (manifest-sha: `de7c0fa`).

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify`: "Check 1.5: PASS — source manifest matches (sha: de7c0fa)"
- All 12 manifest files confirmed git-tracked (`git log --oneline -1 -- <file>` returns a commit
  for each): requirements-e2e.txt, tests/test_requirements_files.py, tests_e2e/conftest.py,
  tests_e2e/mcp_client.py, tests_e2e/servers.py, tests_e2e/test_mcp_client_helper.py,
  tests_e2e/test_mcp_error_paths_e2e.py, tests_e2e/test_mcp_issue_tools_e2e.py,
  tests_e2e/test_mcp_project_tools_e2e.py, tests_e2e/test_mcp_server_fixture.py,
  tests_e2e/test_mcp_server_unreachable_fixture.py, tests_e2e/test_mcp_tool_discovery_e2e.py.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)
- `adev verify spec --check-drift`: `{"drifted":false,"drift_source":null,"drift_at":null}` — no
  drift detected for this spec.
- Note: per the implement-step summary, `mcp_server/server.py` (shared across this and two
  sibling specs) was modified during this implementation, and `project-tools.spec.md` /
  `issue-tools.spec.md` do show `drift_detected: true` as a result. That is drift on those other
  specs, not on this one — this spec's own drift flag is clean. Flagged here as context; no
  action required by this validation run (tracked as deferred housekeeping per the implement
  summary).

## Check 2: Spec Compliance — SKIPPED (disabled)
Disabled in `.context-index/governance/validate.yaml` (`enabled: false` — "subagent-review —
dropped for lightweight validation"), consistent with this repo's constitution ("Validation:
only deterministic checks run; both subagent-review checks and visual-verification are
disabled").

## Check 4: Constitution Compliance — SKIPPED (disabled)
Disabled in `.context-index/governance/validate.yaml` for the same reason as Check 2.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json`: `{"verdict":"SKIP","reason":"no boundary rules declared", ...}`
- No boundary rules declared for this project — SKIP means nothing was read, not that boundaries
  held.

## Check 9: Transition Gates — SKIP
- Transition: `implement-to-validate`
- `adev gate transitions --transition implement-to-validate --json`:
  `{"verdict":"SKIP","reason":"no transitions configured", ...}`
- `governance/gates.yaml` declares `transitions: {}` — no transition requirements configured.

## Check 11: Visual Verification — N/A
Disabled in governance (`enabled: false` — "no UI — mock-jira is a headless HTTP API"). No UI
files in this spec's source manifest either (Case A of the trigger guard: no UI files, no
verification applicable).

## Check 14: Gate Executability and Test Collection — WARN (non-blocking; registry severity: warning)
`adev gate doctor --json` — 9 findings (4 error-severity, 5 warning-severity):

- **error** `gate-doctor/path-gitignored` — gate `test` enters `.venv/bin/python3`, which is
  gitignored; works locally only, never in CI or a fresh clone.
- **error** `gate-doctor/path-gitignored` — gate `lint` enters `.venv/bin/ruff`, same issue.
- **error** `gate-doctor/path-gitignored` — gate `e2e-smoke` enters `.venv/bin/python3`, same issue.
- **error** `gate-doctor/glob-under-expansion` — gate `test-js`'s `tests_js/**/*.test.js` glob
  degrades under `sh` (no globstar); 12 files would be silently skipped if this gate ever ran
  under `sh` instead of the node CLI form used here.
- **warning** `gate-doctor/gate-set-divergence` — raw `gates.yaml` declares `integration-test`,
  absent from the domain-merged set.
- **warning** `gate-doctor/ci-config-missing` — no CI configuration found in the project.
- **warning** `gate-doctor/runner-unknown` (lint) — no known test runner identified for
  `ruff check .`; collection not verifiable.
- **warning** `gate-doctor/runner-unknown` (test-js) — `node:test` has no collect-only mode;
  coverage is glob analysis only.
- **warning** `gate-doctor/empty-command` — gate `integration-test` declares no command.

Per this check's own severity (`warning` in `validate.yaml`), these findings do not fail
validation. All are **pre-existing project infrastructure gaps** (gitignored venv paths, no CI
config, unwired `integration-test` gate) — none were introduced by this spec's implementation,
and none affect the fact that all 4 gates this spec's tests run under (test, lint, test-js,
e2e-smoke) executed successfully in this validation run.

---

**Summary:** 5 checks passed (1, 1.5, 1.6, 8-as-SKIP, 9-as-SKIP), 1 check WARN (14, non-blocking),
2 checks skipped as disabled by governance (2, 4), 1 check N/A (11, disabled + no UI). No FAILs.
Overall: **PASS_WITH_NOTES**.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding — though Check 2 itself is
>   disabled in this project's governance).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check
>   13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
