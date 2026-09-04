# Product Vision: mock-jira

## Vision

A standalone, offline mock of a JIRA-shaped issue tracker — kanban UI, CRUD API, and MCP layer —
that other adev-course tracks integrate against as a realistic external dependency.

## Module Map

| Module | Description | Charter |
|--------|-------------|---------|
| issue-tracker-api | Provide a JIRA-shaped issue-tracking domain (projects, issues, kanban statuses) backed by a local SQLite database, exposed over an HTTP CRUD API. | [charter.md](./features/issue-tracker-api/charter.md) |
| kanban-ui | Gives mock-jira a JIRA-like kanban board web interface — issues as cards in status columns, full CRUD via forms, column-to-column moves — as a pure client of issue-tracker-api. | [charter.md](./features/kanban-ui/charter.md) |
| mcp-server | Exposes issue-tracker-api's CRUD operations as MCP tools so an AI agent can create/read/update/delete Projects and Issues through the Model Context Protocol. | [charter.md](./features/mcp-server/charter.md) |
