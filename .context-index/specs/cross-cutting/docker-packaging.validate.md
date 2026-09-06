---
spec: .context-index/specs/cross-cutting/docker-packaging.spec.md
plan: .context-index/specs/cross-cutting/docker-packaging.plan.md
date: 2026-09-06
rigor_tier: quick
overall_status: PASS
---

# Validation Report: Docker packaging and run instructions

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/cross-cutting/docker-packaging.spec.md
> **Plan:** .context-index/specs/cross-cutting/docker-packaging.plan.md
> **Rigor Tier:** quick (resolved via risk policy — spec `risk_level: low` -> `policies.low.validate_mode: quick`)
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS

Resolved gate set (`adev domain load-gates --module deployment`), fast tier only (no integration/e2e
gates configured; `integration-test` gate is unwired — missing `command` field — and was excluded
from the resolved set with warning `INVALID_GATE`):

- `test` (`.venv/bin/python3 -m pytest -q`): PASS — 103 passed, 3 warnings, 1.08s
- `lint` (`.venv/bin/ruff check .`): PASS — "All checks passed!"
- `test-js` (`node --test tests_js/**/*.test.js`): PASS — 44 passed, 0 failed, 111.9ms

Gate outcomes attested via `adev report --type validator --validator validate.check-1-quality-gates
--gate-outcomes @... --manifest-sha 33dc650` (3 gates: test, lint, test-js — all `pass`, tier `fast`).

## Check 1.5: Source Manifest Verification — SKIP
- Skipped — quick rigor tier.
- Supplementary note: as part of the Prerequisites check, all 11 files listed in the spec's
  `source-manifest` block (sha `33dc650`) were confirmed present on disk and committed to git
  (`git log --oneline -1 -- <file>` returned a match for each): `.context-index/constitution.md`,
  `CLAUDE.md`, `README.md`, `app/main.py`, `docker-compose.yml`,
  `docker/issue-tracker-api/Dockerfile`, `docker/mcp-server/Dockerfile`, `mcp_server/server.py`,
  `requirements.txt`, `tests/mcp_server/test_transport.py`, `tests/test_docker_deploy.py`,
  `tests/test_main_env.py`.

## Check 1.6: Code-Side Drift Warning — SKIP
- Skipped — quick rigor tier.

## Check 2 + Check 4 (synthesized quick-tier compliance check) — SKIP
- Skipped — this project's `governance/validate.yaml` disables all subagent-review checks
  project-wide (`validate.check-2-spec-compliance`, `validate.check-4-constitution`, and
  `validate.check-11-visual-verification` all carry `enabled: false`), and `CLAUDE.md`'s
  Governance Posture states explicitly: "Validation (`governance/validate.yaml`): only
  deterministic checks run; both subagent-review checks and visual-verification are disabled."
  The quick-tier synthesized spec+constitution compliance check is itself a subagent-review
  dispatch, so it is not run, consistent with this project's standing governance choice — not
  merely the tier resolution.
- Deterministic corroboration performed instead: all 12 acceptance criteria in the spec are
  checked off (`[x]`); implementation files for all three Dockerfiles/compose/env-var behaviors
  named in the Module Impact Map are present and committed (see Check 1.5 note); Check 1's fully
  green gate set (pytest + node test suites, including `tests/test_docker_deploy.py` and
  `tests/mcp_server/test_transport.py`, which directly exercise BEH-1 through BEH-5) is the
  deterministic evidence available in lieu of a subagent compliance read.

## Cross-Repo Dependency Validation — N/A
- No workspace detected requiring cross-repo `depends-on` resolution for this spec, or spec
  declares no cross-repo `depends-on` references.

## Check 8: Boundary Compliance — SKIP
- Skipped — quick rigor tier.
- Supplementary note: `governance/boundaries.yaml` declares `boundaries: []` (no rules), so a
  full-tier run would also have recorded SKIP with reason "no boundary rules declared."

## Check 9: Transition Gates — SKIP
- Skipped — quick rigor tier.
- Supplementary note: `governance/gates.yaml` declares `transitions: {}` (empty), so a full-tier
  run would also have recorded SKIP with reason "no transitions configured."

## Check 11: Visual Verification — N/A
- No UI files in implementation diff (mock-jira is a headless HTTP API); registry entry also
  carries `enabled: false` ("no UI — mock-jira is a headless HTTP API").

---

**Summary:** 1 check passed (Check 1), 6 checks skipped (1.5, 1.6, synthesized 2+4, 8, 9, 11 —
per quick rigor tier and/or standing project governance disabling subagent-review), 1 N/A
(cross-repo dependency validation). No failures. Overall Status: **PASS**.

Known non-blocking items carried forward from implementation (not re-litigated by this
validation run, per implement summary): an epic-close CLI bug already reported separately; and
`drift_detected: true` on the unrelated `mcp-server` issue-tools/project-tools specs (caused by
`mcp_server/server.py` being extended with streamable-http transport, shared code touched by this
spec) — deferred housekeeping tracked outside this spec's scope.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This is a **quick-tier** report: Checks 1.5, 1.6, 8, 9 and the separate Check 2/Check 4
> dispatches were skipped per `graduated-rigor-tiers.spec.md` (risk_level: low ->
> validate_mode: quick), and the tier's normal quick-mode substitute — a single synthesized
> spec+constitution compliance subagent check — was additionally skipped because this project's
> governance disables subagent-review checks entirely.
