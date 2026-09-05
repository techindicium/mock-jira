---
partial_schema: implement@1
charter: mcp-server
status: implemented
risk_level: low
milestone: mvp
revision: 2
charter-revision: 9
created: 2026-09-04
updated: 2026-09-05
kind: behavioral
source-manifest:
  sha: "d2ef81d"
  files:
    - mcp_server/client.py
    - mcp_server/server.py
    - mcp_server/tools/issues.py
    - tests/mcp_server/test_client.py
    - tests/mcp_server/test_issue_tools.py
  computed-at: "2026-09-05T18:22:09.781Z"
---

# Live Spec: Issue MCP tools (list/get/create/update/delete)

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `issue-tracker-api`'s `issue-lifecycle` spec is implemented and reachable at `API_BASE_URL`
  (per `project-tools`, already configured for this process).
- The `project-tools` spec is implemented — an agent typically calls `list_projects` or
  `create_project` first to obtain a `project_id` before creating Issues.
- `id`, `key`, and `project_id` are not mutable fields on `update_issue` and are silently
  ignored if present in its input — an Issue's project and key never change after creation (see
  `issue-lifecycle` BEH-7, which this tool wraps verbatim).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_issues` is invoked with optional `project_id`/`status` arguments,
  **then** it calls `GET /issues` with the matching query parameters and returns the result
  unmodified.
- **BEH-2** — **When** `get_issue` is invoked with an id that exists, **then** it calls
  `GET /issues/{id}` and returns the Issue.
- **BEH-3** — **When** `get_issue` is invoked with an id that does not exist, **then** the tool
  call errors with the API's `404` message passed through verbatim.
- **BEH-4** — **When** `create_issue` is invoked with all required fields and a `project_id`
  that exists, **then** it calls `POST /issues` and returns the created Issue, including its
  server-assigned `key`.
- **BEH-4b** — **When** `create_issue` names a `project_id` that does not exist, **then** the
  tool call errors with the API's `404` message passed through verbatim.
- **BEH-5** — **When** `update_issue` is invoked with one or more mutable fields (`summary`,
  `description`, `issue_type`, `priority`, `assignee`, `reporter`, or `status`), **then** it calls
  `PATCH /issues/{id}` and returns the updated Issue. `id`, `key`, and `project_id` are silently
  ignored if present in the input.
- **BEH-6** — **When** `delete_issue` is invoked with an id that exists, **then** it calls
  `DELETE /issues/{id}` and returns a success confirmation shaped `{"deleted": true, "id": <id>}`.
- **BEH-7** — **When** any tool in this spec is invoked with input that fails its declared input
  schema, **then** the tool call errors before any HTTP request is made.

### Postconditions

- An Issue created, updated, or deleted through these tools is immediately reflected in a
  subsequent `list_issues`/`get_issue` call — no caching layer sits between this module and the
  API.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Input fails the tool's input schema | Tool call errors immediately; no HTTP request made | `MCP_INPUT_INVALID` |
| API returns `404` (unknown issue id, or unknown `project_id` on create) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `422` (invalid status/field value on create or update) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API unreachable | Tool call errors with a clear connection message | `MCP_UPSTREAM_UNREACHABLE` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because these five tools are
  thin wrappers over `issue-tracker-api`'s documented Issue endpoints, never a direct database
  access.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because
  `update_issue` wraps the same status-transition endpoint the kanban UI depends on; both
  consumers share one contract.
- **Principle:** "No inbound dependencies." — Applies because mcp-server depends on
  issue-tracker-api, never the reverse.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define tool schemas | JSON-schema input/output definitions for all five tools, registered with the MCP server | medium |
| Wire HTTP calls | Translate each tool call into the matching `issue-tracker-api` request | medium |
| Error passthrough + connection handling | Verbatim upstream error passthrough; clear message on unreachable API (shared with project-tools) | small |

## Acceptance Criteria

- [ ] `list_issues` returns the API's filtered issue list unmodified (BEH-1)
- [ ] `get_issue` returns the Issue for a valid id (BEH-2)
- [ ] `get_issue` on an unknown id errors with the API's message verbatim (BEH-3)
- [ ] `create_issue` creates and returns an Issue with its server-assigned key (BEH-4)
- [ ] `create_issue` with an unknown `project_id` errors with the API's message verbatim (BEH-4b)
- [ ] `update_issue` updates the given mutable fields and returns the result; `id`/`key`/`project_id` are ignored (BEH-5)
- [ ] `delete_issue` deletes an existing Issue and returns `{"deleted": true, "id": <id>}` (BEH-6)
- [ ] Schema-invalid input errors before any HTTP request, for every tool in this spec (BEH-7)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
