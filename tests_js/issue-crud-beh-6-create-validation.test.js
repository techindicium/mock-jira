const test = require("node:test");
const assert = require("node:assert/strict");
const { validateIssueForm } = require("../static/js/board-logic.js");

test("BEH-6/UI_VALIDATION_ERROR: blocks submit when summary, type, or priority is blank", () => {
  assert.equal(validateIssueForm({ summary: "", issue_type: "bug", priority: "high" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "", priority: "high" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "bug", priority: "" }).valid, false);
  assert.equal(validateIssueForm({ summary: "Fix it", issue_type: "bug", priority: "high" }).valid, true);
});

test("BEH-6/UI_VALIDATION_ERROR: names every missing required field", () => {
  const result = validateIssueForm({ summary: "  ", issue_type: "", priority: "low" });
  assert.ok(result.errors.summary);
  assert.ok(result.errors.issue_type);
  assert.equal(result.errors.priority, undefined);
});

test("optional fields (description, assignee) never block submission", () => {
  const result = validateIssueForm({
    summary: "Fix it", issue_type: "bug", priority: "high", description: "", assignee: "",
  });
  assert.equal(result.valid, true);
});
