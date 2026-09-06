# mock-jira

A standalone mock of a JIRA-shaped issue-tracking API for the adev course tracks to consume as
an external system dependency. Required by the `portwell-assist` (SDLC) and `portwell-analytics`
(DDLC) tracks.

Independent repo: no dependency on `course-shared`, the other `mock-*` repos, or any track repo.
Tracks that need it pull it in as a service dependency; this repo never depends on them back.

## Running the UI end-to-end test suite

The kanban-ui end-to-end suite drives a real Chromium browser (via Playwright) against a real
`issue-tracker-api` server process. One-time local setup:

```bash
pip install -r requirements-e2e.txt
playwright install chromium
```

Then run it (already covered by the `e2e-smoke` gate, which runs all of `tests_e2e/`):

```bash
.venv/bin/python3 -m pytest -q tests_e2e/
```

## Running with Docker

```bash
docker compose up
```

This builds two images (`issue-tracker-api`, which also serves `kanban-ui`'s static assets, and
`mcp-server`) and starts them in dependency order — `issue-tracker-api` first, `mcp-server` once
the API reports healthy.

- `issue-tracker-api` is published at `http://localhost:8000` (override with `PORT=<port>`)
- `mcp-server` is published at `http://localhost:8001` (override with `MCP_PORT=<port>`)
- Neither port is exposed beyond `localhost` by default
- The SQLite database lives in a named volume (`mock_jira_db`) and survives `docker compose down`
  (without `-v`)
- Confirm the stack is healthy: `docker compose ps` (both services should show `healthy`/`running`)
  or `curl http://localhost:8000/`
- View combined logs from both containers: `docker compose logs -f`
- Tear down (keeping data): `docker compose down`; tear down and wipe data: `docker compose down -v`
