const test = require("node:test");
const assert = require("node:assert/strict");
const { formatFetchError } = require("../static/js/board-logic.js");

test("BEH-5: names the failed action and the server message on an HTTP error", () => {
  const msg = formatFetchError("Loading issues", { status: 500, message: "boom" });
  assert.match(msg, /Loading issues/);
  assert.match(msg, /500/);
  assert.match(msg, /boom/);
});

test("BEH-5: falls back to a network-error message with no status", () => {
  const msg = formatFetchError("Loading projects", { message: "Failed to fetch" });
  assert.match(msg, /Loading projects/);
  assert.match(msg, /Failed to fetch/);
});

test("BEH-5: never returns an empty message even with a bare error", () => {
  const msg = formatFetchError("Loading projects", {});
  assert.ok(msg && msg.length > 0);
});
