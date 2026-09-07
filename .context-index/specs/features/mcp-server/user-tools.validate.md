---
rigor-tier: quick
---

# Validation Report: User MCP tools (list_users, create_user)

> **Date:** 2026-09-07
> **Spec:** .context-index/specs/features/mcp-server/user-tools.spec.md
> **Plan:** .context-index/specs/features/mcp-server/user-tools.plan.md
> **Overall Status:** PASS

## Rigor Tier

Resolved: **quick** (source: risk policy — `risk_level: low` maps to `policies.low.validate_mode: quick`
in `.context-index/governance/risk-policies.yaml`). Per the graduated-rigor-tiers contract, Check 1
(quality gates) runs in full, followed by one synthesized spec+constitution compliance check;
Checks 1.6, 8, 9, 11 are skipped (Check 11 additionally SKIPs on its own trigger guard — no UI files
in this diff). Check 1.5 (source manifest) was additionally run for extra rigor since it is cheap and
deterministic — its PASS is recorded below though quick tier would have permitted skipping it.

---

## Check 1: Quality Gates — PASS

Gates resolved from `.context-index/governance/gates.yaml` (via `adev domain load-gates`):

- Check 1a (fast tier):
  - `test`: `.venv/bin/python3 -m pytest -q` — PASS (135 passed, 3 warnings, 1.48s)
  - `lint`: `.venv/bin/ruff check .` — PASS (All checks passed!)
  - `test-js`: `node --test tests_js/**/*.test.js` — PASS (65 passed, 0 failed) — unrelated to this
    spec's scope (no JS files touched) but run per project-scoped gate requirement.
- Check 1b (integration tier): no gates configured — SKIP.
- Check 1c (e2e tier):
  - `e2e-smoke`: `.venv/bin/python3 -m pytest -q tests_e2e/` — PASS (40 passed, 15.38s), including
    all 9 targeted MCP e2e tests (tool discovery, project tools, issue tools, the 4 new user-tools
    tests, error paths) run over the real streamable-http transport with a real `mcp.ClientSession`.

## Check 1.5: Source Manifest Verification — PASS

`adev source-manifest verify --spec user-tools.spec.md` → `Check 1.5: PASS — source manifest
matches (sha: 2965cd2)`. All 6 manifest files confirmed committed to git (each has a `git log
--oneline -1` hit): `mcp_server/client.py`, `mcp_server/server.py`, `mcp_server/tools/users.py`,
`tests/mcp_server/test_client.py`, `tests/mcp_server/test_user_tools.py`,
`tests_e2e/test_mcp_user_tools_e2e.py`.

## Check 2: Spec Compliance — PASS

- BEH-1 (`list_users` returns `GET /users` unmodified): PASS — `mcp_server/tools/users.py:16-24`
  (`list_users()` calls `client.list_users()` and returns it directly); `mcp_server/client.py`'s
  `list_users()` does `self._request("GET", "/users")` then `response.json()`. Covered by
  `tests/mcp_server/test_user_tools.py::test_list_users_tool_returns_api_result_unmodified` and
  `tests_e2e/test_mcp_user_tools_e2e.py::test_create_and_list_users_match_real_http_state`.
- BEH-2 (`create_user` valid input → 201, created User): PASS — `mcp_server/tools/users.py:27-43`;
  `client.py`'s `create_user` builds `{"name": name}` plus `email`/`role` only when not `None`.
  Covered by `test_create_user_tool_returns_created_user` and the e2e create/list test.
- BEH-3 (duplicate email → 409 verbatim): PASS — `create_user` tool catches `UpstreamError` and
  raises `ToolError(exc.message)`; `client.py`'s `_request` raises `UpstreamError(status_code,
  message)` for any `>= 400` response, message taken verbatim from the API's `message` field.
  Covered by `test_create_user_tool_duplicate_email_errors_with_verbatim_message` and
  `tests_e2e/test_mcp_user_tools_e2e.py::test_create_user_duplicate_email_errors_with_verbatim_message`
  (real API, real duplicate).
- BEH-4 (schema-invalid input errors before HTTP call): PASS — `name: str` has no default and is
  the tool's only required parameter; the MCP SDK's function-metadata conversion rejects a call
  missing it before the function body runs. Covered by
  `test_create_user_tool_missing_name_errors_before_http_request` (asserts the `_client` spy was
  never invoked) and the e2e schema-invalid test.
- BEH-5 (unreachable API → clear connection message): PASS — `client.py`'s `_request` catches
  `httpx.RequestError` and raises `UpstreamUnreachableError` naming the base URL; both tools catch
  it and raise `ToolError(str(exc))`. Covered by two unit tests and
  `tests_e2e/test_mcp_user_tools_e2e.py::test_user_tools_unreachable_api_errors_with_clear_message`
  against a real `mcp-server` process with an unreachable `API_BASE_URL`.
- Postcondition (created User immediately visible to `list_users`): PASS — verified end to end by
  `test_create_and_list_users_match_real_http_state`, cross-checked against a direct real HTTP call
  to `issue-tracker-api`.
- `mcp-e2e.spec.md` BEH-1 / e2e assertion updated to 9 tools: PASS —
  `.context-index/specs/features/mcp-server/mcp-e2e.spec.md` BEH-1 now reads "9 registered tools";
  `tests_e2e/test_mcp_tool_discovery_e2e.py`'s `_EXPECTED_TOOL_NAMES` includes `list_users`/
  `create_user`, function renamed to `test_real_client_discovers_all_nine_tools_with_correct_schemas`,
  and its source manifest was re-stamped (sha `8eff9a7`, `drift_detected` cleared).
- No `get_user` tool: PASS — absent from `mcp_server/tools/users.py`; charter's Deferred
  Capabilities table records it for v2, consistent with the spec's Design Note.

Test integrity: all new tests assert exact structured values (`result.structured_content ==
<exact dict/wrapped-list>`), not loose matchers; the schema-invalid and unreachable-API tests
assert on `is_error`/message substrings appropriate to protocol-level error surfacing (matching
the existing `project-tools`/`issue-tools` test idiom exactly).

## Check 4: Constitution Compliance — PASS

- **"The HTTP contract is the boundary."** — `mcp_server/tools/users.py` never imports or touches
  anything under `app/`; every operation goes through `IssueTrackerClient`'s HTTP calls.
- **"No inbound dependencies."** — mcp-server continues to depend only on issue-tracker-api; no
  new dependency edges introduced.
- **"Fixture-backed, offline only."** — all e2e tests bind real processes to `127.0.0.1` only (via
  the existing `tests_e2e/servers.py` fixtures, unmodified).
- **Coding standards / naming:** `list_users`/`create_user` follow the exact `_client()` /
  `@mcp.tool()` / `ToolError` mapping pattern of `mcp_server/tools/projects.py`, snake_case
  throughout, docstrings present.
- **Architecture boundaries:** no new service, no auth flow touched, no unauthorized dependency
  added — only additive HTTP client methods and MCP tool registrations.

## Check 8: Boundary Compliance — SKIP (quick tier)

## Check 9: Transition Gates — SKIP (quick tier)

## Check 11: Visual Verification — N/A

No UI files in this implementation's diff (`mcp_server/`, `tests/`, `tests_e2e/`, and
`.context-index/specs/` only) — SKIP per Case A of the trigger guard.

---

**Summary:** 4 checks ran and passed (Check 1 quality gates, Check 1.5 source manifest, the
synthesized Check 2 spec-compliance + Check 4 constitution-compliance pass), 2 skipped per quick
rigor tier (Check 8, Check 9), 1 N/A (Check 11, no UI files). 0 failed.
