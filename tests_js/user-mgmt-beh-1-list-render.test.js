const test = require("node:test");
const assert = require("node:assert/strict");
const { buildUserListHtml } = require("../static/js/board-logic.js");

test("BEH-1: renders one ledger row per User with name, email, role", () => {
  const html = buildUserListHtml([
    { id: 1, name: "Mei Tan", email: "mei.tan@portwell.example", role: "Head of Engineering" },
  ]);
  assert.match(html, /class="ledger-row"/);
  assert.match(html, /Mei Tan/);
  assert.match(html, /mei\.tan@portwell\.example/);
  assert.match(html, /Head of Engineering/);
});

test("BEH-1: missing email/role render as an em dash placeholder, not 'undefined'", () => {
  const html = buildUserListHtml([{ id: 2, name: "No Contact Info" }]);
  assert.doesNotMatch(html, /undefined/);
  assert.match(html, /—/);
});

test("BEH-1: escapes HTML-significant characters", () => {
  const html = buildUserListHtml([{ id: 3, name: "<script>alert(1)</script>" }]);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
});

test("BEH-1: a non-array input renders as an empty string, never throws", () => {
  assert.equal(buildUserListHtml(undefined), "");
  assert.equal(buildUserListHtml(null), "");
});

test("BEH-2: zero Users renders no rows (empty-state hook)", () => {
  assert.equal(buildUserListHtml([]), "");
});
