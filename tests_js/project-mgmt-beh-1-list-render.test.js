const test = require("node:test");
const assert = require("node:assert/strict");
const { buildProjectListHtml, buildProjectCreatePayload } = require("../static/js/board-logic.js");

test("BEH-1: renders one ledger row per Project with key, name, description", () => {
  const html = buildProjectListHtml([
    { id: 1, key: "ASSIST", name: "Portwell Assist Engineering", description: "Support pilot" },
  ]);
  assert.match(html, /class="ledger-row"/);
  assert.match(html, /class="ledger-key">ASSIST/);
  assert.match(html, /Portwell Assist Engineering/);
  assert.match(html, /Support pilot/);
});

test("BEH-1: a blank description renders as an em dash placeholder, not empty/undefined", () => {
  const html = buildProjectListHtml([{ id: 2, key: "EMPTY", name: "No Description", description: "" }]);
  assert.doesNotMatch(html, /undefined/);
  assert.match(html, /—/);
});

test("BEH-1: escapes HTML-significant characters", () => {
  const html = buildProjectListHtml([{ id: 3, key: "X", name: "<b>bold</b>", description: "" }]);
  assert.doesNotMatch(html, /<b>/);
  assert.match(html, /&lt;b&gt;/);
});

test("BEH-1: a non-array input renders as an empty string, never throws", () => {
  assert.equal(buildProjectListHtml(undefined), "");
  assert.equal(buildProjectListHtml(null), "");
});

test("BEH-2: zero Projects renders no rows (empty-state hook)", () => {
  assert.equal(buildProjectListHtml([]), "");
});

test("buildProjectCreatePayload always includes key/name, includes description only when non-blank", () => {
  assert.deepEqual(
    buildProjectCreatePayload({ key: "ASSIST", name: "Portwell Assist", description: "" }),
    { key: "ASSIST", name: "Portwell Assist" }
  );
  assert.deepEqual(
    buildProjectCreatePayload({ key: "ASSIST", name: "Portwell Assist", description: "desc" }),
    { key: "ASSIST", name: "Portwell Assist", description: "desc" }
  );
});
