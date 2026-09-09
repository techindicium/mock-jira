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
