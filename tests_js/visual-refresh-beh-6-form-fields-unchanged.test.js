const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-6: create-project required fields are unchanged", () => {
  assert.match(html, /<input id="project-key" name="key" required/);
  assert.match(html, /<input id="project-name" name="name" required/);
});

test("BEH-6: create-issue required fields are unchanged", () => {
  assert.match(html, /<input id="issue-summary" name="summary" required/);
  assert.match(html, /<select id="issue-type" name="issue_type" required/);
  assert.match(html, /<select id="issue-priority" name="priority" required/);
});

test("BEH-6: create-issue optional fields carry no required attribute", () => {
  assert.match(html, /<textarea id="issue-description" name="description"><\/textarea>/);
  // user-picker.spec.md added a `list="user-directory-options"` attribute here (additive
  // markup only) — this assertion is relaxed to tolerate it while still proving the field
  // carries no `required` attribute, id, or name change.
  const assigneeTag = html.match(/<input id="issue-assignee"[^>]*\/>/)[0];
  assert.match(assigneeTag, /name="assignee"/);
  assert.doesNotMatch(assigneeTag, /required/);
});

test("BEH-6: edit-issue fields carry no required attribute (issue-crud-forms Preconditions)", () => {
  const start = html.indexOf('id="edit-issue-form"');
  const editBlock = html.slice(start, html.indexOf("</form>", start));
  assert.doesNotMatch(editBlock, /required/);
});
