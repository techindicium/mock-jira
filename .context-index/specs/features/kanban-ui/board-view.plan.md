<!-- partial_schema: plan@1 -->

# Implementation Plan: Kanban board view, project switcher, and project creation

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/board-view.spec.md
> **Review:** PASS (2026-09-05)
> **Platform:** FastAPI (Python 3.11) backend; static HTML/CSS/vanilla JS frontend with zero
> build step; Node.js built-in test runner (`node --test`, no npm dependencies) for JS unit tests.

**Goal:** Ship a same-origin kanban board UI (three fixed columns, project switcher,
create-project form) as static assets served directly by `issue-tracker-api`'s own FastAPI
process, with no separate frontend server, framework, or build step.

**Architecture:** `app/main.py` mounts a new `static/` directory via `StaticFiles` and serves
`static/index.html` at `GET /`. The page loads two vanilla-JS files: `board-logic.js`, a
dependency-free module of pure functions (column grouping, default-project selection, form
validation, error-message formatting — the substantive behavior logic for BEH-1 through BEH-6),
and `board.js`, a thin DOM/fetch imperative shell that calls the same-origin `/projects` and
`/issues` endpoints and wires pure-function results into the DOM. Pure logic is unit-tested with
Node's built-in test runner (`node:test` + `node:assert/strict`, shipped with Node — no
`package.json`, no npm install, no build step). The static-serving wiring itself is unit-tested
with the existing pytest + `TestClient` setup already used for the API. This split keeps nearly
all genuinely testable logic in `board-logic.js`; `board.js` stays thin glue (call fetch, call a
pure function, write the result into the DOM) and is not separately unit-tested — this project's
governance already disables subagent visual/browser-review checks (`governance/validate.yaml`
check-11, `governance/review.yaml`), so no automated DOM/browser verification is expected or
required for this spec.

**Note for the human:** `governance/validate.yaml`'s check-11 entry is commented "no UI —
mock-jira is a headless HTTP API." That comment is now stale as of this spec. Not fixed here —
out of scope for `/adev:plan` — but worth a pass from `/adev:hygiene` or a manual edit before
`/adev:validate` runs on this work.

---

## File Structure

**Create:**
- `static/index.html` — board page shell: header + project switcher, error banner, three
  fixed columns (`todo`, `in_progress`, `done`), empty-state section, create-project form.
- `static/css/board.css` — layout and card styling for the board, columns, and forms.
- `static/js/board-logic.js` — pure, dependency-free logic module (UMD-lite: usable as a
  plain browser `<script>` global `BoardLogic` and via Node `require()` in tests). Built up
  incrementally across Tasks 2-7.
- `static/js/board.js` — DOM/fetch imperative shell wiring `board-logic.js` functions to the
  page. Built up incrementally across Tasks 3-7.
- `tests/test_static_assets.py` — pytest: verifies the FastAPI process serves the board shell
  and static assets.
- `tests_js/beh-2-render-columns.test.js` — Node `node:test`: column grouping + card markup.
- `tests_js/beh-5-fetch-error.test.js` — Node `node:test`: fetch-failure message formatting.
- `tests_js/beh-1-board-load.test.js` — Node `node:test`: default-project selection on load.
- `tests_js/beh-3-project-switch.test.js` — Node `node:test`: switching never merges Issues.
- `tests_js/beh-4-create-project.test.js` — Node `node:test`: create-project validation and
  server-error mapping.
- `tests_js/beh-6-empty-state.test.js` — Node `node:test`: zero-projects empty-state decision.

**Modify:**
- `app/main.py` — mount `static/` and serve `static/index.html` at `GET /`.
- `.context-index/governance/gates.yaml` — add a `test-js` gate wiring `node --test tests_js/`
  into the standard quality-gate set (Task 3, alongside the first JS test file it protects).

**Reference (read, do not modify):**
- `app/routers/projects.py` — `POST /projects` (409 `PROJECT_KEY_DUPLICATE`, 422
  `VALIDATION_ERROR`), `GET /projects`, `GET /projects/{id}` — exact response shapes the UI
  must render and the exact error envelopes (`{"message": ..., "code": ...}`) it must surface.
- `app/routers/issues.py` — `GET /issues?project_id=<id>`, `POST /issues` — `IssueRead` shape
  (`summary`, `issue_type`, `status`, `priority`, `assignee`, ...) the board renders.
- `app/models.py` — `ISSUE_TYPES`, `ISSUE_STATUSES`, `ISSUE_PRIORITIES` literal value sets.
- `tests/conftest.py` — existing `client` fixture (`TestClient(main_module.app)` over a
  per-test tmp sqlite db) — reuse this fixture, do not create a second one.
- `.context-index/specs/features/kanban-ui/charter.md` — Capability Map and Domain Model
  (`BoardColumn` grouping, fixed-column invariant).

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/kanban-ui/board-view.spec.md` (Precondition; BEH-1 "page
  loads" precondition)
- Charter: `.context-index/specs/features/kanban-ui/charter.md` (capabilities: Render kanban
  board, Project switcher, Create project — scaffold)
- Source: `app/main.py` (full read — startup hook, router registration, exception handlers)
- Reference: `tests/conftest.py` (`client` fixture signature)

### Task 2 Context
- Spec: board-view.spec.md (BEH-2)
- Charter: charter.md (capability: Render kanban board)
- Source: `app/models.py` (`ISSUE_TYPES`, `ISSUE_STATUSES`, `ISSUE_PRIORITIES` — signatures only)
- Depends on Task 1's `static/index.html` element ids (`col-todo`, `col-in_progress`, `col-done`)

### Task 3 Context
- Spec: board-view.spec.md (BEH-5; Error Cases table row 1, `UI_FETCH_FAILED`)
- Charter: charter.md (cross-cutting: applies to all three consumed-API capabilities)
- Source: none new — pure error-formatting logic only

### Task 4 Context
- Spec: board-view.spec.md (BEH-1)
- Charter: charter.md (capabilities: Render kanban board, Project switcher — initial population)
- Source: `app/routers/projects.py` (`GET /projects` response shape — signature only),
  `app/routers/issues.py` (`GET /issues?project_id=` response shape — signature only)
- Depends on: Task 2 (`board-logic.js` render helpers), Task 3 (`fetchJson`/error banner)

### Task 5 Context
- Spec: board-view.spec.md (BEH-3; Postconditions: "no stale render left over after a switch")
- Charter: charter.md (capability: Project switcher)
- Depends on: Task 4's `board.js` `init()`/render functions

### Task 6 Context
- Spec: board-view.spec.md (BEH-4; Error Cases table rows 2-3, `UI_PROJECT_KEY_DUPLICATE`,
  `UI_VALIDATION_ERROR`)
- Charter: charter.md (capability: Create project)
- Source: `app/routers/projects.py` (`POST /projects` 409/422 error envelopes — full read of
  the two `HTTPException` blocks)
- Depends on: Task 4's `board.js` (switcher render + state)

### Task 7 Context
- Spec: board-view.spec.md (BEH-6; Postconditions: "immediately selectable, immediately shows an
  empty board")
- Charter: charter.md (capabilities: Render kanban board edge case, Create project entry point)
- Depends on: Task 4's `board.js` `init()`

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7

Every task after Task 1 modifies one or both of the two shared frontend files
(`static/js/board-logic.js`, `static/js/board.js`), so there is no independent group to extract
without first splitting `board.js` into per-feature modules — out of scope for this plan. Tasks
5, 6, and 7 are logically independent *behaviors* (switcher, create-form, empty-state) but are
serialized here purely because they share `board.js`.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Static board shell & FastAPI static serving | medium | unit | — | 3 create, 1 modify |
| 2 | Column & card rendering logic | medium | unit | Task 1 | 2 create, 1 modify |
| 3 | Error banner & fetch helper | small | unit | Task 2 | 2 create, 3 modify |
| 4 | Board load & fetch wiring | medium | unit | Task 3 | 1 create, 2 modify |
| 5 | Project switcher selection | small | unit | Task 4 | 1 create, 2 modify |
| 6 | Create-project form | small | unit | Task 4 | 1 create, 2 modify |
| 7 | Empty-state handling | small | unit | Task 4 | 1 create, 2 modify |

All tasks resolve to the `unit` strategy (fallback — no `test_strategies` declared in
`manifest.yaml`, no spec-level `test_strategy`, and auto-detection finds no migration/IaC/schema/
contract/visual signal for this file set: `visual` specifically requires a `react`/`vue`/
`svelte`/`angular` package, which this project deliberately does not have). Strategy Summary and
Test Infrastructure Requirements sections are both omitted per plan template rules (all-unit, no
`infra_requirements:` declared).

Granularity: `per-behavior` (source: `manifest.yaml` `test_policy.granularity`). Each spec
behavior (BEH-1 through BEH-6) gets one canonical suite file under `tests_js/`; a task "creates"
the suite the first time that behavior is implemented and would "extend" it on any later task
touching the same behavior. In this plan every behavior is implemented by exactly one task, so
every JS suite listed is a `create`, not an `extend`. Task 1's `tests/test_static_assets.py` is
outside this behavior-suite scheme — it is foundational/infra rather than behavior logic — so it
gets its own dedicated suite per the "no source-manifest" fallback path.

---

## Task Structure

### Task 1: Static board shell & FastAPI static serving [specialist: none]

**Charter capability:** Render kanban board / Project switcher / Create project (scaffold)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `static/index.html`
- Create: `static/css/board.css`
- Create: `tests/test_static_assets.py`
- Modify: `app/main.py` (add static mount + root route)

**Tests:** `tests/test_static_assets.py` — new suite; foundational (not behavior-suite scheme).

**Context to load:**
- `app/main.py` (full read)
- `tests/conftest.py` (`client` fixture)

- [ ] **Write failing test**

```python
def test_root_serves_board_shell(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert 'id="col-todo"' in body
    assert 'id="col-in_progress"' in body
    assert 'id="col-done"' in body
    assert 'id="project-switcher"' in body
    assert 'id="create-project-form"' in body


def test_static_css_is_served(client):
    resp = client.get("/static/css/board.css")
    assert resp.status_code == 200
```

- [ ] **Verify test fails**

Run: `python3 -m pytest -q -- tests/test_static_assets.py`
Expected: FAIL — `404` on `GET /` (no route yet) and/or `ConnectionError` on the static path.

- [ ] **Implement**

`static/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>mock-jira Kanban Board</title>
  <link rel="stylesheet" href="/static/css/board.css" />
</head>
<body>
  <header>
    <h1>mock-jira</h1>
    <select id="project-switcher" aria-label="Select project"></select>
  </header>

  <div id="board-error" role="alert" hidden></div>

  <main id="board" hidden>
    <section class="column" data-status="todo">
      <h2>To Do</h2>
      <div id="col-todo" class="cards"></div>
    </section>
    <section class="column" data-status="in_progress">
      <h2>In Progress</h2>
      <div id="col-in_progress" class="cards"></div>
    </section>
    <section class="column" data-status="done">
      <h2>Done</h2>
      <div id="col-done" class="cards"></div>
    </section>
  </main>

  <section id="empty-state" hidden>
    <p>No projects yet. Create one to get started.</p>
  </section>

  <section id="create-project">
    <h2>New Project</h2>
    <form id="create-project-form">
      <label>Key <input id="project-key" name="key" required /></label>
      <label>Name <input id="project-name" name="name" required /></label>
      <button type="submit">Create Project</button>
      <p id="create-project-error" role="alert" hidden></p>
    </form>
  </section>
</body>
</html>
```

`static/css/board.css`: basic flex layout for `#board`, `.column`, `.card`, and a
`[hidden] { display: none !important; }` rule so the `hidden` attribute toggles used
throughout this plan actually hide elements.

`app/main.py` (add near the router includes):

```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_board() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
```

`STATIC_DIR` is resolved from `__file__`, not the process CWD, so it works identically whether
pytest, `uvicorn app.main:app`, or a packaged container runs it from a different working
directory. `include_in_schema=False` keeps `tests/test_openapi.py`'s existing route-presence
assertions unaffected (it only asserts `/projects` paths are present, never that other paths are
absent).

- [ ] **Verify test passes**

Run: `python3 -m pytest -q -- tests/test_static_assets.py`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/kanban-ui/board-view`

```bash
git add static/index.html static/css/board.css app/main.py tests/test_static_assets.py
git commit -m "feat(kanban-ui): serve board shell as static assets from issue-tracker-api"
```

---

### Task 2: Column & card rendering logic [specialist: none]

**Charter capability:** Render kanban board
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `static/js/board-logic.js`
- Create: `tests_js/beh-2-render-columns.test.js`
- Modify: `static/index.html` (add `<script src="/static/js/board-logic.js"></script>`)

**Tests:** `tests_js/beh-2-render-columns.test.js` — new suite (BEH-2).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-2)
- `app/models.py` (`ISSUE_TYPES`/`ISSUE_STATUSES`/`ISSUE_PRIORITIES` — signatures only)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { BOARD_COLUMNS, groupIssuesByStatus, buildCardHtml, escapeHtml } =
  require("../static/js/board-logic.js");

test("BEH-2: groups issues into the three fixed columns by status", () => {
  const issues = [
    { id: 1, status: "todo", summary: "A", issue_type: "bug", priority: "high", assignee: "" },
    { id: 2, status: "done", summary: "B", issue_type: "task", priority: "low", assignee: "dee" },
  ];
  const grouped = groupIssuesByStatus(issues);
  assert.deepEqual(Object.keys(grouped).sort(), ["done", "in_progress", "todo"]);
  assert.equal(grouped.todo.length, 1);
  assert.equal(grouped.done.length, 1);
  assert.equal(grouped.in_progress.length, 0);
});

test("BEH-2: handles zero issues without error", () => {
  const grouped = groupIssuesByStatus([]);
  assert.deepEqual(grouped.todo, []);
});

test("BEH-2: card markup shows summary, type, priority, and assignee", () => {
  const html = buildCardHtml({
    id: 7, summary: "Fix bug", issue_type: "bug", priority: "high", assignee: "dana",
  });
  assert.match(html, /Fix bug/);
  assert.match(html, /bug/);
  assert.match(html, /high/);
  assert.match(html, /dana/);
});

test("BEH-2: card markup falls back to Unassigned and escapes HTML", () => {
  const html = buildCardHtml({
    id: 8, summary: "<script>", issue_type: "task", priority: "low", assignee: "",
  });
  assert.match(html, /Unassigned/);
  assert.doesNotMatch(html, /<script>/);
});

test("escapeHtml neutralizes markup-significant characters", () => {
  assert.equal(escapeHtml("<b>&\"'"), "&lt;b&gt;&amp;&quot;&#39;");
});

test("BOARD_COLUMNS is fixed, ordered todo -> in_progress -> done", () => {
  assert.deepEqual(BOARD_COLUMNS.map((c) => c.status), ["todo", "in_progress", "done"]);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-2-render-columns.test.js`
Expected: FAIL — `Cannot find module '../static/js/board-logic.js'`

- [ ] **Implement**

`static/js/board-logic.js` (UMD-lite: browser global `BoardLogic` + Node `require()`):

```javascript
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.BoardLogic = factory();
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  const BOARD_COLUMNS = [
    { status: "todo", label: "To Do", ordinal: 0 },
    { status: "in_progress", label: "In Progress", ordinal: 1 },
    { status: "done", label: "Done", ordinal: 2 },
  ];

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[ch]);
  }

  function groupIssuesByStatus(issues) {
    const grouped = {};
    for (const col of BOARD_COLUMNS) grouped[col.status] = [];
    for (const issue of Array.isArray(issues) ? issues : []) {
      if (grouped[issue.status]) grouped[issue.status].push(issue);
    }
    return grouped;
  }

  function buildCardHtml(issue) {
    return (
      `<article class="card" data-issue-id="${issue.id}">` +
      `<h3>${escapeHtml(issue.summary)}</h3>` +
      `<p class="card-meta">${escapeHtml(issue.issue_type)} &middot; ` +
      `${escapeHtml(issue.priority)} &middot; ` +
      `${escapeHtml(issue.assignee || "Unassigned")}</p>` +
      `</article>`
    );
  }

  return { BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml };
});
```

Add `<script src="/static/js/board-logic.js"></script>` to `static/index.html` before the (not
yet created) `board.js` include point — it only defines a global, so loading it early is inert.

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-2-render-columns.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/index.html tests_js/beh-2-render-columns.test.js
git commit -m "feat(kanban-ui): add column grouping and card rendering logic"
```

---

### Task 3: Error banner & fetch helper [specialist: none]

**Charter capability:** cross-cutting (Render kanban board, Project switcher, Create project all
depend on this for BEH-5)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Create: `static/js/board.js`
- Create: `tests_js/beh-5-fetch-error.test.js`
- Modify: `static/js/board-logic.js` (add `formatFetchError`)
- Modify: `static/index.html` (add `<script src="/static/js/board.js" defer></script>`)
- Modify: `.context-index/governance/gates.yaml` (add a `test-js` gate)

**Tests:** `tests_js/beh-5-fetch-error.test.js` — new suite (BEH-5).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-5, Error Cases row 1)
- `.context-index/governance/gates.yaml` (existing `test`/`lint`/`integration-test` gate shape)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { formatFetchError } = require("../static/js/board-logic.js");

test("BEH-5: names the failed action and the server message on an HTTP error", () => {
  const msg = formatFetchError("Loading issues", { status: 500, message: "boom" });
  assert.match(msg, /Loading issues/);
  assert.match(msg, /500/);
  assert.match(msg, /boom/);
});

test("BEH-5: falls back to a network-error message with no status", () => {
  const msg = formatFetchError("Loading projects", { message: "Failed to fetch" });
  assert.match(msg, /Loading projects/);
  assert.match(msg, /Failed to fetch/);
});

test("BEH-5: never returns an empty message even with a bare error", () => {
  const msg = formatFetchError("Loading projects", {});
  assert.ok(msg && msg.length > 0);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-5-fetch-error.test.js`
Expected: FAIL — `formatFetchError is not a function` (not yet exported)

- [ ] **Implement**

Add to the `board-logic.js` factory's return object (extends the module from Task 2):

```javascript
  function formatFetchError(action, error) {
    if (error && error.status) {
      return `${action} failed (HTTP ${error.status}): ${error.message || "unexpected error"}`;
    }
    return `${action} failed: ${(error && error.message) || "network error"}`;
  }

  // ...
  return { BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError };
```

`static/js/board.js` (fetch + error-banner helpers only — no page wiring yet, added in Task 4):

```javascript
(function () {
  async function fetchJson(url, options) {
    let resp;
    try {
      resp = await fetch(url, options);
    } catch (networkErr) {
      throw { message: networkErr.message };
    }
    if (!resp.ok) {
      let body = null;
      try {
        body = await resp.json();
      } catch (_parseErr) {
        // non-JSON error body — body stays null, message falls back below
      }
      throw { status: resp.status, message: body && body.message };
    }
    return resp.status === 204 ? null : resp.json();
  }

  function showError(message) {
    const banner = document.getElementById("board-error");
    banner.textContent = message;
    banner.hidden = false;
  }

  function clearError() {
    const banner = document.getElementById("board-error");
    banner.hidden = true;
  }

  window.BoardApp = { fetchJson, showError, clearError };
})();
```

`static/index.html`: add `<script src="/static/js/board.js" defer></script>` after the
`board-logic.js` include. No page-load side effects yet (no `DOMContentLoaded` listener), so
this is safe to load before it does anything.

`.context-index/governance/gates.yaml`: add a new gate alongside `test`/`lint`:

```yaml
  - id: test-js
    name: JS Unit Tests
    kind: deterministic
    tier: fast
    command: [node, --test, tests_js/]
    scope: project
    required: true
    severity: error
    triggers:
      - post-task
      - post-implement
```

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-5-fetch-error.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board.js static/js/board-logic.js static/index.html \
        tests_js/beh-5-fetch-error.test.js .context-index/governance/gates.yaml
git commit -m "feat(kanban-ui): add fetch error banner and wire JS test gate"
```

---

### Task 4: Board load & fetch wiring [specialist: none]

**Charter capability:** Render kanban board, Project switcher (initial population)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2, Task 3
**Files:**
- Create: `tests_js/beh-1-board-load.test.js`
- Modify: `static/js/board-logic.js` (add `pickDefaultProject`)
- Modify: `static/js/board.js` (add `init()`, render helpers, `DOMContentLoaded` wiring)

**Tests:** `tests_js/beh-1-board-load.test.js` — new suite (BEH-1).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-1)
- `app/routers/projects.py` (`GET /projects` shape — signature only)
- `app/routers/issues.py` (`GET /issues?project_id=` shape — signature only)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { pickDefaultProject } = require("../static/js/board-logic.js");

const projects = [
  { id: 1, key: "SDLC", name: "SDLC Track" },
  { id: 2, key: "DDLC", name: "DDLC Track" },
];

test("BEH-1: defaults to the first project when nothing was remembered", () => {
  assert.equal(pickDefaultProject(projects, null).id, 1);
});

test("BEH-1: defaults to the last-selected project when it still exists", () => {
  assert.equal(pickDefaultProject(projects, "DDLC").id, 2);
});

test("BEH-1: falls back to the first project when the remembered key is gone", () => {
  assert.equal(pickDefaultProject(projects, "GONE").id, 1);
});

test("BEH-1: returns null for zero projects (BEH-6 empty-state hook)", () => {
  assert.equal(pickDefaultProject([], null), null);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-1-board-load.test.js`
Expected: FAIL — `pickDefaultProject is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function pickDefaultProject(projects, lastSelectedKey) {
    if (!Array.isArray(projects) || projects.length === 0) return null;
    if (lastSelectedKey) {
      const remembered = projects.find((p) => p.key === lastSelectedKey);
      if (remembered) return remembered;
    }
    return projects[0];
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject,
  };
```

Add to `board.js` (extends the module from Task 3):

```javascript
  const LAST_PROJECT_KEY = "kanban-ui:lastProjectKey";

  function getLastSelectedKey() {
    try {
      return window.localStorage.getItem(LAST_PROJECT_KEY);
    } catch (_e) {
      return null; // private browsing / storage disabled — in-memory-only fallback
    }
  }

  function setLastSelectedKey(key) {
    try {
      window.localStorage.setItem(LAST_PROJECT_KEY, key);
    } catch (_e) {
      // storage unavailable — selection just won't persist across reloads
    }
  }

  function renderSwitcher(projects, selectedId) {
    const select = document.getElementById("project-switcher");
    select.innerHTML = projects
      .map((p) => {
        const sel = p.id === selectedId ? " selected" : "";
        return `<option value="${p.id}"${sel}>${BoardLogic.escapeHtml(p.key)} — ` +
          `${BoardLogic.escapeHtml(p.name)}</option>`;
      })
      .join("");
  }

  function renderColumns(grouped) {
    for (const col of BoardLogic.BOARD_COLUMNS) {
      document.getElementById(`col-${col.status}`).innerHTML =
        grouped[col.status].map(BoardLogic.buildCardHtml).join("");
    }
  }

  async function loadIssuesFor(projectId) {
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
      clearError();
      renderColumns(BoardLogic.groupIssuesByStatus(issues));
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading issues", err));
    }
  }

  async function init() {
    let projects;
    try {
      projects = await fetchJson("/projects");
      clearError();
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading projects", err));
      return;
    }
    const board = document.getElementById("board");
    const defaultProject = BoardLogic.pickDefaultProject(projects, getLastSelectedKey());
    if (!defaultProject) {
      // Task 7 fills in the empty-state branch here.
      return;
    }
    board.hidden = false;
    renderSwitcher(projects, defaultProject.id);
    await loadIssuesFor(defaultProject.id);
  }

  window.BoardApp = {
    fetchJson, showError, clearError, renderSwitcher, renderColumns, loadIssuesFor, init,
    getLastSelectedKey, setLastSelectedKey,
  };

  document.addEventListener("DOMContentLoaded", init);
```

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-1-board-load.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js tests_js/beh-1-board-load.test.js
git commit -m "feat(kanban-ui): load projects and issues on board open"
```

---

### Task 5: Project switcher selection [specialist: none]

**Charter capability:** Project switcher
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Create: `tests_js/beh-3-project-switch.test.js`
- Modify: `static/js/board-logic.js` (add `computeBoardState`)
- Modify: `static/js/board.js` (switcher `change` handler)

**Tests:** `tests_js/beh-3-project-switch.test.js` — new suite (BEH-3).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-3, Postconditions)
- `.context-index/specs/features/kanban-ui/charter.md` (Invariants: "switching Projects fully
  replaces the visible set, never merges two Projects' issues on screen at once")

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { computeBoardState } = require("../static/js/board-logic.js");

test("BEH-3: board state for a project holds only that project's issues", () => {
  const stateA = computeBoardState(1, [{ id: 10, status: "todo" }]);
  const stateB = computeBoardState(2, [{ id: 20, status: "done" }]);
  assert.equal(stateA.projectId, 1);
  assert.equal(stateB.projectId, 2);
  assert.equal(stateA.columns.todo.length, 1);
  assert.equal(stateB.columns.todo.length, 0);
  // Recomputing for project 2 never carries project 1's issue forward.
  assert.deepEqual(stateB.columns.done.map((i) => i.id), [20]);
});

test("BEH-3: switching to an empty project fully clears prior columns", () => {
  const state = computeBoardState(3, []);
  assert.deepEqual(state.columns.todo, []);
  assert.deepEqual(state.columns.in_progress, []);
  assert.deepEqual(state.columns.done, []);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-3-project-switch.test.js`
Expected: FAIL — `computeBoardState is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function computeBoardState(projectId, issues) {
    return { projectId, columns: groupIssuesByStatus(issues) };
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState,
  };
```

`computeBoardState` always rebuilds columns from scratch from the given `issues` array — there
is no accumulation across calls, so a second call for a different project cannot leak the first
project's cards into the render. Wire it into `board.js`'s render path and add the switcher
listener:

```javascript
  function renderBoardState(state) {
    renderColumns(state.columns);
  }

  async function loadIssuesFor(projectId) {
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
      clearError();
      renderBoardState(BoardLogic.computeBoardState(projectId, issues));
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading issues", err));
    }
  }

  function onProjectSwitch(event) {
    const projectId = Number(event.target.value);
    setLastSelectedKey(event.target.selectedOptions[0].dataset.key);
    loadIssuesFor(projectId);
  }

  document.getElementById("project-switcher").addEventListener("change", onProjectSwitch);
```

(`loadIssuesFor` is redefined here to route through `computeBoardState`/`renderBoardState`
instead of the Task 4 version's direct `groupIssuesByStatus` call — same public shape, now
switch-safe. Also add a `data-key="${p.key}"` attribute to each `<option>` in `renderSwitcher`
so `onProjectSwitch` can recover the project key for `setLastSelectedKey`.)

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-3-project-switch.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js tests_js/beh-3-project-switch.test.js
git commit -m "feat(kanban-ui): switching projects fully replaces the board"
```

---

### Task 6: Create-project form [specialist: none]

**Charter capability:** Create project
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Create: `tests_js/beh-4-create-project.test.js`
- Modify: `static/js/board-logic.js` (add `validateProjectForm`, `extractProjectSubmitError`)
- Modify: `static/js/board.js` (form `submit` handler)

**Tests:** `tests_js/beh-4-create-project.test.js` — new suite (BEH-4).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-4, Error Cases rows 2-3)
- `app/routers/projects.py` (full read of the two `HTTPException` blocks — 409 body shape
  `{"message": "Project key '<key>' already exists", "code": "PROJECT_KEY_DUPLICATE"}`, 422 body
  shape `{"message": "key is required" | "name is required", "code": "VALIDATION_ERROR"}`)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { validateProjectForm, extractProjectSubmitError } = require("../static/js/board-logic.js");

test("BEH-4/UI_VALIDATION_ERROR: blocks submit when key or name is blank", () => {
  assert.equal(validateProjectForm("", "Name").valid, false);
  assert.equal(validateProjectForm("KEY", "  ").valid, false);
  assert.equal(validateProjectForm("KEY", "Name").valid, true);
});

test("BEH-4/UI_VALIDATION_ERROR: names which field is missing", () => {
  const result = validateProjectForm("", "Name");
  assert.ok(result.errors.key);
  assert.equal(result.errors.name, undefined);
});

test("BEH-4/UI_PROJECT_KEY_DUPLICATE: maps a 409 to an inline key error", () => {
  const err = extractProjectSubmitError(409, {
    message: "Project key 'SDLC' already exists", code: "PROJECT_KEY_DUPLICATE",
  });
  assert.equal(err.field, "key");
  assert.match(err.message, /SDLC/);
});

test("BEH-4/UI_VALIDATION_ERROR: maps a server-side 422 to a form-level error", () => {
  const err = extractProjectSubmitError(422, { message: "name is required", code: "VALIDATION_ERROR" });
  assert.equal(err.field, "form");
});

test("extractProjectSubmitError returns null for a successful status", () => {
  assert.equal(extractProjectSubmitError(201, {}), null);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-4-create-project.test.js`
Expected: FAIL — `validateProjectForm is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function validateProjectForm(key, name) {
    const errors = {};
    if (!key || !key.trim()) errors.key = "Key is required";
    if (!name || !name.trim()) errors.name = "Name is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  function extractProjectSubmitError(status, body) {
    if (status === 409) {
      return { field: "key", message: (body && body.message) || "That project key is already taken." };
    }
    if (status === 422) {
      return { field: "form", message: (body && body.message) || "Please fill in all required fields." };
    }
    return null;
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
  };
```

Add to `board.js`:

```javascript
  function showFormError(message) {
    const el = document.getElementById("create-project-error");
    el.textContent = message;
    el.hidden = false;
  }

  function clearFormError() {
    document.getElementById("create-project-error").hidden = true;
  }

  async function onCreateProjectSubmit(event) {
    event.preventDefault();
    const keyInput = document.getElementById("project-key");
    const nameInput = document.getElementById("project-name");
    const { valid, errors } = BoardLogic.validateProjectForm(keyInput.value, nameInput.value);
    if (!valid) {
      showFormError(Object.values(errors)[0]);
      return; // client-side block — input is not cleared, no request sent (UI_VALIDATION_ERROR)
    }
    clearFormError();
    let resp;
    try {
      resp = await fetch("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: keyInput.value, name: nameInput.value }),
      });
    } catch (networkErr) {
      showError(BoardLogic.formatFetchError("Creating project", { message: networkErr.message }));
      return;
    }
    const body = await resp.json().catch(() => null);
    if (!resp.ok) {
      const submitErr = BoardLogic.extractProjectSubmitError(resp.status, body);
      showFormError(submitErr ? submitErr.message : "Could not create the project.");
      return; // input is not cleared on error, per the spec's Error Cases table
    }
    keyInput.value = "";
    nameInput.value = "";
    setLastSelectedKey(body.key);
    // Re-run init()'s project list + selection so the new project appears and is selected
    // (pickDefaultProject will now find `body.key` as the remembered selection).
    await init();
  }

  document.getElementById("create-project-form").addEventListener("submit", onCreateProjectSubmit);
```

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-4-create-project.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js tests_js/beh-4-create-project.test.js
git commit -m "feat(kanban-ui): add create-project form with inline error handling"
```

---

### Task 7: Empty-state handling [specialist: none]

**Charter capability:** Render kanban board (edge case), Create project (entry point)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Create: `tests_js/beh-6-empty-state.test.js`
- Modify: `static/js/board-logic.js` (add `shouldShowEmptyState`)
- Modify: `static/js/board.js` (`init()` empty-state branch)

**Tests:** `tests_js/beh-6-empty-state.test.js` — new suite (BEH-6).

**Context to load:**
- `.context-index/specs/features/kanban-ui/board-view.spec.md` (BEH-6, Postconditions: "A
  Project created through the create-project form is immediately selectable")

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { shouldShowEmptyState } = require("../static/js/board-logic.js");

test("BEH-6: zero projects shows the empty state", () => {
  assert.equal(shouldShowEmptyState([]), true);
});

test("BEH-6: any project at all means no empty state", () => {
  assert.equal(shouldShowEmptyState([{ id: 1, key: "SDLC", name: "SDLC Track" }]), false);
});

test("BEH-6: a missing/undefined projects value is treated as empty, not a crash", () => {
  assert.equal(shouldShowEmptyState(undefined), true);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/beh-6-empty-state.test.js`
Expected: FAIL — `shouldShowEmptyState is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function shouldShowEmptyState(projects) {
    return !Array.isArray(projects) || projects.length === 0;
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState,
  };
```

Fill in the branch left open in Task 4's `init()`:

```javascript
  async function init() {
    let projects;
    try {
      projects = await fetchJson("/projects");
      clearError();
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading projects", err));
      return;
    }
    const board = document.getElementById("board");
    const emptyState = document.getElementById("empty-state");
    if (BoardLogic.shouldShowEmptyState(projects)) {
      board.hidden = true;
      emptyState.hidden = false;
      return; // BEH-6: prompt to create, not an error, not a blank screen
    }
    emptyState.hidden = true;
    const defaultProject = BoardLogic.pickDefaultProject(projects, getLastSelectedKey());
    board.hidden = false;
    renderSwitcher(projects, defaultProject.id);
    await loadIssuesFor(defaultProject.id);
  }
```

A Project created via the create-project form (Task 6) re-runs this same `init()`, so it lands
in the non-empty branch and the newly created Project is immediately selected with a freshly
rendered — empty, since it has no Issues yet — board, matching the spec's Postconditions.

- [ ] **Verify test passes**

Run: `node --test tests_js/beh-6-empty-state.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js tests_js/beh-6-empty-state.test.js
git commit -m "feat(kanban-ui): show empty-state prompt when there are zero projects"
```

---

## Quality Gates

`.context-index/governance/gates.yaml` exists, so its gate definitions govern instead of the
constitution's Commands section. After Task 3 this plan's changes add one gate to that file;
the full resolved set after all 7 tasks:

- **Tests pass:** `python3 -m pytest -q` (gate `test`) — covers `tests/test_static_assets.py`
  plus all existing API tests (unaffected by this spec).
- **JS unit tests pass:** `node --test tests_js/` (gate `test-js`, added by Task 3) — covers all
  six `tests_js/beh-*.test.js` suites.
- **Lint passes:** `ruff check .` (gate `lint`) — Python only; `static/`, `tests_js/`, and the
  new `*.js`/`*.html`/`*.css` files fall outside ruff's scope, so no lint config change is
  needed for this spec.
- `integration-test` gate stays unwired (`command: ""`) — unaffected by this spec; not
  applicable to a static-asset, no-build-step UI.
- All acceptance criteria from `board-view.spec.md` satisfied: BEH-1 through BEH-6 each traced
  to exactly one task above, plus the spec's three Error Cases rows (`UI_FETCH_FAILED` — Task 3/
  4, `UI_PROJECT_KEY_DUPLICATE` and `UI_VALIDATION_ERROR` — Task 6).

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.
