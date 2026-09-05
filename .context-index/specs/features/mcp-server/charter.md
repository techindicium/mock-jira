---
status: approved
kind: feature
revision: 9
updated: 2026-09-05
---

# Feature Charter: mcp-server

<!-- Feature Charter for the mcp-server module.
     This defines WHAT the module does and its boundaries, not HOW it is built.
     Live Specs within this charter define specific behavioral contracts. -->

## Business Intent

mcp-server exposes `issue-tracker-api`'s CRUD operations as MCP tools, so an AI agent working in
a consuming course track (`portwell-assist`/SDLC, `portwell-analytics`/DDLC) can create and list
Projects, and fully create, read, update, and delete Issues, directly through the Model Context
Protocol, without hand-rolling HTTP calls. Like `kanban-ui`, it is a pure client of `issue-tracker-api`: it owns no
persisted data and never touches the database directly.

## Scope and Boundaries

### In Scope

- MCP tool definitions mirroring every must-have capability of `issue-tracker-api`: list/create
  Project, list/get/create/update/delete Issue.
- A running MCP server process that translates each tool call into an HTTP call against
  `issue-tracker-api` and returns its result (or its error) back through the tool response.
- Structured, JSON-schema tool input/output definitions so any MCP client can discover the tools
  and their parameters without out-of-band documentation.

### Out of Scope

- MCP resources or prompts — only tools are in scope, matching "expose the same CRUD functions."
- Authentication — mirrors `issue-tracker-api`'s no-real-auth stance.
- Real-time subscriptions/streaming tool results.
- Any persistence of its own — every read and write is delegated to `issue-tracker-api`.

### Dependencies

| Dependency | Type | Description |
|-----------|------|-------------|
| issue-tracker-api | internal module | Sole source of data and sole executor of every write. This module never opens the SQLite file directly. |

## Domain Model

<!-- Like kanban-ui, this module owns no persisted entities. The one concept below is a
     view/schema-side wrapper concept, never persisted. -->

### Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| McpTool | A single MCP tool definition wrapping one issue-tracker-api endpoint | `name`, `description`, `input_schema` (JSON Schema), `maps_to_endpoint` |

### Relationships

- Each McpTool maps to exactly one issue-tracker-api endpoint; no tool spans more than one
  endpoint call.

### Invariants

- Every McpTool's `input_schema` validates before the wrapped HTTP call is made — a request the
  schema rejects never reaches `issue-tracker-api`.
- A tool call's error response always carries the underlying API's error message verbatim; the
  MCP layer never swallows or rewrites it.

## Capability Map

| Capability | Description | Priority | Milestone | Status |
|-----------|-------------|----------|-------|--------|
| list_projects tool | Wraps `GET /projects` | must-have | mvp | validated |
| create_project tool | Wraps `POST /projects` | must-have | mvp | validated |
| list_issues tool | Wraps `GET /issues`, with `project_id`/`status` filter parameters | must-have | mvp | planned |
| get_issue tool | Wraps `GET /issues/{id}` | must-have | mvp | planned |
| create_issue tool | Wraps `POST /issues` | must-have | mvp | planned |
| update_issue tool | Wraps `PATCH /issues/{id}`, including status transitions | must-have | mvp | planned |
| delete_issue tool | Wraps `DELETE /issues/{id}` | must-have | mvp | planned |

## Deferred Capabilities

| Capability | Reason | Target Milestone | Depends On |
|-----------|--------|-------------|------------|
| get_project tool | No consumer has asked for single-project fetch via MCP yet; list_projects covers current need | v2 | — |
| MCP resources exposing issue data | Tools-only scope was explicit in the original request | v2 | — |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|-----------|------|-------------|
| `list_projects` | MCP tool | List all Projects |
| `create_project` | MCP tool | Create a Project |
| `list_issues` | MCP tool | List Issues, optional `project_id`/`status` filters |
| `get_issue` | MCP tool | Fetch one Issue |
| `create_issue` | MCP tool | Create an Issue under a Project |
| `update_issue` | MCP tool | Update one or more Issue fields, including `status` |
| `delete_issue` | MCP tool | Delete one Issue |

### Consumed APIs

| Interface | Source Module | Description |
|-----------|-------------|-------------|
| `GET /projects` | issue-tracker-api | Backs `list_projects` |
| `POST /projects` | issue-tracker-api | Backs `create_project` |
| `GET /issues` | issue-tracker-api | Backs `list_issues` |
| `GET /issues/{id}` | issue-tracker-api | Backs `get_issue` |
| `POST /issues` | issue-tracker-api | Backs `create_issue` |
| `PATCH /issues/{id}` | issue-tracker-api | Backs `update_issue` |
| `DELETE /issues/{id}` | issue-tracker-api | Backs `delete_issue` |

## Quality Attributes

| Attribute | Requirement |
|-----------|-------------|
| Performance | Tool-call round trip (MCP call → HTTP call → response) is not latency-sensitive at course scale. |
| Availability | Single local process; restarting it is an acceptable recovery path. |
| Security | No real auth. Bound to localhost only by default — never exposed to a real network. |
| Observability | Tool errors surface the underlying API error message unchanged; no structured logging required beyond what aids local debugging. |
