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
