const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-2: create-issue assignee input references the shared user datalist", () => {
  assert.match(html, /<input id="issue-assignee" name="assignee"[^>]*list="user-directory-options"[^>]*\/>/);
});

test("BEH-3: edit-issue assignee input references the same shared user datalist", () => {
  assert.match(html, /<input id="edit-issue-assignee" name="assignee"[^>]*list="user-directory-options"[^>]*\/>/);
});

test("exactly one shared, initially-empty datalist exists", () => {
  const matches = html.match(/<datalist id="user-directory-options"><\/datalist>/g) || [];
  assert.equal(matches.length, 1);
});

test("neither assignee input gained a required attribute", () => {
  const createTag = html.match(/<input id="issue-assignee"[^>]*\/>/)[0];
  const editTag = html.match(/<input id="edit-issue-assignee"[^>]*\/>/)[0];
  assert.doesNotMatch(createTag, /required/);
  assert.doesNotMatch(editTag, /required/);
});
