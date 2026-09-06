const test = require("node:test");
const assert = require("node:assert/strict");
const { columnCounts, groupIssuesByStatus } = require("../static/js/board-logic.js");

test("BEH-4: columnCounts returns the issue count per fixed column", () => {
  const grouped = groupIssuesByStatus([
    { id: 1, status: "todo" },
    { id: 2, status: "todo" },
    { id: 3, status: "done" },
  ]);
  assert.deepEqual(columnCounts(grouped), { todo: 2, in_progress: 0, done: 1 });
});

test("BEH-4: columnCounts handles zero issues", () => {
  assert.deepEqual(columnCounts(groupIssuesByStatus([])), { todo: 0, in_progress: 0, done: 0 });
});
