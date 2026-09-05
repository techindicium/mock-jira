---
partial_schema: validate@1
spec: .context-index/specs/features/mcp-server/project-tools.spec.md
plan: .context-index/specs/features/mcp-server/project-tools.plan.md
date: 2026-09-05
overall_status: FAIL
---

# Validation Report: Project MCP tools (list_projects, create_project)

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/mcp-server/project-tools.spec.md
> **Plan:** .context-index/specs/features/mcp-server/project-tools.plan.md
> **Overall Status:** FAIL

---

## Governance Configuration Note

This repo's `governance/validate.yaml` enables only deterministic checks (Check 1 quality
gates, Check 1.5 source-manifest, Check 8 boundaries, Check 9 transition gates, Check 14 gate
executability). Both subagent-review checks (Check 2 spec compliance, Check 4 constitution
compliance) and Check 11 (visual verification) are `enabled: false`, respected as-is per this
project's intentionally lightweight training-course governance posture.

## Check 1: Quality Gates — FAIL
- Tier: fast (integration and e2e tiers have no gates configured; `integration-test` gate is
  an unwired sentinel with empty `command`, excluded from the resolved set)
- **Test Suite (`test`, `[python3, -m, pytest, -q]`): FAIL.**
  `/opt/homebrew/opt/python@3.14/bin/python3.14: No module named pytest`
  The `python3` binary resolved on `PATH` in this environment is Homebrew's system Python
  3.14, which has no `pytest` installed. The project's own virtualenv at `.venv` (Python
  3.12.13, created via `python3.12 -m venv`) does have `pytest` installed, and running the
  suite explicitly through it passes cleanly: `.venv/bin/python3 -m pytest -q` → **55 passed,
  3 warnings** (all three warnings are pre-existing `DeprecationWarning`s in `app/main.py` /
  `starlette`/`fastapi` unrelated to this spec's new `mcp_server/` code). This confirms the
  *implementation* is correct; the gate as literally configured in
  `governance/gates.yaml` (`command: [python3, -m, pytest, -q]`) does not activate or
  reference `.venv`, so it fails in any shell where `.venv/bin` is not first on `PATH` —
  including the shell this validation ran in, and (per the constitution's own `Commands`
  section documenting the identical bare `python3 -m pytest -q` invocation) presumably any
  CI runner that installs to a plain interpreter without pre-activating this project's venv.
  command_sha: `22c558be4a77b6dd61531053c7225bd05830d00bfaf46f14f430e2f0a6a0cb2b`
- **Linter (`lint`, `[ruff, check, .]`): SKIP** — intra-tier fail-fast after `test` failed with
  `severity: error`. (Diagnostic-only side check: run anyway for operator context — "All
  checks passed!" — so lint itself is not the problem.)
  command_sha: `91ede4a4ad8774e8660350d4580b9e41c235ea911f560571d82f5d4f81aba16d`
- **JS Unit Tests (`test-js`, `[node, --test, "tests_js/**/*.test.js"]`): SKIP** — intra-tier
  fail-fast after `test` failed. (Diagnostic-only side check: run anyway for operator context
  — 44/44 passed under `node --test` via its own internal glob resolution.)
  command_sha: `4d4e3bbfdf575dc83338694f6da0b95a44b8490751148497dfe931c5af571c77`

**Remediation:** either (a) update `governance/gates.yaml`'s `test` gate command to invoke the
project's venv interpreter explicitly (e.g. `[.venv/bin/python3, -m, pytest, -q]` or an
equivalent portable resolution), or (b) ensure `pytest` is installed to whatever `python3`
resolves to in the environment that runs quality gates (e.g. `pip install -r requirements.txt`
against the system interpreter), then re-run `/adev:validate`. This is an environment/gate
configuration defect, not a defect in the `mcp_server/` implementation.

Per the skill's fail-fast rule, Checks 2 through 13 are skipped except Check 1.5 (metadata,
runs regardless) — recorded below.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify`: PASS — source manifest matches (sha: `665525e`)
- Git-tracked check: all 13 manifest files verified committed via `git log --oneline -1 -- <file>`:
  `mcp_server/__init__.py`, `mcp_server/config.py`, `requirements-mcp.txt`,
  `tests/mcp_server/__init__.py`, `tests/mcp_server/conftest.py`, `tests/mcp_server/test_config.py`
  (commit `3b4c0cb`); `mcp_server/client.py`, `mcp_server/errors.py`,
  `tests/mcp_server/test_client.py` (commit `4349168`); `mcp_server/server.py`,
  `mcp_server/tools/__init__.py` (commit `4f48ffd`); `mcp_server/tools/projects.py`
  (commit `20c4b94`); `tests/mcp_server/test_project_tools.py` (commit `660ff9e`).

## Check 1.6: Code-Side Drift — PASS
- `adev verify spec --check-drift`: `{"drifted":false,"drift_source":null,"drift_at":null}` — no
  drift detected.

## Check 2 / Check 4 / Check 11 — SKIPPED-DISABLED
Disabled in `governance/validate.yaml` per this project's lightweight governance posture
(subagent-review checks and visual verification off; mock-jira is a headless HTTP-API-adjacent
MCP server with no UI). Would additionally be skipped by Check 1's fail-fast even if enabled.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `verdict: SKIP`, reason: `no boundary rules declared`.
  (No rules configured project-wide — nothing was read, so nothing held.)

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec <spec> --json` →
  `verdict: SKIP`, reason: `no transitions configured`. (`gates.yaml`'s `transitions: {}` is
  intentionally empty per its own scaffold comment — "left empty until this repo has real
  code.")

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
`adev gate doctor --json` → 6 findings (1 error, 5 warning):
- `gate-doctor/gate-set-divergence` (warning): `integration-test` declared in `gates.yaml` but
  absent from the merged set every consumer reads (empty command, correctly excluded).
- `gate-doctor/ci-config-missing` (warning): no CI configuration found in the repo.
- `gate-doctor/runner-unknown` (warning) ×2: `lint` (ruff) and `test-js` (node:test) have no
  identifiable collect-only mode for verifying test collection.
- `gate-doctor/glob-under-expansion` **(error)**: `test-js`'s glob `tests_js/**/*.test.js`
  degrades under a `sh`-mediated shell invocation (no globstar). **Verified non-issue for this
  gate as actually run**: the quality-gate runner invokes commands via `execFile` with
  `shell: false`, so the argv string reaches `node --test` directly and Node's own internal
  glob resolution expands it correctly — confirmed empirically (44/44 tests collected and
  passed when invoked that way). The finding is a legitimate portability warning for anyone
  wrapping this gate in a shell script, not a defect in the gate as currently wired.
- `gate-doctor/empty-command` (warning): `integration-test` declares no command (documented
  unwired sentinel).

---

**Summary:** 2 passed (1.5, 1.6), 1 passed-with-notes (14), 1 failed (1), 4 skipped (1
intra-tier fail-fast sub-gates counted within Check 1; 8 and 9 SKIP — nothing configured; 2, 4,
11 disabled by governance). **Overall: FAIL** — the `test` quality gate does not run as
configured outside an activated project virtualenv. The `mcp_server/` implementation itself is
verified correct (55/55 tests pass under `.venv`, ruff clean, source manifest matches, no
drift); the blocker is a gate-configuration/environment-portability issue in
`governance/gates.yaml`, not application code.

Fix the `test` gate's Python resolution (or the environment's `python3`) and re-run:
`/adev:validate --spec .context-index/specs/features/mcp-server/project-tools.spec.md --plan .context-index/specs/features/mcp-server/project-tools.plan.md`

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
