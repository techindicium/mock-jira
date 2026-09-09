---
mode: cross-cutting
affects: [issue-tracker-api, kanban-ui, mcp-server]
status: implemented
revision: 1
created: 2026-09-09
updated: 2026-09-09
kind: behavioral
partial_schema: implement@1
source-manifest:
  sha: "33a3875"
  files:
    - app/db.py
    - app/models.py
    - app/routers/issues.py
    - mcp_server/client.py
    - mcp_server/server.py
    - mcp_server/tools/comments.py
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests/mcp_server/test_comment_tools.py
    - tests/test_comments.py
    - tests_js/issue-comments-beh-1-render.test.js
    - tests_js/issue-comments-beh-2-validation.test.js
  computed-at: "2026-09-09T21:24:45.414Z"
---

# Live Spec: Issue comments and activity log

<!-- Cross-cutting Live Spec. Parent Charter: .context-index/specs/cross-cutting/issue-comments/charter.md -->

## Behavioral Contract

### Preconditions

- issue-tracker-api's `issue-lifecycle` spec is implemented and reachable (Comments attach to an
  existing Issue).
- kanban-ui's `issue-crud-forms` spec is implemented (Comments extend the existing edit-issue
  form).
- mcp-server's `issue-tools` spec is implemented (the new tools follow its existing pattern).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a client calls `POST /issues/{id}/comments` with a non-empty `body`
  **then** issue-tracker-api creates a Comment with a server-assigned `id` and `created_at`,
  belonging to that Issue, and responds `201` with the created Comment.
- **BEH-2** — **When** a client calls `GET /issues/{id}/comments` **then** issue-tracker-api
  responds `200` with that Issue's Comments ordered by `created_at` ascending (oldest first,
  matching a chronological activity log).
- **BEH-3** — **When** the user opens kanban-ui's edit-issue form for an Issue that has Comments
  **then** the comment-thread panel shows them in the same chronological order, each with its
  `body`, `author` (or "Unassigned" if blank, matching the existing assignee-blank convention),
  and a human-readable timestamp.
- **BEH-4** — **When** the user submits the comment-thread panel's add-comment control with
  non-empty text **then** kanban-ui calls `POST /issues/{id}/comments` and, on success, appends
  the new Comment to the visible thread without a full form reload.
- **BEH-5** — **When** the user submits the add-comment control with empty/whitespace-only text
  **then** kanban-ui blocks the submission client-side (no request sent), mirroring the existing
  create-issue form's client-side validation pattern (`UI_VALIDATION_ERROR`).
- **BEH-6** — **When** an MCP client calls the `list_issue_comments` tool with an `issue_id`
  **then** mcp-server calls `GET /issues/{id}/comments` and returns the result unchanged, exactly
  mirroring how existing tools translate HTTP responses.
- **BEH-7** — **When** an MCP client calls the `create_issue_comment` tool with an `issue_id` and
  `body` **then** mcp-server calls `POST /issues/{id}/comments` and returns the created Comment,
  exactly mirroring existing create-shaped tools.
- **BEH-8** — **When** an Issue is deleted (`DELETE /issues/{id}`) **then** all of its Comments
  are deleted with it (cascade) — no orphaned Comment can outlive its Issue.

### Postconditions

- Every Comment that exists has exactly one owning Issue that still exists.
- A Comment's `body`, `author`, and `created_at` never change after creation (append-only,
  matching the charter's Invariants) — there is no update endpoint for a Comment.
- kanban-ui's edit-issue form's existing fields (summary/type/priority/description/assignee) and
  their save/delete behavior are unchanged by this spec — the comment panel is additive.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| `POST /issues/{id}/comments` with empty/missing `body` | `422` with a message naming the missing field | `VALIDATION_ERROR` |
| `POST` or `GET /issues/{id}/comments` where `{id}` does not exist | `404` with a message naming the missing Issue | `ISSUE_NOT_FOUND` |
| kanban-ui's `POST /issues/{id}/comments` call fails with a `404` (the owning Issue was deleted elsewhere while the edit form was open) | Same precedent as `issue-crud-forms.spec.md`'s `UI_ISSUE_NOT_FOUND` case: close the edit form and refresh the board rather than leaving a comment form open against a stale Issue | `UI_ISSUE_NOT_FOUND` |
| kanban-ui's `POST /issues/{id}/comments` call fails for any other reason (network or non-2xx, non-404) | Same generic error-banner pattern the edit-issue form already uses for other save failures | `UI_FETCH_FAILED` |
| `list_issue_comments`/`create_issue_comment` tool called with a non-existent `issue_id` | Tool call fails with the same 404-translated error shape existing tools use (e.g. `get_issue` on a missing id) | `MCP_UPSTREAM_ERROR` |

## System Constitution Reference

- "The HTTP contract is the boundary" / "Breaking API changes are coordinated, not silent" — this
  spec adds two new endpoints and does not modify any existing endpoint's request or response
  shape; falls under the constitution's Autonomous bucket ("Adding new mock endpoints that extend
  (not break) the existing contract").
- "Fixture-backed, offline only" — no real network dependency introduced; Comments persist in the
  same local SQLite file as every other entity.
- "Identifiers reconcile with the shared canon" — Comment `id` is server-assigned and internal
  (not a course-shared identifier), so no reconciliation is needed, matching how Issue/Project
  ids are already handled.

## Module Impact Map

| Module | Impact | Changes Required |
|--------|--------|-------------------|
| issue-tracker-api | High | New Comment table; two new endpoints; cascade-delete on Issue delete |
| kanban-ui | Medium | Comment-thread panel added to the existing edit-issue form only; no other view changes |
| mcp-server | Low | Two new MCP tools, following the existing tool-per-endpoint pattern exactly |

## Integration Points

1. kanban-ui ↔ issue-tracker-api: the comment-thread panel's list and add-comment control call
   `GET`/`POST /issues/{id}/comments` directly, same-origin, exactly like every other kanban-ui
   API call.
2. mcp-server ↔ issue-tracker-api: `list_issue_comments`/`create_issue_comment` translate to the
   same two endpoints, following `mcp_server/tools/issues.py`'s existing translate-and-return
   pattern.
3. issue-tracker-api ↔ Issue lifecycle: Comment deletion is never independent — it only happens
   as a cascade of Issue deletion, so no standalone `DELETE /comments/{id}` endpoint exists in
   this spec (matches the charter's Out of Scope).

## Actionable Task Map

| Task | Description | Complexity |
|------|-------------|------------|
| Comment table + model | SQLite table, Pydantic model, cascade-delete wiring in issue-tracker-api | Medium |
| Comment endpoints | `POST`/`GET /issues/{id}/comments` routes + validation | Medium |
| Comment-thread panel | New section in kanban-ui's edit-issue form: list rendering + add-comment control | Medium |
| Comment MCP tools | `list_issue_comments`/`create_issue_comment` tool definitions in mcp-server | Low |
| Tests | Unit + e2e (API), unit + e2e (UI), unit (MCP tools) | Medium |

## Acceptance Criteria

- [x] `POST /issues/{id}/comments` creates a Comment and returns it (BEH-1)
- [x] `GET /issues/{id}/comments` returns an Issue's Comments in chronological order (BEH-2)
- [x] The edit-issue form's comment panel renders existing Comments chronologically (BEH-3)
- [x] Submitting a non-empty comment appends it to the visible thread without a full reload (BEH-4)
- [x] Submitting an empty/whitespace comment is blocked client-side (BEH-5)
- [x] `list_issue_comments` and `create_issue_comment` MCP tools work end-to-end (BEH-6, BEH-7)
- [x] Deleting an Issue deletes its Comments (BEH-8)
- [x] No existing endpoint's request/response shape changed
- [x] All quality gates pass (`pytest`, `ruff`, `tests_js`, MCP e2e)
- [x] No constitutional violations
