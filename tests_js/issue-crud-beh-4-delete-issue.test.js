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
