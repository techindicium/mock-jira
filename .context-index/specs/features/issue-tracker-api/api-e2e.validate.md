---
partial_schema: validate@1
spec: .context-index/specs/features/issue-tracker-api/api-e2e.spec.md
plan: .context-index/specs/features/issue-tracker-api/api-e2e.plan.md
charter: issue-tracker-api
date: 2026-09-06
overall_status: PASS
rigor_tier: quick
---

# Validation Report: End-to-end API test suite (real HTTP)

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/issue-tracker-api/api-e2e.spec.md
> **Plan:** .context-index/specs/features/issue-tracker-api/api-e2e.plan.md
> **Rigor Tier:** quick (resolved via risk-policies.yaml: `risk_level: low` → `validate_mode: quick`; no explicit `--tier` or routing override was supplied)
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS

Gate set resolved via `adev domain load-gates` (domain: software, source: project `governance/gates.yaml`). One warning surfaced during resolution: `INVALID_GATE: Gate 'integration-test' missing required command field — skipped` (pre-existing, unwired sentinel gate; not part of this spec's scope).

**Check 1a (fast tier):**
- `test` (`.venv/bin/python3 -m pytest -q`): PASS — 105 passed, 3 warnings, 2.03s
- `lint` (`.venv/bin/ruff check .`): PASS — "All checks passed!"
- `test-js` (`node --test tests_js/**/*.test.js`): PASS — 44 passed, 0 failed, 111.7ms

**Check 1b (integration tier):** SKIP — no gates configured (the only integration-tier gate, `integration-test`, has no `command` and was dropped by the loader with a warning; unrelated to this spec).

**Check 1c (e2e tier):**
- `e2e-smoke` (`.venv/bin/python3 -m pytest -q tests_e2e/`, severity: warning, `required: false`): PASS — 11 passed, 2.76s

This is the new e2e-smoke gate/tier introduced alongside this spec's implementation. It ran automatically via the standard gate-resolution logic and passed.

Per-gate outcome attestation emitted as a single `validator_report` (validate.check-1-quality-gates) with `gate_outcomes` for all 4 executed gates and `--manifest-sha 77daccc` (matching the spec's stamped source-manifest).

## Check 1.5: Source Manifest Verification — SKIP (informationally re-verified)

Skipped per quick rigor tier rule ("Skipped — quick rigor tier."). As a courtesy, `adev source-manifest verify --spec <spec>` was run directly and returned: `Check 1.5: PASS — source manifest matches (sha: 77daccc)` — all 12 stamped files are unchanged and git-tracked. No validator_report was emitted for this check since it is out of scope under the resolved tier.

## Check 1.6: Code-Side Drift Warning — SKIP

Skipped per quick rigor tier rule. (Note: this spec's own `drift_detected` flag is not set; a sibling spec, `board-view.spec.md`, is separately reported with `drift_detected: true` because the shared `governance/gates.yaml` was extended for this feature — tracked as deferred housekeeping per the implement step, not a defect of this spec.)

## Check 2 / Check 4 (synthesized quick-tier compliance check) — SKIP (disabled)

Under `quick` rigor tier, checks 2 and 4 are normally replaced by one synthesized spec+constitution compliance subagent pass. This project's `governance/validate.yaml` disables both `validate.check-2-spec-compliance` and `validate.check-4-constitution` (`enabled: false`), and the constitution states: *"Validation (governance/validate.yaml): only deterministic checks run; both subagent-review checks and visual-verification are disabled."* Consistent with that standing project posture, the synthesized subagent check was not dispatched.

## Check 8: Boundary Compliance — SKIP

Skipped per quick rigor tier rule. (`governance/boundaries.yaml` is empty for this project regardless.)

## Check 9: Transition Gates — SKIP

Skipped per quick rigor tier rule. (`governance/gates.yaml` declares `transitions: {}` — no `implement-to-validate` transition is configured for this project regardless.)

## Check 11: Visual Verification — N/A

No UI files in this spec's implementation diff (`tests_e2e/*.py`, `pytest.ini`, `governance/gates.yaml` additions only). mock-jira is a headless HTTP API; this check is also disabled (`enabled: false`) in `governance/validate.yaml`.

## Check 14: Gate Executability and Test Collection — SKIP

Skipped per quick rigor tier rule (deterministic check beyond Check 1).

---

**Summary:** 1 dispatched check (Check 1: Quality Gates) passed. 6 checks skipped — 5 per resolved `quick` rigor tier (1.5, 1.6, 8, 9, 14), 1 (synthesized 2+4 compliance) skipped because subagent-review is disabled project-wide; Check 11 recorded N/A (no UI, and disabled). No failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
