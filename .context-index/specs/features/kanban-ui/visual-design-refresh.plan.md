# Implementation Plan: Visual design refresh — dispatch-board identity

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-06)
> **Platform:** Plain HTML/CSS/vanilla JS (no build step, no framework), served as static assets by `issue-tracker-api`'s FastAPI process.

**Goal:** Restyle kanban-ui's existing board/forms into a ticket/dispatch-board visual identity
(ink/rail/paper palette, priority-striped ticket cards, system font stacks only) with zero change
to `board-view`/`issue-crud-forms`/`ui-e2e`'s DOM hooks or data flow.

**Architecture:** Pure presentation change. `static/css/board.css` carries the new token system and
nearly all of the visual work. `static/js/board-logic.js` gets small, pure additions (a
priority→stripe attribute mapper with an "unknown" fallback, a `columnCounts()` helper) that stay
unit-testable exactly like its existing exports. `static/js/board.js` wires the count badge and the
new attribute into the existing render path. `static/index.html` gets two additive, non-breaking
changes: sentence-case column header text plus a small count-badge element per column, and a
non-semantic wrapper `<div>` around `#project-switcher` for the plate/tab styling hook — the
`<select id="project-switcher">` element itself, its id, and its `change` wiring are untouched.

---

## File Structure

**Modify:**
- `static/css/board.css` — full restyle: design tokens, page/rail/paper surfaces, card stripe,
  switcher plate, form palette, focus-visible, reduced-motion.
- `static/js/board-logic.js` — add `priorityStripeAttr(priority)`, `columnCounts(grouped)`; extend
  `buildCardHtml` to render the escaped issue key and the `data-priority` attribute.
- `static/js/board.js` — call `BoardLogic.columnCounts` after each render and write counts into the
  new badge elements; no change to existing fetch/mutation logic.
- `static/index.html` — sentence-case column header text ("To do", "In progress", "Done"), add one
  `<span class="col-count">` badge element per column header, wrap `#project-switcher` in
  `<div class="switcher-plate">`.

**Create (tests):**
- `tests_js/visual-refresh-beh-1-design-tokens.test.js`
- `tests_js/visual-refresh-beh-2-priority-stripe.test.js`
- `tests_js/visual-refresh-beh-3-issue-key.test.js`
- `tests_js/visual-refresh-beh-4-column-count.test.js`
- `tests_js/visual-refresh-beh-5-switcher-plate.test.js`
- `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js`
- `tests_js/visual-refresh-beh-7-8-accessibility-css.test.js`
- `tests_js/visual-refresh-no-cdn-fonts.test.js`

**Reference (read, do not modify):**
- `static/index.html`, `static/js/board.js`, `static/js/board-logic.js`, `static/css/board.css` (current state)
- `tests_e2e/test_ui_*.py` — real-browser locators that must keep working unmodified
- `.context-index/specs/features/kanban-ui/board-view.spec.md`, `issue-crud-forms.spec.md`, `ui-e2e.spec.md` — DOM-hook contracts this refresh must not break

## Context Packets

### Task 1 Context
- Spec: `visual-design-refresh.spec.md` (BEH-1, Visual Expectations "Page background"/"Header")
- Charter capability: "Visual design refresh"
- Source files: `static/css/board.css` (full, current content)

### Task 2 Context
- Spec: `visual-design-refresh.spec.md` (BEH-4, Visual Expectations "Columns")
- Source files: `static/index.html` (full), `static/js/board.js` (full), `static/js/board-logic.js` (full — `BOARD_COLUMNS`)
- Review note SA-1: verify header/badge text contrast against `--rail` meets WCAG AA.

### Task 3 Context
- Spec: `visual-design-refresh.spec.md` (BEH-2, BEH-3, Error Cases row 1 `UI_STYLE_UNKNOWN_PRIORITY`)
- Source files: `static/js/board-logic.js` (full — `buildCardHtml`, `escapeHtml`), `static/css/board.css`
- Sibling spec: `board-view.spec.md` BEH-2 (card fields), `tests_js/beh-2-render-columns.test.js` (existing `buildCardHtml` contract — must keep passing)
- Review note SEC-1: new interpolated content (issue key) MUST go through `escapeHtml()`.

### Task 4 Context
- Spec: `visual-design-refresh.spec.md` (BEH-5)
- Source files: `static/index.html` (`#project-switcher` block), `static/css/board.css`
- Sibling spec: `board-view.spec.md` BEH-3/BEH-4 (switcher's `change` event contract — unchanged)

### Task 5 Context
- Spec: `visual-design-refresh.spec.md` (BEH-6)
- Source files: `static/index.html` (create-project/create-issue/edit-issue forms), `static/css/board.css`
- Sibling spec: `issue-crud-forms.spec.md` (field ids/required attributes this task must not touch)

### Task 6 Context
- Spec: `visual-design-refresh.spec.md` (BEH-7, BEH-8)
- Source files: `static/css/board.css`

### Task 7 Context
- Spec: `visual-design-refresh.spec.md` (Postconditions — "no network request for fonts", constitution "Fixture-backed, offline only")
- Source files: `static/index.html`, `static/css/board.css`

### Task 8 Context
- All specs in module (`board-view`, `issue-crud-forms`, `ui-e2e`) — full regression pass
- `tests_e2e/test_ui_*.py`, `tests_js/*.test.js`, `tests/test_static_assets.py`

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 (all touch `static/css/board.css`; ordering avoids merge conflicts within the plan and lets each task's visual layer build on the last)
- Group B (independent): Task 8 (runs only after Group A completes — regression/verification pass, no production file overlap)

Group A is inherently sequential given the shared-file constraint; Group B is really "runs last", not parallel with A, and is placed in its own group only to keep it out of A's numbered chain.

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Design tokens + global surfaces | small | unit | — | 0 create, 1 modify |
| 2 | Column panel, header, count badge | medium | unit | Task 1 | 1 create, 4 modify |
| 3 | Card restyle + priority stripe + issue key | medium | unit | Task 1 | 2 create, 2 modify |
| 4 | Project switcher plate styling | small | unit | Task 1 | 1 create, 2 modify |
| 5 | Form restyle (create-project/create-issue/edit-issue) | medium | unit | Task 1 | 1 create, 1 modify |
| 6 | Focus-visible + reduced-motion accessibility | small | unit | Task 1 | 1 create, 1 modify |
| 7 | Offline/no-CDN-font guard | small | unit | Task 1 | 1 create, 0 modify (verification only) |
| 8 | Full regression pass (JS unit, static-asset, real-browser e2e) | small | unit | Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7 | 0 create, 0 modify |

## Task Structure

### Task 1: Design tokens + global surfaces [specialist: none]

**Charter capability:** Visual design refresh
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/css/board.css` (add `:root` tokens; restyle `body`, `header`, `#board`)
- Test: `tests_js/visual-refresh-beh-1-design-tokens.test.js`

**Tests:** `tests_js/visual-refresh-beh-1-design-tokens.test.js` — create. Reads `board.css` as text
and asserts it declares `--ink: #16261f`, `--rail: #2f4a3e`, `--paper: #f1ecdd`,
`--stamp-red: #a3402f`, `--stamp-gold: #b98a2e`, `--stamp-green: #4c7a5e`, `--ink-line: #55483a`
(case-insensitive hex match), and that the `body` rule references `var(--ink)` for `background`.

**Context to load:**
- `visual-design-refresh.spec.md` BEH-1 and Visual Expectations "Page background"/"Header"

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-1: design tokens are declared in :root", () => {
  const tokens = ["--ink:\\s*#16261f", "--rail:\\s*#2f4a3e", "--paper:\\s*#f1ecdd",
    "--stamp-red:\\s*#a3402f", "--stamp-gold:\\s*#b98a2e", "--stamp-green:\\s*#4c7a5e",
    "--ink-line:\\s*#55483a"];
  for (const t of tokens) assert.match(css.toLowerCase(), new RegExp(t.toLowerCase()));
});

test("BEH-1: page background uses the --ink token", () => {
  assert.match(css, /body\s*{[^}]*background:\s*var\(--ink\)/s);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/visual-refresh-beh-1-design-tokens.test.js`
Expected: FAIL — tokens not yet declared, `body` still uses the old `#f5f6f8` background.

- [ ] **Implement**

Add the `:root` token block to `board.css` and restyle `body`/`header`/`#board` per the spec's
Visual Expectations. Keep `[hidden] { display: none !important; }` untouched (BEH-unrelated, and
depended on by `board.js`'s hide/show logic).

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-1-design-tokens.test.js`
Expected: PASS

- [ ] **Commit**

Branch: `feature/kanban-ui-visual-refresh` (already created)

```bash
git add static/css/board.css tests_js/visual-refresh-beh-1-design-tokens.test.js
git commit -m "feat(kanban-ui): add dispatch-board design tokens, restyle page shell" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md"
```

---

### Task 2: Column panel, header, count badge [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (sentence-case header text; add `<span class="col-count">` per column)
- Modify: `static/js/board-logic.js` (add `columnCounts(grouped)`; sentence-case `BOARD_COLUMNS[].label`)
- Modify: `static/js/board.js` (write counts into the new badge elements after every render)
- Modify: `static/css/board.css` (restyle `.column`, `.column-header`, `.col-count`)
- Test: `tests_js/visual-refresh-beh-4-column-count.test.js`

**Tests:** `tests_js/visual-refresh-beh-4-column-count.test.js` — create. Unit-tests the new pure
`columnCounts(grouped)` export against `groupIssuesByStatus`'s output shape.

**Context to load:**
- `visual-design-refresh.spec.md` BEH-4, Visual Expectations "Columns"
- Review note SA-1 (rail-surface contrast) — apply during CSS implementation, verified visually in Task 8.

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { columnCounts, groupIssuesByStatus } = require("../static/js/board-logic.js");

test("BEH-4: columnCounts returns the issue count per fixed column", () => {
  const grouped = groupIssuesByStatus([
    { id: 1, status: "todo" }, { id: 2, status: "todo" }, { id: 3, status: "done" },
  ]);
  assert.deepEqual(columnCounts(grouped), { todo: 2, in_progress: 0, done: 1 });
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/visual-refresh-beh-4-column-count.test.js`
Expected: FAIL — `columnCounts` is not exported yet.

- [ ] **Implement**

In `board-logic.js`, add:
```javascript
function columnCounts(grouped) {
  const counts = {};
  for (const col of BOARD_COLUMNS) counts[col.status] = grouped[col.status].length;
  return counts;
}
```
Export it from the `BoardLogic` object. Update `BOARD_COLUMNS[].label` to sentence case ("To do",
"In progress", "Done") for consistency (the field is currently unused by the renderer but is the
logical source of truth for the label text).

In `index.html`, wrap each column's `<h2>` with a small header row and add the badge span, e.g.:
```html
<section class="column" data-status="todo">
  <div class="column-header"><h2>To do</h2><span class="col-count" id="count-todo"></span></div>
  <div id="col-todo" class="cards"></div>
</section>
```
(repeat with sentence case for `in_progress`/`done`). Do not change `id="col-todo"` etc. — those are
the existing DOM hooks `tests_e2e`/`tests_js` depend on.

In `board.js`, after `renderColumns(grouped)` runs (both in `renderBoardState` and in
`onColumnDrop`'s optimistic/revert paths), call `BoardLogic.columnCounts(grouped)` and write each
count into `#count-<status>`.

Restyle `.column`, `.column-header`, `.col-count` in `board.css` per Visual Expectations (rail
panel, brass rule under the header row, mono count badge).

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-4-column-count.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/js/board-logic.js static/js/board.js static/css/board.css \
  tests_js/visual-refresh-beh-4-column-count.test.js
git commit -m "feat(kanban-ui): restyle columns as rail panels, add mono issue-count badge" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/board-view.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

> Note: `static/index.html`, `static/js/board.js`, `static/js/board-logic.js`, `static/css/board.css`
> are all claimed by `board-view.spec.md` and/or `issue-crud-forms.spec.md`/`ui-e2e.spec.md`'s
> stamped `source-manifest.files`. Every commit in this plan that touches any of these files carries
> `Spec:` trailers for `visual-design-refresh.spec.md` **and** every other spec whose manifest lists
> the touched file(s), per the commit-msg hook. Re-stamp those specs' source manifests once all
> tasks land (see Step 5 of the overall workflow, run once at the end rather than per-task).

---

### Task 3: Card restyle + priority stripe + issue key [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/board-logic.js` (`priorityStripeAttr`, extend `buildCardHtml`)
- Modify: `static/css/board.css` (`.card`, `.card-key`, stripe colors via `[data-priority]`)
- Test: `tests_js/visual-refresh-beh-2-priority-stripe.test.js`, `tests_js/visual-refresh-beh-3-issue-key.test.js`

**Tests:**
`tests_js/visual-refresh-beh-2-priority-stripe.test.js` — create. Asserts `buildCardHtml` emits
`data-priority="high"/"medium"/"low"` for known priorities and `data-priority="unknown"` for a
missing/unrecognized value (Error Case `UI_STYLE_UNKNOWN_PRIORITY`).
`tests_js/visual-refresh-beh-3-issue-key.test.js` — create. Asserts `buildCardHtml` renders the
issue's escaped `key` and that `tests_js/beh-2-render-columns.test.js`'s existing assertions (which
do not pass a `key` field) still pass unmodified — i.e., a missing `key` renders as empty, not the
literal string `"undefined"`.

**Context to load:**
- `visual-design-refresh.spec.md` BEH-2, BEH-3, Error Cases row 1
- `tests_js/beh-2-render-columns.test.js` (existing contract — must not regress)
- Review note SEC-1: route the key through `escapeHtml()`, exactly like the other fields.

- [ ] **Write failing test**

```javascript
// tests_js/visual-refresh-beh-2-priority-stripe.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCardHtml } = require("../static/js/board-logic.js");

test("BEH-2: known priorities get their own data-priority attribute", () => {
  for (const p of ["low", "medium", "high"]) {
    const html = buildCardHtml({ id: 1, summary: "x", issue_type: "task", priority: p, assignee: "" });
    assert.match(html, new RegExp(`data-priority="${p}"`));
  }
});

test("UI_STYLE_UNKNOWN_PRIORITY: unrecognized priority falls back to a neutral attribute", () => {
  const html = buildCardHtml({ id: 1, summary: "x", issue_type: "task", priority: "urgent!!", assignee: "" });
  assert.match(html, /data-priority="unknown"/);
});
```

```javascript
// tests_js/visual-refresh-beh-3-issue-key.test.js
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCardHtml } = require("../static/js/board-logic.js");

test("BEH-3: card markup includes the escaped issue key", () => {
  const html = buildCardHtml({ id: 1, key: "ASSIST-42", summary: "x", issue_type: "task", priority: "low", assignee: "" });
  assert.match(html, /ASSIST-42/);
});

test("BEH-3: a missing key renders as empty, not the string undefined", () => {
  const html = buildCardHtml({ id: 1, summary: "x", issue_type: "task", priority: "low", assignee: "" });
  assert.doesNotMatch(html, /undefined/);
});

test("BEH-3: issue key is HTML-escaped like every other interpolated field", () => {
  const html = buildCardHtml({ id: 1, key: "<script>", summary: "x", issue_type: "task", priority: "low", assignee: "" });
  assert.doesNotMatch(html, /<script>/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/visual-refresh-beh-2-priority-stripe.test.js tests_js/visual-refresh-beh-3-issue-key.test.js`
Expected: FAIL — no `data-priority` attribute, no key rendered yet.

- [ ] **Implement**

```javascript
const KNOWN_PRIORITIES = ["low", "medium", "high"];
function priorityStripeAttr(priority) {
  return KNOWN_PRIORITIES.includes(priority) ? priority : "unknown";
}

function buildCardHtml(issue) {
  return (
    `<article class="card" data-issue-id="${issue.id}" data-priority="${priorityStripeAttr(issue.priority)}" draggable="true">` +
    `<p class="card-key">${escapeHtml(issue.key || "")}</p>` +
    `<h3>${escapeHtml(issue.summary)}</h3>` +
    `<p class="card-meta">${escapeHtml(issue.issue_type)} &middot; ` +
    `${escapeHtml(issue.priority)} &middot; ` +
    `${escapeHtml(issue.assignee || "Unassigned")}</p>` +
    `</article>`
  );
}
```
Export `priorityStripeAttr`. In `board.css`, restyle `.card` (paper surface, sharp corners, hard
offset shadow), add `.card-key` (mono, small), and the stripe via `border-left` keyed on
`[data-priority="high|medium|low|unknown"]` (unknown → a neutral `--ink-line`-toned stripe, never no
stripe/broken style — satisfies `UI_STYLE_UNKNOWN_PRIORITY`). Constrain card width/wrapping
(`overflow-wrap: anywhere`, no fixed-height overflow) so long summary/assignee text never spills
into a neighboring column (`UI_STYLE_TEXT_OVERFLOW`).

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-2-priority-stripe.test.js tests_js/visual-refresh-beh-3-issue-key.test.js tests_js/beh-2-render-columns.test.js`
Expected: PASS (including the pre-existing `beh-2-render-columns.test.js`, unmodified).

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/css/board.css \
  tests_js/visual-refresh-beh-2-priority-stripe.test.js tests_js/visual-refresh-beh-3-issue-key.test.js
git commit -m "feat(kanban-ui): add priority-stripe card treatment and mono issue key" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/board-view.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

---

### Task 4: Project switcher plate styling [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (wrap `#project-switcher` in `<div class="switcher-plate">`)
- Modify: `static/css/board.css` (`.switcher-plate`, `appearance: none` + custom chrome on the `<select>`)
- Test: `tests_js/visual-refresh-beh-5-switcher-plate.test.js`

**Tests:** `tests_js/visual-refresh-beh-5-switcher-plate.test.js` — create. Reads `index.html` and
asserts: (a) `id="project-switcher"` is still present on a `<select>` element, (b) it is now
wrapped by an element carrying `class="switcher-plate"`, (c) no other attribute on the `<select>`
(`aria-label`) was removed.

**Context to load:**
- `visual-design-refresh.spec.md` BEH-5
- `board-view.spec.md` BEH-3/BEH-4 (switcher `change`-event contract — unaffected by a wrapper div)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-5: project switcher is wrapped in a styled plate but stays a real <select>", () => {
  assert.match(html, /<div class="switcher-plate">[\s\S]*?<select[^>]*id="project-switcher"[^>]*>[\s\S]*?<\/select>[\s\S]*?<\/div>/);
  assert.match(html, /aria-label="Select project"/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/visual-refresh-beh-5-switcher-plate.test.js`
Expected: FAIL — no wrapper yet.

- [ ] **Implement**

Wrap the existing `<select id="project-switcher" ...>` in `<div class="switcher-plate">...</div>`
in `index.html`, no attribute changes to the `<select>` itself. In `board.css`, style
`.switcher-plate` (bordered plate, `--ink-line` border) and the `<select>` inside it
(`appearance: none`, brass/mono accent, custom arrow via a CSS background image or `::after` on
the wrapper — not via injected markup inside the `<select>`, which cannot contain non-`<option>`
children).

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-5-switcher-plate.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/index.html static/css/board.css tests_js/visual-refresh-beh-5-switcher-plate.test.js
git commit -m "feat(kanban-ui): style project switcher as a bordered plate control" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/board-view.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

---

### Task 5: Form restyle (create-project/create-issue/edit-issue) [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/css/board.css` (form/button palette, sharp corners, `--ink-line` borders)
- Test: `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js`

**Tests:** `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` — create. Reads
`index.html` and asserts every field id/name this repo's specs depend on is still present with its
`required` attribute unchanged: `project-key`/`key` (required), `project-name`/`name` (required),
`issue-summary`/`summary` (required), `issue-type`/`issue_type` (required), `issue-priority`/`priority`
(required), `issue-description`/`description` (no required), `issue-assignee`/`assignee` (no
required), and the parallel `edit-issue-*` fields with none marked required (per
`issue-crud-forms.spec.md` Preconditions: "The edit-issue form has no required fields").

**Context to load:**
- `visual-design-refresh.spec.md` BEH-6
- `issue-crud-forms.spec.md` Preconditions (required-field contract)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-6: create-issue required fields are unchanged", () => {
  assert.match(html, /<input id="issue-summary" name="summary" required/);
  assert.match(html, /<select id="issue-type" name="issue_type" required/);
  assert.match(html, /<select id="issue-priority" name="priority" required/);
});

test("BEH-6: edit-issue fields carry no required attribute", () => {
  const editBlock = html.slice(html.indexOf('id="edit-issue-form"'), html.indexOf("</form>", html.indexOf('id="edit-issue-form"')));
  assert.doesNotMatch(editBlock, /required/);
});
```

(This test is written against the CURRENT markup, so it should already pass before CSS-only
changes — its purpose is a regression guard proving Task 5's restyle touches CSS only. Confirm it
passes both before and after the CSS edit.)

- [ ] **Verify test fails**

This test is expected to already PASS against current markup (no HTML change planned for this
task). Run it once to confirm it passes now, establishing the regression baseline; the "RED" step
for this task is trivial by design — the risk here is a CSS change accidentally requiring an HTML
attribute change, which this test would catch.

- [ ] **Implement**

Restyle `#create-project`, `#create-issue`, `#edit-issue` sections, their `label`/`input`/`select`/
`textarea`, and their buttons in `board.css`: `--paper` background, `--ink-line` 1px borders, sharp
corners, primary submit button in `--rail`/`--stamp-gold`, cancel/secondary outlined, delete button
in a `--stamp-red`-toned treatment. No HTML attribute changes.

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js`
Expected: PASS (unchanged before and after — confirms the restyle stayed CSS-only).

- [ ] **Commit**

```bash
git add static/css/board.css tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js
git commit -m "feat(kanban-ui): restyle project/issue forms to the dispatch-board palette" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/board-view.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

---

### Task 6: Focus-visible + reduced-motion accessibility [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/css/board.css` (`:focus-visible` rule, `@media (prefers-reduced-motion: reduce)`)
- Test: `tests_js/visual-refresh-beh-7-8-accessibility-css.test.js`

**Tests:** `tests_js/visual-refresh-beh-7-8-accessibility-css.test.js` — create. Asserts `board.css`
contains a `:focus-visible` rule with a non-`none` `outline` declaration, and a
`prefers-reduced-motion: reduce` media query.

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-7: a deliberate :focus-visible style is declared", () => {
  assert.match(css, /:focus-visible\s*{[^}]*outline:\s*(?!none)/s);
});

test("BEH-8: prefers-reduced-motion guard is present", () => {
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/visual-refresh-beh-7-8-accessibility-css.test.js`
Expected: FAIL — neither rule exists yet.

- [ ] **Implement**

Add a `:focus-visible` rule (e.g. `outline: 2px solid var(--stamp-gold); outline-offset: 2px;`)
applied broadly (`button, input, select, a, .card`). Add any hover/lift transitions guarded inside
`@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }`.

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-beh-7-8-accessibility-css.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/css/board.css tests_js/visual-refresh-beh-7-8-accessibility-css.test.js
git commit -m "feat(kanban-ui): add deliberate focus-visible and reduced-motion styling" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/board-view.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

---

### Task 7: Offline/no-CDN-font guard [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Verify only: `static/index.html`, `static/css/board.css` (no CDN `<link>`/`@font-face` should exist by construction — this task is a regression guard, not new styling)
- Test: `tests_js/visual-refresh-no-cdn-fonts.test.js`

**Tests:** `tests_js/visual-refresh-no-cdn-fonts.test.js` — create. Asserts `index.html` has no
`<link ... href="https://fonts.googleapis.com...">` (or any external stylesheet link) and
`board.css` has no `@font-face` referencing a remote `url(http...)`, and that every `font-family`
declaration's final fallback is a generic family (`sans-serif`/`monospace`).

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("offline-only: no external font stylesheet link in index.html", () => {
  assert.doesNotMatch(html, /<link[^>]+href=["']https?:\/\//);
});

test("offline-only: no remote @font-face in board.css", () => {
  assert.doesNotMatch(css, /@font-face[^}]*url\(\s*["']?https?:\/\//s);
});

test("offline-only: font-family stacks end in a generic system fallback", () => {
  const families = [...css.matchAll(/font-family:\s*([^;]+);/g)].map((m) => m[1]);
  for (const stack of families) assert.match(stack, /sans-serif|monospace/);
});
```

- [ ] **Verify test fails**

Run this against the current `index.html`/`board.css` first — expected to already PASS (the
codebase has never had a CDN font). This task's purpose is to lock that invariant in as an
executable regression guard before the rest of this plan's CSS work lands, per the constitution's
"Fixture-backed, offline only" principle.

- [ ] **Implement**

No production change expected. If any prior task (1-6) introduced a `font-family` stack without a
generic fallback, fix it here so this test passes.

- [ ] **Verify test passes**

Run: `node --test tests_js/visual-refresh-no-cdn-fonts.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add tests_js/visual-refresh-no-cdn-fonts.test.js
git commit -m "test(kanban-ui): lock in offline-only font-stack guard" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md"
```

---

### Task 8: Full regression pass (JS unit, static-asset, real-browser e2e) [specialist: none]

**Charter capability:** Visual design refresh
**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5, Task 6, Task 7
**Strategy:** unit (source: fallback, confidence: high)
**Files:** none (verification task — fixes locators only if a real regression is found)

**Tests:** `tests_js/*.test.js` (all), `tests/test_static_assets.py`, `tests_e2e/test_ui_*.py` (all)
— every existing suite in the module, run in full.

- [ ] **Write failing test**

N/A — this task runs the existing suites, it does not author a new one. If any existing e2e
locator turns out to depend on the exact prior markup/CSS in a way this plan did not anticipate,
write the minimal locator fix here (never weaken an assertion) and note it as a plan deviation.

- [ ] **Run full suite**

```bash
.venv/bin/python3 -m pytest -q
.venv/bin/ruff check .
node --test "tests_js/**/*.test.js"
.venv/bin/python3 -m pytest -q tests_e2e/
```

Expected: all green. Take Playwright screenshots of the live board (via `tests_e2e/browser.py`'s
fixtures or a throwaway script) at this point for a final self-critique against the spec's Visual
Expectations section before calling the capability implemented.

- [ ] **Commit**

Only if a locator fix was needed:

```bash
git add tests_e2e/<fixed file>
git commit -m "fix(kanban-ui): update e2e locator for the restyled markup" \
  -m "Spec: .context-index/specs/features/kanban-ui/visual-design-refresh.spec.md" \
  -m "Spec: .context-index/specs/features/kanban-ui/ui-e2e.spec.md"
```

---

## Quality Gates

Per `.context-index/governance/gates.yaml`:

- `test` (required, error): `.venv/bin/python3 -m pytest -q`
- `lint` (required, error): `.venv/bin/ruff check .`
- `test-js` (required, error): `node --test "tests_js/**/*.test.js"`
- `e2e-smoke` (not required, severity warning): `.venv/bin/python3 -m pytest -q tests_e2e/`

All acceptance criteria from `visual-design-refresh.spec.md` must be satisfied. `/adev:validate`
verifies the full quality gate suite and records results in `visual-design-refresh.validate.md`.
