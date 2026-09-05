(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.BoardLogic = factory();
  }
})(typeof window !== "undefined" ? window : globalThis, function () {
  const BOARD_COLUMNS = [
    { status: "todo", label: "To Do", ordinal: 0 },
    { status: "in_progress", label: "In Progress", ordinal: 1 },
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

  function buildCardHtml(issue) {
    return (
      `<article class="card" data-issue-id="${issue.id}">` +
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

  return {
    BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml, formatFetchError,
    pickDefaultProject, computeBoardState, validateProjectForm, extractProjectSubmitError,
    shouldShowEmptyState, isNotFoundError, formatIssueGoneMessage,
  };
});
