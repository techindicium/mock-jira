const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-7: a deliberate :focus-visible style is declared", () => {
  assert.match(css, /:focus-visible\s*{[^}]*outline:\s*(?!none)/s);
});

test("BEH-8: prefers-reduced-motion guard is present", () => {
  assert.match(css, /@media\s*\(prefers-reduced-motion:\s*reduce\)/);
});
