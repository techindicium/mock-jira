const test = require("node:test");
const assert = require("node:assert/strict");
const { buildUserOptionsHtml } = require("../static/js/board-logic.js");

test("BEH-2/BEH-3: builds one <option> per User, escaped, value = name", () => {
  const html = buildUserOptionsHtml([
    { id: 1, name: "Mei Tan" },
    { id: 2, name: 'A & B <script>' },
  ]);
  assert.match(html, /<option value="Mei Tan">/);
  assert.match(html, /<option value="A &amp; B &lt;script&gt;">/);
});

test("BEH-2/BEH-3: skips Users with a blank/missing name", () => {
  const html = buildUserOptionsHtml([{ id: 1, name: "" }, { id: 2 }, { id: 3, name: "Kofi Adjei" }]);
  assert.equal((html.match(/<option/g) || []).length, 1);
  assert.match(html, /Kofi Adjei/);
});

test("BEH-2/BEH-3: returns an empty string for a non-array/empty input", () => {
  assert.equal(buildUserOptionsHtml(undefined), "");
  assert.equal(buildUserOptionsHtml([]), "");
});
