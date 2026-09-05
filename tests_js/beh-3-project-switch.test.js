const test = require("node:test");
const assert = require("node:assert/strict");
const { computeBoardState } = require("../static/js/board-logic.js");

test("BEH-3: board state for a project holds only that project's issues", () => {
  const stateA = computeBoardState(1, [{ id: 10, status: "todo" }]);
  const stateB = computeBoardState(2, [{ id: 20, status: "done" }]);
  assert.equal(stateA.projectId, 1);
  assert.equal(stateB.projectId, 2);
  assert.equal(stateA.columns.todo.length, 1);
  assert.equal(stateB.columns.todo.length, 0);
  // Recomputing for project 2 never carries project 1's issue forward.
  assert.deepEqual(stateB.columns.done.map((i) => i.id), [20]);
});

test("BEH-3: switching to an empty project fully clears prior columns", () => {
  const state = computeBoardState(3, []);
  assert.deepEqual(state.columns.todo, []);
  assert.deepEqual(state.columns.in_progress, []);
  assert.deepEqual(state.columns.done, []);
});
