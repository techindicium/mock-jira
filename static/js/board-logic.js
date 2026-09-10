(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.BoardLogic = factory();
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  const BOARD_COLUMNS = [
    { status: "todo", label: "To do", ordinal: 0 },
    { status: "in_progress", label: "In progress", ordinal: 1 },
    { status: "done", label: "Done", ordinal: 2 },
  ];

  function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[ch]);
  }

  function groupIssuesByStatus(issues) {
    const grouped = {};
    for (const col of BOARD_COLUMNS) grouped[col.status] = [];
    for (const issue of Array.isArray(issues) ? issues : []) {
      if (grouped[issue.status]) grouped[issue.status].push(issue);
    }
    return grouped;
  }

  function columnCounts(grouped) {
    const counts = {};
    for (const col of BOARD_COLUMNS) counts[col.status] = grouped[col.status].length;
    return counts;
  }

  const KNOWN_PRIORITIES = ["low", "medium", "high"];

  function priorityStripeAttr(priority) {
    return KNOWN_PRIORITIES.includes(priority) ? priority : "unknown";
  }

  const FILTERABLE_FIELDS = ["assignee", "issue_type", "priority"];

  function filterIssues(issues, filters) {
    const list = Array.isArray(issues) ? issues : [];
    const active = FILTERABLE_FIELDS.filter((f) => filters && filters[f]);
    if (active.length === 0) return list;
    return list.filter((issue) => active.every((f) => issue[f] === filters[f]));
  }

  function uniqueAssignees(issues) {
    const list = Array.isArray(issues) ? issues : [];
    const names = new Set(
      list.map((i) => (i.assignee || "").trim()).filter((name) => name !== "")
    );
    return Array.from(names).sort();
  }

  function buildBacklogRowsHtml(issues) {
    if (!Array.isArray(issues)) return "";
    return issues
      .map((issue) => (
        `<tr data-issue-id="${issue.id}">` +
        `<td>${escapeHtml(issue.key || "")}</td>` +
        `<td>${escapeHtml(issue.summary)}</td>` +
        `<td>${escapeHtml(issue.issue_type)}</td>` +
        `<td>${escapeHtml(issue.priority)}</td>` +
        `<td>${escapeHtml(issue.status)}</td>` +
        `<td>${escapeHtml(issue.assignee || "Unassigned")}</td>` +
        `<td><button type="button" class="add-to-sprint" data-issue-id="${issue.id}">Add to sprint</button></td>` +
        `</tr>`
      ))
      .join("");
  }

  function buildCardHtml(issue) {
    return (
      `<article class="card" data-issue-id="${issue.id}" ` +
      `data-priority="${priorityStripeAttr(issue.priority)}" draggable="true">` +
      `<p class="card-key">${escapeHtml(issue.key || "")}</p>` +
      `<h3>${escapeHtml(issue.summary)}</h3>` +
      `<p class="card-meta">${escapeHtml(issue.issue_type)} &middot; ` +
      `${escapeHtml(issue.priority)} &middot; ` +
      `${escapeHtml(issue.assignee || "Unassigned")}</p>` +
      `</article>`
    );
  }

  function formatFetchError(action, error) {
    if (error && error.status) {
      return `${action} failed (HTTP ${error.status}): ${error.message || "unexpected error"}`;
    }
    return `${action} failed: ${(error && error.message) || "network error"}`;
  }

  function pickDefaultProject(projects, lastSelectedKey) {
    if (!Array.isArray(projects) || projects.length === 0) return null;
    if (lastSelectedKey) {
      const remembered = projects.find((p) => p.key === lastSelectedKey);
      if (remembered) return remembered;
    }
    return projects[0];
  }

  function computeBoardState(projectId, issues) {
    return { projectId, columns: groupIssuesByStatus(issues) };
  }

  function validateProjectForm(key, name) {
    const errors = {};
    if (!key || !key.trim()) errors.key = "Key is required";
    if (!name || !name.trim()) errors.name = "Name is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  function extractProjectSubmitError(status, body) {
    if (status === 409) {
      return { field: "key", message: (body && body.message) || "That project key is already taken." };
    }
    if (status === 422) {
      return { field: "form", message: (body && body.message) || "Please fill in all required fields." };
    }
    return null;
  }

  function shouldShowEmptyState(projects) {
    return !Array.isArray(projects) || projects.length === 0;
  }

  function isNotFoundError(error) {
    return !!(error && error.status === 404);
  }

  function formatIssueGoneMessage(action) {
    return `${action}: this issue was already removed. The board has been updated.`;
  }

  function validateIssueForm(fields) {
    const errors = {};
    if (!fields.summary || !fields.summary.trim()) errors.summary = "Summary is required";
    if (!fields.issue_type) errors.issue_type = "Type is required";
    if (!fields.priority) errors.priority = "Priority is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  function buildIssueCreatePayload(projectId, fields) {
    const payload = {
      project_id: projectId,
      summary: fields.summary,
      issue_type: fields.issue_type,
      priority: fields.priority,
    };
    if (fields.description && fields.description.trim()) payload.description = fields.description;
    if (fields.assignee && fields.assignee.trim()) payload.assignee = fields.assignee;
    return payload;
  }

  const EDITABLE_ISSUE_FIELDS = ["summary", "description", "issue_type", "priority", "assignee", "reporter"];

  function diffIssueFields(original, edited) {
    const patch = {};
    for (const field of EDITABLE_ISSUE_FIELDS) {
      if (edited[field] !== original[field]) patch[field] = edited[field];
    }
    return patch;
  }

  function moveIssueStatus(issues, issueId, newStatus) {
    return issues.map((issue) =>
      issue.id === issueId ? { ...issue, status: newStatus } : issue
    );
  }

  function removeIssueById(issues, issueId) {
    return issues.filter((issue) => issue.id !== issueId);
  }

  function buildUserListHtml(users) {
    if (!Array.isArray(users)) return "";
    return users
      .map((u) => (
        `<div class="ledger-row">` +
        `<span class="ledger-primary">${escapeHtml(u.name)}</span>` +
        `<span class="ledger-meta">${escapeHtml(u.email || "—")} &middot; ` +
        `${escapeHtml(u.role || "—")}</span>` +
        `</div>`
      ))
      .join("");
  }

  function buildProjectListHtml(projects) {
    if (!Array.isArray(projects)) return "";
    return projects
      .map((p) => (
        `<div class="ledger-row">` +
        `<span class="ledger-key">${escapeHtml(p.key)}</span>` +
        `<span class="ledger-primary">${escapeHtml(p.name)}</span>` +
        `<span class="ledger-meta">${escapeHtml(p.description || "—")}</span>` +
        `</div>`
      ))
      .join("");
  }

  function validateUserForm(name) {
    const errors = {};
    if (!name || !name.trim()) errors.name = "Name is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  function extractUserSubmitError(status, body) {
    if (status === 409) {
      return { field: "email", message: (body && body.message) || "That email is already taken." };
    }
    if (status === 422) {
      return { field: "form", message: (body && body.message) || "Please fill in all required fields." };
    }
    return null;
  }

  function buildUserCreatePayload(fields) {
    const payload = { name: fields.name };
    if (fields.email && fields.email.trim()) payload.email = fields.email;
    if (fields.role && fields.role.trim()) payload.role = fields.role;
    return payload;
  }

  function buildProjectCreatePayload(fields) {
    const payload = { key: fields.key, name: fields.name };
    if (fields.description && fields.description.trim()) payload.description = fields.description;
    return payload;
  }

  function buildCommentListHtml(comments) {
    if (!Array.isArray(comments)) return "";
    return comments
      .map((c) => (
        `<div class="comment-row">` +
        `<p class="comment-meta">${escapeHtml(c.author || "Unassigned")} &middot; ${escapeHtml(c.created_at)}</p>` +
        `<p class="comment-body">${escapeHtml(c.body)}</p>` +
        `</div>`
      ))
      .join("");
  }

  function validateCommentForm(body) {
    const errors = {};
    if (!body || !body.trim()) errors.body = "Comment cannot be empty";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  function buildUserOptionsHtml(users) {
    if (!Array.isArray(users)) return "";
    return users
      .filter((u) => u && u.name && u.name.trim())
      .map((u) => `<option value="${escapeHtml(u.name)}">`)
      .join("");
  }

  function usersOrEmptyOnFailure(users) {
    return Array.isArray(users) ? users : [];
  }

  function filterIssuesBySprintId(issues, sprintId) {
    if (sprintId == null) return [];
    return Array.isArray(issues) ? issues.filter((i) => i.sprint_id === sprintId) : [];
  }

  function findActiveSprint(sprints) {
    return Array.isArray(sprints) ? sprints.find((s) => s.status === "active") : null;
  }

  function validateSprintForm(name) {
    const errors = {};
    if (!name || !name.trim()) errors.name = "Name is required";
    return { valid: Object.keys(errors).length === 0, errors };
  }

  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, columnCounts, buildCardHtml, buildBacklogRowsHtml,
    filterIssues, uniqueAssignees,
    priorityStripeAttr,
    formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage, validateIssueForm,
    buildIssueCreatePayload, diffIssueFields, moveIssueStatus, removeIssueById,
    buildUserOptionsHtml, usersOrEmptyOnFailure,
    buildUserListHtml, buildProjectListHtml, validateUserForm, extractUserSubmitError,
    buildUserCreatePayload, buildProjectCreatePayload,
    buildCommentListHtml, validateCommentForm,
    filterIssuesBySprintId, findActiveSprint, validateSprintForm,
  };
});
