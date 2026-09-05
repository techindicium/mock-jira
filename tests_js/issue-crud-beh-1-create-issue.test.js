const test = require("node:test");
const assert = require("node:assert/strict");
const { buildIssueCreatePayload } = require("../static/js/board-logic.js");

test("BEH-1: assembles the required fields plus the implicit project id", () => {
  const payload = buildIssueCreatePayload(3, {
    summary: "Fix login bug", issue_type: "bug", priority: "high",
  });
  assert.deepEqual(payload, {
    project_id: 3, summary: "Fix login bug", issue_type: "bug", priority: "high",
  });
});

test("BEH-1: includes optional description/assignee only when non-blank", () => {
  const withOptional = buildIssueCreatePayload(3, {
    summary: "A", issue_type: "task", priority: "low", description: "Details", assignee: "dee",
  });
  assert.equal(withOptional.description, "Details");
  assert.equal(withOptional.assignee, "dee");

  const withoutOptional = buildIssueCreatePayload(3, {
    summary: "A", issue_type: "task", priority: "low", description: "", assignee: "  ",
  });
  assert.equal("description" in withoutOptional, false);
  assert.equal("assignee" in withoutOptional, false);
});

test("BEH-1: never sends a status field — the server always defaults to todo", () => {
  const payload = buildIssueCreatePayload(3, { summary: "A", issue_type: "task", priority: "low" });
  assert.equal("status" in payload, false);
});
