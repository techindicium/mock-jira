---
partial_schema: validate@1
spec: .context-index/specs/features/issue-tracker-api/user-directory.spec.md
plan: .context-index/specs/features/issue-tracker-api/user-directory.plan.md
date: 2026-09-06
overall_status: PASS_WITH_NOTES
---

# Validation Report: User directory (create/list/get)

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/issue-tracker-api/user-directory.spec.md
> **Plan:** .context-index/specs/features/issue-tracker-api/user-directory.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Governance Configuration Note

This repo's `governance/validate.yaml` enables only deterministic checks (Check 1 quality gates,
Check 1.5 source-manifest, Check 8 boundaries, Check 9 transition gates, Check 14 gate
executability). Both subagent-review checks (Check 2 spec compliance, Check 4 constitution
compliance) and Check 11 (visual verification) are `enabled: false`. Their coverage for this
spec was obtained via `/adev:review-specs` instead (`user-directory.review.md`, verdict
PASS_WITH_NOTES, both findings addressed in the spec before this validation ran).

## Check 1: Quality Gates — PASS
- Tier: fast (integration and e2e tiers have no required gates configured for this check)
- Test Suite (`test`, `.venv/bin/python3 -m pytest -q`): PASS — 122 passed, 3 warnings
  (pre-existing FastAPI `on_event`/anyio deprecation warnings, unrelated to this change).
  command_sha: 31b9c9a8d50289f3a13f014b3efd8ea3534fc3eea7ca7d9809e166139910b805
- Linter (`lint`, `.venv/bin/ruff check .`): PASS — "All checks passed!"
  command_sha: cb0cdeba051c5c5bdc85c22dc31440ac1ea17651366bf188d4df1f8fe985933a
- Integration Tests (`integration-test`): SKIPPED — `command: ""` (unwired sentinel, unchanged
  from prior validations). Not part of the resolved gate set.
- **Additional, not part of the required gate set but run for proportional coverage:**
  `.venv/bin/python3 -m pytest -q tests_e2e/test_user_directory_e2e.py` — PASS, 5 passed. The
  full non-UI/non-MCP e2e subset (`tests_e2e/ -k "not test_ui_ and not test_mcp_"`, 18 tests
  covering Project/Issue/OpenAPI/seed real-HTTP behavior) also PASS — no regression introduced
  in existing e2e coverage by this spec's `app/main.py`/`app/db.py`/`app/models.py` changes.
  UI (`test_ui_*`) and MCP (`test_mcp_*`) e2e suites were deliberately not run — out of this
  spec's scope (kanban-ui and mcp-server are separate charters/modules; a concurrent session is
  independently working on kanban-ui).

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify --spec user-directory.spec.md`: PASS — source manifest matches
  (sha: 6d65b3b)
- Git-tracked check: `app/routers/users.py`, `tests/test_users.py`,
  `tests_e2e/test_user_directory_e2e.py` are new, uncommitted-until-this-PR files on
  `feature/user-directory`; `app/models.py`, `app/db.py`, `app/main.py`, `app/seed.py`,
  `tests/test_db.py`, `tests/test_seed.py` are pre-existing tracked files, modified in place.
- **Cross-spec drift resolved:** this spec's implementation modified `app/db.py`, `app/main.py`,
  `app/models.py`, `app/seed.py`, `tests/test_db.py`, `tests/test_seed.py`, all of which are also
  listed in one or more already-`validated` sibling specs' own source-manifests
  (`project-management.spec.md`, `issue-lifecycle.spec.md`, `fixture-seeding.spec.md`). All three
  were re-stamped (`adev source-manifest compute --files ...`, same file lists, new SHAs) and now
  `adev source-manifest verify` PASSes clean for all three — no residual `drift_detected: true`
  remains on any sibling spec.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking, advisory)
- `adev source-manifest verify` reports a clean match for `user-directory.spec.md` and all three
  re-stamped siblings; no drift detected since each was stamped.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` verdict: **SKIP** — reason: "no boundary rules declared"
  (`governance/boundaries.yaml` declares `boundaries: []`).
- Findings: none. Disabled: none. Registry warnings: none. `files_checked: 22`.

## Check 9: Transition Gates — SKIP
- `governance/gates.yaml` declares `transitions: {}` — no `implement-to-validate` transition is
  configured to evaluate.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json`: 3 error-severity findings, 5 warning-severity findings (registry
  severity for this check is `warning` per `validate.yaml`, so it does not escalate the
  aggregate verdict to FAIL). All findings are **pre-existing repository conditions, unrelated to
  this spec's change**:
  - **error** `gate-doctor/path-gitignored` (x3: `test`, `lint`, `e2e-smoke` gates) — each gate's
    command enters a `.venv/bin/...` path, which is gitignored, so the gate only works for
    whoever created the venv locally. Pre-existing since the gates were first wired
    (`project-management.validate.md` already flagged the `test` gate's PATH issue under a
    slightly different framing).
  - **warning** `gate-doctor/gate-set-divergence` — `integration-test` declared but dropped from
    the merged set (`command: ""`). Pre-existing.
  - **warning** `gate-doctor/ci-config-missing` — no CI configuration exists. Pre-existing.
  - **warning** `gate-doctor/runner-unknown` (x2: `lint`, `test-js`) — linter/no-collect-only
    runners can't be verified for test collection. Pre-existing, expected for a linter.
  - **warning** `gate-doctor/glob-under-expansion` — `test-js` gate's glob pattern under-expands
    on `sh`. Belongs to the kanban-ui charter's JS test suite, entirely outside this spec's
    scope (`app/`, `tests/`, `tests_e2e/` only) and untouched by this change.
  - **warning** `gate-doctor/empty-command` — `integration-test` declares no command. Pre-existing.

None of these findings were introduced by this spec's implementation; all predate it and apply
equally to every other spec in this repo.

---

**Summary:** 4 passed (Check 1, 1.5, 1.6 advisory, 14 with notes), 2 skipped by configuration
(Check 8, 9 — no rules/transitions declared), 0 failed. Checks 2, 4, 11 disabled by project
governance (`validate.yaml`), not run — spec-compliance and constitution-compliance coverage for
this spec's behaviors was already obtained via `/adev:review-specs` (see `user-directory.review.md`).

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance, cross-cutting compliance, specialist review, and
>   charter consistency. Also the place to recover spec-compliance (Check 2) and
>   constitution-compliance (Check 4) coverage, both disabled here by project governance.
> - `/adev:hygiene` Audit Pass 20 — for platform drift.
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation.
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction, now a
>   non-blocking Stop-event hook.

## Scope Confirmation

- No existing `Project`/`Issue` HTTP endpoint, request/response shape, or status code changed.
- `Issue.assignee`/`Issue.reporter` remain free-text strings — confirmed by
  `tests/test_issues.py` (untouched, still passing) and no code change to
  `app/routers/issues.py`.
- All work stayed within `issue-tracker-api`'s own files (`app/`, `tests/`, `tests_e2e/`) and this
  charter's own spec directory. No file under `static/`,
  `.context-index/specs/features/kanban-ui/`, or `mcp-server/` was read or modified.
