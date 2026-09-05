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

  return { BOARD_COLUMNS, escapeHtml, groupIssuesByStatus, buildCardHtml };
});
