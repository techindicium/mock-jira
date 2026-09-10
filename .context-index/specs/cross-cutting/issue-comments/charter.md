---
status: approved
kind: cross-cutting
revision: 1
updated: 2026-09-09
---

# Cross-Cutting Charter: issue-comments

<!-- Cross-Cutting Charter for the issue-comments concern. Cross-cutting charters describe a
     concern that touches multiple modules. They live under specs/cross-cutting/, NOT
     specs/features/. -->

## Business Intent

issue-comments gives `mock-jira` a per-Issue activity log — a chronological, append-only list of
Comments — so the mock reads like a real issue tracker where discussion and history accumulate on
a ticket, not just its current field values. It is additive across all three existing modules:
`issue-tracker-api` gains a new Comment entity and two new endpoints (no existing endpoint's
request/response shape changes), `kanban-ui` gains a comment thread panel in the issue edit form,
and `mcp-server` gains two new MCP tools mirroring the new endpoints. Every consuming course
track's existing integration surface is untouched.

## Scope

### In Scope

- A Comment entity (`id`, `issue_id`, `body`, `author`, `created_at`) owned by `issue-tracker-api`
  — see that module's Domain Model (charter revision 17) for the canonical definition.
- `POST /issues/{id}/comments` and `GET /issues/{id}/comments` on `issue-tracker-api`.
- A comment thread panel inside `kanban-ui`'s existing edit-issue form: a chronological list of
  the open Issue's Comments, and a simple textarea + submit control to add a new one.
- Two new MCP tools on `mcp-server`: `list_issue_comments` and `create_issue_comment`, mirroring
  the two new REST endpoints exactly as the existing tools mirror Issue/Project/User endpoints.
- `author` is free-text (mirrors `Issue.assignee`/`reporter`) — the comment form may reuse
  kanban-ui's existing User-directory-backed picker (`user-picker.spec.md`) to suggest a name,
  but never enforces or stores a foreign key to `User.id`.

### Out of Scope

- Editing or deleting a Comment once created (append-only log; see issue-tracker-api's Invariants,
  charter revision 17).
- Rich text / markdown rendering, @mentions, or attachments on a Comment — plain text only.
- Real-time push of new Comments to other open browser tabs (a page reload or re-opening the edit
  form is sufficient, matching kanban-ui's existing "no live push" posture).
- Comment notifications of any kind (email, in-app) — no notification system exists in this
  project and this charter does not introduce one.
- Any change to an existing Issue/Project/User endpoint's request or response shape.

## Affected Modules

| Module | Impact (high / medium / low) | Changes Required |
|---|---|---|
| issue-tracker-api | high | New Comment table/entity; two new endpoints (`POST`/`GET /issues/{id}/comments`); `DELETE /issues/{id}` cascades to delete that Issue's Comments (see Invariants, charter revision 17). No existing endpoint's contract changes. |
| kanban-ui | medium | A comment-thread section added to the existing edit-issue form (list + add-comment control); no change to any other existing view, form, or element ID. |
| mcp-server | low | Two new MCP tools (`list_issue_comments`, `create_issue_comment`) added alongside the existing Issue/Project/User tools, following the same translate-to-HTTP-and-return pattern. |

## Interface Contracts

### Exposed APIs

None — this is a cross-cutting concern wiring three existing modules together; the concrete new
endpoints are exposed by `issue-tracker-api` (see its own Interface Contracts, charter revision
17) and the concrete new MCP tools are exposed by `mcp-server`.

### Consumed APIs

| Interface | Source Module | Description |
|-----------|---------------|--------------|
| `GET /issues/{id}/comments` | issue-tracker-api | Populate the comment thread panel in kanban-ui's edit-issue form; backing call for mcp-server's `list_issue_comments` tool |
| `POST /issues/{id}/comments` | issue-tracker-api | Submit a new Comment from kanban-ui's edit-issue form; backing call for mcp-server's `create_issue_comment` tool |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Not a concern at course-fixture volume (a few Comments per Issue); no explicit latency target. |
| Availability | No availability requirement beyond the three modules' own — this concern adds no new process. |
| Security | No real auth, matching every other capability in this project. `body` is stored and rendered as plain text (HTML-escaped on render in kanban-ui) — no script-injection surface. |
| Observability | A failed comment submission surfaces the same error-banner pattern kanban-ui already uses for other failed writes; no new logging infrastructure required. |
