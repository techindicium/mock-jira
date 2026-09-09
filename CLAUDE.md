<!-- Synced from .context-index/constitution.md by adev. Do not edit above the User Additions line. -->

# Constitution: mock-jira

## Identity

mock-jira is a standalone mock of a JIRA-shaped issue-tracking HTTP API. It exists so the
adev-course track repos that need a realistic upstream issue tracker — `portwell-portal` (SDLC)
and `portwell-analytics` (DDLC) today — have something concrete to integrate against, without
any track ever reaching a real external endpoint.

It is course infrastructure, not a course exercise. Its own API surface and internals are not
something students build; they are a fixed dependency other tracks build against.

## Non-Negotiable Principles

1. **No inbound dependencies.** This repo never depends on `course-shared`, another `mock-*`
   repo, or any track repo. Consuming tracks depend on it; it never depends back.
2. **Fixture-backed, offline only.** No network call to a real endpoint, no real credentials.
   Everything this API serves comes from local fixtures.
3. **Identifiers reconcile with the shared canon.** Any account, user, or entity ID this API
   returns must be consistent with `course-shared/canon/identifiers.md` where an overlap exists
   — never invent an ID that could collide with the canon's reserved ranges.
4. **The HTTP contract is the boundary.** Consuming tracks integrate through the documented API
   only, never by importing this repo's internals directly.
5. **Breaking API changes are coordinated, not silent.** Once a track depends on an endpoint or
   response shape, changing it requires updating this constitution's Context Routing table and
   flagging the affected tracks.

## Architecture Boundaries

### Requires Human Approval

- Breaking changes to the public HTTP API contract (endpoint paths, request/response shapes)
- Changing fixture data identifiers that other tracks may already key on
- Adding a dependency on another repo in the workspace

### Autonomous (Agent May Decide)

- Adding new mock endpoints that extend (not break) the existing contract
- Internal refactors that don't change the HTTP surface
- Adding tests
- Fixing lint errors

## Commands

```bash
pip install -r requirements.txt
python3 -m pytest -q    # tests
ruff check .             # lint
docker compose up        # run the full stack (issue-tracker-api + mcp-server)
```

## Context Routing

| Context Need | Location |
|-------------|----------|
| API routes | *(not yet built — chartered via `/adev:brainstorm`)* |
| Fixture data | *(not yet built)* |
| Shared identifiers this mock must respect | `../course-shared/canon/identifiers.md` |
| Consumers of this API | `../adev-workspace.yaml` (`dependencies:` naming `mock-jira` as `to`) |

## Context Index

Structured project context lives under `.context-index/` — constitution, manifest, governance,
and scaffolding for specs, ADRs, and samples once this repo has code to describe.

## Governance Posture

Deliberately lightweight, for a small standalone mock API in a training course:

- **Reviewers** (`governance/review.yaml`): all three bundled reviewers disabled.
- **Validation** (`governance/validate.yaml`): only deterministic checks run; both
  subagent-review checks and visual-verification are disabled.
- **Risk policies** (`governance/risk-policies.yaml`): medium and low risk run `quick` mode,
  `minimal` test depth, no human-in-the-loop — most work here runs fully agentic. `high` risk
  keeps full rigor and human approval.
- `merge_policy: merge`, `protected_branches: []` — no remote/PR capability exists for this
  repo, so direct merges to `main` are allowed after gates pass. Always branch first regardless.

<!-- User Additions -->
