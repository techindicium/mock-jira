const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-6: a filter-empty-state element exists, hidden by default, distinct from #empty-state", () => {
  assert.match(html, /<[a-z]+ id="filter-empty-state"[^>]*hidden[^>]*>/);
});
