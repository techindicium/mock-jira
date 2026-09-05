---
partial_schema: validate@1
spec: .context-index/specs/features/issue-tracker-api/project-management.spec.md
plan: .context-index/specs/features/issue-tracker-api/project-management.plan.md
date: 2026-09-04
overall_status: PASS_WITH_NOTES
---

# Validation Report: Project management and OpenAPI contract

> **Date:** 2026-09-04
> **Spec:** .context-index/specs/features/issue-tracker-api/project-management.spec.md
> **Plan:** .context-index/specs/features/issue-tracker-api/project-management.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Governance Configuration Note

This repo's `governance/validate.yaml` enables only deterministic checks (Check 1 quality
gates, Check 1.5 source-manifest, Check 8 boundaries, Check 9 transition gates, Check 14 gate
executability). Both subagent-review checks (Check 2 spec compliance, Check 4 constitution
compliance) and Check 11 (visual verification) are `enabled: false`, respected as-is per this
project's intentionally lightweight training-course governance posture. Their prior coverage
is available on demand via `/adev:review-specs`.

## Check 1: Quality Gates — PASS
- Tier: fast (integration and e2e tiers have no gates configured)
- Test Suite (`test`, `python -m pytest -q`): PASS — 11 passed, 4 warnings (deprecation
  warnings only: `httpx` TestClient shim, `anyio.abc.BlockingPortal`, FastAPI `on_event`
  lifespan deprecation). command_sha: c3f2578d3a465d10ae97391fe2a54f1c10832286381277ce1355ccfb0bbac529
- Linter (`lint`, `ruff check .`): PASS — "All checks passed!" command_sha: 91ede4a4ad8774e8660350d4580b9e41c235ea911f560571d82f5d4f81aba16d
- Integration Tests (`integration-test`): SKIPPED — `command: ""` (unwired sentinel, no suite exists yet per gates.yaml comment). Not part of the resolved gate set.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify`: PASS — source manifest matches (sha: 2171931)
- Git-tracked check: all 13 manifest files verified committed (`git log --oneline -1 -- <file>`
  returned at least one commit for every file: `app/__init__.py`, `app/db.py`, `app/errors.py`,
  `app/main.py` (2 commits), `app/models.py`, `app/routers/__init__.py`,
  `app/routers/projects.py` (3 commits), `requirements.txt`, `tests/__init__.py`,
  `tests/conftest.py`, `tests/test_db.py`, `tests/test_openapi.py`, `tests/test_projects.py`
  (3 commits)). No untracked/uncommitted manifest files.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking, advisory)
- `adev verify spec --check-drift`: `{"drifted":false,"drift_source":null,"drift_at":null}` —
  no drift detected since the spec was stamped.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` verdict: **SKIP** — reason: "no boundary rules declared"
  (`governance/boundaries.yaml` declares `boundaries: []`). Not "boundaries held" — nothing was
  declared to check.
- Findings: none. Disabled: none. Registry warnings: none.

## Check 9: Transition Gates — SKIP
- Transition evaluated: `implement-to-validate`
- `adev gate transitions --json` verdict: **SKIP** — reason: "no transitions configured"
  (`governance/gates.yaml` declares `transitions: {}`).

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json`: 1 error-severity finding, 4 warning-severity findings (registry
  severity for this check is `warning`, so it does not escalate the aggregate verdict to FAIL,
  per `validate.yaml`'s explicit design for this check).
  - **error** `gate-doctor/binary-not-found` — Gate `test`'s command uses bare `python`, which
    is not on the invoking shell's PATH (only `python3` resolves there); the project's `.venv`
    provides `python` only when activated or invoked directly as `.venv/bin/python`. The gate
    ran successfully in this session because the check runner invoked `.venv/bin/python -m
    pytest -q` explicitly, but the gate as literally declared in `gates.yaml` (`[python, -m,
    pytest, -q]`) would fail on a bare PATH lookup outside an activated venv or CI step that
    doesn't prepend `.venv/bin`. **Recommendation:** point the `test` gate's command at
    `.venv/bin/python` (or ensure CI/dev shells activate the venv before gates run).
  - **warning** `gate-doctor/gate-set-divergence` — `integration-test` is declared in
    `governance/gates.yaml` but dropped from the domain-merged set (empty `command: ""`), so
    the raw file and the set that actually runs disagree.
  - **warning** `gate-doctor/ci-config-missing` — no CI configuration found; gates only ever
    run on a developer's machine.
  - **warning** `gate-doctor/runner-unknown` — the `lint` gate's runner (`ruff check .`) is not
    a recognized test framework, so test collection can't be verified for it (expected — it's a
    linter, not a test suite).
  - **warning** `gate-doctor/empty-command` — `integration-test` declares no command (matches
    the unwired-sentinel note already in `gates.yaml`).

---

**Summary:** 4 passed (Check 1, 1.5, 1.6 advisory, 14 with notes), 2 skipped by configuration
(Check 8, 9 — no rules/transitions declared), 0 failed. Checks 2, 4, 11 disabled by project
governance (`validate.yaml`), not run.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly
>   Check 3, now covered by Check 2's scope-expansion sub-finding). Also the place to recover
>   spec-compliance (Check 2) and constitution-compliance (Check 4) coverage, both disabled here
>   by project governance.
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly
>   Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.

## Known Non-Blocking Gap Carried From Implementation

Per the implement step's summary: `adev issues show/close` could not resolve `epic-kphf39`
(apparent CLI bug in the json issues backend for epics), so the epic was not closed via CLI.
This does not affect validation of the spec's behavioral contract and is out of scope for
`/adev:validate` — it is an issue-board bookkeeping matter, not a code-quality or spec-compliance
one.
