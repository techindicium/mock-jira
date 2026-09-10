---
partial_schema: implement@1
charter: mcp-server
status: validated
risk_level: low
milestone: v1.2
revision: 2
charter-revision: 16
created: 2026-09-06
updated: 2026-09-07
kind: behavioral
source-manifest:
  sha: "2965cd2"
  files:
    - mcp_server/client.py
    - mcp_server/server.py
    - mcp_server/tools/users.py
    - tests/mcp_server/test_client.py
    - tests/mcp_server/test_user_tools.py
    - tests_e2e/test_mcp_user_tools_e2e.py
  computed-at: "2026-09-07T00:24:16.946Z"
drift_detected: true
---

# Live Spec: User MCP tools (list_users, create_user)

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `issue-tracker-api`'s `user-directory` spec is implemented and reachable at `API_BASE_URL`
  (per `project-tools`, already configured for this process). That spec's BEH-2 guarantees
  `email` uniqueness is enforced upstream (case-sensitive, `409` on collision) and its BEH-4
  guarantees `email` is optional with no collision on absence — `create_user`'s BEH-3 409
  passthrough below rests on that upstream contract.
- No authentication is required to reach `issue-tracker-api`'s `/users` endpoints, matching
  this module's existing `project-tools`/`issue-tools` posture.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_users` is invoked, **then** it calls `GET /users` and returns the
  result as the tool's structured output unmodified. `list_users` takes no filter or pagination
  parameters in this milestone, matching `list_projects`.
- **BEH-2** — **When** `create_user` is invoked with a valid, non-empty `name` (and optionally
  `email`/`role`), **then** it calls `POST /users` and returns the created User. `role` is a
  free-text string at the tool boundary — the tool declares no enum for it and delegates all
  value validation to `issue-tracker-api`'s `POST /users` verbatim (same delegation posture as
  `create_issue`'s `issue_type`/`priority` in `issue-tools`), so an invalid `role`, if the API
  ever rejects one, surfaces as the existing `422` `MCP_UPSTREAM_ERROR` case below rather than a
  new error code.
- **BEH-3** — **When** `create_user` is invoked with an `email` that already exists on another
  User, **then** the tool call errors with the API's `409` message passed through verbatim.
- **BEH-4** — **When** `create_user` is invoked with input that fails its declared input schema
  (e.g. a missing `name`), **then** the tool call errors before any HTTP request is made.
- **BEH-5** — **When** `issue-tracker-api` is unreachable, **then** both tools return a clear
  connection-error message rather than hanging or failing silently.

### Postconditions

- A User created through `create_user` is immediately visible to a subsequent `list_users` call
  — no caching layer sits between this module and the API.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Input fails the tool's input schema | Tool call errors immediately; no HTTP request made | `MCP_INPUT_INVALID` |
| API returns `409` (duplicate email) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `422` (missing/empty `name` that passed the tool's own schema but fails the API's) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API unreachable | Tool call errors with a clear connection message | `MCP_UPSTREAM_UNREACHABLE` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because these tools are thin
  wrappers over `issue-tracker-api`'s documented `/users` endpoints, never a direct database
  access.
- **Principle:** "No inbound dependencies." — Applies because mcp-server depends on
  issue-tracker-api, never the reverse.
- **Principle:** "Fixture-backed, offline only." — Applies because every call stays within the
  local `mock-jira` stack.

## Design Note: no `get_user` tool

`project-tools` deliberately has no `get_project` tool — `list_projects` was judged sufficient
and single-fetch was deferred (see charter's Deferred Capabilities). This spec follows the same
"keep it simple" precedent for symmetry: no consumer has asked for single-User fetch via MCP, and
`list_users` already covers the current need. `get_user` is recorded in the charter's Deferred
Capabilities table for a future milestone, not built here.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define tool schemas | JSON-schema input/output definitions for `list_users`/`create_user`, registered with the MCP server | small |
| Wire HTTP calls | Translate each tool call into the matching `issue-tracker-api` `/users` request | small |
| Error passthrough + connection handling | Verbatim upstream error passthrough; clear message on unreachable API (shared pattern with project-tools/issue-tools) | small |
| Register tools module | Import `mcp_server.tools.users` from `mcp_server/server.py`'s `main()` the same way `projects`/`issues` are imported, so tools land on the canonical `MCPServer` instance | small |
| Update `mcp-e2e.spec.md` tool count | `mcp-e2e.spec.md` BEH-1 (status: validated) asserts the server exposes exactly 7 registered tools; registering `list_users`/`create_user` makes the true count 9. Update BEH-1's wording (7 → 9) and the corresponding `tests_e2e/test_mcp_tool_discovery_e2e.py` assertion so the sibling spec/test are not silently falsified by this spec shipping — re-stamp `mcp-e2e.spec.md`'s source manifest once its test file is touched | small |

## Acceptance Criteria

- [x] `list_users` returns the API's user list unmodified (BEH-1)
- [x] `create_user` creates and returns a User on valid input (BEH-2)
- [x] `create_user` on a duplicate email errors with the API's message verbatim (BEH-3)
- [x] Schema-invalid input errors before any HTTP request (BEH-4)
- [x] An unreachable API produces a clear connection-error message (BEH-5)
- [x] `mcp-e2e.spec.md` BEH-1 and its e2e assertion are updated to expect 9 tools (was 7), so the
      validated sibling spec is not left stale by this spec's two new tools
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
