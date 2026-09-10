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

test("BEH-2 (dead-end fix): a cancel-sprint control exists for the oldest unstarted planned sprint", () => {
  // Without this, once a planned Sprint exists, every later-created Sprint is permanently
  // unreachable — "Start sprint" always targets the oldest planned one, and "Close sprint"
  // only ever appears for an already-active Sprint. Reproduced live: creating Alpha then Beta
  // left no control anywhere referencing Beta.
  assert.match(html, /<button id="cancel-sprint" type="button" hidden>[^<]*<\/button>/);
});
