const test = require("node:test");
const assert = require("node:assert/strict");
const { buildBacklogRowsHtml } = require("../static/js/board-logic.js");

test("BEH-11: each backlog row includes an Add-to-sprint control with data-issue-id", () => {
  const html = buildBacklogRowsHtml([
    { id: 7, key: "A-7", summary: "x", issue_type: "task", priority: "low", status: "todo" },
  ]);
  assert.match(html, /<button[^>]*class="add-to-sprint"[^>]*data-issue-id="7"[^>]*>\s*Add to sprint\s*<\/button>/);
});

test("BEH-11: multiple rows each get their own Add-to-sprint control", () => {
  const html = buildBacklogRowsHtml([
    { id: 1, key: "A-1", summary: "x", issue_type: "task", priority: "low", status: "todo" },
    { id: 2, key: "A-2", summary: "y", issue_type: "bug", priority: "high", status: "done" },
  ]);
  assert.match(html, /data-issue-id="1"[^>]*>\s*Add to sprint/);
  assert.match(html, /data-issue-id="2"[^>]*>\s*Add to sprint/);
});

test("zero issues still renders an empty string", () => {
  assert.equal(buildBacklogRowsHtml([]), "");
});
