const test = require("node:test");
const assert = require("node:assert/strict");
const { buildCardHtml } = require("../static/js/board-logic.js");

test("BEH-3: card markup includes the escaped issue key", () => {
  const html = buildCardHtml({
    id: 1, key: "ASSIST-42", summary: "x", issue_type: "task", priority: "low", assignee: "",
  });
  assert.match(html, /ASSIST-42/);
});

test("BEH-3: a missing key renders as empty, not the string undefined", () => {
  const html = buildCardHtml({ id: 1, summary: "x", issue_type: "task", priority: "low", assignee: "" });
  assert.doesNotMatch(html, /undefined/);
});

test("BEH-3: issue key is HTML-escaped like every other interpolated field", () => {
  const html = buildCardHtml({
    id: 1, key: "<script>", summary: "x", issue_type: "task", priority: "low", assignee: "",
  });
  assert.doesNotMatch(html, /<script>/);
});
