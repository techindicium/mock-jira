const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-1: design tokens are declared in :root", () => {
  const tokens = [
    /--ink:\s*#16261f/i,
    /--rail:\s*#2f4a3e/i,
    /--paper:\s*#f1ecdd/i,
    /--stamp-red:\s*#a3402f/i,
    /--stamp-gold:\s*#b98a2e/i,
    /--stamp-green:\s*#4c7a5e/i,
    /--ink-line:\s*#55483a/i,
  ];
  for (const t of tokens) assert.match(css, t);
});

test("BEH-1: page background uses the --ink token", () => {
  assert.match(css, /body\s*{[^}]*background:\s*var\(--ink\)/s);
});
