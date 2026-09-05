---
status: approved
kind: cross-cutting
revision: 4
updated: 2026-09-04
---

# Cross-Cutting Charter: deployment

<!-- Cross-Cutting Charter for the deployment concern. Cross-cutting charters
     describe a concern that touches multiple modules. They live under
     specs/cross-cutting/, NOT specs/features/. -->

## Business Intent

deployment packages `mock-jira` into a single Docker-based, one-command local runtime with
written run instructions, so a student, instructor, or another track's agent can start the whole
stack without manually managing two separate processes (`issue-tracker-api`, which also serves
`kanban-ui`'s static assets, and `mcp-server`) or a Python environment.

## Scope

### In Scope

- A Dockerfile for each module that runs its own process: issue-tracker-api (which also serves
  kanban-ui's static assets) and mcp-server. kanban-ui has no Dockerfile of its own — its build
  output is copied into issue-tracker-api's image.
- A `docker-compose.yml` wiring all modules together, including a named volume so the SQLite file
  survives container restarts.
- An environment-variable convention each module follows so compose can wire them without code
  changes (e.g. a port, and the API base URL the UI and MCP server call).
- Written run instructions (in this repo's README/CLAUDE.md) covering `docker compose up`, which
  ports are exposed, and how to confirm the stack is healthy.

### Out of Scope

- Cloud deployment or any hosted target — this is a local-only course fixture.
- CI/CD pipeline automation.
- Multi-instance scaling or production-grade orchestration (Kubernetes, etc.).
- Publishing images to a registry — local `docker compose build` is sufficient.

## Affected Modules

| Module | Impact (high / medium / low) | Changes Required |
|---|---|---|
| issue-tracker-api | high | Dockerfile; must read its SQLite path from an env var so compose can mount a named volume at that path; also serves kanban-ui's static assets, so its image build includes them. |
| kanban-ui | low | No separate container — built as static assets and copied into issue-tracker-api's image/build step. No env var needed: API calls are same-origin relative requests. |
| mcp-server | medium | Dockerfile; must read the API's base URL from an env var, since it runs as a separate process/container from issue-tracker-api. |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|---|---|---|
| `PORT` env var convention | convention | issue-tracker-api and mcp-server both read their listen port from `PORT` rather than hardcoding one, so compose can remap freely. kanban-ui has no listen port of its own — it has no process. |
| `API_BASE_URL` env var convention | convention | mcp-server reads the issue-tracker-api base URL from this variable instead of hardcoding `localhost`. kanban-ui does not need it — its calls are same-origin. |
| `DATABASE_PATH` env var convention | convention | issue-tracker-api reads its SQLite file path from this variable so compose can bind it to a named volume. |

### Consumed APIs

| Interface | Source Module | Description |
|---|---|---|
| A basic liveness response (any successful response on its root or health path) | issue-tracker-api | Used by compose's healthcheck so the `mcp-server` container can `depends_on` a healthy API. kanban-ui has no runtime dependency here — it is built into issue-tracker-api's image, not started as its own container. |

## Quality Attributes

| Attribute | Requirement |
|---|---|
| Performance | Not a concern — this is packaging, not a runtime path. |
| Availability | `docker compose up` brings up both containers (issue-tracker-api — which already carries kanban-ui's built assets — then mcp-server) in dependency order; restarting the stack is an acceptable recovery path. |
| Security | No ports exposed beyond localhost by default in `docker-compose.yml`. |
| Observability | `docker compose logs` surfaces both containers' output (kanban-ui has no separate log stream — its assets are served from within issue-tracker-api's process); no additional log aggregation required. |
