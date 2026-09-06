const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-5: project switcher is wrapped in a styled plate but stays a real <select>", () => {
  assert.match(
    html,
    /<div class="switcher-plate">[\s\S]*?<select[^>]*id="project-switcher"[^>]*>[\s\S]*?<\/select>[\s\S]*?<\/div>/
  );
});

test("BEH-5: the switcher keeps its aria-label", () => {
  assert.match(html, /aria-label="Select project"/);
});
