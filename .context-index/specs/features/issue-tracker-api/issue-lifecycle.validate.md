---
spec: .context-index/specs/features/issue-tracker-api/issue-lifecycle.spec.md
plan: .context-index/specs/features/issue-tracker-api/issue-lifecycle.plan.md
validated-at: "2026-09-05T00:46:43.279Z"
overall-status: PASS_WITH_NOTES
rigor-tier: full
---

# Validation Report: Issue lifecycle CRUD

> **Date:** 2026-09-04
> **Spec:** .context-index/specs/features/issue-tracker-api/issue-lifecycle.spec.md
> **Plan:** .context-index/specs/features/issue-tracker-api/issue-lifecycle.plan.md
> **Overall Status:** PASS_WITH_NOTES

---

## Advisory: Workspace-scoped run

Advisory: running repo-scoped inside workspace — cross-repo validation skipped (no
cross-repo `depends-on` references in this spec's frontmatter).

## Check 1: Quality Gates — PASS
- Fast tier:
  - `test` (`python3 -m pytest -q`): PASS — 31 passed, 4 warnings, 0.24s
  - `lint` (`ruff check .`): PASS — All checks passed!
- Integration tier: skipped — "integration tier — no gates configured" (the
  `integration-test` gate declares `command: ""`, an invalid/empty command; `adev domain
  load-gates` emitted `INVALID_GATE: Gate 'integration-test' missing required command
  field — skipped.`)
- E2E tier: skipped — no gates configured.

## Check 1.5: Source Manifest Verification — PASS
- `adev source-manifest verify`: `Check 1.5: PASS — source manifest matches (sha: bae9198)`
- Git-tracked check: all 7 manifest files (`app/db.py`, `app/errors.py`, `app/main.py`,
  `app/models.py`, `app/routers/issues.py`, `tests/test_db.py`, `tests/test_issues.py`)
  are committed to git (verified via `git log --oneline -1 -- <file>`).

## Check 1.6: Code-Side Drift Warning — PASS
- `adev verify spec --check-drift`: `{"drifted":false,"drift_source":null,"drift_at":null}`
- No code-side drift detected for this spec's implementation files.
- Note (out of scope for this check, non-blocking): the sibling
  `project-management.spec.md` currently shows `drift_detected: true` because this plan's
  implementation touched shared files (`app/db.py`, `tests/test_db.py`). That is a
  housekeeping item for the operator on that spec, not a finding against this spec.

## Check 2: Spec Compliance — SKIPPED-DISABLED
- Disabled by `governance/validate.yaml` (`enabled: false`, no `disabled_reason` stated).
- Registry warning: `DISABLED_WITHOUT_REASON` — "Entry 'validate.check-2-spec-compliance'
  carries 'enabled: false' with no 'disabled_reason'."

## Check 4: Constitution Compliance — SKIPPED-DISABLED
- Disabled by `governance/validate.yaml` (`enabled: false`, no `disabled_reason` stated).
- Registry warning: `DISABLED_WITHOUT_REASON` — same as above, for
  'validate.check-4-constitution'.

## Check 8: Boundary Compliance — SKIP
- `adev boundaries check --json`: `{"verdict":"SKIP","reason":"no boundary rules
  declared","findings":[],"disabled":[],"warnings":[],"summary":{"errors":0,"warnings":0,
  "infos":0,"files_checked":1}}`
- SKIP means no rules were declared — not that boundaries held.

## Check 9: Transition Gates — SKIP
- Transition: `implement-to-validate`
- `adev gate transitions --transition implement-to-validate --json`:
  `{"transition":"implement-to-validate","verdict":"SKIP","reason":"no transitions
  configured","gates":{}}`
- Matches `governance/gates.yaml`'s `transitions: {}`.

## Check 11: Visual Verification — SKIPPED-DISABLED
- Disabled by `governance/validate.yaml` (`enabled: false`, no `disabled_reason` stated;
  comment notes "no UI — mock-jira is a headless HTTP API").
- Registry warning: `DISABLED_WITHOUT_REASON` — same pattern as Checks 2/4.
- N/A regardless: this spec touches no UI files (headless HTTP API).

## Check 14: Gate Executability and Test Collection — PASS_WITH_NOTES
- `adev gate doctor --json`: 4 warning-severity findings, 0 errors.
  - `gate-doctor/gate-set-divergence` (warning): raw `gates.yaml` declares `integration-test`
    but it is absent from the domain-merged set every consumer reads.
  - `gate-doctor/ci-config-missing` (warning): no CI configuration found.
  - `gate-doctor/runner-unknown` (warning, gate `lint`): no known test runner identified in
    `ruff check .` — collection cannot be verified for a lint gate (expected; lint gates
    have no test-runner concept).
  - `gate-doctor/empty-command` (warning, gate `integration-test`): declares no command.
- No error-severity findings — none of these describe a gate the project believes protects
  it that cannot run; `integration-test` is a known-unwired placeholder per its own comment
  in `gates.yaml` ("unwired — no integration-test suite yet; seed once one exists").

---

**Summary:** 5 checks ran (1, 1.5, 1.6, 8, 9, 14 — grouping 1/1.5/1.6 and 8/9/14 as listed
above, 6 emitted validator events total), all PASS or PASS_WITH_NOTES, 0 failed. 3 checks
skipped as disabled by project governance (2, 4, 11 — subagent-review and visual-verification
are intentionally off per `governance/validate.yaml`, matching this project's lightweight
governance posture documented in `CLAUDE.md`).

---

> **Note for users comparing with historic reports:** Checks 3, 5, 6, 7, 10, 11 (when no UI
> files), 12, and 13 have been relocated by `check-set-restructure.spec.md`. See:
>
> - `/adev:review-specs` — for ADR compliance (formerly Check 5), cross-cutting compliance
>   (formerly Check 6), specialist review (formerly Check 7), and charter consistency
>   (formerly Check 3, now covered by Check 2's scope-expansion sub-finding).
> - `/adev:hygiene` Audit Pass 20 — for platform drift (formerly Check 10).
> - `/adev:reconcile` lifecycle-sync — for lifecycle reconciliation (formerly Check 12, with
>   `--fix` as the default mode).
> - `hooks/post-validate-extract-heuristics.{sh,mjs}` — for heuristic extraction (formerly
>   Check 13 / `check-12-heuristic-extraction`), now a non-blocking Stop-event hook.
>
> This project's own governance additionally disables Checks 2, 4, and 11
> (`governance/validate.yaml`), so the surviving set for this run is 1, 1.5, 1.6, 8, 9, 14.
