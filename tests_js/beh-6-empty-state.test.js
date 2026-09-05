const test = require("node:test");
const assert = require("node:assert/strict");
const { shouldShowEmptyState } = require("../static/js/board-logic.js");

test("BEH-6: zero projects shows the empty state", () => {
  assert.equal(shouldShowEmptyState([]), true);
});

test("BEH-6: any project at all means no empty state", () => {
  assert.equal(shouldShowEmptyState([{ id: 1, key: "SDLC", name: "SDLC Track" }]), false);
});

test("BEH-6: a missing/undefined projects value is treated as empty, not a crash", () => {
  assert.equal(shouldShowEmptyState(undefined), true);
});
