const test = require("node:test");
const assert = require("node:assert/strict");
const { validateUserForm, extractUserSubmitError, buildUserCreatePayload } =
  require("../static/js/board-logic.js");

test("BEH-4/UI_VALIDATION_ERROR: blocks submit when name is blank or whitespace-only", () => {
  assert.equal(validateUserForm("").valid, false);
  assert.equal(validateUserForm("   ").valid, false);
  assert.equal(validateUserForm(undefined).valid, false);
});

test("BEH-4: a non-blank name is valid", () => {
  assert.equal(validateUserForm("Mei Tan").valid, true);
});

test("BEH-5/UI_USER_EMAIL_DUPLICATE: maps a 409 to an inline email error using the API's message", () => {
  const result = extractUserSubmitError(409, { message: "Email 'x@y.com' already exists" });
  assert.equal(result.field, "email");
  assert.equal(result.message, "Email 'x@y.com' already exists");
});

test("BEH-5/UI_VALIDATION_ERROR: maps a server-side 422 to a form-level error", () => {
  const result = extractUserSubmitError(422, { message: "name is required" });
  assert.equal(result.field, "form");
  assert.equal(result.message, "name is required");
});

test("extractUserSubmitError returns null for a successful status", () => {
  assert.equal(extractUserSubmitError(201, {}), null);
});

test("extractUserSubmitError falls back to a generic message when the body carries none", () => {
  const result = extractUserSubmitError(409, null);
  assert.equal(result.message, "That email is already taken.");
});

test("buildUserCreatePayload always includes name, includes email/role only when non-blank", () => {
  assert.deepEqual(buildUserCreatePayload({ name: "Mei Tan", email: "", role: "" }), { name: "Mei Tan" });
  assert.deepEqual(
    buildUserCreatePayload({ name: "Mei Tan", email: "mei@x.com", role: "Engineer" }),
    { name: "Mei Tan", email: "mei@x.com", role: "Engineer" }
  );
});
