<!-- partial_schema: plan@1 -->

# Implementation Plan: Sprints

> **Methodology:** adev
> **Charter:** .context-index/specs/cross-cutting/sprints/charter.md
> **Spec:** .context-index/specs/cross-cutting/sprints.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-09)
> **Platform:** Python 3.11, FastAPI-shaped issue-tracker-api backend, SQLite (no ORM), vanilla JS/HTML/CSS kanban-ui frontend, MCP Python SDK for mcp-server

**Goal:** Add Sprint entity/lifecycle to issue-tracker-api, an optional `Issue.sprint_id` field, a kanban-ui Sprint view + Backlog sprint-assignment action, and three mirroring mcp-server MCP tools.

**Architecture:** issue-tracker-api gains a `sprints` table and a new `app/routers/sprints.py` (following `app/routers/projects.py`'s exact create/list/error pattern), plus an `Issue.sprint_id` column and extended `patch_issue` validation in the existing `app/routers/issues.py`. kanban-ui reuses `board-logic.js`'s existing `buildCardHtml`/`groupIssuesByStatus`/`columnCounts` for the Sprint view (same rendering, different Issue subset) and adds an "Add to sprint" action to `backlog-view`'s table rows once that spec lands. mcp-server gains `mcp_server/tools/sprints.py` (one file per resource, matching the existing convention) and extends `update_issue`.

> **Sequencing note:** Task 4 (Backlog "Add to sprint" integration) modifies `renderBacklog`/the
> Backlog table row markup — code that does not exist in this repo yet, since `backlog-view` is
> only planned, not implemented, as of this plan's authoring. **Task 4 cannot start until
> `backlog-view`'s plan (`.context-index/specs/features/kanban-ui/backlog-view.plan.md`) is
> implemented.** Tasks 1, 2, 3, 5 have no such blocker.

---

## File Structure

**Modify:**
- `app/db.py` — add `sprints` table to `create_schema()`; add `sprint_id` column to `issues` table
- `app/models.py` — add `SprintCreate`, `SprintRead`, `SprintPatch`; add `sprint_id` to `IssueRead`/`IssuePatch`
- `app/routers/issues.py` — extend `patch_issue`'s validation and `_row_to_issue_read`; `create_issue` explicitly ignores any `sprint_id` in the request body (BEH-13)
- `app/main.py` — register the new sprints router
- `static/index.html` — "Sprint" nav item + `#view-sprint` section; start/close-sprint controls
- `static/js/board.js` — `renderSprintView`, `onStartSprint`/`onCloseSprint`, wire `showView`
- `static/js/board-logic.js` — add `filterIssuesBySprintId` (thin wrapper reusing existing patterns, no new rendering function needed — Sprint view reuses `buildCardHtml`/`groupIssuesByStatus`/`columnCounts` verbatim)
- `static/js/board.js` (Task 4, blocked on backlog-view) — "Add to sprint" button in Backlog rows, `onAddToSprint` handler
- `mcp_server/client.py` — add `create_sprint`, `list_sprints`, `update_sprint`; extend `update_issue` with `sprint_id`
- `mcp_server/tools/sprints.py` — **create**: `create_sprint`, `list_sprints`, `update_sprint` tools
- `mcp_server/tools/issues.py` — extend `update_issue` tool's signature with `sprint_id`
- `mcp_server/server.py` — register the new sprints tool module

**Create:**
- `app/routers/sprints.py`

**Reference (read, do not modify):**
- `app/routers/projects.py` — follow `create_project`/`list_projects`'s exact validation/error pattern for Sprint create/list
- `app/routers/issues.py` — follow `patch_issue`'s existing 404-first, `exclude_unset` patch pattern for extending validation
- `static/js/board-logic.js` — `buildCardHtml`/`groupIssuesByStatus`/`columnCounts` (reused verbatim for the Sprint view, not reimplemented)
- `mcp_server/tools/issues.py` / `mcp_server/client.py` — pattern for the new `mcp_server/tools/sprints.py`

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/cross-cutting/sprints.spec.md` (BEH-1, BEH-2, BEH-3, BEH-4, BEH-5, BEH-6; Error Cases rows 1-6)
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: "Sprints (create/list/update, Issue assignment)"; Domain Model: Sprint entity, revision 19)
- Source files: `app/db.py` (full), `app/models.py` (full), `app/routers/projects.py` (full, as the create/list pattern)

### Task 2 Context
- Spec: `.context-index/specs/cross-cutting/sprints.spec.md` (BEH-7, BEH-8, BEH-9, BEH-13; Error Cases rows 4, 6, 7)
- Source files: `app/routers/issues.py` (full), `app/models.py` (full, including Task 1's Sprint additions)

### Task 3 Context
- Spec: `.context-index/specs/cross-cutting/sprints.spec.md` (BEH-10)
- Source files: `static/index.html` (full), `static/js/board.js` (full — `showView`, `renderColumns`, `loadIssuesFor`), `static/js/board-logic.js` (full — `buildCardHtml`, `groupIssuesByStatus`, `columnCounts`)

### Task 4 Context (blocked on backlog-view implementation)
- Spec: `.context-index/specs/cross-cutting/sprints.spec.md` (BEH-11)
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (for the table structure being extended)
- Source files: `static/index.html`, `static/js/board.js`, `static/js/board-logic.js` — **as they exist after backlog-view's plan is implemented**, not as they exist today

### Task 5 Context
- Spec: `.context-index/specs/cross-cutting/sprints.spec.md` (BEH-12)
- Source files: `mcp_server/tools/issues.py` (full), `mcp_server/client.py` (full, including Task 1/2's additions), `mcp_server/server.py` (full)

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 (shared files: `app/db.py`, `app/models.py`; Task 2 extends what Task 1 creates)
- Group B (independent): Task 3 (kanban-ui Sprint view — `static/*`, no file overlap with A)
- Group C (independent): Task 5 (mcp-server — `mcp_server/*`, uses fake-client tests per the `issue-comments` precedent, no dependency on Task 1/2's actual code)
- Task 4 is **not scheduled in a group** — it is blocked on an external plan (`backlog-view`), not on file dependencies within this plan. Once `backlog-view` is implemented, Task 4 can run independently of A/B/C (it touches `static/*` files Task 3 also touches, so sequence it after Task 3 if both are in flight, to avoid a merge conflict on `static/index.html`'s header/nav block).

Group A, Group B, and Group C touch disjoint files and can run fully in parallel; Task 5's tests use the same `_FakeClient` pattern as `issue-comments`' Task 3, so it needs no live API to verify.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Sprint entity + endpoints (issue-tracker-api) | medium | unit+integration | — | 1 create, 3 modify |
| 2 | Issue.sprint_id extension + validation (issue-tracker-api) | medium | unit+integration | Task 1 | 0 create, 3 modify |
| 3 | kanban-ui Sprint view | medium | unit | Task 1, Task 2 | 0 create, 3 modify |
| 4 | Backlog "Add to sprint" integration | small | unit | Task 2, external: `backlog-view` implemented | 0 create, 2 modify |
| 5 | Sprint MCP tools + update_issue extension | small | unit+integration | Task 1, Task 2 | 1 create, 4 modify |

---

## Task Structure

### Task 1: Sprint entity + endpoints (issue-tracker-api) [specialist: none]

**Charter capability:** Sprints (create/list/update, Issue assignment)
**Strategy:** unit (source: fallback, confidence: high); follows `tests/test_issues.py`'s real `TestClient`-driven pattern
**Files:**
- Create: `app/routers/sprints.py`
- Modify: `app/db.py` (add `sprints` table)
- Modify: `app/models.py` (add `SprintCreate`, `SprintRead`, `SprintPatch`)
- Modify: `app/main.py` (register `sprints_router`)
- Test: `tests/test_sprints.py`

**Tests:** `tests/test_sprints.py` — new file, using the real `_create_project(client)` helper (import from `tests/test_issues.py`, matching the `issue-comments` plan's established fix)

- [ ] **Write failing test**

```python
from tests.test_issues import _create_project


def test_create_sprint_returns_201_planned_status(client):
    project = _create_project(client)
    resp = client.post(f"/projects/{project['id']}/sprints", json={"name": "Sprint 1"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "planned"
    assert body["project_id"] == project["id"]

def test_create_sprint_status_field_is_ignored_at_creation(client):
    project = _create_project(client)
    resp = client.post(f"/projects/{project['id']}/sprints", json={"name": "S", "status": "active"})
    assert resp.json()["status"] == "planned"

def test_create_sprint_end_before_start_is_422(client):
    project = _create_project(client)
    resp = client.post(
        f"/projects/{project['id']}/sprints",
        json={"name": "S", "start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert resp.status_code == 422

def test_list_sprints_missing_project_is_404(client):
    resp = client.get("/projects/999999/sprints")
    assert resp.status_code == 404
    assert resp.json()["code"] == "SPRINT_PROJECT_NOT_FOUND"

def test_activate_sprint_while_another_is_active_is_rejected(client):
    project = _create_project(client)
    s1 = client.post(f"/projects/{project['id']}/sprints", json={"name": "S1"}).json()
    s2 = client.post(f"/projects/{project['id']}/sprints", json={"name": "S2"}).json()
    client.patch(f"/sprints/{s1['id']}", json={"status": "active"})
    resp = client.patch(f"/sprints/{s2['id']}", json={"status": "active"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_ALREADY_ACTIVE"

def test_closing_sprint_then_reactivating_is_rejected(client):
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_CLOSED"

def test_renaming_a_closed_sprint_is_allowed(client):
    # A closed Sprint rejects status changes, but name/date edits are NOT a status change
    # and must still succeed (BEH-3 / Error Cases: rejection is scoped to status transitions).
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/sprints/{sprint['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests/test_sprints.py -q`
Expected: FAIL — `404 Not Found` for `/projects/{id}/sprints` (route does not exist yet)

- [ ] **Implement**

In `app/db.py`, add to `create_schema()`:

```python
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS sprints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        name TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT,
        status TEXT NOT NULL DEFAULT 'planned'
    )
    """
)
```

In `app/models.py`, add `SprintCreate` (`name`, optional `start_date`/`end_date`), `SprintRead` (all fields), `SprintPatch` (optional `name`/`start_date`/`end_date`/`status`).

Create `app/routers/sprints.py` following `app/routers/projects.py`'s exact validation/error style: `POST /projects/{project_id}/sprints` (404 if project missing → `SPRINT_PROJECT_NOT_FOUND`; 422 empty name or `end_date < start_date` → `VALIDATION_ERROR`; always inserts `status='planned'` regardless of request body), `GET /projects/{project_id}/sprints` (404 `SPRINT_PROJECT_NOT_FOUND` if project missing), `PATCH /sprints/{sprint_id}` (404 `SPRINT_NOT_FOUND` if missing; 409 `SPRINT_CLOSED` **only when `"status"` is present in the request body** and the Sprint is already `closed` — per BEH-3/Error Cases, name/date-only edits on a closed Sprint are NOT rejected, only status-change attempts are; 409 `SPRINT_ALREADY_ACTIVE` if transitioning to `active` while a sibling Sprint in the same `project_id` is already `active` — query `SELECT id FROM sprints WHERE project_id = ? AND status = 'active' AND id != ?` before allowing the transition).

Register in `app/main.py`: `from app.routers.sprints import router as sprints_router` and `app.include_router(sprints_router)`.

- [ ] **Verify test passes**

Run: `python3 -m pytest tests/test_sprints.py -q`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/sprints/iteration-tracking`

```bash
git add app/db.py app/models.py app/routers/sprints.py app/main.py tests/test_sprints.py
git commit -m "feat(issue-tracker-api): add Sprint entity and endpoints"
```

---

### Task 2: Issue.sprint_id extension + validation (issue-tracker-api) [specialist: none]

**Charter capability:** Sprints (create/list/update, Issue assignment)
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `app/db.py` (`sprint_id` column on `issues`)
- Modify: `app/models.py` (add `sprint_id: int | None = None` to `IssueRead` and `IssuePatch` — required first: without this, `_row_to_issue_read`'s `sprint_id=row["sprint_id"]` is silently dropped by Pydantic's default `extra="ignore"` behavior, and `IssuePatch` never surfaces a client-supplied `sprint_id` for `patch_issue` to act on — every test in this task fails without this file)
- Modify: `app/routers/issues.py` (`_row_to_issue_read`, `create_issue`, `patch_issue`)
- Test: `tests/test_issue_sprint_assignment.py`

**Tests:** `tests/test_issue_sprint_assignment.py` — new file

- [ ] **Write failing test**

```python
from tests.test_issues import _create_project


def _create_issue(client, project_id):
    return client.post(
        "/issues",
        json={"project_id": project_id, "summary": "x", "issue_type": "task", "priority": "low"},
    ).json()


def test_new_issue_starts_unsprinted_even_if_sprint_id_is_supplied(client):
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    resp = client.post(
        "/issues",
        json={
            "project_id": project["id"], "summary": "x", "issue_type": "task", "priority": "low",
            "sprint_id": sprint["id"],
        },
    )
    assert resp.json()["sprint_id"] is None

def test_assign_issue_to_sprint(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    assert resp.json()["sprint_id"] == sprint["id"]

def test_assign_issue_to_sprint_from_different_project_is_422(client):
    p1 = _create_project(client, key="A")
    p2 = _create_project(client, key="B")
    issue = _create_issue(client, p1["id"])
    other_sprint = client.post(f"/projects/{p2['id']}/sprints", json={"name": "S"}).json()
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": other_sprint["id"]})
    assert resp.status_code == 422
    assert resp.json()["code"] == "SPRINT_PROJECT_MISMATCH"

def test_assign_issue_to_closed_sprint_is_409(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_CLOSED"

def test_unassign_issue_from_sprint(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": None})
    assert resp.json()["sprint_id"] is None
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests/test_issue_sprint_assignment.py -q`
Expected: FAIL — `KeyError: 'sprint_id'` or 422 on an unrecognized field

- [ ] **Implement**

In `app/db.py`, add `sprint_id INTEGER REFERENCES sprints(id)` to the `issues` table's `CREATE TABLE` statement (nullable, no default — SQLite defaults new columns to `NULL`).

In `app/models.py`, add `sprint_id: int | None = None` to `IssueRead` and `IssuePatch`.

In `app/routers/issues.py`: add `sprint_id=row["sprint_id"]` to `_row_to_issue_read`. In `create_issue`, explicitly do not read `sprint_id` from `payload` even if a client sends it (the `IssueCreate` model simply does not declare a `sprint_id` field, so FastAPI/Pydantic already ignores it — BEH-13 is satisfied by the model shape, not extra code). Add `"sprint_id"` to `_PATCHABLE_FIELDS`. In `patch_issue`, before the existing `set_clauses` construction, when `"sprint_id" in updates and updates["sprint_id"] is not None`: look up the sprint (404 `ISSUE_SPRINT_NOT_FOUND` if missing), compare `sprint["project_id"] != row["project_id"]` (422 `SPRINT_PROJECT_MISMATCH`), compare `sprint["status"] == "closed"` (409 `SPRINT_CLOSED`) — in that exact order (existence → project-match → status), per the spec's BEH-7.

- [ ] **Verify test passes**

Run: `python3 -m pytest tests/test_issue_sprint_assignment.py -q`
Expected: PASS

- [ ] **Commit**

```bash
git add app/db.py app/models.py app/routers/issues.py tests/test_issue_sprint_assignment.py
git commit -m "feat(issue-tracker-api): add Issue.sprint_id assignment with cross-Project/closed-sprint validation"
```

---

### Task 3: kanban-ui Sprint view [specialist: none]

**Charter capability:** Sprint view and Backlog sprint assignment
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 2
**Files:**
- Modify: `static/index.html` (`#nav-sprint`, `#view-sprint`, start/close-sprint controls)
- Modify: `static/js/board.js` (`renderSprintView`, `onStartSprint`, `onCloseSprint`)
- Modify: `static/js/board-logic.js` (thin `filterIssuesBySprintId(issues, sprintId)` helper)
- Test: `tests_js/sprints-beh-1-nav-and-render.test.js`

**Tests:** `tests_js/sprints-beh-1-nav-and-render.test.js` — new file

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { filterIssuesBySprintId } = require("../static/js/board-logic.js");

test("BEH-10: nav item and view container exist", () => {
  const html = readFileSync(require.resolve("../static/index.html"), "utf8");
  assert.match(html, /<button[^>]+id="nav-sprint"[^>]+data-view="sprint"[^>]*>/);
  assert.match(html, /<section id="view-sprint" class="view" hidden>/);
});

test("filterIssuesBySprintId: returns only issues matching the active sprint id", () => {
  const issues = [{ id: 1, sprint_id: 5 }, { id: 2, sprint_id: null }, { id: 3, sprint_id: 5 }];
  assert.deepEqual(filterIssuesBySprintId(issues, 5).map((i) => i.id), [1, 3]);
});

test("filterIssuesBySprintId: null active sprint returns an empty array", () => {
  const issues = [{ id: 1, sprint_id: 5 }];
  assert.deepEqual(filterIssuesBySprintId(issues, null), []);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/sprints-beh-1-nav-and-render.test.js`
Expected: FAIL — no `#nav-sprint`, `filterIssuesBySprintId is not a function`

- [ ] **Implement**

In `static/js/board-logic.js`, add:

```javascript
function filterIssuesBySprintId(issues, sprintId) {
  if (sprintId == null) return [];
  return Array.isArray(issues) ? issues.filter((i) => i.sprint_id === sprintId) : [];
}
```

Add to the export object. In `static/index.html`, add `<button type="button" class="nav-item" id="nav-sprint" data-view="sprint">Sprint</button>` after `#nav-backlog`, and `<section id="view-sprint" class="view" hidden>` containing a `<h1>Sprint</h1>`, a "Start sprint"/"Close sprint" button pair, and the same three-column board markup structure `#view-board` already uses (`.column` sections for `todo`/`in_progress`/`done`, reusing the same CSS classes — no new styling needed). In `static/js/board.js`, add `"sprint"` to `NAV_VIEWS`, `renderSprintView(issues, activeSprintId)` that calls `BoardLogic.groupIssuesByStatus(BoardLogic.filterIssuesBySprintId(issues, activeSprintId))` and renders via the same column-rendering logic `renderColumns` already uses (extract a shared helper if `renderColumns`'s body is reused, rather than duplicating it), and `onStartSprint`/`onCloseSprint` handlers calling `PATCH /sprints/{id}` with `status: "active"`/`"closed"`. When no Sprint is `active` for the selected Project, render the "No active sprint" message BEH-10 requires instead of an empty board.

- [ ] **Verify test passes**

Run: `node --test tests_js/sprints-beh-1-nav-and-render.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board.js static/js/board-logic.js tests_js/sprints-beh-1-nav-and-render.test.js
git commit -m "feat(kanban-ui): add Sprint nav view scoped to the active sprint"
```

---

### Task 4: Backlog "Add to sprint" integration [specialist: none] — BLOCKED on external plan

**Charter capability:** Sprint view and Backlog sprint assignment
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2, and **`backlog-view`'s implementation plan being executed first** (`.context-index/specs/features/kanban-ui/backlog-view.plan.md`) — `renderBacklog`/the Backlog table row markup this task extends do not exist in the repo until that plan lands.
**Files:**
- Modify: `static/index.html` (an "Add to sprint" button per Backlog row — exact markup depends on `backlog-view`'s landed implementation)
- Modify: `static/js/board.js` (`onAddToSprint` handler)
- Test: `tests_js/sprints-beh-2-add-to-sprint.test.js`

**Tests:** `tests_js/sprints-beh-2-add-to-sprint.test.js` — new file; exact assertions depend on `backlog-view`'s landed `buildBacklogRowsHtml` markup shape, so this task's test-writing step happens after that markup exists, not before

- [ ] **Write failing test**

Once `backlog-view` is implemented, read the landed `buildBacklogRowsHtml` output shape from `static/js/board-logic.js` and write a test asserting each row includes an "Add to sprint" control with `data-issue-id="<id>"`, following `backlog-view`'s own row-attribute convention.

- [ ] **Verify test fails**

Run: `node --test tests_js/sprints-beh-2-add-to-sprint.test.js`
Expected: FAIL — no "Add to sprint" control in the row markup

- [ ] **Implement**

Add an "Add to sprint" button to each Backlog row (in `buildBacklogRowsHtml`, or via a `board.js`-side augmentation — follow whatever pattern `backlog-view`'s landed code actually uses for per-row actions). Wire `onAddToSprint(issueId)` to call `PATCH /issues/{issueId}` with the Project's current `active` Sprint's id (read from the same state Task 3's Sprint view uses), then re-render the Backlog row to reflect the new `sprint_id` without a full page reload (BEH-11).

- [ ] **Verify test passes**

Run: `node --test tests_js/sprints-beh-2-add-to-sprint.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board.js tests_js/sprints-beh-2-add-to-sprint.test.js
git commit -m "feat(kanban-ui): add 'Add to sprint' action to Backlog rows"
```

---

### Task 5: Sprint MCP tools + update_issue extension [specialist: none]

**Charter capability:** create_sprint tool, list_sprints tool, update_sprint tool
**Strategy:** unit (source: fallback, confidence: high); `_FakeClient` + `monkeypatch` pattern per `tests/mcp_server/test_issue_tools.py` (same fix already validated in the `issue-comments` plan)
**Depends on:** Task 1, Task 2
**Files:**
- Create: `mcp_server/tools/sprints.py`
- Modify: `mcp_server/client.py` (`create_sprint`, `list_sprints`, `update_sprint`)
- Modify: `mcp_server/tools/issues.py` (`update_issue` tool gains `sprint_id`/`unassign_sprint` parameters)
- Modify: `mcp_server/server.py` (register `mcp_server.tools.sprints`)
- Modify: `tests/mcp_server/test_issue_tools.py` (append 2 tests for the extended `update_issue` tool)
- Test: `tests/mcp_server/test_sprint_tools.py`

**Tests:** `tests/mcp_server/test_sprint_tools.py` — new file, following `tests/mcp_server/test_issue_tools.py`'s real `_FakeClient`/`monkeypatch`/`Client(mcp).call_tool(...)` structure exactly (see the `issue-comments` plan's Task 3 for the validated version of this pattern)

- [ ] **Write failing test**

```python
import pytest
from mcp import Client

import mcp_server.tools.sprints as sprints_tools
from mcp_server.server import mcp


class _FakeClient:
    def __init__(self, sprints=None, sprint=None):
        self._sprints = sprints or []
        self._sprint = sprint

    async def list_sprints(self, project_id):
        return self._sprints

    async def create_sprint(self, project_id, name, start_date=None, end_date=None):
        return self._sprint

    async def update_sprint(self, sprint_id, **fields):
        return self._sprint

    async def aclose(self):
        pass


_SAMPLE_SPRINT = {"id": 1, "project_id": 1, "name": "Sprint 1", "start_date": None, "end_date": None, "status": "planned"}


@pytest.mark.anyio
async def test_create_sprint_tool_returns_the_sprint(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprint=_SAMPLE_SPRINT))

    async with Client(mcp) as client:
        result = await client.call_tool("create_sprint", {"project_id": 1, "name": "Sprint 1"})

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_SPRINT


@pytest.mark.anyio
async def test_list_sprints_tool_returns_api_result_unmodified(monkeypatch):
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprints=[_SAMPLE_SPRINT]))

    async with Client(mcp) as client:
        result = await client.call_tool("list_sprints", {"project_id": 1})

    assert result.is_error is False
    assert result.structured_content == {"result": [_SAMPLE_SPRINT]}


@pytest.mark.anyio
async def test_update_sprint_tool_returns_updated_sprint(monkeypatch):
    updated = {**_SAMPLE_SPRINT, "status": "active"}
    monkeypatch.setattr(sprints_tools, "_client", lambda: _FakeClient(sprint=updated))

    async with Client(mcp) as client:
        result = await client.call_tool("update_sprint", {"sprint_id": 1, "status": "active"})

    assert result.is_error is False
    assert result.structured_content == updated
```

```python
# Appended to tests/mcp_server/test_issue_tools.py (extends the existing update_issue coverage,
# not a new file — the tool being tested already lives there)
import mcp_server.tools.issues as issues_tools


class _SprintAssignClient(_FakeClient):
    def __init__(self):
        super().__init__(issue={**_SAMPLE_ISSUE, "sprint_id": 5})

    async def update_issue(self, issue_id, **fields):
        return {**_SAMPLE_ISSUE, "sprint_id": fields.get("sprint_id")}


@pytest.mark.anyio
async def test_update_issue_tool_assigns_sprint_id(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _SprintAssignClient())

    async with Client(mcp) as client:
        result = await client.call_tool("update_issue", {"issue_id": 1, "sprint_id": 5})

    assert result.is_error is False
    assert result.structured_content["sprint_id"] == 5


@pytest.mark.anyio
async def test_update_issue_tool_unassigns_sprint_via_dedicated_flag(monkeypatch):
    monkeypatch.setattr(issues_tools, "_client", lambda: _SprintAssignClient())

    async with Client(mcp) as client:
        result = await client.call_tool("update_issue", {"issue_id": 1, "unassign_sprint": True})

    assert result.is_error is False
    assert result.structured_content["sprint_id"] is None
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests/mcp_server/test_sprint_tools.py tests/mcp_server/test_issue_tools.py -q`
Expected: FAIL — `ModuleNotFoundError: mcp_server.tools.sprints`, then (once that module exists) `TypeError: update_issue() got an unexpected keyword argument 'unassign_sprint'`

- [ ] **Implement**

**Design note — why `unassign_sprint` is a separate boolean, not just `sprint_id: None`:** `mcp_server/client.py`'s existing `update_issue(self, issue_id, **fields)` filters `payload = {k: v for k, v in fields.items() if v is not None}` (confirmed in `test_update_issue_tool_ignores_immutable_fields`). Passing `sprint_id=None` to mean "unassign" is therefore indistinguishable from "sprint_id wasn't provided at all" — a pre-existing pattern limitation of this method that a plain `sprint_id: int | None = None` tool parameter cannot work around. Rather than special-casing a sentinel value through this shared method (which every other tool call also relies on), add a second, unambiguous tool parameter.

In `mcp_server/client.py`, add `create_sprint(self, project_id, name, start_date=None, end_date=None)`, `list_sprints(self, project_id)`, `update_sprint(self, sprint_id, **fields)`, following `create_issue`/`update_issue`'s existing `_request` patterns exactly.

Create `mcp_server/tools/sprints.py` mirroring `mcp_server/tools/issues.py`'s structure: `create_sprint`, `list_sprints`, `update_sprint` tools, each with the same `ToolError`/`UpstreamError`/`UpstreamUnreachableError` translation.

In `mcp_server/tools/issues.py`, add two parameters to `update_issue`: `sprint_id: int | None = None` (assign to this Sprint) and `unassign_sprint: bool = False` (explicitly clear it). **Precedence, as a deliberate design decision:** if both `sprint_id` and `unassign_sprint=True` are passed in the same call, `unassign_sprint` wins — the caller is treated as asking to clear the assignment regardless of what `sprint_id` was also set to. In the function body, compute the value to pass through: `effective_sprint_id = None if unassign_sprint else sprint_id`, then call `client.update_issue(issue_id, ..., sprint_id=effective_sprint_id)` **only when `sprint_id is not None or unassign_sprint`** (i.e., build the call's kwargs conditionally so the client's `is not None` filter still applies correctly to the assign case, while the unassign case needs the client to actually send `sprint_id: null` — extend `mcp_server/client.py`'s `update_issue` to accept `sprint_id` as a distinct parameter outside the generic `**fields` filtering, defaulting to a module-level sentinel `_UNSET = object()`, and only include it in the outgoing JSON payload when `sprint_id is not _UNSET` — this lets the tool pass `sprint_id=None` through to the HTTP layer when unassigning, while every other field keeps the existing omit-if-None behavior).

In `mcp_server/server.py`'s `main()`, add `import mcp_server.tools.sprints`.

- [ ] **Verify test passes**

Run: `python3 -m pytest tests/mcp_server/test_sprint_tools.py -q`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/sprints.py mcp_server/client.py mcp_server/tools/issues.py mcp_server/server.py tests/mcp_server/test_sprint_tools.py tests/mcp_server/test_issue_tools.py
git commit -m "feat(mcp-server): add Sprint MCP tools and extend update_issue with sprint_id"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

- Tests pass: `python3 -m pytest -q` and `node --test tests_js/`
- Lint passes: `ruff check .`
- All acceptance criteria from spec satisfied
- No existing endpoint's response shape loses or renames a field — only `Issue` gains `sprint_id` (verify via `git diff` on every existing route in `app/routers/issues.py`, `app/routers/projects.py`, `app/routers/users.py`)
- Task 4 was not started before `backlog-view`'s plan was fully implemented and validated
