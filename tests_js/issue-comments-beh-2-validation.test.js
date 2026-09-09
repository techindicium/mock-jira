const test = require("node:test");
const assert = require("node:assert/strict");
const { validateCommentForm } = require("../static/js/board-logic.js");

test("BEH-5: empty body is invalid", () => {
  assert.equal(validateCommentForm("").valid, false);
  assert.equal(validateCommentForm("   ").valid, false);
});

test("BEH-4: non-empty body is valid", () => {
  assert.equal(validateCommentForm("looks good").valid, true);
});
