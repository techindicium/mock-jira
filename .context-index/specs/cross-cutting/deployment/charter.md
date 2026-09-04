---
status: draft
kind: cross-cutting
revision: 1
updated: 2026-09-04
---

# Cross-Cutting Charter: deployment

<!-- Cross-Cutting Charter for the deployment concern. Cross-cutting charters
     describe a concern that touches multiple modules. They live under
     specs/cross-cutting/, NOT specs/features/. -->

## Business Intent

deployment packages `issue-tracker-api`, `kanban-ui`, and `mcp-server` together into a single
Docker-based, one-command local runtime with written run instructions, so a student, instructor,
or another track's agent can start the whole `mock-jira` stack without manually managing three
separate processes or a Python environment.

## Scope

### In Scope

- A Dockerfile per module that needs its own runtime (issue-tracker-api, kanban-ui if served as
  its own process, mcp-server).
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
| issue-tracker-api | high | Dockerfile; must read its SQLite path from an env var so compose can mount a named volume at that path. |
| kanban-ui | high | Dockerfile (or confirmation it is served by issue-tracker-api's process); must read the API's base URL from an env var rather than hardcoding `localhost`. |
| mcp-server | medium | Dockerfile; must read the API's base URL from an env var, same convention as kanban-ui. |

## Interface Contracts

### Exposed APIs

| Interface | Type | Description |
|---|---|---|
| `PORT` env var convention | convention | Every module reads its listen port from `PORT` rather than hardcoding one, so compose can remap freely. |
| `API_BASE_URL` env var convention | convention | kanban-ui and mcp-server both read the issue-tracker-api base URL from this variable instead of hardcoding `localhost`. |
| `DATABASE_PATH` env var convention | convention | issue-tracker-api reads its SQLite file path from this variable so compose can bind it to a named volume. |

### Consumed APIs

| Interface | Source Module | Description |
|---|---|---|
| A basic liveness response (any successful response on its root or health path) | issue-tracker-api | Used by compose's healthcheck so `mcp-server`/`kanban-ui` containers can `depends_on` a healthy API. |

## Quality Attributes

| Attribute | Requirement |
|---|---|
| Performance | Not a concern — this is packaging, not a runtime path. |
| Availability | `docker compose up` brings up all three modules in dependency order (API first); restarting the stack is an acceptable recovery path. |
| Security | No ports exposed beyond localhost by default in `docker-compose.yml`. |
| Observability | `docker compose logs` surfaces all three modules' output; no additional log aggregation required. |
