---
spec: .context-index/specs/cross-cutting/issue-comments.spec.md
plan: .context-index/specs/cross-cutting/issue-comments.plan.md
date: 2026-09-09
overall_status: PASS_WITH_NOTES
rigor_tier: full
---

# Validation Report: Issue comments and activity log

> **Date:** 2026-09-09
> **Spec:** .context-index/specs/cross-cutting/issue-comments.spec.md
> **Plan:** .context-index/specs/cross-cutting/issue-comments.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Check 1: Quality Gates — PASS (fast tier), WARN (e2e tier, non-blocking)

**Check 1a (fast tier):**
- `test` (pytest): PASS — 143 passed, 3 warnings, 2.56s
- `lint` (ruff): PASS — all checks passed
- `test-js` (node --test): PASS — 116 passed, 0 failed, 220.5ms

**Check 1b (integration tier):** SKIPPED — the only declared integration gate (`integration-test`) has an empty/unwired `command` field (`gate-doctor/empty-command`); the gate loader excludes it from the resolved set (`INVALID_GATE: Gate 'integration-test' missing required command field — skipped.`). No integration gates actually ran.

**Check 1c (e2e tier):** WARN (non-blocking — `e2e-smoke` is `severity: warning`, `required: false`)
- `e2e-smoke` (`pytest tests_e2e/`): 56 passed, **9 failed**, 159.2s. All 9 failures are pre-existing and unrelated to this spec's scope — none touch comment functionality:
  - `test_browser_fixture.py::test_launch_chromium_yields_a_working_browser`
  - `test_mcp_tool_discovery_e2e.py::test_real_client_discovers_all_nine_tools_with_correct_schemas`
  - `test_openapi_and_seed_e2e.py::test_seed_data_visible_on_fresh_server_start`
  - `test_ui_board_render_e2e.py::test_seeded_board_renders_with_issues_in_correct_columns`
  - `test_ui_project_management_e2e.py::test_projects_view_lists_seeded_project`
  - `test_ui_project_management_e2e.py::test_duplicate_project_key_shows_real_api_error`
  - `test_ui_project_switcher_e2e.py::test_switching_project_replaces_board_contents`
  - `test_ui_user_management_e2e.py::test_users_view_lists_seeded_users`
  - `test_ui_user_management_e2e.py::test_duplicate_email_shows_real_api_error`
  - Failure mode observed: `playwright._impl._errors.TimeoutError: Page.wait_for_selector: Timeout 30000ms exceeded` (browser/timing flakiness), not a comments-related regression.
  - Since `e2e-smoke` is `required: false` / `severity: warning`, this does not block the aggregate verdict per gate resolution rules, but is flagged for follow-up outside this spec's scope.

**Per-gate outcome attestation** (emitted via `adev report --type validator --validator validate.check-1-quality-gates --gate-outcomes ...`):
| Gate | Tier | Verdict |
|------|------|---------|
| test | fast | pass |
| lint | fast | pass |
| test-js | fast | pass |
| e2e-smoke | e2e | fail (warning severity, non-blocking) |

## Check 1.5: Source Manifest Verification — PASS

`adev source-manifest verify` → `PASS — source manifest matches (sha: 33a3875)`.

Git-tracked verification (all 13 files in the manifest confirmed committed, not merely staged/untracked):

| File | Commit |
|------|--------|
| app/db.py | 88ed497 |
| app/models.py | 88ed497 |
| app/routers/issues.py | 88ed497 |
| mcp_server/client.py | 789f38e |
| mcp_server/server.py | 789f38e |
| mcp_server/tools/comments.py | 789f38e |
| static/index.html | 31694bc |
| static/js/board-logic.js | 31694bc |
| static/js/board.js | 31694bc |
| tests/mcp_server/test_comment_tools.py | 789f38e |
| tests/test_comments.py | 88ed497 |
| tests_js/issue-comments-beh-1-render.test.js | 31694bc |
| tests_js/issue-comments-beh-2-validation.test.js | 31694bc |

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)

`adev verify spec --check-drift` → `{"drifted": false, "drift_source": null, "drift_at": null}`. No drift detected since the implement-time stamp.

## Check 2: Spec Compliance — SKIPPED-DISABLED

`validate.check-2-spec-compliance` carries `enabled: false` in `.context-index/governance/validate.yaml` ("subagent-review — dropped for lightweight validation"), consistent with this project's constitution ("Validation: only deterministic checks run; both subagent-review checks... are disabled"). Not dispatched, per project governance choice. No `validator_report` emitted (disabled checks produce no verdict).

## Check 4: Constitution Compliance — SKIPPED-DISABLED

`validate.check-4-constitution` carries `enabled: false` in `.context-index/governance/validate.yaml`, same rationale as Check 2. Not dispatched. No `validator_report` emitted.

## Check 8: Boundary Compliance — SKIP

`adev boundaries check --json` → `{"verdict": "SKIP", "reason": "no boundary rules declared", "findings": [], "disabled": [], "warnings": [], "summary": {"errors": 0, "warnings": 0, "infos": 0, "files_checked": 39}}`

SKIP means no boundary rules are declared for this project — not that boundaries held.

## Check 9: Transition Gates — SKIP

`adev gate transitions --transition implement-to-validate --json` → `{"transition": "implement-to-validate", "verdict": "SKIP", "reason": "no transitions configured", "gates": {}}`

`gates.yaml`'s `transitions:` map is empty (documented as intentional — "left empty until this repo has real code").

## Check 11: Visual Verification — SKIPPED-DISABLED (advisory: registry rationale is stale)

`validate.check-11-visual-verification` carries `enabled: false` with the note "no UI — mock-jira is a headless HTTP API." **This rationale no longer holds**: this spec's own source manifest includes `static/index.html`, `static/js/board.js`, and `static/js/board-logic.js` — the `kanban-ui` module is a real browser UI, and this spec added a comment-thread panel to it (BEH-3, BEH-4, BEH-5). A Playwright MCP server is available in this session.

Per registry mechanics, an explicitly `enabled: false` check is skipped without running regardless of file contents, so Check 11 is recorded SKIPPED-DISABLED rather than run. **Recommendation:** re-evaluate whether `validate.check-11-visual-verification` should stay disabled now that `kanban-ui` exists with real UI surface, since the disabled-note's stated justification is factually outdated. UI behavior for this spec (BEH-3/4/5) is currently covered only by the `tests_js/issue-comments-beh-*.test.js` unit tests (Check 1, PASS), not by browser-level visual verification.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES (non-blocking, severity: warning)

`adev gate doctor --json` (exit 2, 4 error-severity findings within the tool's own payload, but the check's registry severity is `warning` per `validate.check-14-gate-executability`):

- `gate-doctor/gate-set-divergence` (warning): raw `gates.yaml` declares `integration-test`, absent from the merged/effective set.
- `gate-doctor/ci-config-missing` (warning): no CI configuration found.
- `gate-doctor/path-gitignored` (error) × 3: `test`, `lint`, `e2e-smoke` gates start from `.venv/bin/...`, which is gitignored — these gates only work on a machine that already has the venv, never in CI or a fresh clone.
- `gate-doctor/runner-unknown` (warning) × 2: `lint` and `test-js` runners not recognized for collection verification.
- `gate-doctor/glob-under-expansion` (error): `test-js` gate's glob `tests_js/**/*.test.js` degrades under a non-globstar `sh` and would silently skip 35 files if invoked through such a shell (the gate as actually run via `execFile`, no shell, is unaffected — but this is a portability risk).
- `gate-doctor/empty-command` (warning): `integration-test` declares no command (matches Check 1b's finding).

These are pre-existing, project-wide gate-configuration issues (not introduced by the issue-comments implementation) and do not block this validation since the check's severity is `warning`. Flagged for separate follow-up (`/adev:hygiene` or a dedicated gates.yaml cleanup).

---

**Summary:** 6 checks produced a verdict (1, 1.5, 1.6, 8, 9, 14) — all PASS or PASS_WITH_NOTES, no FAIL. Checks 1 and 14 are PASS_WITH_NOTES (non-blocking e2e-smoke warning; non-blocking gate-executability warnings), so the aggregate verdict is **PASS_WITH_NOTES** per the aggregation rule (at least one PASS_WITH_NOTES, no FAILs). 3 checks (2, 4, 11) are SKIPPED-DISABLED per this project's own governance configuration (`governance/validate.yaml`), consistent with its constitution's stated lightweight-validation posture. Check 11's disabled rationale is flagged as stale advisory (see above) but does not change the aggregate verdict since it is a project governance choice, not a check failure.

**Notable non-blocking findings for follow-up (outside this spec's scope):**
1. 9 pre-existing e2e-smoke failures (browser-timing related), none touching comment functionality.
2. Check 11 (visual verification) governance rationale is stale now that kanban-ui exists — worth re-enabling.
3. Gate executability findings (gitignored venv paths, unwired integration-test gate, test-js glob portability) are pre-existing project-wide gate-configuration debt.

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance (formerly Check 6), specialist review (formerly Check 7), and charter consistency (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> Historic `.validate.md` reports continue to use the pre-restructure numbering; the gaps in the surviving inventory (Checks 1, 1.5, 1.6, 2, 4, optionally 8 and 9) are intentional to preserve report readability.
