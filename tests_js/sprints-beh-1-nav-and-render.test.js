const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { filterIssuesBySprintId } = require("../static/js/board-logic.js");

test("BEH-10: nav item and view container exist", () => {
  const html = readFileSync(require.resolve("../static/index.html"), "utf8");
  assert.match(html, /<button[^>]+id="nav-sprint"[^>]+data-view="sprint"[^>]*>/);
  assert.match(html, /<section id="view-sprint" class="view" hidden>/);
});

test("filterIssuesBySprintId: returns only issues matching the active sprint id", () => {
  const issues = [{ id: 1, sprint_id: 5 }, { id: 2, sprint_id: null }, { id: 3, sprint_id: 5 }];
  assert.deepEqual(filterIssuesBySprintId(issues, 5).map((i) => i.id), [1, 3]);
});

test("filterIssuesBySprintId: null active sprint returns an empty array", () => {
  const issues = [{ id: 1, sprint_id: 5 }];
  assert.deepEqual(filterIssuesBySprintId(issues, null), []);
});
