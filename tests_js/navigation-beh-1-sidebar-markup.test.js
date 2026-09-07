const test = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");

const html = readFileSync(require.resolve("../static/index.html"), "utf8");

test("BEH-1: sidebar has three nav items in sentence case, Board active by default", () => {
  assert.match(html, /<nav class="sidebar"/);
  assert.match(html, /<button type="button" class="nav-item active" id="nav-board" data-view="board"/);
  assert.match(html, /<button type="button" class="nav-item" id="nav-users" data-view="users">Users<\/button>/);
  assert.match(html, /<button type="button" class="nav-item" id="nav-projects" data-view="projects">Projects<\/button>/);
  // sentence case, no ALL-CAPS labels
  assert.doesNotMatch(html, />BOARD</);
  assert.doesNotMatch(html, />USERS</);
  assert.doesNotMatch(html, />PROJECTS</);
});

test("Postconditions: existing board-view/issue-crud-forms DOM hooks are preserved, just relocated", () => {
  assert.match(html, /<section id="view-board" class="view">/);
  assert.match(html, /<div id="board-error" role="alert" hidden><\/div>/);
  assert.match(html, /<main id="board" hidden>/);
  assert.match(html, /<select id="project-switcher" aria-label="Select project"><\/select>/);
  assert.match(html, /<section id="create-issue" hidden>/);
  assert.match(html, /<section id="edit-issue" hidden>/);
});

test("BEH-2: Users/Projects view containers exist, hidden by default", () => {
  assert.match(html, /<section id="view-users" class="view" hidden>/);
  assert.match(html, /<section id="view-projects" class="view" hidden>/);
});
