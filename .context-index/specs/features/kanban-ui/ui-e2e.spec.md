---
partial_schema: spec@1
charter: kanban-ui
status: review-passed
risk_level: low
milestone: v1.1
revision: 1
charter-revision: 10
created: 2026-09-06
updated: 2026-09-06
kind: behavioral
infra_requirements:
  systems:
    - name: "Playwright browser binary (Chromium)"
      env_vars: []
      cli_tools:
        - name: playwright
      notes: "One-time local setup: `playwright install chromium` downloads the browser binary this suite drives. No credentials, no network target beyond the real server this suite itself starts on localhost."
  ci_tag: "e2e"
---

# Live Spec: End-to-end UI test suite (real browser)

<!-- Live Spec within the kanban-ui charter.
     This defines a specific behavioral contract that drives implementation and testing.
     Parent Charter: .context-index/specs/features/kanban-ui/charter.md -->

## Behavioral Contract

### Preconditions

- Both kanban-ui specs (`board-view`, `issue-crud-forms`) are implemented.
- These tests reuse `issue-tracker-api`'s `api-e2e` spec's real-server-process fixture — the
  same live server (bound to `127.0.0.1`, serving `static/` and the API from one process) that
  the API e2e suite starts, not a separate mock or stub.
- A real browser (Playwright, Chromium) navigates to the live server's root URL and interacts
  with the actual rendered DOM — real clicks, real drag events, real form fills. No test in this
  suite calls a `board-logic.js`/`board.js` function directly; every assertion is made against
  what a real browser rendered.

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** a real browser loads the live server's root URL, **then** the seeded
  board renders with issues visible in their correct columns, read from the actual DOM, not from
  a mocked fetch response.
- **BEH-2** — **When** a real browser drags a card to a different column, **then** the change
  persists server-side — verified by reloading the page in the same real browser and confirming
  the card is still in the new column.
- **BEH-3** — **When** a real browser fills and submits the create-issue form, **then** a new
  card becomes visible in the `todo` column without a page reload.
- **BEH-4** — **When** a real browser fills and submits the edit-issue form, **then** the
  visible card reflects the edited fields without a page reload.
- **BEH-5** — **When** a real browser deletes a card and confirms the deletion, **then** the
  card disappears — verified by reloading the page and confirming it does not reappear.
- **BEH-6** — **When** a real browser selects a different Project from the switcher, **then**
  the visible board fully replaces its contents with that Project's Issues.

### Postconditions

- Every assertion in this suite reads the real, rendered DOM (via Playwright locators) — never
  the JS module's internal state or a mocked network layer.
- The browser and the underlying live server are both torn down after the test session.

### Error Cases

| Condition | Expected Behavior | Error Code |
|-----------|-------------------|------------|
| Real server becomes unreachable mid-test (simulated via Playwright route interception forcing a network failure) | The real browser shows a visible error message, matching `issue-crud-forms` BEH-5 — verified by reading the rendered DOM, not a mock | `E2E_UI_FETCH_FAILED` |
| Playwright cannot launch the browser (binary not installed) | Test setup fails loudly naming the missing binary and the `playwright install chromium` remedy | `E2E_BROWSER_NOT_INSTALLED` |

## System Constitution Reference

- **Principle:** "The HTTP contract is the boundary." — Applies because this suite still only
  interacts with kanban-ui through the real, served page — it never reaches past the browser
  into internal JS state or the database.
- **Principle:** "Fixture-backed, offline only." — Applies because the real server and browser
  this suite drives are both local-only.
- **Principle:** "No inbound dependencies." — Applies because this suite depends on
  `issue-tracker-api`'s real-server fixture (an internal-module dependency within this same
  repo), never on another repo.

## Actionable Task Map

| Task | Description | Estimated Complexity |
|------|-------------|---------------------|
| Playwright setup | Add `playwright`/`pytest-playwright` to dev dependencies; document the one-time `playwright install chromium` step | small |
| Board-render e2e test | Real-browser test for BEH-1 | small |
| Column-move e2e test | Real-browser drag-and-drop test for BEH-2 | medium |
| Create/edit-issue e2e tests | Real-browser form tests for BEH-3 and BEH-4 | medium |
| Delete-issue e2e test | Real-browser test for BEH-5 | small |
| Project-switcher e2e test | Real-browser test for BEH-6 | small |
| Error-path e2e test | Route-interception test for the error case | small |

## Acceptance Criteria

- [ ] A real browser renders the seeded board with correctly-columned cards (BEH-1)
- [ ] A real drag-and-drop column move persists across a real page reload (BEH-2)
- [ ] A real create-issue form submission produces a visible new card (BEH-3)
- [ ] A real edit-issue form submission updates the visible card (BEH-4)
- [ ] A real delete removes the card, confirmed after reload (BEH-5)
- [ ] A real project switch replaces the visible board contents (BEH-6)
- [ ] All quality gates pass (tests, lint)
- [ ] No constitutional violations introduced
