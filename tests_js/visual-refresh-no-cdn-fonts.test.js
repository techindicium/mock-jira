const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");
const css = readFileSync(require.resolve("../static/css/board.css"), "utf8");

test("offline-only: no external stylesheet/font link in index.html", () => {
  assert.doesNotMatch(html, /<link[^>]+href=["']https?:\/\//);
});

test("offline-only: no remote @font-face in board.css", () => {
  assert.doesNotMatch(css, /@font-face[^}]*url\(\s*["']?https?:\/\//s);
});

test("offline-only: font-family stacks end in a generic system fallback", () => {
  const families = [...css.matchAll(/font-family:\s*([^;]+);/g)]
    .map((m) => m[1])
    .filter((stack) => stack.trim() !== "inherit"); // inherit is not a stack declaration
  assert.ok(families.length > 0, "expected at least one font-family stack declaration");
  for (const stack of families) assert.match(stack, /sans-serif|monospace/);
});
