const test = require("node:test");
const assert = require("node:assert/strict");
const { usersOrEmptyOnFailure } = require("../static/js/board-logic.js");

test("BEH-6: a successful array of Users passes through unchanged", () => {
  const users = [{ id: 1, name: "Mei Tan" }];
  assert.deepEqual(usersOrEmptyOnFailure(users), users);
});

test("BEH-6: a failed fetch (no array) degrades to an empty array, never throws", () => {
  assert.deepEqual(usersOrEmptyOnFailure(undefined), []);
  assert.deepEqual(usersOrEmptyOnFailure(null), []);
  assert.deepEqual(usersOrEmptyOnFailure({ status: 500 }), []);
});
