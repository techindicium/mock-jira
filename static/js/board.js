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
  }

  function renderBoardState(state) {
    renderColumns(state.columns);
  }

  let currentProjectId = null;

  async function loadIssuesFor(projectId) {
    currentProjectId = projectId;
    try {
      const issues = await fetchJson(`/issues?project_id=${projectId}`);
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

  async function init() {
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
    onCreateProjectSubmit, onCreateIssueSubmit,
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
})();
