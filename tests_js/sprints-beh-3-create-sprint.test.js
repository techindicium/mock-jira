const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { validateSprintForm } = require("../static/js/board-logic.js");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-1: a create-sprint form exists in the Sprint view", () => {
  assert.match(html, /<form id="create-sprint-form">[\s\S]*?<input id="sprint-name" name="name" required \/>/);
});

test("validateSprintForm: empty/whitespace name is invalid", () => {
  assert.equal(validateSprintForm("").valid, false);
  assert.equal(validateSprintForm("   ").valid, false);
});

test("validateSprintForm: non-empty name is valid", () => {
  assert.equal(validateSprintForm("Sprint 1").valid, true);
});
