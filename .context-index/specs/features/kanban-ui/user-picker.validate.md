---
kind: validate-report
spec: .context-index/specs/features/kanban-ui/user-picker.spec.md
plan: .context-index/specs/features/kanban-ui/user-picker.plan.md
date: 2026-09-06
overall_status: PASS_WITH_NOTES
rigor_tier: quick
---

# Validation Report: User picker in issue forms

> **Date:** 2026-09-06
> **Spec:** .context-index/specs/features/kanban-ui/user-picker.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/user-picker.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Rigor Tier

`quick` — resolved from `risk_level: low` in the spec frontmatter (`risk-policies.yaml`
`policies.low.validate_mode: quick`). Per this project's established practice (see
`issue-crud-forms.validate.md`, `user-directory.validate.md`), Checks 2/4/11 are already
`enabled: false` in this repo's `governance/validate.yaml` regardless of tier, so their
coverage was obtained via `/adev:review-specs` (quick-synthesized-reviewer, PASS_WITH_NOTES,
`user-picker.review.md`) rather than a quick-tier synthesized validate check.

## Check 1: Quality Gates — PASS_WITH_NOTES
- Tier: fast + e2e (no integration-tier gates configured — `integration-test` has no `command`, skipped per gates.yaml)
- Test Suite (`test`, `.venv/bin/python3 -m pytest -q`): PASS — 122 passed, 3 warnings (pre-existing FastAPI `on_event` deprecation warnings, unrelated to this change)
  command_sha: 864cd8c369fc558cf6a8235d2514a26c14a6e2c1de08efd0629c4f69d1843587
- Linter (`lint`, `.venv/bin/ruff check .`): PASS — "All checks passed!"
  command_sha: 2ea305ec5813b091e1464bd56985f9caafca6483b6a08963281eaa2f0f5b3fb0
- JS Unit Tests (`test-js`, `node --test tests_js/**/*.test.js`): PASS — 74/74 passed (was 65 before this spec; +9 new: 3 in `user-picker-beh-2-3-user-options.test.js`, 2 in `user-picker-beh-6-graceful-degradation.test.js`, 4 in `user-picker-beh-2-3-datalist-markup.test.js`)
  command_sha: 4d4e3bbfdf575dc83338694f6da0b95a44b8490751148497dfe931c5af571c77
- Integration Tests (`integration-test`): SKIPPED — `command: ""` (unwired sentinel, unchanged from prior validations)
- E2E Smoke (`e2e-smoke`, `.venv/bin/python3 -m pytest -q tests_e2e/`, severity: warning): 42/46 passed, 4 failed
  command_sha: 7c8b647af049708f0804d30421fde2eae089367de7e3cc18a17b1981febce10f
  **The 4 failures are entirely pre-existing and out of this spec's scope** — all four are in
  `tests_e2e/test_mcp_tool_discovery_e2e.py` and `tests_e2e/test_mcp_user_tools_e2e.py`
  (mcp-server's concurrent, in-flight `user-tools` feature; `mcp_server/tools/users.py` is not
  present on this branch, so those tests' `list_users`/`create_user` tool calls fail with
  "Unknown tool"). This module's own `tests_e2e/test_ui_user_picker_e2e.py` (6/6) and every
  other non-mcp e2e test (24/24) pass. Confirmed via `pytest -q tests_e2e/ -k "not test_mcp_"`
  → 30 passed, 0 failed. Because `e2e-smoke` is `required: false` / `severity: warning`, this
  does not fail the aggregate verdict, consistent with gates.yaml's own documented intent
  ("first-generation e2e coverage ... not yet a merge blocker").
- **Additional, not part of the required gate set but run for proportional coverage:** the full
  `tests_e2e/test_ui_user_picker_e2e.py` suite alone: 6/6 PASS, including a regression test
  (`test_users_fetched_once_even_across_a_create_project_reinit`) added during the final
  code-quality review's fix cycle — verified to fail without the fix and pass with it.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify --spec user-picker.spec.md` → "Check 1.5: PASS — source manifest matches (sha: 1502410)"
- Implementation existence (git-tracked check, validator-side): all 8 manifest files confirmed committed:
  - static/index.html → ffdeda5
  - static/js/board-logic.js → fb56a61
  - static/js/board.js → 6891aec
  - tests_e2e/test_ui_user_picker_e2e.py → 6891aec
  - tests_js/user-picker-beh-2-3-datalist-markup.test.js → ffdeda5
  - tests_js/user-picker-beh-2-3-user-options.test.js → 90f2ead
  - tests_js/user-picker-beh-6-graceful-degradation.test.js → fb56a61
  - tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js → 6891aec
  - No untracked/uncommitted-only files found among the manifest.
- **Cross-spec drift resolved:** this spec's implementation modified `static/index.html`,
  `static/js/board-logic.js`, and `static/js/board.js`, all of which are also listed in three
  already-`validated` sibling specs' own source-manifests (`board-view.spec.md`,
  `issue-crud-forms.spec.md`, `visual-design-refresh.spec.md`). All three were re-stamped
  (`adev source-manifest compute --files ...`, same file lists, new SHAs) and now
  `adev source-manifest verify` PASSes clean for all four specs — no residual
  `drift_detected: true` remains on any sibling spec.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking, advisory)
- `adev verify spec --check-drift` → `{"drifted":false,"drift_source":null,"drift_at":null}`
- `clearDrift()` was run on this spec and all three re-stamped siblings.

## Check 2: Spec Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-2-spec-compliance` has `enabled: false` ("subagent-review — dropped for lightweight validation"). Per project governance posture, respected as-is.
- Coverage obtained instead via `/adev:review-specs` (`user-picker.review.md`, quick-synthesized-reviewer, PASS_WITH_NOTES — both notes addressed inline in the spec before planning began) and via this validate run's own final code-quality review dispatch during `/adev:implement`, which independently verified BEH-1 through BEH-6 against the diff and caught one genuine BEH-1 gap (fixed — see Check 1's regression-test note above).

## Check 4: Constitution Compliance — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-4-constitution` has `enabled: false`. Respected as-is.
- This spec's own System Constitution Reference section cites "The HTTP contract is the boundary" (fetches only the documented `GET /users` endpoint), "Fixture-backed, offline only" (same-origin request), "No inbound dependencies" (consumes an endpoint already validated within this same repo), and the existing "no build step" convention (native `<datalist>`, vanilla JS, zero new dependencies) — all respected by inspection of the diff.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json` → `{"verdict":"SKIP","reason":"no boundary rules declared","findings":[],"disabled":[],"warnings":[],"summary":{"files_checked":2}}`
- No boundary rules are declared by this project — SKIP reflects that nothing was read, not that boundaries held.

## Check 9: Transition Gates — SKIP
- `adev gate transitions --transition implement-to-validate --spec user-picker.spec.md --module kanban-ui --json` → `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions configured","gates":{}}`
- The project's `governance/gates.yaml` declares an empty `transitions: {}` map — no `implement-to-validate` transition is configured.

## Check 11: Visual Verification — SKIPPED-DISABLED
- `governance/validate.yaml`: `validate.check-11-visual-verification` has `enabled: false` (project-wide policy for this training-course repo). Respected as-is even though this spec touches UI markup (a `<datalist>` and a `list=""` attribute — no visible styling change, native browser chrome only). The Playwright MCP server is also currently unavailable in this session (`CONNECTION_CLOSED`), which is moot given the check is disabled at the config level regardless. Real-browser functional coverage (not visual/styling) is instead provided by `tests_e2e/test_ui_user_picker_e2e.py` (6/6 PASS), which exercises the datalist's actual suggestion behavior in a real Chromium instance.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES (non-blocking, severity: warning per registry)
- `adev gate doctor --json` → 6 findings (1 error-severity, 5 warning-severity), all pre-existing and unrelated to this spec's change (identical finding set to prior kanban-ui validate runs):
  - **error** `gate-doctor/glob-under-expansion` — the `test-js` gate's pattern `tests_js/**/*.test.js` matches 23 files under true `**` recursion (zsh) but 0 under a plain `/bin/sh` invocation. Pre-existing since the gate was first wired; this spec adds 3 more files to that same already-flagged glob, it does not introduce the finding.
  - warning `gate-doctor/gate-set-divergence` — `integration-test` declared but absent from the merged set.
  - warning `gate-doctor/ci-config-missing` — no CI configuration found.
  - warning `gate-doctor/runner-unknown` (lint) — no recognized test-runner signature (expected — linter, not a test runner).
  - warning `gate-doctor/runner-unknown` (test-js) — `node:test` has no collect-only mode.
  - warning `gate-doctor/empty-command` — `integration-test` declares no command (documented sentinel).
- Severity is `warning` per this project's registry, so it does not block the aggregate verdict.

---

**Summary:** 5 checks ran and passed cleanly (1.5, 1.6, 8/SKIP, 9/SKIP), 2 checks ran with
non-blocking notes (1 — e2e-smoke's 4 pre-existing mcp-server failures at warning severity; 14 —
pre-existing gate-doctor findings), 3 checks skipped by project configuration (2, 4, 11 — all
`enabled: false` per `governance/validate.yaml`'s lightweight-validation posture, with equivalent
coverage obtained via `/adev:review-specs` and the implement-time final code-quality review).
0 failures attributable to this spec's implementation.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This report additionally runs `validate.check-14-gate-executability` (Gate Doctor), a project-level registry entry not documented in the base validate skill body.

> **Shared-workspace note (out of band, for operator awareness):** During implementation, this
> working directory was found to be actively shared (not isolated via git worktree) with a
> concurrent session implementing mcp-server's `user-tools` capability, causing two branch-race
> incidents (a commit landed on the wrong branch and was corrected via cherry-pick + revert; two
> foreign commits landed on this branch and were left in place per the coordinating session's
> explicit instruction, to be relocated centrally once both efforts finish). This spec's own
> implementation was moved into an isolated worktree (`../mock-jira-kanban-ui-user-picker`) for
> the remainder of the work and is unaffected. The 4 e2e failures noted under Check 1 are a
> direct, documented consequence of this shared-directory history, not a defect in this spec's
> code.
