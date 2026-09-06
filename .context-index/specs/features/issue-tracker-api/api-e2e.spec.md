---
partial_schema: spec@1
charter: issue-tracker-api
status: review-passed
risk_level: low
milestone: v1.1
revision: 1
charter-revision: 9
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
---

# Live Spec: End-to-end API test suite (real HTTP)

<!-- Live Spec within the issue-tracker-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/issue-tracker-api/charter.md -->

## Behavioral Contract

### Preconditions

- The Project and Issue CRUD surface (`project-management`, `issue-lifecycle`, `fixture-seeding`
  specs) is implemented.
- These tests start the real application as its own OS process — `uvicorn app.main:app` bound
  to an ephemeral local port, with `DATABASE_PATH` pointed at a fresh temporary file per test
  session — and poll `GET /` (the app's existing root route; there is no dedicated `/health`
  endpoint) until it responds, before any test runs. They never import
  `app.main:app` into the test process or use FastAPI's `TestClient` (an in-process ASGI
  transport). This is the one thing that distinguishes this spec from the module's existing
  unit/integration tests: every request in this suite travels over a real TCP socket, exactly as
  `portwell-assist`/`portwell-analytics` or any other real consumer would connect.
- A real HTTP client (`httpx.Client(base_url=...)`) issues every request in this suite.
- The server process is torn down after the test session, whether it passed or failed.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the real server process starts and a real `POST /projects` request
  creates a Project, **then** a subsequent real `GET /projects` request shows it, over the same
  live HTTP connection to the same process.
- **BEH-2** — **When** a full Issue lifecycle (create → list/get → status-transition patch →
  delete) is driven as a sequence of real HTTP requests against the live server, **then** every
  step succeeds and matches the documented contract, end to end.
- **BEH-3** — **When** a request that should fail (unknown id, duplicate Project key, invalid
  enum value) is sent as a real HTTP request, **then** the live server returns the documented
  status code and error body — not just a mocked or in-process equivalent.
- **BEH-4** — **When** a real `GET /openapi.json` request is sent to the live server, **then** it
  returns a valid OpenAPI document listing every implemented route.
- **BEH-5** — **When** the real server starts against a fresh (empty) database, **then** a real
  `GET /issues` request shows the seeded fixture data — proving the seed-on-startup behavior
  works end to end, not just under test-harness conditions.

### Postconditions

- No test in this suite ever calls into `app.main` Python objects directly — every assertion is
  made against an `httpx` response coming back over a real socket.
- The temporary database file and server process used by this suite are cleaned up after the
  session; a second run starts from a clean slate.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Real server process fails to become healthy within the startup timeout | Test setup fails loudly, naming the timeout and the last-seen process output — never a silent hang | `E2E_SERVER_START_TIMEOUT` |
| A real HTTP request targets an unknown Issue/Project id | `404`, matching the documented `ISSUE_NOT_FOUND`/`PROJECT_NOT_FOUND` body | (inherited from issue-lifecycle/project-management) |
| A real HTTP request submits a duplicate Project `key` | `409`, matching `PROJECT_KEY_DUPLICATE` | (inherited) |
| A real HTTP request submits an invalid `status`/`issue_type`/`priority` enum value | `422`, matching `VALIDATION_ERROR` | (inherited) |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies directly: this suite is the one
  place in the repo that actually exercises that boundary as a real network client would,
  rather than through an in-process shortcut.
- **Principle:** "Fixture-backed, offline only." — Applies because the real server this suite
  starts is bound to `127.0.0.1` only, never a real external network.
- **Principle:** "Breaking API changes are coordinated, not silent." — Applies because this
  suite is the strongest guard against an accidental contract break: it fails if the real,
  running server's actual wire behavior ever diverges from what the spec says.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Real-server-process fixture | A pytest fixture that launches `uvicorn app.main:app` as a subprocess on an ephemeral port with a temp `DATABASE_PATH`, polls until healthy, yields the base URL, and tears down afterward | medium |
| Project CRUD e2e tests | `httpx`-driven tests for BEH-1 | small |
| Issue lifecycle e2e tests | `httpx`-driven tests for BEH-2 | medium |
| Error-path e2e tests | `httpx`-driven tests for BEH-3 | small |
| OpenAPI + seed-data e2e tests | `httpx`-driven tests for BEH-4 and BEH-5 | small |
| Wire the `e2e` gate tier | Add an `e2e-smoke` gate to `governance/gates.yaml` running this suite, `tier: e2e` (currently unwired in this project) | small |

## Acceptance Criteria

- [ ] The real server starts as its own process (never imported in-process) and becomes healthy before tests run (BEH-1 precondition)
- [ ] Project create/list round-trips over real HTTP (BEH-1)
- [ ] Full Issue lifecycle succeeds over a sequence of real HTTP requests (BEH-2)
- [ ] Documented error responses (404/409/422) are returned correctly over real HTTP (BEH-3)
- [ ] `GET /openapi.json` over real HTTP returns a valid document (BEH-4)
- [ ] Seeded fixture data is visible over real HTTP on a fresh server start (BEH-5)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
