---
partial_schema: spec@1
charter: mcp-server
status: review-pending
risk_level: low
milestone: v1.1
revision: 1
charter-revision: 10
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
---

# Live Spec: End-to-end MCP test suite (real client/transport)

<!-- Live Spec within the mcp-server charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/mcp-server/charter.md -->

## Behavioral Contract

### Preconditions

- Both mcp-server specs (`project-tools`, `issue-tools`) are implemented, including the
  streamable-http transport added by `docker-packaging`.
- These tests start two real processes: `issue-tracker-api` (reusing its `api-e2e` real-server
  fixture) and `mcp-server` itself, configured with `API_BASE_URL` pointed at the API's
  ephemeral port and its own `PORT` for the streamable-http transport.
- A real MCP client (the `mcp` SDK's `streamablehttp_client` + `ClientSession`) connects to the
  live `mcp-server` process over that real transport. No test in this suite calls a tool
  function in `mcp_server/tools/*.py` directly — every call goes through the actual MCP
  protocol, the same way an external agent would use this server.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a real MCP client sends the protocol's tool-listing call to the live
  server, **then** it returns all 7 registered tools with their correct names and input schemas.
- **BEH-2** — **When** a real MCP client calls `list_projects`/`create_project` against the live
  server, **then** the structured result matches what a direct real HTTP call to
  `issue-tracker-api` shows for the same data.
- **BEH-3** — **When** a real MCP client calls each of the five issue tools against the live
  server, **then** the real CRUD operation happens — cross-verified by a direct real HTTP call
  to `issue-tracker-api` after each mutating call.
- **BEH-4** — **When** a real MCP client calls a tool with input that fails its declared schema,
  **then** the protocol surfaces a tool-level error to the client — the call never hangs and
  never reaches `issue-tracker-api`.
- **BEH-5** — **When** `mcp-server` is started with `API_BASE_URL` pointed at a port nothing is
  listening on, **then** a real MCP client's tool call surfaces a clear connection error through
  the protocol, not a hang or a crash.

### Postconditions

- Every assertion in this suite is made against what the real MCP client received over the real
  transport — never against `mcp_server`'s internal Python objects.
- Both server processes are torn down after the test session.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Real MCP client calls a tool with schema-invalid input | Protocol-level tool error returned to the client; no upstream HTTP call made | `E2E_MCP_INPUT_INVALID` |
| `mcp-server` cannot reach `issue-tracker-api` (BEH-5 setup) | Protocol-level tool error naming the connection failure | `E2E_MCP_UPSTREAM_UNREACHABLE` |
| Either real server process fails to become healthy within the startup timeout | Test setup fails loudly, naming which process and the timeout | `E2E_SERVER_START_TIMEOUT` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because this suite verifies
  mcp-server's real, end-to-end path to that boundary — client → MCP protocol → mcp-server →
  real HTTP → issue-tracker-api — rather than any single link in isolation.
- **Principle:** "No inbound dependencies." — Applies because this suite still only drives
  mcp-server through its real client-facing surface; it never reaches into issue-tracker-api's
  internals except via the same real HTTP calls project-tools/issue-tools already use.
- **Principle:** "Fixture-backed, offline only." — Applies because both real processes this
  suite starts are bound to `127.0.0.1` only.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Dual-server e2e fixture | A pytest fixture starting both `issue-tracker-api` (reusing `api-e2e`'s fixture) and `mcp-server` as real processes, wired together via `API_BASE_URL`, torn down together | medium |
| Real MCP client helper | A small helper wrapping the `mcp` SDK's `streamablehttp_client`/`ClientSession` connect-and-call pattern, reused across this suite's tests | medium |
| Tool-discovery e2e test | Real-client test for BEH-1 | small |
| Project-tools e2e tests | Real-client tests for BEH-2 | small |
| Issue-tools e2e tests | Real-client tests for BEH-3, cross-verified via real HTTP | medium |
| Error-path e2e tests | Real-client tests for BEH-4 and BEH-5 | small |

## Acceptance Criteria

- [ ] A real MCP client discovers all 7 tools with correct schemas (BEH-1)
- [ ] Project tools work end to end over the real protocol, matching real API state (BEH-2)
- [ ] All 5 issue tools work end to end over the real protocol, cross-verified via real HTTP (BEH-3)
- [ ] Schema-invalid tool input surfaces a protocol-level error, no upstream call made (BEH-4)
- [ ] An unreachable upstream API surfaces a protocol-level connection error (BEH-5)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
