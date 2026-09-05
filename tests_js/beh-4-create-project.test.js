const test = require("node:test");
const assert = require("node:assert/strict");
const { validateProjectForm, extractProjectSubmitError } = require("../static/js/board-logic.js");

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

test("BEH-4/UI_PROJECT_KEY_DUPLICATE: maps a 409 to an inline key error", () => {
  const err = extractProjectSubmitError(409, {
    message: "Project key 'SDLC' already exists", code: "PROJECT_KEY_DUPLICATE",
  });
  assert.equal(err.field, "key");
  assert.match(err.message, /SDLC/);
});

test("BEH-4/UI_VALIDATION_ERROR: maps a server-side 422 to a form-level error", () => {
  const err = extractProjectSubmitError(422, { message: "name is required", code: "VALIDATION_ERROR" });
  assert.equal(err.field, "form");
});

test("extractProjectSubmitError returns null for a successful status", () => {
  assert.equal(extractProjectSubmitError(201, {}), null);
});
