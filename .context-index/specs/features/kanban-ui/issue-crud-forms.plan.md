<!-- partial_schema: plan@1 -->

# Implementation Plan: Issue create, edit, delete, and column move

> **Methodology:** adev
> **Charter:** .context-index/specs/features/kanban-ui/charter.md
> **Spec:** .context-index/specs/features/kanban-ui/issue-crud-forms.spec.md
> **Review:** PASS_WITH_NOTES (2026-09-05)
> **Platform:** FastAPI (Python 3.11) backend; static HTML/CSS/vanilla JS frontend with zero
> build step; Node.js built-in test runner (`node --test`, no npm dependencies) for JS unit tests.

**Goal:** Extend the existing kanban board with create/edit/delete forms for Issues and a
column-move interaction, all backed by `issue-tracker-api`'s `issue-lifecycle` endpoints, with
optimistic-then-reconcile behavior for the drag move and a shared revert/error path for every
mutation.

**Architecture:** This spec extends `board-view`'s established split unchanged: pure, dependency-
free logic (form validation, payload building, field diffing, error classification, and the
column-move state transform) lives in `static/js/board-logic.js` and is unit-tested with Node's
built-in test runner; `static/js/board.js` stays thin DOM/fetch glue that calls the same-origin
`/issues/{id}` endpoints and wires pure-function results into the DOM — consistent with
`board-view.plan.md`'s Architecture note and this project's disabled visual/browser-review checks
(`governance/validate.yaml`, `governance/review.yaml`), so no automated DOM/browser verification is
expected here either. Per the review's `PASS_WITH_NOTES`, the required create-issue fields are
exactly `issue-lifecycle`'s `POST /issues` requirements (`summary`, `issue_type`, `priority`, with
`project_id` implicit from the selected board); the edit-issue form has no required fields; a new
Issue's `status` always defaults to `todo` server-side, so the create flow never sends `status`
and always renders the new card in the `todo` column; and the 404 case
(`PATCH`/`DELETE` on an id the API no longer has) is a deliberate, explicitly-called-out exception
to the generic BEH-5 revert rule — the card is removed, not reverted, because 404 means it is
already gone server-side.

Of this spec's five behaviors most tightly coupled to a shared mechanism, BEH-5 (revert-on-failure
plus the 404 exception) is pulled to the front of the task order rather than left last as in the
spec's own Actionable Task Map: `PATCH`/`DELETE` calls in Tasks 4-6 (edit, move, delete) all need
the same error-classification helpers, so building them first keeps every later task's "Verify
test passes" step meaningful rather than referencing not-yet-written glue. Only the column-move
interaction (BEH-3) is genuinely optimistic (the card's DOM position changes before the server
confirms); the create/edit/delete flows never mutate the board's rendered state ahead of a
successful response, so for those three, "reverting an optimistic change" reduces to "leave the
prior state alone and show an inline or banner error" — there is nothing to move back.

---

## File Structure

**Create:**
- `tests_js/issue-crud-beh-5-error-handling.test.js` — Node `node:test`: 404-vs-generic mutation
  error classification and messaging (BEH-5, Error Cases row 2 `UI_ISSUE_NOT_FOUND`).
- `tests_js/issue-crud-beh-6-create-validation.test.js` — Node `node:test`: create-issue form
  client-side required-field validation (BEH-6).
- `tests_js/issue-crud-beh-1-create-issue.test.js` — Node `node:test`: create-issue payload
  assembly, always-`todo` placement (BEH-1).
- `tests_js/issue-crud-beh-2-edit-issue.test.js` — Node `node:test`: edit-issue field diffing to a
  minimal non-status patch payload (BEH-2).
- `tests_js/issue-crud-beh-3-column-move.test.js` — Node `node:test`: optimistic status-move state
  transform and its exact-reversal on failure (BEH-3).
- `tests_js/issue-crud-beh-4-delete-issue.test.js` — Node `node:test`: delete-by-id state removal,
  reused for both the success path and the 404 exception path (BEH-4).

**Modify:**
- `static/js/board-logic.js` — add all pure functions listed per task below (extends the module
  built up across `board-view.plan.md`'s Tasks 2-7).
- `static/js/board.js` — add DOM/fetch wiring for the create-issue form, edit-issue form,
  column-move drag handlers, and delete confirmation (extends the module from
  `board-view.plan.md`'s Tasks 3-7).
- `static/index.html` — add the create-issue trigger + form section, the edit-issue form section
  (opened by clicking a card), and `draggable`/drop-target wiring hooks on cards and columns.
- `static/css/board.css` — styling for the two new form sections, the drag-over affordance on
  columns, and the dragging-card affordance.

**Reference (read, do not modify):**
- `app/routers/issues.py` — `POST /issues`, `GET /issues/{id}`, `PATCH /issues/{id}`,
  `DELETE /issues/{id}` — exact request/response shapes and the exact error envelopes
  (`{"message": ..., "code": ...}`) this spec's UI must surface.
- `app/models.py` — `IssueCreate`, `IssuePatch`, `IssueRead`, and the `ISSUE_TYPES`/
  `ISSUE_STATUSES`/`ISSUE_PRIORITIES` literal value sets the two new forms' `<select>` options
  must match exactly.
- `.context-index/specs/features/issue-tracker-api/issue-lifecycle.spec.md` — BEH-1 (`todo`
  default), BEH-7 (patchable field set, `id`/`key`/`project_id` immutable), BEH-9 (`DELETE` → 204),
  and the Error Cases table (`ISSUE_NOT_FOUND`, `VALIDATION_ERROR`) this spec's client-side
  behavior must match.
- `static/js/board-logic.js` / `static/js/board.js` (current state, pre-this-plan) — `fetchJson`,
  `showError`/`clearError`, `formatFetchError`, `escapeHtml`, `BOARD_COLUMNS`,
  `groupIssuesByStatus`, `buildCardHtml`, `renderColumns`, `loadIssuesFor`, `init` — every task
  below extends these rather than replacing them.
- `.context-index/specs/features/kanban-ui/board-view.plan.md` — the established plan-writing
  and code-style precedent this plan follows (UMD-lite module shape, hidden-section form
  convention, `data-key`/`data-issue-id` DOM-id conventions, per-behavior test suite naming).

---

## Context Packets

### Task 1 Context
- Spec: `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-5; Error Cases
  rows 2-3, `UI_ISSUE_NOT_FOUND` and `UI_FETCH_FAILED`)
- Charter: `.context-index/specs/features/kanban-ui/charter.md` (capabilities: Edit issue, Delete
  issue, Move issue between columns — cross-cutting error path all three share)
- Source: `static/js/board-logic.js` (full read — current exports), `static/js/board.js` (full
  read — current `fetchJson`/`showError`/`clearError`)
- Sample: `.context-index/specs/features/kanban-ui/board-view.plan.md` Task 3 (`formatFetchError`
  precedent)

### Task 2 Context
- Spec: issue-crud-forms.spec.md (BEH-6; Error Cases row 1, `UI_VALIDATION_ERROR`)
- Charter: charter.md (capability: Create issue)
- Source: `app/models.py` (`IssueCreate` — signature only: required vs optional fields)
- Depends on: Task 1 (none directly — validation has no error-classification dependency, but
  shares the form-section DOM convention Task 1's context establishes)

### Task 3 Context
- Spec: issue-crud-forms.spec.md (BEH-1; Preconditions — required-field list, `todo` default)
- Charter: charter.md (capability: Create issue)
- Source: `app/routers/issues.py` (`POST /issues` — full read of the handler and its 404/422
  branches), `app/models.py` (`IssueCreate`, `IssueRead` — signatures only)
- Depends on: Task 2 (`validateIssueForm`, create-issue form DOM), Task 1
  (`formatFetchError` reused for the generic failure path)

### Task 4 Context
- Spec: issue-crud-forms.spec.md (BEH-2)
- Charter: charter.md (capability: Edit issue)
- Source: `app/routers/issues.py` (`PATCH /issues/{issue_id}` — full read, including
  `_PATCHABLE_FIELDS`), `app/models.py` (`IssuePatch` — signature only)
- Depends on: Task 1 (`isNotFoundError`, `formatIssueGoneMessage`, `formatFetchError`)

### Task 5 Context
- Spec: issue-crud-forms.spec.md (BEH-3; Postconditions: "board never shows a card in a column
  that does not match the server's last-confirmed status")
- Charter: charter.md (capability: Move issue between columns; Domain Model Invariants — fixed
  three-column set)
- Source: `app/routers/issues.py` (`PATCH /issues/{issue_id}` — status branch only, already read
  in Task 4)
- Depends on: Task 1 (error classification), Task 2's card DOM (`buildCardHtml`/`data-issue-id`,
  read-only reuse)

### Task 6 Context
- Spec: issue-crud-forms.spec.md (BEH-4; Error Cases row 2, `UI_ISSUE_NOT_FOUND`)
- Charter: charter.md (capability: Delete issue)
- Source: `app/routers/issues.py` (`DELETE /issues/{issue_id}` — full read, already read in Task 4
  context)
- Depends on: Task 1 (error classification), Task 4 (edit-issue form/panel hosts the delete
  control)

---

## Parallelization

- Group A (sequential): Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6

Every task after Task 1 modifies one or both of the two shared frontend files
(`static/js/board-logic.js`, `static/js/board.js`) and Task 1's error-classification helpers are a
direct dependency of Tasks 4-6, so there is no independent group to extract without first
splitting `board.js` into per-feature modules — out of scope for this plan, matching
`board-view.plan.md`'s Parallelization note for the same two files.

---

## Task Summary

| # | Title | Complexity | Strategy | Depends On | Files |
|---|-------|-----------|----------|------------|-------|
| 1 | Shared mutation error handling | small | unit | — | 1 create, 2 modify |
| 2 | Create-issue form shell & validation | small | unit | Task 1 | 1 create, 3 modify |
| 3 | Create-issue submit wiring | medium | unit | Task 2 | 1 create, 2 modify |
| 4 | Edit-issue form & diff-patch wiring | medium | unit | Task 1, Task 3 | 1 create, 4 modify |
| 5 | Column-move drag-and-drop interaction | medium | unit | Task 1, Task 4 | 1 create, 3 modify |
| 6 | Delete confirmation | small | unit | Task 1, Task 4 | 1 create, 2 modify |

All tasks resolve to the `unit` strategy (fallback — no `test_strategies` declared in
`manifest.yaml`, no spec-level `test_strategy`, and auto-detection finds no migration/IaC/schema/
contract/visual signal for this file set — same reasoning as `board-view.plan.md`). Strategy
Summary and Test Infrastructure Requirements sections are both omitted per plan template rules
(all-unit, no `infra_requirements:` declared).

Granularity: `per-behavior` (source: `manifest.yaml` `test_policy.granularity`). This spec's six
behaviors (BEH-1 through BEH-6) are new relative to `board-view.spec.md`'s own BEH-1 through BEH-6
— they are a different spec, so they resolve to distinct suites rather than extending
`board-view`'s existing `tests_js/beh-N-*.test.js` files (which cover unrelated behaviors and must
not be touched by this plan). Every suite below is a `create`, not an `extend`, and is named with
an `issue-crud-` prefix specifically to avoid colliding with `board-view`'s existing `beh-1`
through `beh-6` filenames in the same `tests_js/` directory.

---

## Task Structure

### Task 1: Shared mutation error handling [specialist: none]

**Charter capability:** cross-cutting (Edit issue, Move issue between columns, Delete issue all
depend on this for BEH-5 and the 404 exception)
**Strategy:** unit (source: fallback, confidence: high)
**Files:**
- Create: `tests_js/issue-crud-beh-5-error-handling.test.js`
- Modify: `static/js/board-logic.js` (add `isNotFoundError`, `formatIssueGoneMessage`)
- Modify: `static/js/board.js` (add `reportIssueMutationFailure`)

**Tests:** `tests_js/issue-crud-beh-5-error-handling.test.js` — new suite (BEH-5).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-5; Error Cases rows 2-3)
- `static/js/board-logic.js` (current `formatFetchError` — reused unchanged)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { isNotFoundError, formatIssueGoneMessage, formatFetchError } =
  require("../static/js/board-logic.js");

test("BEH-5/UI_ISSUE_NOT_FOUND: a 404 mutation error is classified as not-found", () => {
  assert.equal(isNotFoundError({ status: 404, message: "Issue 7 not found" }), true);
});

test("BEH-5/UI_ISSUE_NOT_FOUND: a 5xx or network error is not classified as not-found", () => {
  assert.equal(isNotFoundError({ status: 500, message: "boom" }), false);
  assert.equal(isNotFoundError({ message: "Failed to fetch" }), false);
});

test("BEH-5/UI_ISSUE_NOT_FOUND: names the action and notes the card was already gone", () => {
  const msg = formatIssueGoneMessage("Updating issue");
  assert.match(msg, /Updating issue/);
  assert.match(msg, /already/i);
});

test("BEH-5/UI_FETCH_FAILED: generic failures still use the existing formatter", () => {
  const msg = formatFetchError("Moving issue", { status: 500, message: "boom" });
  assert.match(msg, /Moving issue/);
  assert.match(msg, /500/);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-5-error-handling.test.js`
Expected: FAIL — `isNotFoundError is not a function`

- [ ] **Implement**

Add to the `board-logic.js` factory's return object (extends the module from
`board-view.plan.md`'s Task 3):

```javascript
  function isNotFoundError(error) {
    return !!(error && error.status === 404);
  }

  function formatIssueGoneMessage(action) {
    return `${action}: this issue was already removed. The board has been updated.`;
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage,
  };
```

Add to `board.js` (glue only — not separately unit-tested, per the established architecture
split; `onNotFound` runs a caller-supplied DOM cleanup, e.g. removing the stale card):

```javascript
  function reportIssueMutationFailure(action, err, onNotFound) {
    if (BoardLogic.isNotFoundError(err)) {
      if (typeof onNotFound === "function") onNotFound();
      showError(BoardLogic.formatIssueGoneMessage(action));
      return;
    }
    showError(BoardLogic.formatFetchError(action, err));
  }
```

`reportIssueMutationFailure` is exported alongside the module's existing `window.BoardApp` object
in Task 4 (its first caller); Task 1 only defines it.

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-5-error-handling.test.js`
Expected: PASS

- [ ] **Commit**

Branch (already created by board-view): `feat/kanban-ui/board-view`

```bash
git add static/js/board-logic.js static/js/board.js \
        tests_js/issue-crud-beh-5-error-handling.test.js
git commit -m "feat(kanban-ui): add shared issue-mutation error classification"
```

---

### Task 2: Create-issue form shell & validation [specialist: none]

**Charter capability:** Create issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1
**Files:**
- Create: `tests_js/issue-crud-beh-6-create-validation.test.js`
- Modify: `static/js/board-logic.js` (add `validateIssueForm`)
- Modify: `static/index.html` (add "New Issue" trigger + `#create-issue` form section)
- Modify: `static/css/board.css` (style the new form section — same rules as `#create-project`)

**Tests:** `tests_js/issue-crud-beh-6-create-validation.test.js` — new suite (BEH-6).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-6; Preconditions —
  required field list)
- `app/models.py` (`IssueCreate` — signature only)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { validateIssueForm } = require("../static/js/board-logic.js");

test("BEH-6/UI_VALIDATION_ERROR: blocks submit when summary, type, or priority is blank", () => {
  assert.equal(validateIssueForm({ summary: "", issue_type: "bug", priority: "high" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "", priority: "high" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "bug", priority: "" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "bug", priority: "high" }).valid, true);
});

test("BEH-6/UI_VALIDATION_ERROR: names every missing required field", () => {
  const result = validateIssueForm({ summary: "  ", issue_type: "", priority: "low" });
  assert.ok(result.errors.summary);
  assert.ok(result.errors.issue_type);
  assert.equal(result.errors.priority, undefined);
});

test("optional fields (description, assignee) never block submission", () => {
  const result = validateIssueForm({
    summary: "Fix it", issue_type: "bug", priority: "high", description: "", assignee: "",
  });
  assert.equal(result.valid, true);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-6-create-validation.test.js`
Expected: FAIL — `validateIssueForm is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function validateIssueForm(fields) {
    const errors = {};
    if (!fields.summary || !fields.summary.trim()) errors.summary = "Summary is required";
    if (!fields.issue_type) errors.issue_type = "Type is required";
    if (!fields.priority) errors.priority = "Priority is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
  };
```

`static/index.html`: add a trigger button near the header (opens the form) and a hidden form
section, following the same `hidden`-toggle convention as `#create-project`:

```html
  <header>
    <h1>mock-jira</h1>
    <select id="project-switcher" aria-label="Select project"></select>
    <button id="open-create-issue" type="button">New Issue</button>
  </header>

  <!-- ... after #create-project ... -->
  <section id="create-issue" hidden>
    <h2>New Issue</h2>
    <form id="create-issue-form">
      <label>Summary <input id="issue-summary" name="summary" required /></label>
      <label>Type
        <select id="issue-type" name="issue_type" required>
          <option value="">Select type&hellip;</option>
          <option value="bug">Bug</option>
          <option value="task">Task</option>
          <option value="story">Story</option>
        </select>
      </label>
      <label>Priority
        <select id="issue-priority" name="priority" required>
          <option value="">Select priority&hellip;</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <label>Description <textarea id="issue-description" name="description"></textarea></label>
      <label>Assignee <input id="issue-assignee" name="assignee" /></label>
      <button type="submit">Create Issue</button>
      <button id="cancel-create-issue" type="button">Cancel</button>
      <p id="create-issue-error" role="alert" hidden></p>
    </form>
  </section>
```

`static/css/board.css`: add `#create-issue { /* same block/border/padding rules as #empty-state,
#create-project */ }` and a `#create-issue form textarea { display: block; width: 100%; box-
sizing: border-box; }` rule — reuses the existing `#create-project form label`/`input` selectors
by adding `#create-issue` to their selector lists (comma-joined), not duplicating the rule bodies.

Wiring the open/cancel toggle only (submit handler arrives in Task 3) in `board.js`:

```javascript
  document.getElementById("open-create-issue").addEventListener("click", () => {
    document.getElementById("create-issue").hidden = false;
  });
  document.getElementById("cancel-create-issue").addEventListener("click", (event) => {
    event.preventDefault();
    document.getElementById("create-issue-form").reset();
    document.getElementById("create-issue-error").hidden = true;
    document.getElementById("create-issue").hidden = true;
  });
```

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-6-create-validation.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/index.html static/css/board.css \
        tests_js/issue-crud-beh-6-create-validation.test.js
git commit -m "feat(kanban-ui): add create-issue form shell and required-field validation"
```

---

### Task 3: Create-issue submit wiring [specialist: none]

**Charter capability:** Create issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 2
**Files:**
- Create: `tests_js/issue-crud-beh-1-create-issue.test.js`
- Modify: `static/js/board-logic.js` (add `buildIssueCreatePayload`)
- Modify: `static/js/board.js` (create-issue form `submit` handler)

**Tests:** `tests_js/issue-crud-beh-1-create-issue.test.js` — new suite (BEH-1).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-1; Preconditions)
- `app/routers/issues.py` (`POST /issues` handler — full read)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { buildIssueCreatePayload } = require("../static/js/board-logic.js");

test("BEH-1: assembles the required fields plus the implicit project id", () => {
  const payload = buildIssueCreatePayload(3, {
    summary: "Fix login bug", issue_type: "bug", priority: "high",
  });
  assert.deepEqual(payload, {
    project_id: 3, summary: "Fix login bug", issue_type: "bug", priority: "high",
  });
});

test("BEH-1: includes optional description/assignee only when non-blank", () => {
  const withOptional = buildIssueCreatePayload(3, {
    summary: "A", issue_type: "task", priority: "low", description: "Details", assignee: "dee",
  });
  assert.equal(withOptional.description, "Details");
  assert.equal(withOptional.assignee, "dee");

  const withoutOptional = buildIssueCreatePayload(3, {
    summary: "A", issue_type: "task", priority: "low", description: "", assignee: "  ",
  });
  assert.equal("description" in withoutOptional, false);
  assert.equal("assignee" in withoutOptional, false);
});

test("BEH-1: never sends a status field — the server always defaults to todo", () => {
  const payload = buildIssueCreatePayload(3, { summary: "A", issue_type: "task", priority: "low" });
  assert.equal("status" in payload, false);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-1-create-issue.test.js`
Expected: FAIL — `buildIssueCreatePayload is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function buildIssueCreatePayload(projectId, fields) {
    const payload = {
      project_id: projectId,
      summary: fields.summary,
      issue_type: fields.issue_type,
      priority: fields.priority,
    };
    if (fields.description && fields.description.trim()) payload.description = fields.description;
    if (fields.assignee && fields.assignee.trim()) payload.assignee = fields.assignee;
    return payload;
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
    buildIssueCreatePayload,
  };
```

The current `board.js` (as of `board-view.plan.md`) has no module-scope variable tracking which
project is selected — `init()` and `onProjectSwitch` each compute a local `projectId` and pass it
straight into `loadIssuesFor(projectId)` without storing it anywhere durable. This task introduces
`let currentProjectId = null;` at the top of the IIFE (alongside the existing `editingIssue`-style
module state) and sets it at the top of `loadIssuesFor`, so `onCreateIssueSubmit` below has a
reliable place to read the currently selected project from:

```javascript
  let currentProjectId = null;

  async function loadIssuesFor(projectId) {
    currentProjectId = projectId;
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
      clearError();
      renderBoardState(BoardLogic.computeBoardState(projectId, issues));
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading issues", err));
    }
  }
```

Add to `board.js` (replaces the open/cancel-only stub from Task 2's submit non-wiring):

```javascript
  async function onCreateIssueSubmit(event) {
    event.preventDefault();
    const fields = {
      summary: document.getElementById("issue-summary").value,
      issue_type: document.getElementById("issue-type").value,
      priority: document.getElementById("issue-priority").value,
      description: document.getElementById("issue-description").value,
      assignee: document.getElementById("issue-assignee").value,
    };
    const { valid, errors } = BoardLogic.validateIssueForm(fields);
    const errorEl = document.getElementById("create-issue-error");
    if (!valid) {
      errorEl.textContent = Object.values(errors)[0];
      errorEl.hidden = false;
      return; // client-side block — no request sent (UI_VALIDATION_ERROR)
    }
    errorEl.hidden = true;
    try {
      await fetchJson("/issues", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(BoardLogic.buildIssueCreatePayload(currentProjectId, fields)),
      });
    } catch (err) {
      showError(BoardLogic.formatFetchError("Creating issue", err));
      return; // form stays open with prior input intact
    }
    document.getElementById("create-issue-form").reset();
    document.getElementById("create-issue").hidden = true;
    await loadIssuesFor(currentProjectId); // new issue is always todo — reload shows it there
  }

  document.getElementById("create-issue-form").addEventListener("submit", onCreateIssueSubmit);
```

`currentProjectId` must be readable here; if `board-view`'s `loadIssuesFor` does not already
capture it at module scope, add `let currentProjectId = null;` near the top of the IIFE and set it
at the two existing call sites (`init()`'s and `onProjectSwitch`'s calls into `loadIssuesFor`)
before this task's code depends on it.

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-1-create-issue.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js \
        tests_js/issue-crud-beh-1-create-issue.test.js
git commit -m "feat(kanban-ui): wire create-issue form submission to POST /issues"
```

---

### Task 4: Edit-issue form & diff-patch wiring [specialist: none]

**Charter capability:** Edit issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 3
**Files:**
- Create: `tests_js/issue-crud-beh-2-edit-issue.test.js`
- Modify: `static/js/board-logic.js` (add `diffIssueFields`)
- Modify: `static/js/board.js` (card-click opens edit form; edit form `submit` handler)
- Modify: `static/index.html` (add `#edit-issue` form section, same field set as create minus
  required-ness)
- Modify: `static/css/board.css` (style `#edit-issue`, reusing `#create-issue`'s selectors)

**Tests:** `tests_js/issue-crud-beh-2-edit-issue.test.js` — new suite (BEH-2).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-2; Preconditions — edit
  form has no required fields)
- `app/routers/issues.py` (`GET /issues/{issue_id}`, `PATCH /issues/{issue_id}` — full read)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { diffIssueFields } = require("../static/js/board-logic.js");

const original = {
  id: 5, summary: "Old summary", description: "Old desc", issue_type: "bug",
  priority: "low", assignee: "dana", reporter: "sam",
};

test("BEH-2: only changed fields appear in the patch payload", () => {
  const patch = diffIssueFields(original, { ...original, summary: "New summary" });
  assert.deepEqual(patch, { summary: "New summary" });
});

test("BEH-2: multiple changed fields are all included", () => {
  const patch = diffIssueFields(original, { ...original, priority: "high", assignee: "dee" });
  assert.deepEqual(patch, { priority: "high", assignee: "dee" });
});

test("BEH-2: unchanged fields produce an empty patch payload", () => {
  assert.deepEqual(diffIssueFields(original, { ...original }), {});
});

test("BEH-2: status is never part of the diff — column move owns status changes", () => {
  const patch = diffIssueFields(original, { ...original, summary: "New", status: "done" });
  assert.equal("status" in patch, false);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-2-edit-issue.test.js`
Expected: FAIL — `diffIssueFields is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  const EDITABLE_ISSUE_FIELDS = ["summary", "description", "issue_type", "priority", "assignee", "reporter"];

  function diffIssueFields(original, edited) {
    const patch = {};
    for (const field of EDITABLE_ISSUE_FIELDS) {
      if (edited[field] !== original[field]) patch[field] = edited[field];
    }
    return patch;
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
    buildIssueCreatePayload, diffIssueFields,
  };
```

`static/index.html`: add the edit form section (all fields optional; no `required` attributes),
mirroring `#create-issue`'s field set:

```html
  <section id="edit-issue" hidden>
    <h2>Edit Issue</h2>
    <form id="edit-issue-form">
      <input type="hidden" id="edit-issue-id" />
      <label>Summary <input id="edit-issue-summary" name="summary" /></label>
      <label>Type
        <select id="edit-issue-type" name="issue_type">
          <option value="bug">Bug</option>
          <option value="task">Task</option>
          <option value="story">Story</option>
        </select>
      </label>
      <label>Priority
        <select id="edit-issue-priority" name="priority">
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </label>
      <label>Description <textarea id="edit-issue-description" name="description"></textarea></label>
      <label>Assignee <input id="edit-issue-assignee" name="assignee" /></label>
      <button type="submit">Save Changes</button>
      <button id="cancel-edit-issue" type="button">Cancel</button>
      <button id="delete-issue" type="button">Delete</button>
      <p id="edit-issue-error" role="alert" hidden></p>
    </form>
  </section>
```

Add to `board.js` — track the issue currently open for edit (needed by `diffIssueFields` and by
Task 6's delete button), open the form on card click, and wire submit through
`reportIssueMutationFailure` (defined in Task 1) for the not-found exception:

```javascript
  let editingIssue = null; // the full IssueRead currently loaded into the edit form

  function openEditIssue(issue) {
    editingIssue = issue;
    document.getElementById("edit-issue-id").value = issue.id;
    document.getElementById("edit-issue-summary").value = issue.summary;
    document.getElementById("edit-issue-type").value = issue.issue_type;
    document.getElementById("edit-issue-priority").value = issue.priority;
    document.getElementById("edit-issue-description").value = issue.description;
    document.getElementById("edit-issue-assignee").value = issue.assignee;
    document.getElementById("edit-issue-error").hidden = true;
    document.getElementById("edit-issue").hidden = false;
  }

  function onCardClick(event) {
    const card = event.target.closest(".card");
    if (!card) return;
    const issue = currentIssues.find((i) => i.id === Number(card.dataset.issueId));
    if (issue) openEditIssue(issue);
  }

  async function onEditIssueSubmit(event) {
    event.preventDefault();
    const edited = {
      ...editingIssue,
      summary: document.getElementById("edit-issue-summary").value,
      issue_type: document.getElementById("edit-issue-type").value,
      priority: document.getElementById("edit-issue-priority").value,
      description: document.getElementById("edit-issue-description").value,
      assignee: document.getElementById("edit-issue-assignee").value,
    };
    const patch = BoardLogic.diffIssueFields(editingIssue, edited);
    if (Object.keys(patch).length === 0) {
      document.getElementById("edit-issue").hidden = true;
      return; // nothing changed — close quietly, no network call
    }
    try {
      await fetchJson(`/issues/${editingIssue.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
    } catch (err) {
      reportIssueMutationFailure("Updating issue", err, () => {
        document.getElementById("edit-issue").hidden = true;
        loadIssuesFor(currentProjectId); // 404: card is gone — refresh removes it from view
      });
      return; // non-404 failure: form stays open, prior input intact (nothing was optimistic)
    }
    document.getElementById("edit-issue").hidden = true;
    await loadIssuesFor(currentProjectId); // reflect the server's response, not the local edit
  }

  document.getElementById("board").addEventListener("click", onCardClick);
  document.getElementById("edit-issue-form").addEventListener("submit", onEditIssueSubmit);
  document.getElementById("cancel-edit-issue").addEventListener("click", (event) => {
    event.preventDefault();
    document.getElementById("edit-issue").hidden = true;
  });
```

The current `board.js` discards the fetched issues array after rendering — there is no place to
look one back up by id. This task introduces a second module-scope variable, `let currentIssues =
[];`, and extends `loadIssuesFor` (already modified once in Task 3 to set `currentProjectId`) to
also capture the fetched array before rendering:

```javascript
  let currentIssues = [];

  async function loadIssuesFor(projectId) {
    currentProjectId = projectId;
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
      currentIssues = issues;
      clearError();
      renderBoardState(BoardLogic.computeBoardState(projectId, issues));
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading issues", err));
    }
  }
```

`onCardClick` (below) reads `currentIssues` to look up the full record a clicked card
represents — the DOM only carries `data-issue-id`, not the full Issue.

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-2-edit-issue.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js static/index.html static/css/board.css \
        tests_js/issue-crud-beh-2-edit-issue.test.js
git commit -m "feat(kanban-ui): add edit-issue form with minimal-diff PATCH wiring"
```

---

### Task 5: Column-move drag-and-drop interaction [specialist: none]

**Charter capability:** Move issue between columns
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 4
**Files:**
- Create: `tests_js/issue-crud-beh-3-column-move.test.js`
- Modify: `static/js/board-logic.js` (add `moveIssueStatus`)
- Modify: `static/js/board.js` (`dragstart`/`dragover`/`drop` handlers; optimistic move + PATCH +
  reconcile/revert)
- Modify: `static/css/board.css` (drag-over affordance on `.column`, dragging affordance on
  `.card`)

No `static/index.html` edit in this task: cards already carry `data-status` on each `.column`
section (from `board-view.plan.md` Task 1), and the `draggable="true"` attribute is added to card
markup via `buildCardHtml` in `board-logic.js` below, not via static HTML.

**Tests:** `tests_js/issue-crud-beh-3-column-move.test.js` — new suite (BEH-3).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-3; Postconditions)
- `.context-index/specs/features/kanban-ui/charter.md` (Domain Model — fixed `BOARD_COLUMNS`
  ordering invariant, must not be violated by the move transform)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { moveIssueStatus } = require("../static/js/board-logic.js");

const issues = [
  { id: 1, status: "todo" },
  { id: 2, status: "in_progress" },
];

test("BEH-3: moves the target issue to the new status, leaving others untouched", () => {
  const moved = moveIssueStatus(issues, 1, "done");
  assert.equal(moved.find((i) => i.id === 1).status, "done");
  assert.equal(moved.find((i) => i.id === 2).status, "in_progress");
});

test("BEH-3: is a pure transform — the original array is never mutated", () => {
  const before = JSON.stringify(issues);
  moveIssueStatus(issues, 1, "done");
  assert.equal(JSON.stringify(issues), before);
});

test("BEH-3: moving back to the original status is the exact revert operation", () => {
  const moved = moveIssueStatus(issues, 1, "done");
  const reverted = moveIssueStatus(moved, 1, "todo");
  assert.deepEqual(reverted, issues);
});

test("BEH-3: an unknown issue id leaves the list unchanged", () => {
  assert.deepEqual(moveIssueStatus(issues, 999, "done"), issues);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-3-column-move.test.js`
Expected: FAIL — `moveIssueStatus is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function moveIssueStatus(issues, issueId, newStatus) {
    return issues.map((issue) =>
      issue.id === issueId ? { ...issue, status: newStatus } : issue
    );
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
    buildIssueCreatePayload, diffIssueFields, moveIssueStatus,
  };
```

Update `buildCardHtml` (from `board-view.plan.md` Task 2) to add `draggable="true"` — a pure,
additive markup change; existing `beh-2-render-columns.test.js` assertions are substring/regex
based and are unaffected:

```javascript
  function buildCardHtml(issue) {
    return (
      `<article class="card" data-issue-id="${issue.id}" draggable="true">` +
      // ...unchanged...
```

Add to `board.js` — optimistic move, then PATCH, then reconcile on success or revert on failure
(the one genuinely optimistic flow in this spec):

```javascript
  function onDragStart(event) {
    const card = event.target.closest(".card");
    if (!card) return;
    event.dataTransfer.setData("text/plain", card.dataset.issueId);
  }

  function onColumnDragOver(event) {
    event.preventDefault(); // required to allow a drop
    event.currentTarget.classList.add("drag-over");
  }

  function onColumnDragLeave(event) {
    event.currentTarget.classList.remove("drag-over");
  }

  async function onColumnDrop(event) {
    event.preventDefault();
    const column = event.currentTarget;
    column.classList.remove("drag-over");
    const issueId = Number(event.dataTransfer.getData("text/plain"));
    const newStatus = column.dataset.status;
    const originalIssue = currentIssues.find((i) => i.id === issueId);
    if (!originalIssue || originalIssue.status === newStatus) return;
    const originalStatus = originalIssue.status;

    currentIssues = BoardLogic.moveIssueStatus(currentIssues, issueId, newStatus);
    renderColumns(BoardLogic.groupIssuesByStatus(currentIssues)); // optimistic move

    try {
      await fetchJson(`/issues/${issueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      clearError();
    } catch (err) {
      reportIssueMutationFailure("Moving issue", err, () => {
        // 404: the card is gone server-side — drop the optimistic move and refresh from truth
        loadIssuesFor(currentProjectId);
      });
      if (!BoardLogic.isNotFoundError(err)) {
        currentIssues = BoardLogic.moveIssueStatus(currentIssues, issueId, originalStatus);
        renderColumns(BoardLogic.groupIssuesByStatus(currentIssues)); // exact revert
      }
    }
  }

  for (const col of BoardLogic.BOARD_COLUMNS) {
    const section = document.querySelector(`.column[data-status="${col.status}"]`);
    section.addEventListener("dragover", onColumnDragOver);
    section.addEventListener("dragleave", onColumnDragLeave);
    section.addEventListener("drop", onColumnDrop);
  }
  document.getElementById("board").addEventListener("dragstart", onDragStart);
```

`renderColumns` re-renders straight from `currentIssues`, so the optimistic move and its revert
both go through the exact same render path as a normal load — there is no separate "undo" code
path to keep in sync with the columns' actual contents.

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-3-column-move.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js static/css/board.css \
        tests_js/issue-crud-beh-3-column-move.test.js
git commit -m "feat(kanban-ui): add drag-and-drop column move with optimistic reconcile/revert"
```

---

### Task 6: Delete confirmation [specialist: none]

**Charter capability:** Delete issue
**Strategy:** unit (source: fallback, confidence: high)
**Depends on:** Task 1, Task 4
**Files:**
- Create: `tests_js/issue-crud-beh-4-delete-issue.test.js`
- Modify: `static/js/board-logic.js` (add `removeIssueById`)
- Modify: `static/js/board.js` (`#delete-issue` button `click` handler — confirm, then `DELETE`)

**Tests:** `tests_js/issue-crud-beh-4-delete-issue.test.js` — new suite (BEH-4).

**Context to load:**
- `.context-index/specs/features/kanban-ui/issue-crud-forms.spec.md` (BEH-4; Error Cases row 2)
- `app/routers/issues.py` (`DELETE /issues/{issue_id}` handler — already read in Task 4)

- [ ] **Write failing test**

```javascript
const test = require("node:test");
const assert = require("node:assert/strict");
const { removeIssueById } = require("../static/js/board-logic.js");

const issues = [{ id: 1, status: "todo" }, { id: 2, status: "done" }];

test("BEH-4: removes exactly the targeted issue", () => {
  const remaining = removeIssueById(issues, 1);
  assert.deepEqual(remaining.map((i) => i.id), [2]);
});

test("BEH-4/UI_ISSUE_NOT_FOUND: removing an id already absent is a safe no-op", () => {
  assert.deepEqual(removeIssueById(issues, 999), issues);
});

test("BEH-4: is a pure transform — the original array is never mutated", () => {
  const before = JSON.stringify(issues);
  removeIssueById(issues, 1);
  assert.equal(JSON.stringify(issues), before);
});
```

- [ ] **Verify test fails**

Run: `node --test tests_js/issue-crud-beh-4-delete-issue.test.js`
Expected: FAIL — `removeIssueById is not a function`

- [ ] **Implement**

Add to `board-logic.js`:

```javascript
  function removeIssueById(issues, issueId) {
    return issues.filter((issue) => issue.id !== issueId);
  }

  // ...
  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
    buildIssueCreatePayload, diffIssueFields, moveIssueStatus, removeIssueById,
  };
```

Add to `board.js` — the confirmation step itself (`window.confirm`) is untestable imperative glue,
consistent with this architecture's established scope for `board.js`; the removal it triggers goes
through the same pure `removeIssueById` + `renderColumns` path used by the 404 exception in
Tasks 4 and 5:

```javascript
  async function onDeleteIssueClick(event) {
    event.preventDefault();
    if (!editingIssue) return;
    const confirmed = window.confirm(`Delete issue "${editingIssue.summary}"? This cannot be undone.`);
    if (!confirmed) return;
    const issueId = editingIssue.id;
    try {
      await fetchJson(`/issues/${issueId}`, { method: "DELETE" });
      clearError();
    } catch (err) {
      reportIssueMutationFailure("Deleting issue", err, () => {
        // 404: already gone — fall through to the same removal below
      });
      if (!BoardLogic.isNotFoundError(err)) {
        return; // non-404 failure: card stays, edit form stays open, error shown
      }
    }
    currentIssues = BoardLogic.removeIssueById(currentIssues, issueId);
    renderColumns(BoardLogic.groupIssuesByStatus(currentIssues));
    document.getElementById("edit-issue").hidden = true;
    editingIssue = null;
  }

  document.getElementById("delete-issue").addEventListener("click", onDeleteIssueClick);

  window.BoardApp = {
    fetchJson, showError, clearError, renderSwitcher, renderColumns, renderBoardState,
    loadIssuesFor, init, getLastSelectedKey, setLastSelectedKey, onProjectSwitch,
    onCreateProjectSubmit, onCreateIssueSubmit, onCardClick, onEditIssueSubmit, onDragStart,
    onColumnDrop, onDeleteIssueClick, reportIssueMutationFailure,
  };
```

(The `window.BoardApp` export list above is the final cumulative state after all six tasks in this
plan — each earlier task's own commit should append only its own new function names to whatever
`window.BoardApp` already contains at that point, rather than restating the whole object; it is
written out in full here only so the finished shape is unambiguous.)

- [ ] **Verify test passes**

Run: `node --test tests_js/issue-crud-beh-4-delete-issue.test.js`
Expected: PASS

- [ ] **Commit**

```bash
git add static/js/board-logic.js static/js/board.js \
        tests_js/issue-crud-beh-4-delete-issue.test.js
git commit -m "feat(kanban-ui): add delete-issue confirmation and DELETE wiring"
```

---

## Quality Gates

`.context-index/governance/gates.yaml` exists, so its gate definitions govern instead of the
constitution's Commands section. This plan touches no gate definitions (the `test-js` gate
already runs `node --test "tests_js/**/*.test.js"`, which picks up this plan's six new suites
without modification):

- **Tests pass:** `python3 -m pytest -q` (gate `test`) — unaffected by this spec; no Python files
  are created or modified by this plan.
- **JS unit tests pass:** `node --test "tests_js/**/*.test.js"` (gate `test-js`) — covers
  `board-view`'s existing six suites plus this plan's six new `issue-crud-beh-*.test.js` suites.
- **Lint passes:** `ruff check .` (gate `lint`) — Python only; unaffected, no Python changes here.
- `integration-test` gate stays unwired (`command: ""`) — unaffected by this spec.
- All acceptance criteria from `issue-crud-forms.spec.md` satisfied: BEH-1 through BEH-6 each
  traced to exactly one task above (Task 3, 4, 5, 6, 1, 2 respectively), plus the spec's three
  Error Cases rows (`UI_VALIDATION_ERROR` — Tasks 2/6 form-submit blocking, `UI_ISSUE_NOT_FOUND` —
  Task 1's classification consumed by Tasks 4-6, `UI_FETCH_FAILED` — Task 1 consumed by Tasks
  3-6).

After all tasks are complete, `/adev:validate` verifies the full quality gate suite. Results are
recorded in the validation report (`.validate.md`), not in this plan.
