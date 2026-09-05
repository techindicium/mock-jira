const test = require("node:test");
const assert = require("node:assert/strict");
const { pickDefaultProject } = require("../static/js/board-logic.js");

const projects = [
  { id: 1, key: "SDLC", name: "SDLC Track" },
  { id: 2, key: "DDLC", name: "DDLC Track" },
];

test("BEH-1: defaults to the first project when nothing was remembered", () => {
  assert.equal(pickDefaultProject(projects, null).id, 1);
});

test("BEH-1: defaults to the last-selected project when it still exists", () => {
  assert.equal(pickDefaultProject(projects, "DDLC").id, 2);
});

test("BEH-1: falls back to the first project when the remembered key is gone", () => {
  assert.equal(pickDefaultProject(projects, "GONE").id, 1);
});

test("BEH-1: returns null for zero projects (BEH-6 empty-state hook)", () => {
  assert.equal(pickDefaultProject([], null), null);
});
