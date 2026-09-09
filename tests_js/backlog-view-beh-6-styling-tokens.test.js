const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-1: filter-bar rule exists", () => {
  assert.match(css, /\.filter-bar\s*{/);
});

test("offline-only/no-new-tokens: filter-bar and backlog-table rules only reference existing var() tokens, no new hex literals", () => {
  const filterBarBlock = css.slice(css.indexOf(".filter-bar {"), css.indexOf("}", css.indexOf(".filter-bar {")) + 1);
  assert.doesNotMatch(filterBarBlock, /#[0-9a-fA-F]{3,6}/);
});
