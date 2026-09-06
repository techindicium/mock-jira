const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCardHtml } = require("../static/js/board-logic.js");

test("BEH-2: known priorities get their own data-priority attribute", () => {
  for (const p of ["low", "medium", "high"]) {
    const html = buildCardHtml({
      id: 1, summary: "x", issue_type: "task", priority: p, assignee: "",
    });
    assert.match(html, new RegExp(`data-priority="${p}"`));
  }
});

test("UI_STYLE_UNKNOWN_PRIORITY: unrecognized priority falls back to a neutral attribute", () => {
  const html = buildCardHtml({
    id: 1, summary: "x", issue_type: "task", priority: "urgent!!", assignee: "",
  });
  assert.match(html, /data-priority="unknown"/);
});

test("UI_STYLE_UNKNOWN_PRIORITY: missing priority falls back to a neutral attribute", () => {
  const html = buildCardHtml({ id: 1, summary: "x", issue_type: "task", assignee: "" });
  assert.match(html, /data-priority="unknown"/);
});
