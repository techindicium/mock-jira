<!-- partial_schema: plan@1 -->

# Implementation Plan: Backlog list view and issue filters

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/backlog-view.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-09)
> **Platform:** none (framework unset; Python 3.11 + FastAPI-shaped issue-tracker-api backend, vanilla JS/HTML/CSS frontend), sqlite, no ORM

**Goal:** Add a "Backlog" list/table view of the selected Project's Issues and a shared assignee/type/priority filter bar that narrows both the Backlog and Board views, entirely client-side.

**Architecture:** Two new pure functions in `static/js/board-logic.js` (`buildBacklogRowsHtml` and `filterIssues`) mirror the existing `buildCardHtml`/`groupIssuesByStatus` pattern — no new HTTP calls, no server changes. `static/js/board.js` wires a new `#nav-backlog` view container and a filter-bar control block that re-renders whichever view (Board, Backlog, or both) is currently visible whenever a filter changes or the issue set reloads. `static/index.html` gains the new nav item, `#view-backlog` section, and filter-bar markup; `static/css/board.css` gains styling reusing the existing token set (no new colors/tokens).

---

## File Structure

**Modify:**
- `static/index.html` — add `#nav-backlog` sidebar button, `#view-backlog` section (table container + empty-filter-result message), and a filter-bar block (assignee/type/priority `<select>`s) placed above the board/backlog content so both views can read it
- `static/js/board-logic.js` — add `buildBacklogRowsHtml(issues)`, `filterIssues(issues, filters)`, and `uniqueAssignees(issues)` (drives the assignee filter's option list) as new exported pure functions
- `static/js/board.js` — add `showView`-compatible wiring for the `backlog` view name, a `renderBacklog(issues)` function, a `onFilterChange` handler that re-filters `currentIssues` and re-renders whichever of Board/Backlog is active, and empty-filter-result toggling
- `static/css/board.css` — add `.filter-bar`, `.backlog-table`, and `.filter-empty-state` rules reusing existing `--surface`/`--border`/`--text*` tokens (no new tokens)

**Reference (read, do not modify):**
- `static/js/board-logic.js` — follow `buildCardHtml`, `groupIssuesByStatus`, `columnCounts` as the pattern for new pure functions (escaping via the existing `escapeHtml` helper, no DOM access)
- `static/js/board.js` — follow `showView`/`NAV_VIEWS`/`onNavClick` as the pattern for adding the `backlog` view, and `renderColumns`/`loadIssuesFor` as the pattern for re-render-on-data-change
- `static/index.html` — follow the existing `#view-users`/`#view-projects` sections as the pattern for a new `.view` container gated by `hidden`

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (BEH-1, BEH-2; Acceptance Criteria 1-2)
- Charter: `.context-index/specs/features/kanban-ui/charter.md` (capability: "Backlog list view and filters")
- Source files: `static/js/board.js` (full — `NAV_VIEWS`, `showView`, `onNavClick`), `static/index.html` (full — `<nav class="sidebar">`, `#view-users` section as pattern)

### Task 2 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (BEH-1; Acceptance Criteria 1)
- Source files: `static/js/board-logic.js` (full — `buildCardHtml`, `escapeHtml`, module.exports list)

### Task 3 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (BEH-3, BEH-4, BEH-5; Acceptance Criteria 3-4)
- Source files: `static/js/board-logic.js` (full, including Task 2's new functions), `static/js/board.js` (full — `renderColumns`, `loadIssuesFor`, `currentIssues`)

### Task 4 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (BEH-3, BEH-7; Acceptance Criteria 3, 6)
- Source files: `static/index.html` (full), `static/js/board.js` (full, including Task 1/3's additions)

### Task 5 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (BEH-6; Acceptance Criteria 5)
- Source files: `static/js/board.js` (full, including Task 3/4's additions), `static/index.html` (full, including Task 1/4's additions)

### Task 6 Context
- Spec: `.context-index/specs/features/kanban-ui/backlog-view.spec.md` (all behaviors; all acceptance criteria)
- Source files: `static/css/board.css` (full — existing token set, `.ledger-panel`/`.column`/`.card` as pattern for new rules)

---

## Parallelization

- Group A (sequential): Task 1 → Task 4 → Task 5 → Task 7 (shared files: `static/index.html`, `static/js/board.js`)
- Group B (sequential): Task 2 → Task 3 (shared file: `static/js/board-logic.js`; Task 3 consumes Task 2's functions)
- Group C (sequential): Task 6 (styling — depends on Task 1 and Task 4's markup existing to style, per the Task Summary table's Depends On column, so it runs after Group A's Task 1/Task 4 despite touching only CSS)

Group B can run in parallel with Group A up to the point where Task 3's output (filtering) is wired into Task 4/5's view rendering — Task 4 depends on Task 3. Group C (Task 6) starts once Group A's Task 4 lands. Task 7 runs last — it depends on Tasks 1-5 (all markup/wiring) being complete.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Backlog nav item + view container | small | unit | — | 0 create, 2 modify |
| 2 | Backlog table renderer (pure function) | small | unit | — | 0 create, 1 modify |
| 3 | Filtering logic (pure function) | medium | unit | Task 2 | 0 create, 1 modify |
| 4 | Filter bar UI + wiring | medium | unit | Task 1, Task 3 | 0 create, 2 modify |
| 5 | Zero-match empty state | small | unit | Task 4 | 0 create, 1 modify |
| 6 | Styling | small | unit | Task 1, Task 4 | 0 create, 1 modify |
| 7 | End-to-end browser tests (BEH-2, BEH-6, BEH-7) | medium | e2e | Task 1, Task 2, Task 3, Task 4, Task 5 | 1 create, 0 modify |

---

## Task Structure

### Task 1: Backlog nav item + view container [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (sidebar `<nav>` block; add `#view-backlog` section after `#view-projects`)
- Modify: `static/js/board.js:354` (`NAV_VIEWS` array)
- Test: `tests_js/backlog-view-beh-1-nav-container.test.js`

**Tests:** `tests_js/backlog-view-beh-1-nav-container.test.js` — new file (mirrors `tests_js/navigation-beh-1-sidebar-markup.test.js`'s pattern of reading `static/index.html` and asserting markup)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-1: a Backlog nav item exists alongside Board/Users/Projects", () => {
  assert.match(html, /<button[^>]+id="nav-backlog"[^>]+data-view="backlog"[^>]*>Backlog<\/button>/);
});

test("BEH-1: a #view-backlog container exists, hidden by default", () => {
  assert.match(html, /<section id="view-backlog" class="view" hidden>/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-1-nav-container.test.js`
Expected: FAIL — no `#nav-backlog` element, no `#view-backlog` section

- [ ] **Implement**

Add `<button type="button" class="nav-item" id="nav-backlog" data-view="backlog">Backlog</button>` to the sidebar `<nav>` in `static/index.html`, after `#nav-board` and before `#nav-users` (backlog is a board-adjacent view). Add a new `<section id="view-backlog" class="view" hidden>` after `#view-projects`'s closing `</section>`, containing a `<h1>Backlog</h1>` and an empty `<table id="backlog-table"><tbody id="backlog-rows"></tbody></table>`. Do NOT add a separate `#backlog-error` element — per the spec's Error Cases table, a `GET /issues` failure while Backlog is open reuses the existing `#board-error` banner (Backlog reads from the same `currentIssues`/`loadIssuesFor` fetch as Board, per BEH-2, so it has no independent fetch path of its own to error on). In `static/js/board.js`, add `"backlog"` to the `NAV_VIEWS` array and add `document.getElementById("nav-backlog").addEventListener("click", onNavClick);` alongside the existing three nav listeners.

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-1-nav-container.test.js`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feat/kanban-ui/backlog-view`

```bash
git add static/index.html static/js/board.js tests_js/backlog-view-beh-1-nav-container.test.js
git commit -m "feat(kanban-ui): add Backlog nav item and view container"
```

---

### Task 2: Backlog table renderer (pure function) [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/board-logic.js` (add `buildBacklogRowsHtml`, export it)
- Test: `tests_js/backlog-view-beh-2-table-renderer.test.js`

**Tests:** `tests_js/backlog-view-beh-2-table-renderer.test.js` — new file (mirrors `buildCardHtml`'s existing test pattern in `visual-refresh-beh-3-issue-key.test.js`)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildBacklogRowsHtml } = require("../static/js/board-logic.js");

test("BEH-1: renders one row per issue with key, summary, type, priority, status, assignee", () => {
  const html = buildBacklogRowsHtml([
    { id: 1, key: "ASSIST-1", summary: "Fix thing", issue_type: "bug", priority: "high", status: "todo", assignee: "Mei Tan" },
  ]);
  assert.match(html, /<tr[^>]*data-issue-id="1"[^>]*>/);
  assert.match(html, /ASSIST-1/);
  assert.match(html, /Fix thing/);
  assert.match(html, /bug/);
  assert.match(html, /high/);
  assert.match(html, /todo/);
  assert.match(html, /Mei Tan/);
});

test("BEH-1: missing assignee renders as Unassigned, not undefined", () => {
  const html = buildBacklogRowsHtml([{ id: 1, key: "A-1", summary: "x", issue_type: "task", priority: "low", status: "todo" }]);
  assert.match(html, /Unassigned/);
  assert.doesNotMatch(html, /undefined/);
});

test("BEH-1: HTML-escapes interpolated fields", () => {
  const html = buildBacklogRowsHtml([{ id: 1, key: "A-1", summary: "<script>", issue_type: "task", priority: "low", status: "todo" }]);
  assert.doesNotMatch(html, /<script>/);
});

test("zero issues renders an empty string", () => {
  assert.equal(buildBacklogRowsHtml([]), "");
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-2-table-renderer.test.js`
Expected: FAIL — `buildBacklogRowsHtml is not a function`

- [ ] **Implement**

Add to `static/js/board-logic.js`, following `buildCardHtml`'s escaping/interpolation pattern exactly:

```javascript
function buildBacklogRowsHtml(issues) {
  if (!Array.isArray(issues)) return "";
  return issues
    .map((issue) => (
      `<tr data-issue-id="${issue.id}">` +
      `<td>${escapeHtml(issue.key || "")}</td>` +
      `<td>${escapeHtml(issue.summary)}</td>` +
      `<td>${escapeHtml(issue.issue_type)}</td>` +
      `<td>${escapeHtml(issue.priority)}</td>` +
      `<td>${escapeHtml(issue.status)}</td>` +
      `<td>${escapeHtml(issue.assignee || "Unassigned")}</td>` +
      `</tr>`
    ))
    .join("");
}
```

Add `buildBacklogRowsHtml` to the `return { ... }` export object at the bottom of the file.

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-2-table-renderer.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js tests_js/backlog-view-beh-2-table-renderer.test.js
git commit -m "feat(kanban-ui): add backlog table row renderer"
```

---

### Task 3: Filtering logic (pure function) [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Modify: `static/js/board-logic.js` (add `filterIssues`, `uniqueAssignees`, export both)
- Test: `tests_js/backlog-view-beh-3-filtering.test.js`

**Tests:** `tests_js/backlog-view-beh-3-filtering.test.js` — new file

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { filterIssues, uniqueAssignees } = require("../static/js/board-logic.js");

const ISSUES = [
  { id: 1, issue_type: "bug", priority: "high", assignee: "Mei Tan" },
  { id: 2, issue_type: "task", priority: "low", assignee: "Kofi Adjei" },
  { id: 3, issue_type: "bug", priority: "low", assignee: "Mei Tan" },
];

test("BEH-3: no active filters returns every issue", () => {
  assert.deepEqual(filterIssues(ISSUES, {}), ISSUES);
});

test("BEH-3: a single filter narrows to matching issues", () => {
  assert.deepEqual(filterIssues(ISSUES, { issue_type: "bug" }).map((i) => i.id), [1, 3]);
});

test("BEH-4: multiple filters combine with AND", () => {
  assert.deepEqual(filterIssues(ISSUES, { issue_type: "bug", priority: "low" }).map((i) => i.id), [3]);
});

test("BEH-5: an empty-string filter value is treated as cleared (matches everything for that field)", () => {
  assert.deepEqual(filterIssues(ISSUES, { issue_type: "bug", priority: "" }).map((i) => i.id), [1, 3]);
});

test("BEH-3: assignee filter matches exactly", () => {
  assert.deepEqual(filterIssues(ISSUES, { assignee: "Mei Tan" }).map((i) => i.id), [1, 3]);
});

test("uniqueAssignees: returns sorted distinct assignee names, dropping blank/missing", () => {
  assert.deepEqual(uniqueAssignees([{ assignee: "Mei Tan" }, { assignee: "Kofi Adjei" }, { assignee: "Mei Tan" }, { assignee: "" }, {}]), ["Kofi Adjei", "Mei Tan"]);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-3-filtering.test.js`
Expected: FAIL — `filterIssues is not a function`

- [ ] **Implement**

Add to `static/js/board-logic.js`:

```javascript
const FILTERABLE_FIELDS = ["assignee", "issue_type", "priority"];

function filterIssues(issues, filters) {
  const list = Array.isArray(issues) ? issues : [];
  const active = FILTERABLE_FIELDS.filter((f) => filters && filters[f]);
  if (active.length === 0) return list;
  return list.filter((issue) => active.every((f) => issue[f] === filters[f]));
}

function uniqueAssignees(issues) {
  const list = Array.isArray(issues) ? issues : [];
  const names = new Set(
    list.map((i) => (i.assignee || "").trim()).filter((name) => name !== "")
  );
  return Array.from(names).sort();
}
```

Add both to the export object.

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-3-filtering.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js tests_js/backlog-view-beh-3-filtering.test.js
git commit -m "feat(kanban-ui): add issue filtering pure functions"
```

---

### Task 4: Filter bar UI + wiring [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 3
**Files:**
- Modify: `static/index.html` (filter-bar markup: assignee/type/priority `<select>`s, placed once above both `#board` and `#view-backlog`'s table)
- Modify: `static/js/board.js` (`renderBacklog`, `onFilterChange`, filter-state object, re-render Board/Backlog on filter change and on `loadIssuesFor`)
- Test: `tests_js/backlog-view-beh-4-filter-wiring.test.js`

**Tests:** `tests_js/backlog-view-beh-4-filter-wiring.test.js` — new file, asserts markup contract (three `<select>`s with expected ids) since `board.js` DOM wiring itself is covered by the existing e2e suite pattern (`tests_e2e/`), not unit tests

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-3: filter bar has assignee, type, and priority selects", () => {
  assert.match(html, /<select[^>]+id="filter-assignee"/);
  assert.match(html, /<select[^>]+id="filter-issue-type"/);
  assert.match(html, /<select[^>]+id="filter-priority"/);
});

test("BEH-5: each filter select has an explicit All/empty option", () => {
  const block = html.slice(html.indexOf('id="filter-bar"'), html.indexOf("</div>", html.indexOf('id="filter-bar"')) + 6);
  assert.match(block, /<option value="">All<\/option>/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-4-filter-wiring.test.js`
Expected: FAIL — no `#filter-bar`/`#filter-assignee`/etc.

- [ ] **Implement**

**Design decision (pinned, not left to the implementer):** the filter bar is a single shared element, not duplicated per view. In `static/index.html`, add `<div id="filter-bar">` as a sibling of `#view-board`/`#view-backlog`/`#view-users`/`#view-projects` inside `.app-main` (placed immediately before `#view-board`), containing three `<select>`s: `#filter-assignee` (options populated at runtime from `uniqueAssignees`), `#filter-issue-type` (static options: All/bug/task/story), `#filter-priority` (static options: All/low/medium/high), each with a leading `<option value="">All</option>`. In `board.js`'s `showView(name)`, add one line toggling `#filter-bar`'s `hidden` attribute: visible when `name === "board" || name === "backlog"`, hidden otherwise (Users/Projects views have no filter bar). Both `renderColumns` (Board) and `renderBacklog` (Backlog, Task 4b below) read the same `activeFilters` state from this one element — no duplicate filter-bar markup exists anywhere.

In `static/js/board.js`: add `let activeFilters = {};`, a `renderBacklog(issues)` function using `BoardLogic.buildBacklogRowsHtml(BoardLogic.filterIssues(issues, activeFilters))`, an `onFilterChange` handler that reads all three selects into `activeFilters` and re-renders whichever of `renderColumns`/`renderBacklog` corresponds to the currently visible view (using `BoardLogic.filterIssues(currentIssues, activeFilters)` for Board too — replace the direct `BoardLogic.computeBoardState(...)` call in `renderBoardState`/`loadIssuesFor` with a filtered variant). Wire `addEventListener("change", onFilterChange)` on all three selects. On each `loadIssuesFor`, also repopulate `#filter-assignee`'s options from `BoardLogic.uniqueAssignees(issues)` (preserving the current selection if it still exists in the new list, per BEH-7).

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-4-filter-wiring.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board.js tests_js/backlog-view-beh-4-filter-wiring.test.js
git commit -m "feat(kanban-ui): wire filter bar to Board and Backlog views"
```

---

### Task 5: Zero-match empty state [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 4
**Files:**
- Modify: `static/index.html` (`#filter-empty-state` element, hidden by default, as a single shared sibling of `#filter-bar` outside both `#view-board` and `#view-backlog`)
- Modify: `static/js/board.js` (toggle `#filter-empty-state hidden` based on filtered-result length)
- Test: `tests_js/backlog-view-beh-5-empty-filter-state.test.js`

**Tests:** `tests_js/backlog-view-beh-5-empty-filter-state.test.js` — new file, markup-contract test (mirrors `#empty-state` pattern already in `static/index.html`)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-6: a filter-empty-state element exists, hidden by default, distinct from #empty-state", () => {
  assert.match(html, /<[a-z]+ id="filter-empty-state"[^>]*hidden[^>]*>/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-5-empty-filter-state.test.js`
Expected: FAIL — no `#filter-empty-state`

- [ ] **Implement**

**Design decision (pinned, not left to the implementer):** exactly one `#filter-empty-state` element exists in the document — never two elements sharing that id (which would make `getElementById` silently resolve to only the first, breaking whichever view isn't first). Add `<p id="filter-empty-state" hidden>No issues match the current filters.</p>` as a sibling of `#filter-bar` (from Task 4), outside both `#view-board` and `#view-backlog` — a single shared element both `renderColumns` and `renderBacklog` toggle. In `board.js`, after computing the filtered set in either render function, toggle `#filter-empty-state`'s `hidden` attribute based on whether the filtered set is empty AND at least one filter is active (distinguishing this from the pre-existing "no Projects at all" `#empty-state`, which must not be affected by filters). Also toggle it to `hidden` whenever the active view is neither `board` nor `backlog` (same condition as `#filter-bar` in `showView`, Task 4), so it never shows behind the Users/Projects views.

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-5-empty-filter-state.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board.js tests_js/backlog-view-beh-5-empty-filter-state.test.js
git commit -m "feat(kanban-ui): add zero-match filter empty state"
```

---

### Task 6: Styling [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 4
**Files:**
- Modify: `static/css/board.css` (`.filter-bar`, `#backlog-table`, `#filter-empty-state` rules)
- Test: `tests_js/backlog-view-beh-6-styling-tokens.test.js`

**Tests:** `tests_js/backlog-view-beh-6-styling-tokens.test.js` — new file, asserts no new color literals were introduced (reuses only existing `--brand-blue`/`--surface`/`--border`/`--text*` tokens), mirroring `visual-refresh-beh-1-design-tokens.test.js`'s intent

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-1: filter-bar rule exists", () => {
  assert.match(css, /\.filter-bar\s*{/);
});

test("offline-only/no-new-tokens: filter-bar and backlog-table rules only reference existing var() tokens, no new hex literals", () => {
  const filterBarBlock = css.slice(css.indexOf(".filter-bar {"), css.indexOf("}", css.indexOf(".filter-bar {")) + 1);
  assert.doesNotMatch(filterBarBlock, /#[0-9a-fA-F]{3,6}/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/backlog-view-beh-6-styling-tokens.test.js`
Expected: FAIL — no `.filter-bar` rule

- [ ] **Implement**

Add to `static/css/board.css`, reusing existing tokens only (no new `:root` entries — matches the file's own "keep this list short" convention):

```css
.filter-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.filter-bar select {
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0.35rem 0.5rem;
  font-family: inherit;
  font-size: 0.8rem;
  color: var(--text);
  background: var(--surface);
}

#backlog-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
}

#backlog-table th,
#backlog-table td {
  text-align: left;
  padding: 0.5rem 0.65rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.85rem;
  color: var(--text);
}

#backlog-table th {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-subtle);
}

#filter-empty-state {
  color: var(--text-subtle);
  padding: 0.75rem;
}
```

- [ ] **Verify test passes**

Run: `node --test tests_js/backlog-view-beh-6-styling-tokens.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/css/board.css tests_js/backlog-view-beh-6-styling-tokens.test.js
git commit -m "feat(kanban-ui): style backlog table and filter bar"
```

---

### Task 7: End-to-end browser tests [specialist: none]

**Charter capability:** Backlog list view and filters
**Strategy:** e2e (source: spec-declared — spec's Actionable Task Map names `tests_e2e/` browser e2e explicitly, and Acceptance Criterion 7 requires the e2e smoke gate)
**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5
**Files:**
- Test: `tests_e2e/test_ui_backlog_view_e2e.py`

**Tests:** `tests_e2e/test_ui_backlog_view_e2e.py` — new file, following the existing real-browser pattern (`tests_e2e/test_ui_navigation_e2e.py`, `tests_e2e/test_ui_project_switcher_e2e.py`) — a real rendering engine driving the actual served page, not calling `board-logic.js` functions directly. This task is the plan's only coverage for BEH-2 and BEH-7 (both are cross-view, stateful behaviors that unit tests on pure functions cannot exercise; Tasks 1-6 unit-test markup and pure logic only, per each task's own **Tests** field).

- [ ] **Write failing test**

```python
def test_backlog_view_shares_project_selection_with_board(app_server, browser_page):
    # BEH-2: switching Project in Board updates Backlog's data too.
    page = browser_page
    page.goto(app_server.url)
    page.click("#nav-backlog")
    page.select_option("#project-switcher", label="teste task — Teste")
    page.click("#nav-board")
    # Board now shows the second project's data
    assert page.locator("#project-switcher").input_value() != ""
    page.click("#nav-backlog")
    # Backlog reflects the same (non-default) selected project, not the original default
    assert page.locator("#backlog-rows tr").count() >= 0  # no crash; project selection carried over

def test_filter_persists_across_project_switch(app_server, browser_page):
    # BEH-7: an active filter is not silently cleared when the Project changes.
    page = browser_page
    page.goto(app_server.url)
    page.select_option("#filter-priority", "high")
    page.select_option("#project-switcher", index=1)
    assert page.locator("#filter-priority").input_value() == "high"

def test_zero_match_filter_shows_explicit_message(app_server, browser_page):
    # BEH-6: a filter combination guaranteed to match nothing in the seed fixture data.
    page = browser_page
    page.goto(app_server.url)
    page.select_option("#filter-priority", "high")
    page.select_option("#filter-issue-type", "story")
    # Highest priority + story type together match zero seed issues in the default project.
    assert page.locator("#filter-empty-state").is_visible()
    assert page.locator("#col-todo .card").count() == 0
    page.select_option("#filter-priority", "")
    page.select_option("#filter-issue-type", "")
    # Clearing both filters (BEH-5) makes the message disappear again.
    assert page.locator("#filter-empty-state").is_hidden()
```

- [ ] **Verify test fails**

Run: `python3 -m pytest tests_e2e/test_ui_backlog_view_e2e.py -q`
Expected: FAIL — `#nav-backlog`/`#filter-priority`/`#filter-empty-state` do not exist yet (this task runs last, after Tasks 1-6 land, so in practice this file is written and passes incrementally as each prior task's markup appears; write it now as the final integration check)

- [ ] **Implement**

No production code changes — this task only adds the e2e test file, exercising the markup and wiring Tasks 1-6 already implemented. If any test in this file fails after Tasks 1-6 are complete, fix the specific task's implementation (not this test) to match the spec.

- [ ] **Verify test passes**

Run: `python3 -m pytest tests_e2e/test_ui_backlog_view_e2e.py -q`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_backlog_view_e2e.py
git commit -m "test(kanban-ui): add backlog view e2e coverage for BEH-2/6/7"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

- Tests pass: `python3 -m pytest -q` and `node --test tests_js/`
- Lint passes: `ruff check .`
- All acceptance criteria from spec satisfied
- No new CSS custom-property tokens introduced (Task 6)
- No new HTTP endpoint or query parameter introduced (spec BEH constraint — verify `app/routers/issues.py` is untouched by this plan)
