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
