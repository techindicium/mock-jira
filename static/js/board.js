(function () {
  async function fetchJson(url, options) {
    let resp;
    try {
      resp = await fetch(url, options);
    } catch (networkErr) {
      throw { message: networkErr.message };
    }
    if (!resp.ok) {
      let body = null;
      try {
        body = await resp.json();
      } catch (_parseErr) {
        // non-JSON error body — body stays null, message falls back below
      }
      throw { status: resp.status, message: body && body.message };
    }
    return resp.status === 204 ? null : resp.json();
  }

  function showError(message) {
    const banner = document.getElementById("board-error");
    banner.textContent = message;
    banner.hidden = false;
  }

  function clearError() {
    const banner = document.getElementById("board-error");
    banner.hidden = true;
  }

  const LAST_PROJECT_KEY = "kanban-ui:lastProjectKey";

  function getLastSelectedKey() {
    try {
      return window.localStorage.getItem(LAST_PROJECT_KEY);
    } catch (_e) {
      return null; // private browsing / storage disabled — in-memory-only fallback
    }
  }

  function setLastSelectedKey(key) {
    try {
      window.localStorage.setItem(LAST_PROJECT_KEY, key);
    } catch (_e) {
      // storage unavailable — selection just won't persist across reloads
    }
  }

  function renderSwitcher(projects, selectedId) {
    const select = document.getElementById("project-switcher");
    select.innerHTML = projects
      .map((p) => {
        const sel = p.id === selectedId ? " selected" : "";
        return `<option value="${p.id}" data-key="${BoardLogic.escapeHtml(p.key)}"${sel}>` +
          `${BoardLogic.escapeHtml(p.key)} — ${BoardLogic.escapeHtml(p.name)}</option>`;
      })
      .join("");
  }

  function renderColumns(grouped) {
    for (const col of BoardLogic.BOARD_COLUMNS) {
      document.getElementById(`col-${col.status}`).innerHTML =
        grouped[col.status].map(BoardLogic.buildCardHtml).join("");
    }
    const counts = BoardLogic.columnCounts(grouped);
    for (const status of Object.keys(counts)) {
      const badge = document.getElementById(`count-${status}`);
      if (badge) badge.textContent = String(counts[status]);
    }
  }

  function renderBoardState(state) {
    renderColumns(state.columns);
  }

  let currentProjectId = null;
  let currentIssues = [];
  let editingIssue = null; // the full IssueRead currently loaded into the edit form

  async function loadIssuesFor(projectId) {
    currentProjectId = projectId;
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
      currentIssues = issues;
      clearError();
      renderBoardState(BoardLogic.computeBoardState(projectId, issues));
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading issues", err));
    }
  }

  function onProjectSwitch(event) {
    const projectId = Number(event.target.value);
    const selectedOption = event.target.selectedOptions[0];
    if (selectedOption) setLastSelectedKey(selectedOption.dataset.key);
    loadIssuesFor(projectId);
  }

  let cachedUsers = [];

  function renderUserDatalist(users) {
    const datalist = document.getElementById("user-directory-options");
    if (datalist) datalist.innerHTML = BoardLogic.buildUserOptionsHtml(users);
  }

  async function loadUsers() {
    let users;
    try {
      users = await fetchJson("/users");
    } catch (_err) {
      users = null; // BEH-6: degrade silently — no board-error banner for this convenience source
    }
    cachedUsers = BoardLogic.usersOrEmptyOnFailure(users);
    renderUserDatalist(cachedUsers);
  }

  async function init() {
    loadUsers(); // BEH-1: fetch GET /users exactly once per board load; never blocks board render
    let projects;
    try {
      projects = await fetchJson("/projects");
      clearError();
    } catch (err) {
      showError(BoardLogic.formatFetchError("Loading projects", err));
      return;
    }
    const board = document.getElementById("board");
    const emptyState = document.getElementById("empty-state");
    if (BoardLogic.shouldShowEmptyState(projects)) {
      board.hidden = true;
      emptyState.hidden = false;
      return; // BEH-6: prompt to create, not an error, not a blank screen
    }
    emptyState.hidden = true;
    const defaultProject = BoardLogic.pickDefaultProject(projects, getLastSelectedKey());
    board.hidden = false;
    renderSwitcher(projects, defaultProject.id);
    await loadIssuesFor(defaultProject.id);
  }

  function reportIssueMutationFailure(action, err, onNotFound) {
    if (BoardLogic.isNotFoundError(err)) {
      if (typeof onNotFound === "function") onNotFound();
      showError(BoardLogic.formatIssueGoneMessage(action));
      return;
    }
    showError(BoardLogic.formatFetchError(action, err));
  }

  function showFormError(message) {
    const el = document.getElementById("create-project-error");
    el.textContent = message;
    el.hidden = false;
  }

  function clearFormError() {
    document.getElementById("create-project-error").hidden = true;
  }

  async function onCreateProjectSubmit(event) {
    event.preventDefault();
    const keyInput = document.getElementById("project-key");
    const nameInput = document.getElementById("project-name");
    const { valid, errors } = BoardLogic.validateProjectForm(keyInput.value, nameInput.value);
    if (!valid) {
      showFormError(Object.values(errors)[0]);
      return; // client-side block — input is not cleared, no request sent (UI_VALIDATION_ERROR)
    }
    clearFormError();
    let resp;
    try {
      resp = await fetch("/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: keyInput.value, name: nameInput.value }),
      });
    } catch (networkErr) {
      showError(BoardLogic.formatFetchError("Creating project", { message: networkErr.message }));
      return;
    }
    const body = await resp.json().catch(() => null);
    if (!resp.ok) {
      const submitErr = BoardLogic.extractProjectSubmitError(resp.status, body);
      showFormError(submitErr ? submitErr.message : "Could not create the project.");
      return; // input is not cleared on error, per the spec's Error Cases table
    }
    keyInput.value = "";
    nameInput.value = "";
    setLastSelectedKey(body.key);
    // Re-run init()'s project list + selection so the new project appears and is selected
    // (pickDefaultProject will now find `body.key` as the remembered selection).
    await init();
  }

  window.BoardApp = {
    fetchJson, showError, clearError, renderSwitcher, renderColumns, renderBoardState,
    loadIssuesFor, init, getLastSelectedKey, setLastSelectedKey, onProjectSwitch,
    onCreateProjectSubmit, onCreateIssueSubmit, onCardClick, onEditIssueSubmit,
    onDragStart, onColumnDrop, onDeleteIssueClick, reportIssueMutationFailure,
    loadUsers, renderUserDatalist,
  };

  document.addEventListener("DOMContentLoaded", init);
  document.getElementById("project-switcher").addEventListener("change", onProjectSwitch);
  document.getElementById("create-project-form").addEventListener("submit", onCreateProjectSubmit);

  document.getElementById("open-create-issue").addEventListener("click", () => {
    document.getElementById("create-issue").hidden = false;
  });
  document.getElementById("cancel-create-issue").addEventListener("click", (event) => {
    event.preventDefault();
    document.getElementById("create-issue-form").reset();
    document.getElementById("create-issue-error").hidden = true;
    document.getElementById("create-issue").hidden = true;
  });

  async function onCreateIssueSubmit(event) {
    event.preventDefault();
    const fields = {
      summary: document.getElementById("issue-summary").value,
      issue_type: document.getElementById("issue-type").value,
      priority: document.getElementById("issue-priority").value,
      description: document.getElementById("issue-description").value,
      assignee: document.getElementById("issue-assignee").value,
    };
    const { valid, errors } = BoardLogic.validateIssueForm(fields);
    const errorEl = document.getElementById("create-issue-error");
    if (!valid) {
      errorEl.textContent = Object.values(errors)[0];
      errorEl.hidden = false;
      return; // client-side block — no request sent (UI_VALIDATION_ERROR)
    }
    errorEl.hidden = true;
    try {
      await fetchJson("/issues", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(BoardLogic.buildIssueCreatePayload(currentProjectId, fields)),
      });
    } catch (err) {
      showError(BoardLogic.formatFetchError("Creating issue", err));
      return; // form stays open with prior input intact
    }
    document.getElementById("create-issue-form").reset();
    document.getElementById("create-issue").hidden = true;
    await loadIssuesFor(currentProjectId); // new issue is always todo — reload shows it there
  }

  document.getElementById("create-issue-form").addEventListener("submit", onCreateIssueSubmit);

  function openEditIssue(issue) {
    editingIssue = issue;
    document.getElementById("edit-issue-id").value = issue.id;
    document.getElementById("edit-issue-summary").value = issue.summary;
    document.getElementById("edit-issue-type").value = issue.issue_type;
    document.getElementById("edit-issue-priority").value = issue.priority;
    document.getElementById("edit-issue-description").value = issue.description;
    document.getElementById("edit-issue-assignee").value = issue.assignee;
    document.getElementById("edit-issue-error").hidden = true;
    document.getElementById("edit-issue").hidden = false;
  }

  function onCardClick(event) {
    const card = event.target.closest(".card");
    if (!card) return;
    const issue = currentIssues.find((i) => i.id === Number(card.dataset.issueId));
    if (issue) openEditIssue(issue);
  }

  async function onEditIssueSubmit(event) {
    event.preventDefault();
    const edited = {
      ...editingIssue,
      summary: document.getElementById("edit-issue-summary").value,
      issue_type: document.getElementById("edit-issue-type").value,
      priority: document.getElementById("edit-issue-priority").value,
      description: document.getElementById("edit-issue-description").value,
      assignee: document.getElementById("edit-issue-assignee").value,
    };
    const patch = BoardLogic.diffIssueFields(editingIssue, edited);
    if (Object.keys(patch).length === 0) {
      document.getElementById("edit-issue").hidden = true;
      return; // nothing changed — close quietly, no network call
    }
    try {
      await fetchJson(`/issues/${editingIssue.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(patch),
      });
    } catch (err) {
      reportIssueMutationFailure("Updating issue", err, () => {
        document.getElementById("edit-issue").hidden = true;
        loadIssuesFor(currentProjectId); // 404: card is gone — refresh removes it from view
      });
      return; // non-404 failure: form stays open, prior input intact (nothing was optimistic)
    }
    document.getElementById("edit-issue").hidden = true;
    await loadIssuesFor(currentProjectId); // reflect the server's response, not the local edit
  }

  document.getElementById("board").addEventListener("click", onCardClick);
  document.getElementById("edit-issue-form").addEventListener("submit", onEditIssueSubmit);
  document.getElementById("cancel-edit-issue").addEventListener("click", (event) => {
    event.preventDefault();
    document.getElementById("edit-issue").hidden = true;
  });

  function onDragStart(event) {
    const card = event.target.closest(".card");
    if (!card) return;
    event.dataTransfer.setData("text/plain", card.dataset.issueId);
  }

  function onColumnDragOver(event) {
    event.preventDefault(); // required to allow a drop
    event.currentTarget.classList.add("drag-over");
  }

  function onColumnDragLeave(event) {
    event.currentTarget.classList.remove("drag-over");
  }

  async function onColumnDrop(event) {
    event.preventDefault();
    const column = event.currentTarget;
    column.classList.remove("drag-over");
    const issueId = Number(event.dataTransfer.getData("text/plain"));
    const newStatus = column.dataset.status;
    const originalIssue = currentIssues.find((i) => i.id === issueId);
    if (!originalIssue || originalIssue.status === newStatus) return;
    const originalStatus = originalIssue.status;

    currentIssues = BoardLogic.moveIssueStatus(currentIssues, issueId, newStatus);
    renderColumns(BoardLogic.groupIssuesByStatus(currentIssues)); // optimistic move

    try {
      await fetchJson(`/issues/${issueId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      clearError();
    } catch (err) {
      reportIssueMutationFailure("Moving issue", err, () => {
        // 404: the card is gone server-side — drop the optimistic move and refresh from truth
        loadIssuesFor(currentProjectId);
      });
      if (!BoardLogic.isNotFoundError(err)) {
        currentIssues = BoardLogic.moveIssueStatus(currentIssues, issueId, originalStatus);
        renderColumns(BoardLogic.groupIssuesByStatus(currentIssues)); // exact revert
      }
    }
  }

  for (const col of BoardLogic.BOARD_COLUMNS) {
    const section = document.querySelector(`.column[data-status="${col.status}"]`);
    section.addEventListener("dragover", onColumnDragOver);
    section.addEventListener("dragleave", onColumnDragLeave);
    section.addEventListener("drop", onColumnDrop);
  }
  document.getElementById("board").addEventListener("dragstart", onDragStart);

  async function onDeleteIssueClick(event) {
    event.preventDefault();
    if (!editingIssue) return;
    const confirmed = window.confirm(`Delete issue "${editingIssue.summary}"? This cannot be undone.`);
    if (!confirmed) return;
    const issueId = editingIssue.id;
    try {
      await fetchJson(`/issues/${issueId}`, { method: "DELETE" });
      clearError();
    } catch (err) {
      reportIssueMutationFailure("Deleting issue", err, () => {
        // 404: already gone — fall through to the same removal below
      });
      if (!BoardLogic.isNotFoundError(err)) {
        return; // non-404 failure: card stays, edit form stays open, error shown
      }
    }
    currentIssues = BoardLogic.removeIssueById(currentIssues, issueId);
    renderColumns(BoardLogic.groupIssuesByStatus(currentIssues));
    document.getElementById("edit-issue").hidden = true;
    editingIssue = null;
  }

  document.getElementById("delete-issue").addEventListener("click", onDeleteIssueClick);
})();
