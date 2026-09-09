const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("BEH-1: design tokens are declared in :root", () => {
  const tokens = [
    /--brand-blue:\s*#0c66e4/i,
    /--brand-blue-dark:\s*#0052cc/i,
    /--surface:\s*#ffffff/i,
    /--surface-sunken:\s*#f7f8f9/i,
    /--border:\s*#dfe1e6/i,
    /--text:\s*#172b4d/i,
    /--text-subtle:\s*#6b778c/i,
  ];
  for (const t of tokens) assert.match(css, t);
});

test("BEH-1: page background uses the --surface-sunken token", () => {
  assert.match(css, /body\s*{[^}]*background:\s*var\(--surface-sunken\)/s);
});
