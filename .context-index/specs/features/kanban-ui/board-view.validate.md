---
spec: .context-index/specs/features/kanban-ui/board-view.spec.md
plan: .context-index/specs/features/kanban-ui/board-view.plan.md
date: 2026-09-05
overall_status: PASS_WITH_NOTES
rigor_tier: quick
---

# Validation Report: Kanban board view, project switcher, and project creation

> **Date:** 2026-09-05
> **Spec:** .context-index/specs/features/kanban-ui/board-view.spec.md
> **Plan:** .context-index/specs/features/kanban-ui/board-view.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Rigor Tier

Resolved tier: **quick** (risk_level: medium → `policies.medium.validate_mode: quick` in
`governance/risk-policies.yaml`). No `--tier` override, no routing signal.

Per project governance (`governance/validate.yaml`, mirrored in `CLAUDE.md`'s Governance
Posture), **all subagent-review checks (2, 4, 11) are disabled project-wide** for this
lightweight-validation repo. Since quick tier's synthesized compliance check would itself be a
subagent-review dispatch substituting for disabled Checks 2 and 4, it was not run — there is
nothing for it to synthesize. Instead, the full set of enabled deterministic checks (1, 1.5, 8,
9, 14) was run to produce a substantive report.

## Check 1: Quality Gates — PASS
- Test (fast, `python3 -m pytest -q`): PASS — 41 passed, 0 failed
- Lint (fast, `ruff check .`): PASS — all checks passed
- JS Unit Tests (fast, `node --test tests_js/**/*.test.js`): PASS — 23 passed, 0 failed
- Integration tier: no gates configured (`integration-test` gate is unwired — empty `command`,
  seeded as a sentinel per its own comment in `gates.yaml`; skipped with `INVALID_GATE` warning
  by `adev domain load-gates`, consistent with the project's stated intent)
- E2E tier: no gates configured

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify` → PASS — sha `5ff0304` matches current file contents.
- All 13 manifest files verified present on disk and committed to git (spot-checked via
  `git log --oneline -1 -- <file>` for each): `.context-index/governance/gates.yaml`,
  `app/main.py`, `static/css/board.css`, `static/index.html`, `static/js/board-logic.js`,
  `static/js/board.js`, `tests/test_static_assets.py`, and all six `tests_js/beh-*.test.js`
  files. None are untracked or staged-only.

## Check 1.6: Code-Side Drift Warning — PASS (non-blocking)
- `adev verify spec --check-drift` → `{"drifted": false}` for this spec's own manifest.
- Note (informational, out of scope for this validate run): the implement summary reports
  `drift_detected: true` on issue-tracker-api's `project-management`, `issue-lifecycle`, and a
  third spec, because the shared `app/main.py` was modified here to add the static mount. That
  drift belongs to those specs, not to board-view.spec.md, and was already flagged as deferred
  housekeeping by the implementer.

## Check 2: Spec Compliance — SKIPPED-DISABLED
`validate.check-2-spec-compliance` has `enabled: false` in `governance/validate.yaml`
("subagent-review — dropped for lightweight validation"). Not dispatched, per project
governance. Does not contribute to the verdict.

## Check 4: Constitution Compliance — SKIPPED-DISABLED
`validate.check-4-constitution` has `enabled: false` in `governance/validate.yaml`
("subagent-review — dropped for lightweight validation"). Not dispatched, per project
governance. Does not contribute to the verdict.

## Check 8: Boundary Compliance — PASS_WITH_NOTES (SKIP)
- `adev boundaries check --json` → `{"verdict": "SKIP", "reason": "no boundary rules
  declared", "findings": [], "disabled": [], "warnings": []}`
- The project declares no boundary rules; this is a SKIP, not evidence the boundaries held.

## Check 9: Transition Gates — PASS_WITH_NOTES (SKIP)
- `adev gate transitions --transition implement-to-validate --module kanban-ui --json` →
  `{"transition": "implement-to-validate", "verdict": "SKIP", "reason": "no transitions
  configured", "gates": {}}`
- `governance/gates.yaml` declares `transitions: {}` — no gates are wired to this transition.

## Check 11: Visual Verification — SKIPPED-DISABLED
`validate.check-11-visual-verification` has `enabled: false` in `governance/validate.yaml`
("no UI — mock-jira is a headless HTTP API"). This comment predates the kanban-ui module;
board-view.spec.md is in fact a UI feature. Per explicit instruction for this validation run,
this is respected as-is and **not substituted for** — visual verification is deliberately
disabled project-wide in this training-course repo, independent of whether any given spec has
UI files. Not dispatched. Does not contribute to the verdict.

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
`adev gate doctor --json` (severity: warning per registry) returned 6 findings:
- **error-level (within the doctor's own internal scale, but bounded to `warning` by this
  check's registry severity):** `gate-doctor/glob-under-expansion` — the `test-js` gate's
  pattern `tests_js/**/*.test.js` matches 6 files under true `**` recursion but would match 0
  files if ever expanded by `sh` (which lacks globstar and degrades `**` to `*`). In practice
  this does not currently bite: the quality-gate runner (`lib/governance/quality-gate.mjs`)
  invokes gates via `execFile` with `shell: false`, so the glob string is handed to `node`
  directly and `node --test` expands it internally — confirmed by direct execution in this run
  (23/23 passed across all 6 files). This is a legitimate portability caveat should the command
  ever be re-wrapped in a shell script (e.g., a future CI config), not a live defect today.
- `gate-doctor/ci-config-missing` (warning) — no CI configuration found in this repo.
- `gate-doctor/runner-unknown` (warning) x2 — for `lint` (ruff has no recognized collect-only
  mode) and `test-js` (node:test has no collect-only mode); test collection could not be
  independently verified for either, only the glob-match analysis.
- `gate-doctor/empty-command` (warning) — `integration-test` gate declares no command (known,
  intentional unwired sentinel per its own comment in `gates.yaml`).
- `gate-doctor/gate-set-divergence` (warning) — the raw `gates.yaml` gate set and the
  domain-merged set disagree (raw declares `integration-test`, merged set omits it since it has
  no command) — same root cause as `empty-command`, surfaced from a different angle.

None of these findings are new regressions introduced by this spec's implementation; all trace
to the pre-existing unwired `integration-test` sentinel and the absence of a CI pipeline in this
training-course repo.

---

**Summary:** 4 passed (Check 1, Check 1.5, Check 1.6, and the constituent commands they cover),
3 passed-with-notes (Check 8 SKIP, Check 9 SKIP, Check 14 advisory findings), 3 skipped-disabled
(Checks 2, 4, 11 — all subagent-review, project governance). No failures. No missing-configuration
skips requiring `/adev:init`.

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
>
> Historic `.validate.md` reports continue to use the pre-restructure numbering; the gaps in the
> surviving inventory (Checks 1, 1.5, 1.6, 2, 4, 8, 9, 14) are intentional to preserve report
> readability.
