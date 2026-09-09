const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-3: filter bar has assignee, type, and priority selects", () => {
  assert.match(html, /<select[^>]+id="filter-assignee"/);
  assert.match(html, /<select[^>]+id="filter-issue-type"/);
  assert.match(html, /<select[^>]+id="filter-priority"/);
});

test("BEH-5: each filter select has an explicit All/empty option", () => {
  const block = html.slice(html.indexOf('id="filter-bar"'), html.indexOf("</div>", html.indexOf('id="filter-bar"')) + 6);
  assert.match(block, /<option value="">All<\/option>/);
});
