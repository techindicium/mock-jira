---
kind: validate-report
spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md
plan: .context-index/specs/features/kanban-ui/issue-crud-forms.plan.md
date: 2026-09-05
overall_status: PASS
rigor_tier: full
---

# Validation Report: Issue create, edit, delete, and column move

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/issue-crud-forms.plan.md
> **Overall Status:** PASS

---

## Check 1: Quality Gates — PASS
- Tests (pytest): PASS — `41 passed, 4 warnings in 0.46s` (run via project `.venv`; the bare `python3` named in `governance/gates.yaml` resolves to a pytest-less system interpreter unless the repo's `.venv` is on `PATH` — see advisory below)
- Lint (ruff): PASS — `ruff check .` → "All checks passed!"
- JS Unit Tests (node --test): PASS — `44/44 tests passed, 0 failed` across `tests_js/**/*.test.js`
- Fast tier: all three gates PASS. No integration or e2e tier gates configured (`integration-test` gate has no `command`, skipped per gates.yaml).

**Advisory (non-blocking):** `governance/gates.yaml`'s `test` gate command is `[python3, -m, pytest, -q]` with no venv activation. In a shell without `.venv/bin` on `PATH`, this resolves to the Homebrew system `python3` (3.14) which lacks `pytest`, producing `No module named pytest`. The project ships a `.venv` (Python 3.12) and `requirements.txt` with pytest installed — the gate passes only when invoked with that venv active. This is an environment/CI-wiring gap in the gate definition, not a code defect; flagged for follow-up outside this validate run.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify` → "Check 1.5: PASS — source manifest matches (sha: a987602)"
- Implementation existence (git-tracked check, validator-side): all 10 manifest files confirmed committed via `git log --oneline -1 -- <file>`:
  - static/css/board.css → 6d51da4
  - static/index.html → c56ff1a
  - static/js/board-logic.js → f1eebe8
  - static/js/board.js → f1eebe8
  - tests_js/issue-crud-beh-1-create-issue.test.js → 2c0829d
  - tests_js/issue-crud-beh-2-edit-issue.test.js → c56ff1a
  - tests_js/issue-crud-beh-3-column-move.test.js → 6d51da4
  - tests_js/issue-crud-beh-4-delete-issue.test.js → f1eebe8
  - tests_js/issue-crud-beh-5-error-handling.test.js → 72373b1
  - tests_js/issue-crud-beh-6-create-validation.test.js → d8f30a0
  - No untracked/uncommitted-only files found among the manifest.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)
- `adev verify spec --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}`
- No drift detected for this spec's own source-manifest files. (Note: the sibling `board-view.spec.md` shows `drift_detected:true` because the shared `board-logic.js` was extended after that spec's manifest was stamped — this is a separate spec's concern, not this one's; not blocking here.)

## Check 2: Spec Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-2-spec-compliance` has `enabled: false` ("subagent-review — dropped for lightweight validation"). Per project governance posture, respected as-is.

## Check 4: Constitution Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-4-constitution` has `enabled: false`. Respected as-is.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","findings":[],"disabled":[],"warnings":[]}`
- No boundary rules are declared by this project — SKIP reflects that nothing was read, not that boundaries held.

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec <spec> --module kanban-ui --json` → `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions configured","gates":{}}`
- The project's `governance/gates.yaml` declares an empty `transitions: {}` map — no `implement-to-validate` transition is configured.

## Check 11: Visual Verification — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-11-visual-verification` has `enabled: false` (project-wide policy for this training-course repo). Respected as-is even though this spec is UI work (JS/HTML board forms). Playwright MCP is also currently unavailable in this session (`CONNECTION_CLOSED`), which is moot given the check is disabled at the config level regardless.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES (non-blocking, severity: warning per registry)
- `adev gate doctor --json` → 6 findings (1 error-severity, 5 warning-severity):
  - **error** `gate-doctor/glob-under-expansion` — the `test-js` gate's pattern `tests_js/**/*.test.js` matches 12 files under true `**` recursion (e.g., zsh) but 0 files under a plain `/bin/sh` invocation, where `**` degrades to a single `*` without globstar. If this gate is ever invoked by a runner that spawns via `/bin/sh`, all 12 JS test files would be silently skipped. Confirmed empirically in this run: the same argv list executed correctly under the zsh-backed Bash tool (44/44 tests collected), so the risk is specific to `sh`-based invocation paths (e.g., some CI images), not this validate run.
  - warning `gate-doctor/gate-set-divergence` — `integration-test` is declared in `gates.yaml` but absent from the merged/materialized set every consumer reads.
  - warning `gate-doctor/ci-config-missing` — no CI configuration found in the repo.
  - warning `gate-doctor/runner-unknown` (lint) — `ruff check .` has no recognized test-runner signature, so collection cannot be verified (expected — it is a linter, not a test runner).
  - warning `gate-doctor/runner-unknown` (test-js) — `node:test` has no collect-only mode; coverage is glob-analysis only.
  - warning `gate-doctor/empty-command` — the `integration-test` gate declares no command (documented sentinel — "unwired — no integration-test suite yet").
- This check's registry severity is `warning`, so it does not block the aggregate verdict, but the glob-under-expansion finding is worth remediating in `governance/gates.yaml` (e.g., pin the JS test gate to a shell-independent invocation, or ensure the CI runner uses a globstar-capable shell).

---

**Summary:** 5 checks ran and passed (1, 1.5, 1.6, 8/SKIP, 9/SKIP), 1 check ran with non-blocking notes (14), 3 checks skipped by project configuration (2, 4, 11 — all `enabled: false` per `governance/validate.yaml`'s lightweight-validation posture). 0 failures.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally runs `validate.check-14-gate-executability` (Gate Doctor), a project-level registry entry not documented in the base validate skill body.
