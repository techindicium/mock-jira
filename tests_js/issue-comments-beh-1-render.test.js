const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCommentListHtml } = require("../static/js/board-logic.js");

test("BEH-3: renders one entry per comment, chronological order preserved from input", () => {
  const html = buildCommentListHtml([
    { id: 1, body: "first", author: "Mei Tan", created_at: "2026-09-09 10:00:00" },
    { id: 2, body: "second", author: "", created_at: "2026-09-09 10:05:00" },
  ]);
  const firstIdx = html.indexOf("first");
  const secondIdx = html.indexOf("second");
  assert.ok(firstIdx >= 0 && secondIdx > firstIdx);
  assert.match(html, /Unassigned/); // blank author, BEH-3
});

test("BEH-3: HTML-escapes comment body and author", () => {
  const html = buildCommentListHtml([{ id: 1, body: "<script>", author: "<b>", created_at: "x" }]);
  assert.doesNotMatch(html, /<script>/);
  assert.doesNotMatch(html, /<b>/);
});

test("zero comments renders an empty string", () => {
  assert.equal(buildCommentListHtml([]), "");
});
