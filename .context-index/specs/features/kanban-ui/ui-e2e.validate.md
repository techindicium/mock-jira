---
kind: validate-report
spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md
plan: .context-index/specs/features/kanban-ui/ui-e2e.plan.md
date: 2026-09-06
overall_status: PASS_WITH_NOTES
rigor_tier: full
---

# Validation Report: End-to-end UI test suite (real browser)

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/kanban-ui/ui-e2e.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/ui-e2e.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS
- Preflight: infra_requirements declared the `playwright` CLI tool. `adev preflight run` initially reported `passed:false` (`missing_tools:["playwright"]`) because it probes the ambient `PATH`, not `.venv/bin`. Confirmed `playwright` is present at `.venv/bin/playwright` (`.venv/bin` is simply not on the invoking shell's PATH by default). Prepended `.venv/bin` to `PATH` and re-ran preflight — `passed:true`. This is a genuine false-negative in the preflight tool-check, not a real defect (matches the implement-step's known-issue note); no `--no-infra` bypass was used.
- Fast tier:
  - Tests (pytest): PASS — `105 passed, 3 warnings in 2.21s` (`.venv/bin/python3 -m pytest -q`)
  - Lint (ruff): PASS — `.venv/bin/ruff check .` → "All checks passed!"
  - JS Unit Tests (node --test): PASS — `44/44 tests passed, 0 failed` across `tests_js/**/*.test.js`
- Integration tier: no gates configured (`integration-test` gate has no `command`, skipped per `gates.yaml`).
- E2E tier: e2e-smoke (severity: warning, `required: false`) — PASS — `20 passed in 9.58s` (`.venv/bin/python3 -m pytest -q tests_e2e/`), a real Chromium browser driven by Playwright against the live server this suite starts on `127.0.0.1`. Longer wall-clock time than the fast tier is expected (browser launch overhead), not a failure.
- `gate_outcomes` attested: test=pass, lint=pass, test-js=pass, e2e-smoke=pass (manifest_sha: b49b915).

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify` → "Check 1.5: PASS — source manifest matches (sha: b49b915)"
- Implementation existence (git-tracked check, validator-side): all 12 manifest files confirmed committed via `git log --oneline -1 -- <file>`:
  - .context-index/constitution.md → 06356e6
  - README.md → 06356e6
  - requirements-e2e.txt → 06356e6
  - tests_e2e/browser.py → 06356e6
  - tests_e2e/conftest.py → 06356e6
  - tests_e2e/test_browser_fixture.py → 06356e6
  - tests_e2e/test_ui_board_render_e2e.py → 60a11e8
  - tests_e2e/test_ui_column_move_e2e.py → 4729f60
  - tests_e2e/test_ui_delete_issue_e2e.py → 7a3be05
  - tests_e2e/test_ui_error_path_e2e.py → 583d4f7
  - tests_e2e/test_ui_issue_forms_e2e.py → af3276f
  - tests_e2e/test_ui_project_switcher_e2e.py → 994cd51
  - No untracked/uncommitted-only files found among the manifest.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)
- `adev verify spec --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}`
- No drift detected for this spec's source-manifest files.

## Check 2: Spec Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-2-spec-compliance` has `enabled: false` ("subagent-review — dropped for lightweight validation"). Per project governance posture, respected as-is.

## Check 4: Constitution Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-4-constitution` has `enabled: false`. Respected as-is.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","findings":[],"disabled":[],"warnings":[],"summary":{"errors":0,"warnings":0,"infos":0,"files_checked":1}}`
- No boundary rules are declared by this project — SKIP reflects that nothing was read, not that boundaries held.

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec <spec> --json` → `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions configured","gates":{}}`
- The project's `governance/gates.yaml` declares an empty `transitions: {}` map — no `implement-to-validate` transition is configured.

## Check 11: Visual Verification — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-11-visual-verification` has `enabled: false` (project-wide governance posture for this training-course repo: "both subagent-review checks and visual-verification are disabled"). Respected as-is even though this spec is a genuine real-browser (Playwright/Chromium) UI test suite — the repo's project-wide governance decision on visual-verification applies regardless of how "real" the browser coverage underneath it is. No substitute check was performed. (Separately, the Playwright MCP server for this session reported `CONNECTION_CLOSED`, which is moot given the check is disabled at the config level regardless.)

## Check 14: Gate Executability and Test Collection — FAIL (non-blocking, severity: warning per registry)
- `adev gate doctor --json` → 9 findings (4 error-severity, 5 warning-severity):
  - **error** `gate-doctor/path-gitignored` (test) — gate enters `.venv/bin/python3`, which is gitignored; nothing creates that path first, so the gate only works locally, never in CI or a fresh clone.
  - **error** `gate-doctor/path-gitignored` (lint) — same issue for `.venv/bin/ruff`.
  - **error** `gate-doctor/path-gitignored` (e2e-smoke) — same issue for `.venv/bin/python3` (new gate added by this spec's implementation, inherits the pre-existing pattern).
  - **error** `gate-doctor/glob-under-expansion` (test-js) — the pattern `tests_js/**/*.test.js` matches 12 files under true `**` recursion (e.g. zsh) but 0 files under a plain `/bin/sh` invocation, where `**` degrades to a single `*` without globstar. Confirmed empirically in this run: the same argv executed correctly under the zsh-backed Bash tool (44/44 tests collected), so the risk is specific to `sh`-based invocation paths (e.g. some CI images), not this validate run.
  - warning `gate-doctor/gate-set-divergence` — `integration-test` is declared in `gates.yaml` but absent from the merged/materialized set every consumer reads.
  - warning `gate-doctor/ci-config-missing` — no CI configuration found in the repo.
  - warning `gate-doctor/runner-unknown` (lint) — `ruff check .` has no recognized test-runner signature (expected — it is a linter).
  - warning `gate-doctor/runner-unknown` (test-js) — `node:test` has no collect-only mode; coverage is glob-analysis only.
  - warning `gate-doctor/empty-command` — `integration-test` declares no command (documented sentinel — "unwired — no integration-test suite yet").
- This check's registry severity is `warning`, so per `lib/lifecycle-state.mjs` severity-weighted aggregation this FAIL rolls up to `PASS_WITH_NOTES` at the step level rather than blocking the overall verdict (confirmed via `adev state current` — `steps.validate.verdict: "PASS_WITH_NOTES"`). The three `path-gitignored` findings and the pre-existing `glob-under-expansion` finding describe a real, repo-wide gate-wiring gap (not introduced by this spec) that is worth remediating in `governance/gates.yaml` — e.g. activating the venv before invoking gate commands in CI, or pinning the JS test gate to a shell-independent invocation.

---

**Summary:** 6 checks ran and passed or SKIPped as expected (1, 1.5, 1.6, 8/SKIP, 9/SKIP), 1 check ran with non-blocking notes that roll up as PASS_WITH_NOTES (14 — severity: warning), 3 checks skipped by project configuration (2, 4, 11 — all `enabled: false` per `governance/validate.yaml`'s lightweight-validation posture). 0 blocking failures. Aggregate lifecycle verdict: **PASS_WITH_NOTES**.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally runs `validate.check-14-gate-executability` (Gate Doctor), a project-level registry entry not documented in the base validate skill body.
