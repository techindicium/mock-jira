const test = require("node:test");
const assert = require("node:assert/strict");
const { validateProjectForm, extractProjectSubmitError } = require("../static/js/board-logic.js");

// These pure functions are shared logic wired to the Projects-tab add-project form
// (project-management-screen.spec.md BEH-3/BEH-4/BEH-5) — board-view.spec.md's own,
// switcher-adjacent create-project form that originally exercised this logic has been
// retired (see board-view.spec.md's retired-behavior-ids: BEH-4).

test("BEH-4/UI_VALIDATION_ERROR: blocks submit when key or name is blank", () => {
  assert.equal(validateProjectForm("", "Name").valid, false);
  assert.equal(validateProjectForm("KEY", "  ").valid, false);
  assert.equal(validateProjectForm("KEY", "Name").valid, true);
});

test("BEH-4/UI_VALIDATION_ERROR: names which field is missing", () => {
  const result = validateProjectForm("", "Name");
  assert.ok(result.errors.key);
  assert.equal(result.errors.name, undefined);
});

test("BEH-5/UI_PROJECT_KEY_DUPLICATE: maps a 409 to an inline key error", () => {
  const err = extractProjectSubmitError(409, {
    message: "Project key 'SDLC' already exists", code: "PROJECT_KEY_DUPLICATE",
  });
  assert.equal(err.field, "key");
  assert.match(err.message, /SDLC/);
});

test("BEH-5/UI_VALIDATION_ERROR: maps a server-side 422 to a form-level error", () => {
  const err = extractProjectSubmitError(422, { message: "name is required", code: "VALIDATION_ERROR" });
  assert.equal(err.field, "form");
});

test("extractProjectSubmitError returns null for a successful status", () => {
  assert.equal(extractProjectSubmitError(201, {}), null);
});
