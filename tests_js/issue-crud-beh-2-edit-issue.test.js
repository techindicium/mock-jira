const test = require("node:test");
const assert = require("node:assert/strict");
const { diffIssueFields } = require("../static/js/board-logic.js");

const original = {
  id: 5, summary: "Old summary", description: "Old desc", issue_type: "bug",
  priority: "low", assignee: "dana", reporter: "sam",
};

test("BEH-2: only changed fields appear in the patch payload", () => {
  const patch = diffIssueFields(original, { ...original, summary: "New summary" });
  assert.deepEqual(patch, { summary: "New summary" });
});

test("BEH-2: multiple changed fields are all included", () => {
  const patch = diffIssueFields(original, { ...original, priority: "high", assignee: "dee" });
  assert.deepEqual(patch, { priority: "high", assignee: "dee" });
});

test("BEH-2: unchanged fields produce an empty patch payload", () => {
  assert.deepEqual(diffIssueFields(original, { ...original }), {});
});

test("BEH-2: status is never part of the diff — column move owns status changes", () => {
  const patch = diffIssueFields(original, { ...original, summary: "New", status: "done" });
  assert.equal("status" in patch, false);
});
