---
partial_schema: implement@1
charter: kanban-ui
status: implemented
risk_level: low
milestone: v1.5
revision: 1
charter-revision: 38
created: 2026-09-09
updated: 2026-09-09
kind: behavioral
charter-extension: true
source-manifest:
  sha: "5ca09c6"
  files:
    - static/css/board.css
    - static/index.html
    - static/js/board-logic.js
    - static/js/board.js
    - tests_e2e/test_ui_backlog_view_e2e.py
    - tests_js/backlog-view-beh-1-nav-container.test.js
    - tests_js/backlog-view-beh-2-table-renderer.test.js
    - tests_js/backlog-view-beh-3-filtering.test.js
    - tests_js/backlog-view-beh-4-filter-wiring.test.js
    - tests_js/backlog-view-beh-5-empty-filter-state.test.js
    - tests_js/backlog-view-beh-6-styling-tokens.test.js
  computed-at: "2026-09-09T18:22:16.647Z"
---

# Live Spec: Backlog list view and issue filters

<!-- charter-extension: "Backlog list view and filters" was not in the kanban-ui charter's
     Capability Map at authoring time. It has since been added (status: specified) as part of
     writing this spec — see charter.md revision 38. -->

## Behavioral Contract

### Preconditions

- issue-tracker-api is reachable.
- At least one Project exists and is selected (mirrors board-view.spec.md's preconditions —
  the empty-state screen for zero Projects is unchanged and out of scope here).

### Behaviors

<!-- retired-behavior-ids: (none) -->

- **BEH-1** — **When** the user clicks a new "Backlog" sidebar nav item **then** the app shows a
  list/table view of the selected Project's Issues (key, summary, type, priority, status,
  assignee) as rows, without navigating away from the app shell or reloading the page.
- **BEH-2** — **When** the Backlog view is open **then** it reads the same selected Project as
  the Board view — switching Project from either view's switcher updates both views' data.
- **BEH-3** — **When** the user sets one or more filters (assignee, issue type, priority) in the
  filter bar **then** only Issues matching every active filter are shown, in both the Backlog
  view and the Board view.
- **BEH-4** — **When** multiple filters are active **then** they combine with AND semantics — an
  Issue must match every active filter's value to remain visible.
- **BEH-5** — **When** the user clears a filter (selects the "All" option) **then** Issues
  previously excluded only by that filter reappear.
- **BEH-6** — **When** no Issue matches the active filters **then** the affected view shows an
  explicit "No issues match the current filters" message instead of an empty column or table.
- **BEH-7** — **When** filters are active and the user switches Project **then** the filter
  selections persist and are re-applied against the newly selected Project's Issues, rather than
  silently resetting to "All".

### Postconditions

- The Issues displayed in Backlog and Board both reflect the intersection of: the current
  Project selection AND all active filters.
- No write to issue-tracker-api ever occurs as a result of setting, changing, or clearing a
  filter — filtering is read-only client-side view state.
- Filter selections live only in the page's in-memory state (not persisted server-side, not sent
  as new HTTP query parameters) — `GET /issues?project_id=` continues to be called exactly as
  board-view.spec.md already describes.

### Error Cases

| Condition | Expected Behavior | Notes |
|-----------|-------------------|-------|
| `GET /issues` fails while the Backlog view is open | Same error-banner pattern the Board view already uses (`formatFetchError`) | Reuses `#board-error`; no new error-handling path |
| The assignee filter is opened but `GET /users` returned no Users | Assignee filter still renders with only the "All" option | Degrades gracefully, matches user-picker.spec.md's existing degrade-silently behavior for `GET /users` failures |
| A filter narrows results to zero, then the user switches Project | The zero-match message updates immediately to reflect the new Project's (possibly non-empty) filtered set | No stale "no results" message left over from the prior Project |

## System Constitution Reference

- "The HTTP contract is the boundary" — this capability adds no new endpoint and no new query
  parameter to issue-tracker-api; filtering happens entirely client-side over data `GET /issues`
  already returns. Consuming tracks' integration surface is unchanged.
- "Fixture-backed, offline only" — no new fixture data, no new network dependency; filters
  operate only on Issues already fetched for the selected Project.

## Actionable Task Map

| Task | Description | Complexity |
|------|-------------|------------|
| Add "Backlog" nav item + view container | Sidebar entry and `#view-backlog` section, following the existing `showView`/`NAV_VIEWS` pattern from app-navigation.spec.md | Low |
| Backlog table renderer | New pure function in `board-logic.js`: Issues → table-row HTML | Low |
| Filter bar UI + state | Assignee/type/priority `<select>` controls in a shared filter bar, readable by both Board and Backlog renderers | Medium |
| Filtering logic | New pure function in `board-logic.js`: `(issues, filters) -> filtered issues`, used by both views | Low |
| Zero-match empty state | Message shown when active filters produce zero results, distinct from the "no Projects" empty state | Low |
| Tests | Unit tests for the filtering function and table renderer (`tests_js/`); browser e2e for nav + filter interaction (`tests_e2e/`) | Medium |

## Acceptance Criteria

- [x] A "Backlog" nav item exists alongside Board/Users/Projects and shows a table of the
      selected Project's Issues (BEH-1)
- [x] Backlog and Board share the same Project switcher/selection (BEH-2)
- [x] The filter bar filters both Board and Backlog by assignee, type, and priority, combined
      with AND semantics (BEH-3, BEH-4)
- [x] Clearing a filter restores previously-excluded Issues (BEH-5)
- [x] A zero-match filter state shows an explicit message, not a blank view (BEH-6)
- [x] Filters persist across Project switches (BEH-7)
- [x] All quality gates pass (`pytest`, `ruff`, `tests_js`, e2e smoke)
- [x] No constitutional violations — confirmed no new/changed HTTP endpoint or fixture identifier
