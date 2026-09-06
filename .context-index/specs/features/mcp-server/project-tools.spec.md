---
partial_schema: implement@1
charter: mcp-server
status: validated
risk_level: low
milestone: mvp
revision: 1
charter-revision: 2
created: 2026-09-04
updated: 2026-09-05
kind: behavioral
source-manifest:
  sha: "edefb62"
  files:
    - mcp_server/__init__.py
    - mcp_server/client.py
    - mcp_server/config.py
    - mcp_server/errors.py
    - mcp_server/server.py
    - mcp_server/tools/__init__.py
    - mcp_server/tools/projects.py
    - requirements-mcp.txt
    - tests/mcp_server/__init__.py
    - tests/mcp_server/conftest.py
    - tests/mcp_server/test_client.py
    - tests/mcp_server/test_config.py
    - tests/mcp_server/test_project_tools.py
  computed-at: "2026-09-06T17:45:47.539Z"
drift_detected: true
---

# Live Spec: Project MCP tools (list_projects, create_project)

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- `issue-tracker-api`'s `project-management` spec is implemented and reachable.
- The MCP server process has been configured with the API's base URL via `API_BASE_URL`.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** `list_projects` is invoked, **then** it calls `GET /projects` and
  returns the result as the tool's structured output unmodified.
- **BEH-2** — **When** `create_project` is invoked with a valid, non-empty `key` and `name`,
  **then** it calls `POST /projects` and returns the created Project.
- **BEH-3** — **When** `create_project` is invoked with a `key` that already exists, **then**
  the tool call errors with the API's `409` message passed through verbatim.
- **BEH-4** — **When** either tool is invoked with input that fails its declared input schema
  (e.g. a missing `key`), **then** the tool call errors before any HTTP request is made.
- **BEH-5** — **When** `issue-tracker-api` is unreachable, **then** both tools return a clear
  connection-error message rather than hanging or failing silently.

### Postconditions

- A Project created through `create_project` is immediately visible to a subsequent
  `list_projects` call — no caching layer sits between this module and the API.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Input fails the tool's input schema | Tool call errors immediately; no HTTP request made | `MCP_INPUT_INVALID` |
| API returns `409` (duplicate key) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API returns `422` (blank `key`/`name` that passed the tool's own schema but fails the API's) | Tool call errors with the API's message verbatim | `MCP_UPSTREAM_ERROR` |
| API unreachable | Tool call errors with a clear connection message | `MCP_UPSTREAM_UNREACHABLE` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because these tools are thin
  wrappers over `issue-tracker-api`'s documented endpoints, never a direct database access.
- **Principle:** "No inbound dependencies." — Applies because mcp-server depends on
  issue-tracker-api, never the reverse.
- **Principle:** "Fixture-backed, offline only." — Applies because every call stays within the
  local `mock-jira` stack.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Define tool schemas | JSON-schema input/output definitions for `list_projects`/`create_project`, registered with the MCP server | small |
| Wire HTTP calls | Translate each tool call into the matching `issue-tracker-api` request | small |
| Error passthrough + connection handling | Verbatim upstream error passthrough; clear message on unreachable API | small |

## Acceptance Criteria

- [x] `list_projects` returns the API's project list unmodified (BEH-1)
- [x] `create_project` creates and returns a Project on valid input (BEH-2)
- [x] `create_project` on a duplicate key errors with the API's message verbatim (BEH-3)
- [x] Schema-invalid input errors before any HTTP request (BEH-4)
- [x] An unreachable API produces a clear connection-error message (BEH-5)
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
