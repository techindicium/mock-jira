---
partial_schema: implement@1
charter: issue-tracker-api
status: validated
risk_level: low
milestone: mvp
revision: 2
charter-revision: 8
created: 2026-09-04
updated: 2026-09-05
kind: behavioral
source-manifest:
  sha: "5757243"
  files:
    - app/main.py
    - app/seed.py
    - tests/test_seed.py
  computed-at: "2026-09-06T23:14:54.272Z"
---

# Live Spec: Fixture seed data

<!-- Live Spec within the issue-tracker-api charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/issue-tracker-api/charter.md -->

## Behavioral Contract

### Preconditions

- The `project-management` and `issue-lifecycle` specs' schemas exist — seeding writes through
  the same Project/Issue tables those specs define.
- Reconciliation with `../course-shared/canon` happens once, at spec-authoring time (this
  document), never at runtime. The values below are hardcoded into this repo's own seed fixture
  module; the running program never opens any file outside this repository. This is
  non-negotiable: a runtime read of `../course-shared/canon/*` would be an inbound dependency on
  another repo, which the constitution forbids outright.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the API starts against an empty database (no Project rows exist),
  **then** it seeds exactly one Project (`key: PORTAL`, `name: Help portal engineering`) and
  six Issues under it in a single transaction, all present and queryable immediately once
  startup completes — no placeholder or lorem-ipsum text in any field. The six Issues span all
  three statuses (two `todo`, two `in_progress`, two `done`) and a mix of `issue_type`
  (`bug`/`task`/`story`) and `priority` (`low`/`medium`/`high`) values, so a fresh kanban board
  shows populated columns rather than one column with six cards.
- **BEH-2** — **When** the API starts against a database that already has at least one Project
  row, **then** it performs no seeding — existing data is left untouched, and restarting the
  process any number of times never creates a second copy.
- **BEH-3** — **When** seed Issues are generated, **then** every `assignee` and `reporter` value
  is a real name drawn from `course-shared/canon/company.md`'s Named People table (e.g. "Kofi
  Adjei", "Mei Tan", "Joao Pinto") — never an invented placeholder name.
- **BEH-4** — **When** the seed module assigns a Project `key` or derives an Issue `key`,
  **then** neither value collides with any reserved-range identifier scheme in
  `course-shared/canon/identifiers.md` (`ACCOUNT-*`, `TICKET-*`, `ARTICLE-*`, `PROPOSAL-*`,
  `INCIDENT-*`, `POLICY-*`, `OPPORTUNITY-*`, `EXPERIMENT-*`) are avoided. `PORTAL` and
  `PORTAL-<n>` are outside every reserved prefix.

### Postconditions

- After a fresh-database startup, `GET /projects` returns exactly one Project and
  `GET /issues?project_id=<PORTAL's id>` returns exactly six Issues.
- Seed Issue descriptions may mention canon entities by their real ID (e.g. `INCIDENT-01`,
  `ACCOUNT-1001`) as read-only narrative references, but this module never creates, owns, or
  exposes an endpoint for any canon-owned entity type (Account, Incident, Ticket, Article, etc.).

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Seed data fails validation (a hardcoded row is malformed) | Startup aborts with a clear error naming the offending row | `SEED_DATA_INVALID` |
| Database file path is not writable | Startup aborts with a clear error naming the path | `SEED_DB_NOT_WRITABLE` |

## System Constitution Reference

- **Principle:** "Identifiers reconcile with the shared canon. Any account, user, or entity ID
  this API returns must be consistent with `course-shared/canon/identifiers.md` where an overlap
  exists — never invent an ID that could collide with the canon's reserved ranges." — This spec
  exists specifically to satisfy this principle for the module's first real data.
- **Principle:** "No inbound dependencies. This repo never depends on `course-shared`... Consuming
  tracks depend on it; it never depends back." — Applies because reconciliation must be a
  one-time authoring-time act (this document), never a runtime file read across the repo
  boundary — see Preconditions.
- **Principle:** "Fixture-backed, offline only." — Applies directly: this is the fixture.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Write the seed fixture module | Hardcoded Project + 6 Issues, values reconciled with canon at authoring time (this spec), committed only in this repo | small |
| Wire seed-on-empty-database startup check | Run the seed module once, only when no Project rows exist yet | small |
| Idempotency test | Start twice against the same database file; assert exactly one Project and six Issues after both runs | small |

## Acceptance Criteria

- [x] Fresh-database startup seeds one Project and six Issues, no placeholder text (BEH-1)
- [x] Restarting against an already-seeded database creates no duplicate rows (BEH-2)
- [x] Every seeded `assignee`/`reporter` is a real canon name (BEH-3)
- [x] No seeded Project/Issue key collides with a canon-reserved prefix (BEH-4)
- [x] The seed module contains no runtime file read outside this repository
- [x] All quality gates pass (tests, lint)
- [x] No constitutional violations introduced
