const test = require("node:test");
const assert = require("node:assert/strict");
const { isNotFoundError, formatIssueGoneMessage, formatFetchError } =
  require("../static/js/board-logic.js");

test("BEH-5/UI_ISSUE_NOT_FOUND: a 404 mutation error is classified as not-found", () => {
  assert.equal(isNotFoundError({ status: 404, message: "Issue 7 not found" }), true);
});

test("BEH-5/UI_ISSUE_NOT_FOUND: a 5xx or network error is not classified as not-found", () => {
  assert.equal(isNotFoundError({ status: 500, message: "boom" }), false);
  assert.equal(isNotFoundError({ message: "Failed to fetch" }), false);
});

test("BEH-5/UI_ISSUE_NOT_FOUND: names the action and notes the card was already gone", () => {
  const msg = formatIssueGoneMessage("Updating issue");
  assert.match(msg, /Updating issue/);
  assert.match(msg, /already/i);
});

test("BEH-5/UI_FETCH_FAILED: generic failures still use the existing formatter", () => {
  const msg = formatFetchError("Moving issue", { status: 500, message: "boom" });
  assert.match(msg, /Moving issue/);
  assert.match(msg, /500/);
});
