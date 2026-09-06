<!-- partial_schema: plan@1 -->

# Implementation Plan: End-to-end UI test suite (real browser)

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/ui-e2e.spec.md
> **Review:** PASS (2026-09-06)
> **Platform:** FastAPI (uvicorn) + vanilla JS static frontend, Python 3.11, Playwright (Chromium, sync API), pytest

**Goal:** Add a real-browser end-to-end test suite that drives kanban-ui's actual served page — a
real Chromium instance clicking, dragging, and filling forms against the real, rendered DOM — over
the same real `issue-tracker-api` server process the sibling `api-e2e` suite already starts, never
calling `board-logic.js`'s functions directly.

**Architecture:** Tests land in the same `tests_e2e/` directory `api-e2e` already created, reusing
its `start_issue_tracker_api(tmp_path)` context manager (`tests_e2e/servers.py`) unchanged — no new
server-launch logic. A new `tests_e2e/browser.py` mirrors that module's shape for the browser side:
`launch_chromium()` wraps `playwright.sync_api.sync_playwright().chromium.launch()` in a context
manager, translating Playwright's own "binary not installed" error into a clearly-named
`E2EBrowserNotInstalled` exception (spec's `E2E_BROWSER_NOT_INSTALLED`). `tests_e2e/conftest.py`
gains three fixtures: session-scoped `browser` (one real Chromium instance for the whole run),
function-scoped `page` (a fresh browser context/tab per test), and function-scoped `ui_board_server`
— deliberately its own fixture, not the shared session-scoped `server` fixture `api-e2e`'s tests use.
This directly resolves the review's SA-1 suggestion (test-isolation clarity): `api-e2e`'s `server`
fixture accumulates every project/issue those tests create across the whole session, which would
break BEH-1's exact "2 cards per column" seeded-state assertion and make BEH-6's project-switcher
counts unpredictable if reused as-is. `ui_board_server` starts its own fresh subprocess per test
(via pytest's function-scoped `tmp_path`), so every ui-e2e test sees the same deterministic
6-seed-issue starting state, independent of whatever `api-e2e`'s tests have done in the same run.
Playwright itself is a new dependency, isolated into `requirements-e2e.txt` (not `requirements.txt`)
matching this repo's existing `requirements-mcp.txt` precedent for a component-scoped dependency
set; the one-time `playwright install chromium` step is documented in README.md and constitution.md
alongside the existing `pip install -r requirements.txt` step. No new gate is wired — these tests
land inside `tests_e2e/`, which the existing `e2e-smoke` gate (`tier: e2e`, already `severity:
warning`) already runs.

---

## File Structure

**Create:**
- `requirements-e2e.txt` — `playwright`, the one new dependency this spec adds (kept out of
  `requirements.txt`, matching the existing `requirements-mcp.txt` precedent for a component-scoped
  dependency file).
- `tests_e2e/browser.py` — `launch_chromium()` context manager and `E2EBrowserNotInstalled`
  exception; the browser-side counterpart to `tests_e2e/servers.py`.
- `tests_e2e/test_browser_fixture.py` — tests the `launch_chromium()` contract itself (a working
  browser; the wrapped `E2EBrowserNotInstalled` error path), same convention as `api-e2e`'s
  `test_server_fixture.py`.
- `tests_e2e/test_ui_board_render_e2e.py` — BEH-1.
- `tests_e2e/test_ui_column_move_e2e.py` — BEH-2.
- `tests_e2e/test_ui_issue_forms_e2e.py` — BEH-3 and BEH-4 (grouped per the spec's own Actionable
  Task Map row "Create/edit-issue e2e tests").
- `tests_e2e/test_ui_delete_issue_e2e.py` — BEH-5.
- `tests_e2e/test_ui_project_switcher_e2e.py` — BEH-6.
- `tests_e2e/test_ui_error_path_e2e.py` — the route-interception network-failure Error Case
  (`E2E_UI_FETCH_FAILED`).

**Modify:**
- `tests_e2e/conftest.py` — add `browser`, `page`, `ui_board_server` fixtures (existing `server`
  fixture is untouched — `api-e2e`'s tests keep using it exactly as before).
- `README.md` — add a "Running the UI end-to-end test suite" section documenting
  `pip install -r requirements-e2e.txt` and the one-time `playwright install chromium` step.
- `.context-index/constitution.md` (and, after `/adev:sync`, `CLAUDE.md`) — add the same one-time
  setup step to the Commands section, alongside the existing `pip install -r requirements.txt` line.

**Reference (read, do not modify):**
- `tests_e2e/servers.py` — `start_issue_tracker_api(tmp_path)`, reused unchanged.
- `static/index.html` — every element id this suite locates against (`#board`, `#board-error`,
  `#project-switcher`, `#col-todo`/`#col-in_progress`/`#col-done`, `#create-issue`/`#edit-issue`
  forms and their field ids, `#delete-issue`, `#create-project-form`).
- `static/js/board.js` — event wiring this suite exercises indirectly through the real DOM: form
  submit handlers, `onColumnDrop` (HTML5 drag/drop via `dataTransfer`), `onDeleteIssueClick`
  (`window.confirm`), `onProjectSwitch`.
- `static/js/board-logic.js` — `buildCardHtml` (`.card[data-issue-id]` shape), `formatFetchError`
  (the "`<action> failed: ...`" text prefix the error-path test asserts).
- `app/seed.py` — `SEED_PROJECT` (`ASSIST`) / `SEED_ISSUES` (exactly 2 issues per status), the
  deterministic starting state BEH-1's counts assert against.
- `tests_js/beh-1-board-load.test.js`, `tests_js/beh-3-project-switch.test.js`,
  `tests_js/issue-crud-beh-*.test.js` — existing fast unit tests already covering these behaviors
  at the `board-logic.js` function level (mocked fetch, no real browser). This suite covers the
  same behaviors through the real rendered page instead — it does not replace or duplicate them.
- `requirements.txt`, `requirements-mcp.txt` — precedent for the new `requirements-e2e.txt`'s shape
  and the component-scoped-dependency-file convention.
- `governance/gates.yaml` — existing `e2e-smoke` gate; already covers this suite's location, no
  change needed.

---

## Context Packets

No `source-manifest.files[]` exists yet on this spec (first implementation pass), so context
packets fall back to the charter Capability Map, this spec's own Preconditions/Behaviors, and full
reads of the small static frontend files this suite drives.

### Task 1 Context
- Spec: `ui-e2e.spec.md` — Preconditions, `E2E_BROWSER_NOT_INSTALLED` Error Case row
- Charter: `charter.md` (capability: "End-to-end UI test suite")
- Source files: `tests_e2e/servers.py` (full read — the pattern `browser.py` mirrors),
  `tests_e2e/conftest.py` (full read — existing `server` fixture, not to be touched)
- Reference: `requirements.txt`, `requirements-mcp.txt` (component-scoped dependency file
  precedent)
- Constitution: "Fixture-backed, offline only" (no real network target; Chromium is a local
  binary)

### Task 2 Context
- Spec: `ui-e2e.spec.md` — BEH-1
- Charter: `charter.md` (capability: "Render kanban board")
- Source files: `static/index.html` (`#board`, `#col-todo`/`#col-in_progress`/`#col-done`),
  `app/seed.py` (`SEED_ISSUES` — exact 2-per-status counts and summaries)
- Sibling test (signatures only): `tests_js/beh-1-board-load.test.js`

### Task 3 Context
- Spec: `ui-e2e.spec.md` — BEH-2
- Charter: `charter.md` (capability: "Move issue between columns")
- Source files: `static/js/board.js` (`onDragStart`/`onColumnDrop`, full read — HTML5
  `dataTransfer` wiring), `static/index.html` (`.column[data-status]` sections)
- Sibling test (signatures only): `tests_js/issue-crud-beh-3-column-move.test.js`

### Task 4 Context
- Spec: `ui-e2e.spec.md` — BEH-3, BEH-4
- Charter: `charter.md` (capabilities: "Create issue", "Edit issue")
- Source files: `static/index.html` (`#create-issue-form`, `#edit-issue-form` field ids),
  `static/js/board.js` (`onCreateIssueSubmit`, `onEditIssueSubmit`, `openEditIssue`, full read)
- Sibling tests (signatures only): `tests_js/issue-crud-beh-1-create-issue.test.js`,
  `tests_js/issue-crud-beh-2-edit-issue.test.js`

### Task 5 Context
- Spec: `ui-e2e.spec.md` — BEH-5
- Charter: `charter.md` (capability: "Delete issue")
- Source files: `static/js/board.js` (`onDeleteIssueClick` — `window.confirm` dialog, full read)
- Sibling test (signatures only): `tests_js/issue-crud-beh-4-delete-issue.test.js`

### Task 6 Context
- Spec: `ui-e2e.spec.md` — BEH-6
- Charter: `charter.md` (capabilities: "Project switcher", "Create project")
- Source files: `static/js/board.js` (`onProjectSwitch`, `renderSwitcher`, `onCreateProjectSubmit`,
  full read), `static/js/board-logic.js` (`pickDefaultProject`)
- Sibling test (signatures only): `tests_js/beh-3-project-switch.test.js`

### Task 7 Context
- Spec: `ui-e2e.spec.md` — Error Cases table, row 1 (`E2E_UI_FETCH_FAILED`)
- Charter: `charter.md` (capability: "Render kanban board" — error path)
- Source files: `static/js/board.js` (`loadIssuesFor`'s `catch` → `showError`),
  `static/js/board-logic.js` (`formatFetchError`)
- Cross-cutting: `issue-crud-forms.spec.md` BEH-5 (the revert-and-error behavior this error case
  cross-references per the spec's Error Cases table and review note CON-1)
- Sibling test (signatures only): `tests_js/beh-5-fetch-error.test.js`

---

## Parallelization

- Group A (sequential): Task 1
- Group B (independent): Task 2
- Group C (independent): Task 3
- Group D (independent): Task 4
- Group E (independent): Task 5
- Group F (independent): Task 6
- Group G (independent): Task 7

Groups B through G each depend only on Task 1 (the `browser`/`page`/`ui_board_server` fixtures) and
can run in parallel with each other — none touches a file another group touches.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Playwright browser fixture + dependency setup | small | unit | — | 3 create, 3 modify |
| 2 | Board-render e2e test (BEH-1) | small | unit | Task 1 | 1 create, 0 modify |
| 3 | Column-move e2e test (BEH-2) | medium | unit | Task 1 | 1 create, 0 modify |
| 4 | Create/edit-issue e2e tests (BEH-3, BEH-4) | medium | unit | Task 1 | 1 create, 0 modify |
| 5 | Delete-issue e2e test (BEH-5) | small | unit | Task 1 | 1 create, 0 modify |
| 6 | Project-switcher e2e test (BEH-6) | small | unit | Task 1 | 1 create, 0 modify |
| 7 | Error-path e2e test | small | unit | Task 1 | 1 create, 0 modify |

All seven tasks resolve to the `unit` strategy (source: fallback — no `test_strategy` in the
spec's frontmatter, no matching `manifest.yaml` glob rule, and no file path matches any
auto-detection heuristic in `lib/test-strategies/detection.mjs`). The Strategy Summary section is
omitted per the plan template (all-unit, backward compatible). The Test Infrastructure
Requirements section below is still included, because the spec declares `infra_requirements:` in
its frontmatter regardless of strategy.

---

## Test Infrastructure Requirements

> These requirements must be satisfied before this suite's tests can run. Missing them produces a
> clear setup error (`E2E_BROWSER_NOT_INSTALLED`-style message), not a test failure.

### External Systems

| System | Required By | Strategy |
|--------|-------------|----------|
| Playwright Chromium browser binary | Task 1 (fixture), Tasks 2-7 (all UI e2e tests) | unit |

### Credentials / Environment Variables

None. Per the spec's `infra_requirements.systems[0].env_vars: []` — Chromium is a local binary,
not a remote system; no credentials of any kind are involved.

### Pre-Provisioned State

- [ ] `playwright` Python package installed (`pip install -r requirements-e2e.txt`)
- [ ] Chromium browser binary installed via `playwright install chromium` (one-time, per machine —
  not per test run)

### CI Configuration

No new gate — these tests land inside `tests_e2e/`, which the existing `e2e-smoke` gate
(`.venv/bin/python3 -m pytest -q tests_e2e/`, `tier: e2e`, `severity: warning`) already runs,
matching the spec's `infra_requirements.ci_tag: "e2e"`. CI (and any local run of the `e2e-smoke`
gate) must complete the one-time `pip install -r requirements-e2e.txt && playwright install
chromium` step before invoking it — documented in README.md (Task 1).

> **Local runs:** no `.env.test` needed — there are no credentials to keep out of version control
> for this suite.

### Unresolved Requirements

None — `infra_requirements:` is spec-declared (confidence: high), so auto-detection was skipped
entirely per the plan template's precedence rule.

---

## Task Structure

> Task status lives in the spec's lifecycle event log (`plan_task` events), not in the `- [ ]`
> checkboxes below — those are authoring guides only.

### Task 1: Playwright browser fixture + dependency setup [specialist: none]

**Charter capability:** End-to-end UI test suite
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `requirements-e2e.txt`
- Create: `tests_e2e/browser.py`
- Modify: `tests_e2e/conftest.py`
- Modify: `README.md`
- Modify: `.context-index/constitution.md`
- Test: `tests_e2e/test_browser_fixture.py`

**Tests:** `tests_e2e/test_browser_fixture.py` — new suite (per-behavior granularity: this covers
the Preconditions/`E2E_BROWSER_NOT_INSTALLED` contract of the reusable browser fixture itself, not
one of BEH-1..6).

**Context to load:**
- `tests_e2e/servers.py` (the pattern this mirrors)
- `tests_e2e/conftest.py` (existing `server` fixture — do not modify its body)
- `requirements.txt`, `requirements-mcp.txt` (component-scoped dependency file precedent)

- [ ] **Write failing test**

```python
# tests_e2e/test_browser_fixture.py
import pytest

from tests_e2e.browser import E2EBrowserNotInstalled, launch_chromium


def test_launch_chromium_yields_a_working_browser(ui_board_server):
    with launch_chromium() as browser:
        page = browser.new_page()
        page.goto(ui_board_server)
        assert page.title() == "mock-jira Kanban Board"
        page.close()


def test_launch_chromium_wraps_missing_binary_error(monkeypatch):
    from playwright.sync_api import Error as PlaywrightError

    class _FakeChromium:
        def launch(self):
            raise PlaywrightError(
                "Executable doesn't exist at .../chromium-1234/chrome-linux/chrome\n"
                "Looks like Playwright was just installed or updated.\n"
                "Please run the following command to download new browsers:\n"
                "    playwright install"
            )

    class _FakePlaywrightContext:
        chromium = _FakeChromium()

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    monkeypatch.setattr(
        "tests_e2e.browser.sync_playwright", lambda: _FakePlaywrightContext()
    )

    with pytest.raises(E2EBrowserNotInstalled) as exc_info:
        with launch_chromium():
            pass  # pragma: no cover - should never be reached

    assert "playwright install chromium" in str(exc_info.value)
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_browser_fixture.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests_e2e.browser'` for both tests, and
`fixture 'ui_board_server' not found` once `browser.py` exists but `conftest.py` hasn't been
updated yet.

- [ ] **Implement**

```txt
# requirements-e2e.txt
playwright
```

```python
# tests_e2e/browser.py
"""Reusable real-browser-process fixture for e2e suites.

Launches a real Chromium browser via Playwright's sync API (never headless-mocked, always a real
rendering engine) so ui-e2e's suite drives the actual served page — real clicks, real drags, real
form fills — never board-logic.js's functions directly. Wraps Playwright's own browser-launch
failure (binary not installed) into a clearly-named exception per ui-e2e.spec.md's
E2E_BROWSER_NOT_INSTALLED error case.
"""
import contextlib
from collections.abc import Iterator

from playwright.sync_api import Browser, Error as PlaywrightError, sync_playwright


class E2EBrowserNotInstalled(RuntimeError):
    """Raised when Playwright's Chromium binary is not installed locally."""


@contextlib.contextmanager
def launch_chromium() -> Iterator[Browser]:
    """Launch a real headless Chromium browser; yield it. Closes it (and Playwright) on exit.

    Raises:
        E2EBrowserNotInstalled: Chromium's binary is missing locally. The message names the
            remedy (`playwright install chromium`) per ui-e2e.spec.md's E2E_BROWSER_NOT_INSTALLED
            error case.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except PlaywrightError as exc:
            raise E2EBrowserNotInstalled(
                "Playwright's Chromium binary is not installed. Run `playwright install "
                f"chromium` once, then re-run this suite. Original error: {exc}"
            ) from exc
        try:
            yield browser
        finally:
            browser.close()
```

Append to `tests_e2e/conftest.py` (existing `server` fixture stays exactly as-is):

```python
from tests_e2e.browser import launch_chromium


@pytest.fixture(scope="session")
def browser():
    """Session-scoped real Chromium browser, shared across all ui-e2e tests."""
    with launch_chromium() as browser:
        yield browser


@pytest.fixture
def page(browser):
    """Function-scoped browser context/tab — a fresh, isolated page per test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def ui_board_server(tmp_path) -> str:
    """Function-scoped real server, isolated from the shared session-scoped `server` fixture.

    Deliberately NOT `server` above: ui-e2e's BEH-1 asserts the *seeded* board (exactly 2 issues
    per column) renders correctly, and BEH-2/BEH-5 verify persistence by reloading in the same
    browser — both are sensitive to any other e2e test's writes landing in a shared database.
    A fresh function-scoped server (per review note SA-1) keeps each ui-e2e test's seeded
    starting state deterministic and independent of api-e2e's tests in the same run.
    """
    with start_issue_tracker_api(tmp_path) as base_url:
        yield base_url
```

Add a "Running the UI end-to-end test suite" section to `README.md`, and a matching one-time setup
line to `.context-index/constitution.md`'s Commands section (next to `pip install -r
requirements.txt`):

```markdown
## Running the UI end-to-end test suite

The kanban-ui end-to-end suite drives a real Chromium browser (via Playwright) against a real
`issue-tracker-api` server process. One-time local setup:

\`\`\`bash
pip install -r requirements-e2e.txt
playwright install chromium
\`\`\`

Then run it (already covered by the `e2e-smoke` gate, which runs all of `tests_e2e/`):

\`\`\`bash
.venv/bin/python3 -m pytest -q tests_e2e/
\`\`\`
```

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_browser_fixture.py`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/e2e-testing/core`

```bash
git add requirements-e2e.txt tests_e2e/browser.py tests_e2e/conftest.py \
  tests_e2e/test_browser_fixture.py README.md .context-index/constitution.md
git commit -m "feat(kanban-ui): add reusable real-browser e2e fixture and Playwright setup"
```

### Task 2: Board-render e2e test [specialist: none]

**Charter capability:** Render kanban board
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_board_render_e2e.py`

**Tests:** `tests_e2e/test_ui_board_render_e2e.py` — new suite (BEH-1).

**Context to load:**
- `static/index.html` (`#board`, column containers), `app/seed.py` (`SEED_ISSUES`)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_board_render_e2e.py
def test_seeded_board_renders_with_issues_in_correct_columns(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    # Real DOM only — never board-logic.js's internal state or a mocked fetch response.
    assert page.locator("#col-todo .card").count() == 2
    assert page.locator("#col-in_progress .card").count() == 2
    assert page.locator("#col-done .card").count() == 2

    assert page.locator(
        '#col-todo .card:has-text("Investigate INCIDENT-01")'
    ).count() == 1
    assert page.locator(
        '#col-done .card:has-text("Publish pilot-expansion readiness checklist")'
    ).count() == 1
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_board_render_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — the board already renders correctly (`static/js/board.js`,
`app/seed.py`). This task's "implement" step is the test file itself; it goes green as soon as
Task 1's fixtures are in place.

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_board_render_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_board_render_e2e.py
git commit -m "test(kanban-ui): add real-browser board-render e2e coverage (BEH-1)"
```

### Task 3: Column-move e2e test [specialist: none]

**Charter capability:** Move issue between columns
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_column_move_e2e.py`

**Tests:** `tests_e2e/test_ui_column_move_e2e.py` — new suite (BEH-2).

**Context to load:**
- `static/js/board.js` (`onDragStart`, `onColumnDrop` — HTML5 `dataTransfer` wiring),
  `static/index.html` (`.column[data-status]` sections)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_column_move_e2e.py
def test_drag_card_to_new_column_persists_after_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    card = page.locator("#col-todo .card").first
    issue_id = card.get_attribute("data-issue-id")

    # Real drag event, not a direct call into board-logic.js's moveIssueStatus().
    card.drag_to(page.locator('.column[data-status="done"]'))

    page.wait_for_selector(f'#col-done .card[data-issue-id="{issue_id}"]')
    assert page.locator(f'#col-todo .card[data-issue-id="{issue_id}"]').count() == 0

    # BEH-2: verified by reloading the page in the same real browser.
    page.reload()
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator(f'#col-done .card[data-issue-id="{issue_id}"]').count() == 1
    assert page.locator(f'#col-todo .card[data-issue-id="{issue_id}"]').count() == 0
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_column_move_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — drag-and-drop and its server-side PATCH already exist
(`static/js/board.js`'s `onColumnDrop`, `app/routers/issues.py`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_column_move_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_column_move_e2e.py
git commit -m "test(kanban-ui): add real-browser column-move e2e coverage (BEH-2)"
```

### Task 4: Create/edit-issue e2e tests [specialist: none]

**Charter capability:** Create issue, Edit issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_issue_forms_e2e.py`

**Tests:** `tests_e2e/test_ui_issue_forms_e2e.py` — new suite (BEH-3 and BEH-4; two distinct spec
behaviors covered by one task, per the spec's own Actionable Task Map grouping).

**Context to load:**
- `static/index.html` (`#create-issue-form`, `#edit-issue-form` field ids), `static/js/board.js`
  (`onCreateIssueSubmit`, `onEditIssueSubmit`, `openEditIssue`)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_issue_forms_e2e.py
def test_create_issue_form_shows_new_card_without_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.evaluate("window.__e2eNoReloadMarker = true")

    page.click("#open-create-issue")
    page.fill("#issue-summary", "e2e-created issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "medium")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-created issue")')
    assert page.locator("#create-issue").is_hidden()
    # BEH-3: no page reload occurred — the marker set above survives.
    assert page.evaluate("window.__e2eNoReloadMarker") is True


def test_edit_issue_form_updates_visible_card_without_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.evaluate("window.__e2eNoReloadMarker = true")

    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")

    page.fill("#edit-issue-summary", "e2e-edited summary")
    page.click("#edit-issue-form button[type=submit]")

    page.wait_for_selector('.card:has-text("e2e-edited summary")')
    assert page.locator("#edit-issue").is_hidden()
    # BEH-4: no page reload occurred — the marker set above survives.
    assert page.evaluate("window.__e2eNoReloadMarker") is True
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_issue_forms_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — create/edit forms and their PATCH/POST calls already exist
(`static/js/board.js`'s `onCreateIssueSubmit`, `onEditIssueSubmit`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_issue_forms_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_issue_forms_e2e.py
git commit -m "test(kanban-ui): add real-browser create/edit-issue e2e coverage (BEH-3, BEH-4)"
```

### Task 5: Delete-issue e2e test [specialist: none]

**Charter capability:** Delete issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_delete_issue_e2e.py`

**Tests:** `tests_e2e/test_ui_delete_issue_e2e.py` — new suite (BEH-5).

**Context to load:**
- `static/js/board.js` (`onDeleteIssueClick` — the native `window.confirm` dialog)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_delete_issue_e2e.py
def test_delete_issue_removes_card_confirmed_after_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    card = page.locator("#col-todo .card").first
    issue_id = card.get_attribute("data-issue-id")

    # onDeleteIssueClick uses a native window.confirm() dialog — accept it for real.
    page.on("dialog", lambda dialog: dialog.accept())

    card.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    page.click("#delete-issue")

    page.wait_for_selector(f'.card[data-issue-id="{issue_id}"]', state="detached")
    assert page.locator(f'.card[data-issue-id="{issue_id}"]').count() == 0

    # BEH-5: verified by reloading the page and confirming it does not reappear.
    page.reload()
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator(f'.card[data-issue-id="{issue_id}"]').count() == 0
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_delete_issue_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — delete (with its confirm dialog and DELETE call) already exists
(`static/js/board.js`'s `onDeleteIssueClick`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_delete_issue_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_delete_issue_e2e.py
git commit -m "test(kanban-ui): add real-browser delete-issue e2e coverage (BEH-5)"
```

### Task 6: Project-switcher e2e test [specialist: none]

**Charter capability:** Project switcher, Create project
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_project_switcher_e2e.py`

**Tests:** `tests_e2e/test_ui_project_switcher_e2e.py` — new suite (BEH-6).

**Context to load:**
- `static/js/board.js` (`onProjectSwitch`, `renderSwitcher`, `onCreateProjectSubmit`),
  `static/js/board-logic.js` (`pickDefaultProject`)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_project_switcher_e2e.py
def test_switching_project_replaces_board_contents(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    # Create a second, empty Project via the real create-project form so there is
    # something distinct to switch to/from.
    page.fill("#project-key", "E2ESWITCH")
    page.fill("#project-name", "E2E Switch Project")
    page.click("#create-project-form button[type=submit]")

    page.wait_for_function(
        "() => document.getElementById('project-switcher')"
        ".selectedOptions[0]?.dataset.key === 'E2ESWITCH'"
    )
    # The new project has no issues yet — every column should now be empty.
    assert page.locator("#col-todo .card").count() == 0
    assert page.locator("#col-in_progress .card").count() == 0
    assert page.locator("#col-done .card").count() == 0

    # BEH-6: select a different Project from the switcher control.
    page.select_option("#project-switcher", label="ASSIST — Portwell Assist Engineering")

    page.wait_for_selector('#col-todo .card:has-text("Investigate INCIDENT-01")')
    assert page.locator("#col-todo .card").count() == 2
    assert page.locator("#col-in_progress .card").count() == 2
    assert page.locator("#col-done .card").count() == 2
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_project_switcher_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — the project switcher, create-project form, and per-project issue
reload already exist (`static/js/board.js`'s `renderSwitcher`, `onProjectSwitch`,
`onCreateProjectSubmit`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_project_switcher_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_project_switcher_e2e.py
git commit -m "test(kanban-ui): add real-browser project-switcher e2e coverage (BEH-6)"
```

### Task 7: Error-path e2e test [specialist: none]

**Charter capability:** Render kanban board (error path)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_e2e/test_ui_error_path_e2e.py`

**Tests:** `tests_e2e/test_ui_error_path_e2e.py` — new suite (Error Cases table row 1,
`E2E_UI_FETCH_FAILED`; a client-simulated network failure via Playwright route interception, per
review note SEC-1 — a reasonable substitute for this tier, not a real server outage).

**Context to load:**
- `static/js/board.js` (`loadIssuesFor`'s `catch` → `showError`), `static/js/board-logic.js`
  (`formatFetchError`)
- Cross-cutting: `issue-crud-forms.spec.md` BEH-5 (the revert-and-error behavior this error case
  cross-references; see review note CON-1 on the intentional `E2E_UI_FETCH_FAILED` /
  `UI_FETCH_FAILED` naming divergence — no action needed, both names are correct for their own
  spec)

- [ ] **Write failing test**

```python
# tests_e2e/test_ui_error_path_e2e.py
def test_network_failure_shows_visible_error_message(page, ui_board_server):
    # Simulate the real server becoming unreachable mid-load by aborting the
    # issues fetch at the network layer — no mocked fetch, a real aborted request.
    page.route("**/issues*", lambda route: route.abort("failed"))

    page.goto(ui_board_server)

    page.wait_for_selector("#board-error:not([hidden])")
    error_text = page.locator("#board-error").inner_text()
    assert "Loading issues failed" in error_text
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_error_path_e2e.py`
Expected: FAIL — `fixture 'page' not found` / `fixture 'ui_board_server' not found` until Task 1
lands.

- [ ] **Implement**

No production code changes — the fetch-failure error banner already exists
(`static/js/board.js`'s `loadIssuesFor` catch block, `static/js/board-logic.js`'s
`formatFetchError`).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_error_path_e2e.py`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_error_path_e2e.py
git commit -m "test(kanban-ui): add real-browser network-failure e2e coverage (E2E_UI_FETCH_FAILED)"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.

`governance/gates.yaml` defines the deterministic gates for this project — used here instead of
constitution Quality Gates, per plan template precedence:

| Gate | Tier | Command | Severity |
|------|------|---------|----------|
| `test` | fast | `.venv/bin/python3 -m pytest -q` | error |
| `lint` | fast | `.venv/bin/ruff check .` | error |
| `test-js` | fast | `node --test "tests_js/**/*.test.js"` | error |
| `integration-test` | integration | *(unwired — `command: ""`)* | error (skipped, no command) |
| `e2e-smoke` | e2e | `.venv/bin/python3 -m pytest -q tests_e2e/` | warning |

- No gate changes needed — `e2e-smoke` already runs the whole `tests_e2e/` directory, so this
  suite's new files are picked up automatically once created.
- The `test` gate must keep passing unaffected — `pytest.ini`'s `testpaths = tests` (already in
  place from `api-e2e`) keeps `tests_e2e/` out of the fast gate's bare-invocation discovery scope.
- CI/local runners must complete the one-time `pip install -r requirements-e2e.txt && playwright
  install chromium` step (Task 1, documented in README.md) before `e2e-smoke` can pass; without it,
  every test in this suite fails fast with the `E2E_BROWSER_NOT_INSTALLED` message from
  `tests_e2e/browser.py`, not a silent hang.
- All eight acceptance criteria in `ui-e2e.spec.md` must be satisfied: seeded board renders
  correctly (BEH-1), drag-and-drop column move persists across reload (BEH-2), create-issue form
  produces a visible card (BEH-3), edit-issue form updates the visible card (BEH-4), delete removes
  the card and it stays gone after reload (BEH-5), project switch replaces the board's visible
  contents (BEH-6), all quality gates passing, no constitutional violations.
- `e2e-smoke` stays `severity: warning` / `required: false` per its existing e2e-tier default — not
  escalated by this plan, consistent with `api-e2e`'s precedent (first-generation e2e coverage for
  a course-fixture repo, not yet a merge blocker).
