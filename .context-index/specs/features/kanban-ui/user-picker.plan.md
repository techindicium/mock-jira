# Implementation Plan: User picker in issue forms

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/user-picker.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-06)
> **Platform:** vanilla JS / HTML / CSS (no build step), served as static assets by issue-tracker-api (FastAPI, Python 3.11)

**Goal:** Let a person fill the existing free-text `assignee` field in the create/edit-issue forms by picking a name from issue-tracker-api's User directory (`GET /users`), while the field stays fully free-text with no schema change.

**Architecture:** A single shared `<datalist>` element in `index.html`, populated once from `GET /users` during board init and reused by both `#issue-assignee` and `#edit-issue-assignee` via a `list` attribute — no new required field, no id/name changes, no polling. All new decision logic (option-building, graceful degradation) lives in testable pure functions in `board-logic.js`, following the same split this module already uses everywhere: `board-logic.js` holds pure logic covered by `tests_js/` unit tests, `board.js` holds the thin fetch/DOM wiring covered by real-browser Playwright e2e tests.

---

## File Structure

**Create:**
- `tests_js/user-picker-beh-2-3-user-options.test.js` — unit tests for the new option-builder pure function
- `tests_js/user-picker-beh-6-graceful-degradation.test.js` — unit tests for the safe-fallback pure function
- `tests_js/user-picker-beh-2-3-datalist-markup.test.js` — unit tests asserting the new markup is additive-only
- `tests_e2e/test_ui_user_picker_e2e.py` — real-browser tests for fetch-once/suggest/free-text/degrade

**Modify:**
- `static/js/board-logic.js` — add `buildUserOptionsHtml(users)` and `usersOrEmptyOnFailure(users)` pure functions
- `static/js/board.js` — fetch `GET /users` once during `init()`, cache in memory, populate the shared datalist, degrade gracefully on failure
- `static/index.html` — add one shared `<datalist id="user-directory-options">`; add `list="user-directory-options"` to `#issue-assignee` and `#edit-issue-assignee`
- `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` — relax the two assignee-input regexes to tolerate the additive `list` attribute while still asserting no `required` attribute and unchanged `id`/`name`

**Reference (read, do not modify):**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` — existing assignee-field contract (id/name/no-required)
- `.context-index/specs/features/issue-tracker-api/user-directory.spec.md` — `GET /users` response shape (`id`, `name`, `email?`, `role?`)
- `tests_e2e/test_ui_issue_forms_e2e.py` — existing create/edit-issue form e2e pattern to follow
- `tests_e2e/conftest.py` — `page`, `ui_board_server` fixtures (function-scoped, fresh DB, auto-seeds Users per `user-directory` BEH-9)
- `tests_e2e/test_ui_error_path_e2e.py` — route-interception pattern for simulating a failed fetch

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/kanban-ui/user-picker.spec.md` (BEH-2, BEH-3)
- Charter: `.context-index/specs/features/kanban-ui/charter.md` (capability: User picker in issue forms)
- Source files: `static/js/board-logic.js` (full read — follow existing pure-function style, e.g. `buildCardHtml`/`escapeHtml`)
- Sample pattern: `static/js/board-logic.js`'s `renderSwitcher`-adjacent option-building style (see `board.js`'s `renderSwitcher`, which builds `<option>` HTML from an array)

### Task 2 Context
- Spec: `.context-index/specs/features/kanban-ui/user-picker.spec.md` (BEH-6)
- Source files: `static/js/board-logic.js` (full read)
- Sibling pattern: `formatFetchError`/`isNotFoundError` in `board-logic.js` — small, single-purpose pure helpers around fetch-failure handling

### Task 3 Context
- Spec: `.context-index/specs/features/kanban-ui/user-picker.spec.md` (BEH-2, BEH-3, postconditions on unchanged id/name/required)
- Source files: `static/index.html` (full read), `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (assignee field contract), `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` (existing regex this task must keep passing in intent, adjusted in form)

### Task 4 Context
- Spec: `.context-index/specs/features/kanban-ui/user-picker.spec.md` (BEH-1, BEH-2, BEH-3, BEH-4, BEH-5, BEH-6 — full behavioral contract)
- Source files: `tests_e2e/test_ui_issue_forms_e2e.py` (pattern to follow), `tests_e2e/test_ui_error_path_e2e.py` (route-interception pattern), `tests_e2e/conftest.py` (`page`, `ui_board_server` fixtures)
- Depends on: Task 1, Task 2, Task 3 (the suite targets the real markup/ids those tasks add)

### Task 5 Context
- Spec: `.context-index/specs/features/kanban-ui/user-picker.spec.md` (BEH-1, BEH-6)
- Source files: `static/js/board.js` (full read — `init()`, `openEditIssue`, `document.getElementById("open-create-issue")` handler), `static/js/board-logic.js` (signatures of `buildUserOptionsHtml`, `usersOrEmptyOnFailure` from Tasks 1-2)
- Depends on: Task 4 (this task's "verify test fails / verify test passes" steps run Task 4's e2e suite)

---

## Parallelization

- Group A (independent): Task 1
- Group B (independent): Task 2
- Group C (sequential): Task 3 → Task 4 → Task 5

Groups A and B can run in parallel with each other and with Group C's Task 3 (no file overlap).
Task 4 (the e2e suite) needs Tasks 1, 2, and 3 done first so it targets real markup/ids rather
than ones that don't exist yet, so it is sequenced after all three — but it is written and
confirmed *failing* before Task 5's implementation runs (TDD test-first, at the plan level
rather than within a single task). Task 5 (the `board.js` wiring) needs Task 4's failing suite
to implement against and turn green.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Add `buildUserOptionsHtml` pure function | small | unit | — | 1 create, 1 modify |
| 2 | Add `usersOrEmptyOnFailure` pure function | small | unit | — | 1 create, 1 modify |
| 3 | Add datalist markup to index.html | small | unit | — | 1 create, 2 modify |
| 4 | Real-browser e2e coverage (written first, confirmed failing) | medium | e2e | Task 1, Task 2, Task 3 | 1 create, 0 modify |
| 5 | Wire fetch/cache/render into board.js (turns Task 4 green) | medium | unit (e2e-verified) | Task 4 | 0 create, 1 modify |

---

## Task Structure

### Task 1: Add `buildUserOptionsHtml` pure function [specialist: none]

**Charter capability:** User picker in issue forms
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/board-logic.js` (add function + export)
- Test: `tests_js/user-picker-beh-2-3-user-options.test.js`

**Tests:** `tests_js/user-picker-beh-2-3-user-options.test.js` — new suite (BEH-2, BEH-3).

**Context to load:**
- `static/js/board-logic.js` (existing `escapeHtml`, `buildCardHtml` for style)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildUserOptionsHtml } = require("../static/js/board-logic.js");

test("BEH-2/BEH-3: builds one <option> per User, escaped, value = name", () => {
  const html = buildUserOptionsHtml([
    { id: 1, name: "Mei Tan" },
    { id: 2, name: 'A & B <script>' },
  ]);
  assert.match(html, /<option value="Mei Tan">/);
  assert.match(html, /<option value="A &amp; B &lt;script&gt;">/);
});

test("BEH-2/BEH-3: skips Users with a blank/missing name", () => {
  const html = buildUserOptionsHtml([{ id: 1, name: "" }, { id: 2 }, { id: 3, name: "Kofi Adjei" }]);
  assert.equal((html.match(/<option/g) || []).length, 1);
  assert.match(html, /Kofi Adjei/);
});

test("BEH-2/BEH-3: returns an empty string for a non-array/empty input", () => {
  assert.equal(buildUserOptionsHtml(undefined), "");
  assert.equal(buildUserOptionsHtml([]), "");
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/user-picker-beh-2-3-user-options.test.js`
Expected: FAIL — `buildUserOptionsHtml is not a function` (not yet exported)

- [ ] **Implement**

```javascript
function buildUserOptionsHtml(users) {
  if (!Array.isArray(users)) return "";
  return users
    .filter((u) => u && u.name && u.name.trim())
    .map((u) => `<option value="${escapeHtml(u.name)}">`)
    .join("");
}
```

Add `buildUserOptionsHtml` to the module's returned object (the existing
`return { ... }` block at the bottom of `board-logic.js`).

- [ ] **Verify test passes**

Run: `node --test tests_js/user-picker-beh-2-3-user-options.test.js`
Expected: PASS

- [ ] **Commit**

Branch (if not already created): `feature/kanban-ui-user-picker`

```bash
git add static/js/board-logic.js tests_js/user-picker-beh-2-3-user-options.test.js
git commit -m "feat(kanban-ui): add buildUserOptionsHtml pure function"
```

---

### Task 2: Add `usersOrEmptyOnFailure` pure function [specialist: none]

**Charter capability:** User picker in issue forms
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/js/board-logic.js` (add function + export)
- Test: `tests_js/user-picker-beh-6-graceful-degradation.test.js`

**Tests:** `tests_js/user-picker-beh-6-graceful-degradation.test.js` — new suite (BEH-6).

**Context to load:**
- `static/js/board-logic.js` (existing `formatFetchError`, `isNotFoundError` for the small-single-purpose-helper style)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { usersOrEmptyOnFailure } = require("../static/js/board-logic.js");

test("BEH-6: a successful array of Users passes through unchanged", () => {
  const users = [{ id: 1, name: "Mei Tan" }];
  assert.deepEqual(usersOrEmptyOnFailure(users), users);
});

test("BEH-6: a failed fetch (no array) degrades to an empty array, never throws", () => {
  assert.deepEqual(usersOrEmptyOnFailure(undefined), []);
  assert.deepEqual(usersOrEmptyOnFailure(null), []);
  assert.deepEqual(usersOrEmptyOnFailure({ status: 500 }), []);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/user-picker-beh-6-graceful-degradation.test.js`
Expected: FAIL — `usersOrEmptyOnFailure is not a function`

- [ ] **Implement**

```javascript
function usersOrEmptyOnFailure(users) {
  return Array.isArray(users) ? users : [];
}
```

Add `usersOrEmptyOnFailure` to the module's returned object.

- [ ] **Verify test passes**

Run: `node --test tests_js/user-picker-beh-6-graceful-degradation.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js tests_js/user-picker-beh-6-graceful-degradation.test.js
git commit -m "feat(kanban-ui): add usersOrEmptyOnFailure graceful-degradation helper"
```

---

### Task 3: Add datalist markup to index.html [specialist: none]

**Charter capability:** User picker in issue forms
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Modify: `static/index.html` (add shared `<datalist>`, add `list` attribute to both assignee inputs)
- Modify: `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` (relax the two assignee regexes; assertions stay equally strict on `id`/`name`/absence of `required`)
- Test: `tests_js/user-picker-beh-2-3-datalist-markup.test.js`

**Tests:** `tests_js/user-picker-beh-2-3-datalist-markup.test.js` — new suite (BEH-2, BEH-3, and the "no id/name/required change" postcondition).

**Context to load:**
- `static/index.html` (full read)
- `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js` (existing regexes to relax)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-2: create-issue assignee input references the shared user datalist", () => {
  assert.match(html, /<input id="issue-assignee" name="assignee"[^>]*list="user-directory-options"[^>]*\/>/);
});

test("BEH-3: edit-issue assignee input references the same shared user datalist", () => {
  assert.match(html, /<input id="edit-issue-assignee" name="assignee"[^>]*list="user-directory-options"[^>]*\/>/);
});

test("exactly one shared, initially-empty datalist exists", () => {
  const matches = html.match(/<datalist id="user-directory-options"><\/datalist>/g) || [];
  assert.equal(matches.length, 1);
});

test("neither assignee input gained a required attribute", () => {
  const createTag = html.match(/<input id="issue-assignee"[^>]*\/>/)[0];
  const editTag = html.match(/<input id="edit-issue-assignee"[^>]*\/>/)[0];
  assert.doesNotMatch(createTag, /required/);
  assert.doesNotMatch(editTag, /required/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/user-picker-beh-2-3-datalist-markup.test.js`
Expected: FAIL — no `list="user-directory-options"` attribute yet, no `<datalist>` element yet

- [ ] **Implement**

In `static/index.html`:
1. Change `<label>Assignee <input id="issue-assignee" name="assignee" /></label>` to
   `<label>Assignee <input id="issue-assignee" name="assignee" list="user-directory-options" /></label>`.
2. Change `<label>Assignee <input id="edit-issue-assignee" name="assignee" /></label>` to
   `<label>Assignee <input id="edit-issue-assignee" name="assignee" list="user-directory-options" /></label>`.
3. Add one shared, empty datalist right before `</body>`:
   `<datalist id="user-directory-options"></datalist>`.

Then update `tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js`'s two assignee
assertions (currently exact-match self-closing regexes) to tolerate the additive `list`
attribute while still proving no `required` attribute was added, e.g.:

```javascript
test("create-issue optional fields carry no required attribute", () => {
  assert.match(html, /<textarea id="issue-description" name="description"><\/textarea>/);
  const assigneeTag = html.match(/<input id="issue-assignee"[^>]*\/>/)[0];
  assert.doesNotMatch(assigneeTag, /required/);
});
```

(Apply the same relaxation to the edit-issue block's existing `doesNotMatch(editBlock, /required/)`
assertion — it already tolerates any attribute since it checks the whole `<form>` block, so no
change is needed there; only the `create-issue optional fields` test's exact self-closing regex
needs relaxing.)

- [ ] **Verify test passes**

Run: `node --test tests_js/user-picker-beh-2-3-datalist-markup.test.js tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js`
Expected: PASS (both suites)

- [ ] **Commit**

```bash
git add static/index.html tests_js/user-picker-beh-2-3-datalist-markup.test.js tests_js/visual-refresh-beh-6-form-fields-unchanged.test.js
git commit -m "feat(kanban-ui): add shared user-directory datalist to issue forms"
```

---

### Task 4: Real-browser e2e coverage (written first, confirmed failing) [specialist: none]

**Charter capability:** User picker in issue forms
**Depends on:** Task 1, Task 2, Task 3 (the suite targets the real markup/ids those tasks add — the shared datalist, the `list` attribute on both assignee inputs)
**Strategy:** e2e (source: detected, confidence: high — file path `tests_e2e/**`)
**Files:**
- Create: `tests_e2e/test_ui_user_picker_e2e.py`

**Tests:** `tests_e2e/test_ui_user_picker_e2e.py` — new suite (BEH-1, BEH-2, BEH-3, BEH-4, BEH-5, BEH-6). This suite is written in THIS task and is deliberately red at the end of this task (Task 5's implementation does not exist yet) — that is the correct TDD state to commit at this point, not a mistake to fix here.

**Context to load:**
- `tests_e2e/test_ui_issue_forms_e2e.py` (pattern: `page`, `ui_board_server`, `page.wait_for_selector`, form fill/submit)
- `tests_e2e/test_ui_error_path_e2e.py` (pattern: `page.route(...).abort(...)`)
- `tests_e2e/conftest.py` (`ui_board_server` auto-seeds Users per `user-directory` BEH-9 on a fresh DB — real seeded names, e.g. "Mei Tan", are available without any test-side setup)

- [ ] **Write failing test**

```python
def test_assignee_datalist_is_populated_from_seeded_users(page, ui_board_server):
    users_requests = []
    page.on("request", lambda req: users_requests.append(req) if "/users" in req.url else None)

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")
    page.wait_for_function(
        "document.getElementById('user-directory-options').options.length > 0"
    )
    option_values = page.eval_on_selector_all(
        "#user-directory-options option", "opts => opts.map(o => o.value)"
    )
    assert len(option_values) > 0  # BEH-1/BEH-2: real seeded Users populate the suggestion list

    # BEH-1: fetched exactly once — opening the edit form must not trigger a second /users call.
    page.click("#cancel-create-issue")
    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    assert len(users_requests) == 1


def test_picking_a_suggested_name_still_submits_as_free_text(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")
    page.wait_for_function(
        "document.getElementById('user-directory-options').options.length > 0"
    )
    picked_name = page.eval_on_selector(
        "#user-directory-options option", "o => o.value"
    )

    page.fill("#issue-summary", "e2e-picker issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "medium")
    page.fill("#issue-assignee", picked_name)  # BEH-4: typing the exact suggested value
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-picker issue")')
    card_text = page.locator('#col-todo .card:has-text("e2e-picker issue")').inner_text()
    assert picked_name in card_text  # BEH-4/BEH-5: submitted exactly as free text


def test_arbitrary_free_text_assignee_still_accepted(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")

    page.fill("#issue-summary", "e2e-freetext issue")
    page.select_option("#issue-type", "bug")
    page.select_option("#issue-priority", "low")
    page.fill("#issue-assignee", "Someone Not In The Directory")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-freetext issue")')
    card_text = page.locator('#col-todo .card:has-text("e2e-freetext issue")').inner_text()
    assert "Someone Not In The Directory" in card_text  # BEH-5: no directory-match validation


def test_edit_issue_assignee_also_offers_suggestions(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    list_attr = page.eval_on_selector("#edit-issue-assignee", "el => el.getAttribute('list')")
    assert list_attr == "user-directory-options"  # BEH-3


def test_user_directory_failure_degrades_gracefully(page, ui_board_server):
    # Real aborted request, matching the existing error-path e2e pattern — not a mocked fetch.
    page.route("**/users", lambda route: route.abort("failed"))

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator("#board-error").is_hidden()  # BEH-6: no board-error banner for this

    page.click("#open-create-issue")
    page.fill("#issue-summary", "e2e-degraded issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "high")
    page.fill("#issue-assignee", "Still Works")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-degraded issue")')
    # form/board remained fully functional despite the /users failure
```

- [ ] **Verify test fails**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_user_picker_e2e.py`
Expected: 4 FAIL / 1 PASS — no datalist options, `/users` never called, `list` attribute
lookups return `None` (Tasks 1-3 add markup/pure-functions but nothing in `board.js` calls them
yet), so `test_assignee_datalist_is_populated_from_seeded_users`,
`test_picking_a_suggested_name_still_submits_as_free_text`,
`test_edit_issue_assignee_also_offers_suggestions`, and
`test_user_directory_failure_degrades_gracefully` all fail. `test_arbitrary_free_text_assignee_still_accepted`
is expected to already PASS — it only exercises the pre-existing, unmodified
`issue-crud-forms` free-text submit path, not anything Tasks 1-3/5 add.

- [ ] **Implement**

No production code changes in this task. This task's deliverable is the suite itself, committed
in its confirmed-red state — the implementation that turns it green is Task 5, which follows
immediately.

- [ ] **Verify test passes**

Not applicable to this task — see Task 5's "Verify test passes" step, which re-runs this exact
suite and expects all 5 tests to pass once `board.js` is wired.

- [ ] **Commit**

```bash
git add tests_e2e/test_ui_user_picker_e2e.py
git commit -m "test(kanban-ui): add failing real-browser e2e coverage for the user picker"
```

---

### Task 5: Wire fetch/cache/render into board.js (turns Task 4 green) [specialist: none]

**Charter capability:** User picker in issue forms
**Depends on:** Task 4 (this task implements against Task 4's already-committed, confirmed-failing e2e suite)
**Strategy:** unit (source: fallback, confidence: high) — the fetch/DOM wiring itself is verified end-to-end by Task 4's Playwright suite, consistent with every other `board.js` behavior in this module (no `tests_js/` suite requires `board.js` directly anywhere in this codebase; only `board-logic.js`'s pure functions and static markup are unit-tested).
**Files:**
- Modify: `static/js/board.js`

**Tests:** `tests_e2e/test_ui_user_picker_e2e.py` (already created by Task 4) — this task's correctness is exercised there; no new `tests_js/` suite targets `board.js` directly, matching the established pattern (see e.g. `init()`/`onCardClick` in `board.js`, which are e2e-only today too).

**Context to load:**
- `static/js/board.js` (full read — `init()`, `renderSwitcher`, `openEditIssue`, the `open-create-issue` click handler)
- `static/js/board-logic.js` (signatures: `buildUserOptionsHtml`, `usersOrEmptyOnFailure`)
- `tests_e2e/test_ui_user_picker_e2e.py` (the failing suite from Task 4 this task must turn green)

- [ ] **Write failing test**

Already written and committed in Task 4 (`tests_e2e/test_ui_user_picker_e2e.py`). Re-confirm it
still fails against the current `board.js` before implementing:

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_user_picker_e2e.py`
Expected: FAIL (same 5 failures as Task 4's "Verify test fails" step)

- [ ] **Implement**

In `static/js/board.js`:

```javascript
let cachedUsers = [];

function renderUserDatalist(users) {
  const datalist = document.getElementById("user-directory-options");
  if (datalist) datalist.innerHTML = BoardLogic.buildUserOptionsHtml(users);
}

async function loadUsers() {
  let users;
  try {
    users = await fetchJson("/users");
  } catch (_err) {
    users = null; // BEH-6: degrade silently — no board-error banner for this convenience source
  }
  cachedUsers = BoardLogic.usersOrEmptyOnFailure(users);
  renderUserDatalist(cachedUsers);
}
```

Call `loadUsers()` once, fire-and-forget (not awaited — it must never delay board rendering),
near the top of `init()`:

```javascript
async function init() {
  loadUsers(); // BEH-1: fetch GET /users exactly once per board load; never blocks board render
  let projects;
  ...
```

No other change is needed — `cachedUsers` backs the datalist for the lifetime of the page load,
reused by both the create-issue form (already open before/after this fetch resolves — the
datalist repopulates whenever `loadUsers()` resolves, so an already-open form's suggestions
appear as soon as they arrive) and the edit-issue form opened via `openEditIssue`.

Add `loadUsers` to the `window.BoardApp` export object for e2e debuggability parity with the
rest of the module's exports (optional but consistent with existing style).

- [ ] **Verify test passes**

Run: `.venv/bin/python3 -m pytest -q tests_e2e/test_ui_user_picker_e2e.py`
Expected: PASS (all 5 tests)

- [ ] **Commit**

```bash
git add static/js/board.js
git commit -m "feat(kanban-ui): fetch and cache the User directory once, populate the assignee datalist"
```

---

## Quality Gates

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are recorded in the validation report (`.validate.md`), not in this plan.

Per `.context-index/governance/gates.yaml`:

- Test Suite: `.venv/bin/python3 -m pytest -q` (required, error severity)
- Linter: `.venv/bin/ruff check .` (required, error severity)
- JS Unit Tests: `node --test tests_js/**/*.test.js` (required, error severity)
- E2E API Smoke Suite: `.venv/bin/python3 -m pytest -q tests_e2e/` (not required — e2e tier default, severity: warning — but must still be run and reported per this repo's established practice of full regression on every kanban-ui change)
- All acceptance criteria from `user-picker.spec.md` satisfied
