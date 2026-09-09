const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-1: a Backlog nav item exists alongside Board/Users/Projects", () => {
  assert.match(html, /<button[^>]+id="nav-backlog"[^>]+data-view="backlog"[^>]*>Backlog<\/button>/);
});

test("BEH-1: a #view-backlog container exists, hidden by default", () => {
  assert.match(html, /<section id="view-backlog" class="view" hidden>/);
});
