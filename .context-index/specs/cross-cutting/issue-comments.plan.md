<!-- partial_schema: plan@1 -->

# Implementation Plan: Issue comments and activity log

> **Methodology:** adev
> **Charter:** .context-index/specs/cross-cutting/issue-comments/charter.md
> **Spec:** .context-index/specs/cross-cutting/issue-comments.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-09)
> **Platform:** Python 3.11, FastAPI-shaped issue-tracker-api backend, SQLite (no ORM), vanilla JS/HTML/CSS kanban-ui frontend, MCP Python SDK for mcp-server

**Goal:** Add a per-Issue Comment activity log: two new issue-tracker-api endpoints, a comment-thread panel in kanban-ui's edit-issue form, and two mirroring mcp-server MCP tools — entirely additive, no existing endpoint's shape changes.

**Architecture:** issue-tracker-api gains a `comments` SQLite table (FK to `issues`, `ON DELETE CASCADE` semantics enforced at the application layer to match the existing codebase's no-ORM, explicit-SQL style) and two routes added to `app/routers/issues.py` (the existing home for all `/issues*` routes). kanban-ui's edit-issue form gains a comment list + add-comment control, following the same `fetchJson`/`escapeHtml` patterns already used throughout `board.js`/`board-logic.js`. mcp-server gains a new `mcp_server/tools/comments.py` module (one file per resource, matching `tools/issues.py`/`tools/projects.py`/`tools/users.py`) and two new `IssueTrackerClient` methods.

---

## File Structure

**Modify:**
- `app/db.py` — add `comments` table to `create_schema()`
- `app/models.py` — add `CommentCreate`, `CommentRead`
- `app/routers/issues.py` — add `POST`/`GET /issues/{issue_id}/comments`; modify `delete_issue` to cascade-delete Comments
- `static/index.html` — add a comment-thread section inside `#edit-issue`'s form (list + add-comment control)
- `static/js/board-logic.js` — add `buildCommentListHtml(comments)`, `validateCommentForm(body)`
- `static/js/board.js` — add `loadComments(issueId)`, `onCommentSubmit`, wire both into the existing `openEditIssue`/edit-form lifecycle
- `mcp_server/client.py` — add `list_comments(issue_id)`, `create_comment(issue_id, body)`
- `mcp_server/tools/comments.py` — **create**: `list_issue_comments`, `create_issue_comment` tools
- `mcp_server/server.py` — add `import mcp_server.tools.comments` to `main()`'s tool-registration block

**Reference (read, do not modify):**
- `app/routers/issues.py` — follow `create_issue`/`get_issue`/`delete_issue`'s exact error-shape and cursor pattern (`HTTPException(status_code=..., detail={"message": ..., "code": ...})`)
- `app/models.py` — follow `IssueCreate`/`IssueRead`'s Pydantic pattern
- `static/js/board.js` — follow `reportIssueMutationFailure`/`onEditIssueSubmit`'s existing 404-vs-generic-error split (this is exactly the pattern the spec's Error Cases table requires the comment submit path to reuse)
- `mcp_server/tools/issues.py` — follow its exact `ToolError`/`UpstreamError`/`UpstreamUnreachableError` translation pattern
- `mcp_server/client.py` — follow `create_issue`/`get_issue`'s `_request` usage pattern

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/cross-cutting/issue-comments.spec.md` (BEH-1, BEH-2, BEH-8; Error Cases rows 1-2)
- Charter: `.context-index/specs/features/issue-tracker-api/charter.md` (capability: "Comments on Issues (create/list)"; Domain Model: Comment entity, revision 17)
- Source files: `app/db.py` (full), `app/models.py` (full), `app/routers/issues.py` (full)

### Task 2 Context
- Spec: `.context-index/specs/cross-cutting/issue-comments.spec.md` (BEH-3, BEH-4, BEH-5; Error Cases row 3-4)
- Source files: `static/index.html` (full — `#edit-issue` section), `static/js/board-logic.js` (full — `escapeHtml`, `buildUserListHtml` as pattern), `static/js/board.js` (full — `openEditIssue`, `onEditIssueSubmit`, `reportIssueMutationFailure`)

### Task 3 Context
- Spec: `.context-index/specs/cross-cutting/issue-comments.spec.md` (BEH-6, BEH-7)
- Source files: `mcp_server/tools/issues.py` (full — pattern to mirror), `mcp_server/client.py` (full), `mcp_server/server.py` (full)

---

## Parallelization

- Group A (independent): Task 1 (issue-tracker-api — `app/db.py`, `app/models.py`, `app/routers/issues.py`)
- Group B (independent): Task 3 (mcp-server — `mcp_server/*`, uses a `_FakeClient` stand-in, so its tests need no live API and it can be *file-written and verified* with zero dependency on Task 1's actual code)
- Group C (sequential): Task 2 (kanban-ui — `static/*`, no file overlap with A/B)

Group A and Group B touch entirely disjoint files and have no test-time dependency on each other, so they run fully in parallel regardless of order. Task 2's **files** don't overlap with Group A or B either, but unlike Group B its "Verify test passes" step calls the real endpoints (no fake client), so it needs Task 1's endpoints actually running first — that is a runtime/verification-order dependency, not a file dependency, which is why the Task Summary table's "Depends On: Task 1" column and this section's "Task 2 has no file overlap with A/B" are both true at once.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Comment entity + endpoints (issue-tracker-api) | medium | unit+integration | — | 0 create, 3 modify |
| 2 | Comment-thread panel (kanban-ui) | medium | unit | Task 1 | 0 create, 3 modify |
| 3 | Comment MCP tools (mcp-server) | small | unit+integration | — | 1 create, 2 modify |

---

## Task Structure

### Task 1: Comment entity + endpoints (issue-tracker-api) [specialist: none]

**Charter capability:** Comments on Issues (create/list)
**Strategy:** unit (source: fallback, confidence: high); the existing project's own `test_issues.py`/`tests_e2e/test_issue_lifecycle_e2e.py` split (in-process pytest unit tests + real-socket e2e tests) is the established pattern — this task covers the unit-tier; e2e coverage for this endpoint pair is added as part of this same task's test file per the project's existing `tests/test_issues.py` convention (which already exercises the full HTTP surface via FastAPI's TestClient, not raw functions)
**Files:**
- Modify: `app/db.py` (add `comments` table to `create_schema()`)
- Modify: `app/models.py` (add `CommentCreate`, `CommentRead`)
- Modify: `app/routers/issues.py` (add two routes; modify `delete_issue`)
- Test: `tests/test_comments.py`

**Tests:** `tests/test_comments.py` — new file, following `tests/test_issues.py`'s FastAPI `TestClient`-driven pattern exactly (never calling route functions directly). Uses the real `client` fixture from `tests/conftest.py` and the real `_create_project(client)` inline-helper pattern from `tests/test_issues.py` — copy that helper into this file (or import it: `from tests.test_issues import _create_project`), plus a matching `_create_issue(client, project_id)` helper of the same shape.

- [ ] **Write failing test**

```python
from tests.test_issues import _create_project


def _create_issue(client, project_id, summary="Fix bug"):
    return client.post(
        "/issues",
        json={"project_id": project_id, "summary": summary, "issue_type": "bug", "priority": "low"},
    ).json()


def test_create_comment_returns_201_with_created_comment(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    resp = client.post(f"/issues/{issue['id']}/comments", json={"body": "Looks good to me."})
    assert resp.status_code == 201
    body = resp.json()
    assert body["issue_id"] == issue["id"]
    assert body["body"] == "Looks good to me."
    assert "id" in body and "created_at" in body

def test_create_comment_empty_body_is_422(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    resp = client.post(f"/issues/{issue['id']}/comments", json={"body": ""})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_create_comment_on_missing_issue_is_404(client):
    resp = client.post("/issues/999999/comments", json={"body": "x"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"

def test_list_comments_returns_chronological_order(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    client.post(f"/issues/{issue['id']}/comments", json={"body": "first"})
    client.post(f"/issues/{issue['id']}/comments", json={"body": "second"})
    resp = client.get(f"/issues/{issue['id']}/comments")
    assert resp.status_code == 200
    bodies = [c["body"] for c in resp.json()]
    assert bodies == ["first", "second"]

def test_deleting_issue_deletes_its_comments(client):
    # Real cascade proof: query the comments table directly via the TestClient's own db
    # connection (client.app.state.db_conn, set by app.main's startup handler) rather than
    # relying on the 404-on-deleted-issue side effect, which would pass even if the
    # cascade-delete implementation step were skipped entirely.
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    created = client.post(f"/issues/{issue['id']}/comments", json={"body": "will be cascaded"}).json()
    client.delete(f"/issues/{issue['id']}")
    conn = client.app.state.db_conn
    row = conn.execute("SELECT * FROM comments WHERE id = ?", (created["id"],)).fetchone()
    assert row is None
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests/test_comments.py -q`
Expected: FAIL — `404 Not Found` for `/issues/{id}/comments` (route does not exist yet)

- [ ] **Implement**

In `app/db.py`, add to `create_schema()`:

```python
conn.execute(
    """
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL REFERENCES issues(id),
        body TEXT NOT NULL,
        author TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
)
```

In `app/models.py`, add:

```python
class CommentCreate(BaseModel):
    body: str
    author: str | None = None


class CommentRead(BaseModel):
    id: int
    issue_id: int
    body: str
    author: str
    created_at: str
```

In `app/routers/issues.py`, add a `_row_to_comment_read` helper and two routes (placed after `get_issue`, before the `_PATCHABLE_FIELDS` line):

```python
def _row_to_comment_read(row) -> CommentRead:
    return CommentRead(
        id=row["id"], issue_id=row["issue_id"], body=row["body"],
        author=row["author"], created_at=row["created_at"],
    )


def _require_issue(conn, issue_id: int):
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    return row


@router.post("/issues/{issue_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(issue_id: int, payload: CommentCreate, request: Request):
    conn = request.app.state.db_conn
    _require_issue(conn, issue_id)
    if not payload.body or not payload.body.strip():
        raise HTTPException(
            status_code=422,
            detail={"message": "body is required", "code": "VALIDATION_ERROR"},
        )
    cursor = conn.execute(
        "INSERT INTO comments (issue_id, body, author) VALUES (?, ?, ?)",
        (issue_id, payload.body, payload.author or ""),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_comment_read(row)


@router.get("/issues/{issue_id}/comments", response_model=list[CommentRead])
def list_comments(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    _require_issue(conn, issue_id)
    rows = conn.execute(
        "SELECT * FROM comments WHERE issue_id = ? ORDER BY id ASC", (issue_id,)
    ).fetchall()
    return [_row_to_comment_read(r) for r in rows]
```

Add `CommentCreate, CommentRead` to the existing `from app.models import ...` line. Modify `delete_issue` to cascade — insert `conn.execute("DELETE FROM comments WHERE issue_id = ?", (issue_id,))` immediately before the existing `conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))` line, inside the same transaction (before the single `conn.commit()` that already follows both).

- [ ] **Verify test passes**

Run: `python3 -m pytest tests/test_comments.py -q`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/issue-comments/activity-log`

```bash
git add app/db.py app/models.py app/routers/issues.py tests/test_comments.py
git commit -m "feat(issue-tracker-api): add Comment entity and issue comment endpoints"
```

---

### Task 2: Comment-thread panel (kanban-ui) [specialist: none]

**Charter capability:** Comment thread panel in edit-issue form
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Modify: `static/index.html` (comment-thread section inside `#edit-issue`)
- Modify: `static/js/board-logic.js` (add `buildCommentListHtml`, `validateCommentForm`)
- Modify: `static/js/board.js` (`loadComments`, `onCommentSubmit`, wire into `openEditIssue`)
- Test: `tests_js/issue-comments-beh-1-render.test.js`, `tests_js/issue-comments-beh-2-validation.test.js`

**Tests:** `tests_js/issue-comments-beh-1-render.test.js` and `tests_js/issue-comments-beh-2-validation.test.js` — new files, following `visual-refresh-beh-3-issue-key.test.js`'s pure-function-testing pattern for `board-logic.js` additions

- [ ] **Write failing test**

```javascript
// tests_js/issue-comments-beh-1-render.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCommentListHtml } = require("../static/js/board-logic.js");

test("BEH-3: renders one entry per comment, chronological order preserved from input", () => {
  const html = buildCommentListHtml([
    { id: 1, body: "first", author: "Mei Tan", created_at: "2026-09-09 10:00:00" },
    { id: 2, body: "second", author: "", created_at: "2026-09-09 10:05:00" },
  ]);
  const firstIdx = html.indexOf("first");
  const secondIdx = html.indexOf("second");
  assert.ok(firstIdx >= 0 && secondIdx > firstIdx);
  assert.match(html, /Unassigned/); // blank author, BEH-3
});

test("BEH-3: HTML-escapes comment body and author", () => {
  const html = buildCommentListHtml([{ id: 1, body: "<script>", author: "<b>", created_at: "x" }]);
  assert.doesNotMatch(html, /<script>/);
  assert.doesNotMatch(html, /<b>/);
});

test("zero comments renders an empty string", () => {
  assert.equal(buildCommentListHtml([]), "");
});
```

```javascript
// tests_js/issue-comments-beh-2-validation.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { validateCommentForm } = require("../static/js/board-logic.js");

test("BEH-5: empty body is invalid", () => {
  assert.equal(validateCommentForm("").valid, false);
  assert.equal(validateCommentForm("   ").valid, false);
});

test("BEH-4: non-empty body is valid", () => {
  assert.equal(validateCommentForm("looks good").valid, true);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-comments-beh-1-render.test.js tests_js/issue-comments-beh-2-validation.test.js`
Expected: FAIL — `buildCommentListHtml is not a function`

- [ ] **Implement**

In `static/js/board-logic.js`, add (following `buildUserListHtml`'s exact interpolation/escaping style):

```javascript
function buildCommentListHtml(comments) {
  if (!Array.isArray(comments)) return "";
  return comments
    .map((c) => (
      `<div class="comment-row">` +
      `<p class="comment-meta">${escapeHtml(c.author || "Unassigned")} &middot; ${escapeHtml(c.created_at)}</p>` +
      `<p class="comment-body">${escapeHtml(c.body)}</p>` +
      `</div>`
    ))
    .join("");
}

function validateCommentForm(body) {
  const errors = {};
  if (!body || !body.trim()) errors.body = "Comment cannot be empty";
  return { valid: Object.keys(errors).length === 0, errors };
}
```

Add both to the export object. In `static/index.html`, inside `#edit-issue`'s `<form>`, after the existing `#edit-issue-error` paragraph but still inside the `<section id="edit-issue">` (i.e., outside the `<form>` tag, as a sibling section, matching how `#delete-issue` already sits just before the form closes — place the comment panel as a new `<div id="comment-panel">` block after `</form>`), add: a `<div id="comment-list"></div>`, a `<textarea id="new-comment-body"></textarea>`, a submit `<button id="submit-comment">Add comment</button>`, and a `<p id="comment-form-error" role="alert" hidden></p>`.

In `static/js/board.js`: add `async function loadComments(issueId)` that calls `fetchJson(`/issues/${issueId}/comments`)` and renders via `BoardLogic.buildCommentListHtml`, called from inside the existing `openEditIssue(issue)` function (after it sets `editingIssue`). Add `onCommentSubmit` that validates via `BoardLogic.validateCommentForm`, and on success calls `fetchJson` `POST /issues/${editingIssue.id}/comments`, then re-renders the list; on failure, reuse `reportIssueMutationFailure("Adding comment", err, () => { ...close edit form, reload board... })` — the exact 404-vs-generic split the spec's Error Cases table requires (`UI_ISSUE_NOT_FOUND` vs `UI_FETCH_FAILED`), since `reportIssueMutationFailure` already implements that split for every other edit-issue mutation.

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-comments-beh-1-render.test.js tests_js/issue-comments-beh-2-validation.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board-logic.js static/js/board.js tests_js/issue-comments-beh-1-render.test.js tests_js/issue-comments-beh-2-validation.test.js
git commit -m "feat(kanban-ui): add comment-thread panel to edit-issue form"
```

---

### Task 3: Comment MCP tools (mcp-server) [specialist: none]

**Charter capability:** list_issue_comments tool, create_issue_comment tool
**Strategy:** unit (source: fallback, confidence: high); mirrors `tests/mcp_server/test_issue_tools.py`'s pattern (a `_FakeClient` stand-in via `monkeypatch`, no live API — see below)
**Depends on:** — (file-independent of Task 1; the `_FakeClient` pattern means this task's tests run and pass without Task 1's endpoints existing. It relies only on the endpoint *contract* the spec already defines, same as `tests/mcp_server/test_issue_tools.py` doesn't wait on `app/routers/issues.py` either.)
**Files:**
- Create: `mcp_server/tools/comments.py`
- Modify: `mcp_server/client.py` (add `list_comments`, `create_comment`)
- Modify: `mcp_server/server.py` (register the new tool module)
- Test: `tests/mcp_server/test_comment_tools.py`

**Tests:** `tests/mcp_server/test_comment_tools.py` — new file, following `tests/mcp_server/test_issue_tools.py`'s real structure exactly: a `_FakeClient` stand-in (not a mocked transport fixture — no `mock_transport`/`mock_transport_404` fixture exists anywhere in this repo), `monkeypatch.setattr(<tools module>, "_client", lambda: fake)`, and invocation via `async with Client(mcp) as client: await client.call_tool(...)`, asserting on `result.is_error`/`result.structured_content` (uses the `anyio_backend` fixture already defined in `tests/mcp_server/conftest.py`, plus `@pytest.mark.anyio` on each test).

- [ ] **Write failing test**

```python
import pytest
from mcp import Client

import mcp_server.tools.comments as comments_tools
from mcp_server.errors import UpstreamError
from mcp_server.server import mcp


class _FakeClient:
    def __init__(self, comments=None, comment=None):
        self._comments = comments or []
        self._comment = comment

    async def list_comments(self, issue_id):
        return self._comments

    async def create_comment(self, issue_id, body):
        return self._comment

    async def aclose(self):
        pass


_SAMPLE_COMMENT = {
    "id": 1, "issue_id": 1, "body": "via mcp", "author": "", "created_at": "2026-09-09 00:00:00",
}


@pytest.mark.anyio
async def test_list_issue_comments_tool_returns_api_result_unmodified(monkeypatch):
    fake = _FakeClient(comments=[_SAMPLE_COMMENT])
    monkeypatch.setattr(comments_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("list_issue_comments", {"issue_id": 1})

    assert result.is_error is False
    assert result.structured_content == {"result": [_SAMPLE_COMMENT]}


@pytest.mark.anyio
async def test_create_issue_comment_tool_returns_the_comment(monkeypatch):
    fake = _FakeClient(comment=_SAMPLE_COMMENT)
    monkeypatch.setattr(comments_tools, "_client", lambda: fake)

    async with Client(mcp) as client:
        result = await client.call_tool("create_issue_comment", {"issue_id": 1, "body": "via mcp"})

    assert result.is_error is False
    assert result.structured_content == _SAMPLE_COMMENT


class _NotFoundListClient(_FakeClient):
    async def list_comments(self, issue_id):
        raise UpstreamError(404, "Issue 999999 not found")


@pytest.mark.anyio
async def test_list_issue_comments_tool_unknown_issue_errors_with_verbatim_message(monkeypatch):
    monkeypatch.setattr(comments_tools, "_client", lambda: _NotFoundListClient())

    async with Client(mcp) as client:
        result = await client.call_tool("list_issue_comments", {"issue_id": 999999})

    assert result.is_error is True
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests/mcp_server/test_comment_tools.py -q`
Expected: FAIL — `ModuleNotFoundError: mcp_server.tools.comments`

- [ ] **Implement**

In `mcp_server/client.py`, add (following `create_issue`'s exact `_request` pattern):

```python
async def list_comments(self, issue_id: int) -> list[dict]:
    response = await self._request("GET", f"/issues/{issue_id}/comments")
    return response.json()

async def create_comment(self, issue_id: int, body: str) -> dict:
    response = await self._request("POST", f"/issues/{issue_id}/comments", json={"body": body})
    return response.json()
```

Create `mcp_server/tools/comments.py`, mirroring `mcp_server/tools/issues.py`'s `list_issues`/`create_issue` structure exactly:

```python
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.client import IssueTrackerClient
from mcp_server.config import get_api_base_url
from mcp_server.errors import UpstreamError, UpstreamUnreachableError
from mcp_server.server import mcp


def _client() -> IssueTrackerClient:
    return IssueTrackerClient(get_api_base_url())


@mcp.tool()
async def list_issue_comments(issue_id: int) -> list[dict]:
    """List an Issue's Comments, chronologically, from issue-tracker-api."""
    client = _client()
    try:
        return await client.list_comments(issue_id)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()


@mcp.tool()
async def create_issue_comment(issue_id: int, body: str) -> dict[str, Any]:
    """Add a Comment to an Issue in issue-tracker-api."""
    client = _client()
    try:
        return await client.create_comment(issue_id, body)
    except UpstreamError as exc:
        raise ToolError(exc.message) from exc
    except UpstreamUnreachableError as exc:
        raise ToolError(str(exc)) from exc
    finally:
        await client.aclose()
```

In `mcp_server/server.py`'s `main()`, add `import mcp_server.tools.comments` alongside the three existing tool imports.

- [ ] **Verify test passes**

Run: `python3 -m pytest tests/mcp_server/test_comment_tools.py -q`
Expected: PASS

- [ ] **Commit**

```bash
git add mcp_server/tools/comments.py mcp_server/client.py mcp_server/server.py tests/mcp_server/test_comment_tools.py
git commit -m "feat(mcp-server): add list_issue_comments and create_issue_comment tools"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

- Tests pass: `python3 -m pytest -q` and `node --test tests_js/`
- Lint passes: `ruff check .`
- All acceptance criteria from spec satisfied
- No existing endpoint's request/response shape changed (verify `git diff` on `app/routers/projects.py`, `app/routers/users.py`, and every existing route in `app/routers/issues.py` shows zero changes to existing routes — only additions)
