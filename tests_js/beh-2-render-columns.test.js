const test = require("node:test");
const assert = require("node:assert/strict");
const { BOARD_COLUMNS, groupIssuesByStatus, buildCardHtml, escapeHtml } =
  require("../static/js/board-logic.js");

test("BEH-2: groups issues into the three fixed columns by status", () => {
  const issues = [
    { id: 1, status: "todo", summary: "A", issue_type: "bug", priority: "high", assignee: "" },
    { id: 2, status: "done", summary: "B", issue_type: "task", priority: "low", assignee: "dee" },
  ];
  const grouped = groupIssuesByStatus(issues);
  assert.deepEqual(Object.keys(grouped).sort(), ["done", "in_progress", "todo"]);
  assert.equal(grouped.todo.length, 1);
  assert.equal(grouped.done.length, 1);
  assert.equal(grouped.in_progress.length, 0);
});

test("BEH-2: handles zero issues without error", () => {
  const grouped = groupIssuesByStatus([]);
  assert.deepEqual(grouped.todo, []);
});

test("BEH-2: card markup shows summary, type, priority, and assignee", () => {
  const html = buildCardHtml({
    id: 7, summary: "Fix bug", issue_type: "bug", priority: "high", assignee: "dana",
  });
  assert.match(html, /Fix bug/);
  assert.match(html, /bug/);
  assert.match(html, /high/);
  assert.match(html, /dana/);
});

test("BEH-2: card markup falls back to Unassigned and escapes HTML", () => {
  const html = buildCardHtml({
    id: 8, summary: "<script>", issue_type: "task", priority: "low", assignee: "",
  });
  assert.match(html, /Unassigned/);
  assert.doesNotMatch(html, /<script>/);
});

test("escapeHtml neutralizes markup-significant characters", () => {
  assert.equal(escapeHtml("<b>&\"'"), "&lt;b&gt;&amp;&quot;&#39;");
});

test("BOARD_COLUMNS is fixed, ordered todo -> in_progress -> done", () => {
  assert.deepEqual(BOARD_COLUMNS.map((c) => c.status), ["todo", "in_progress", "done"]);
});
