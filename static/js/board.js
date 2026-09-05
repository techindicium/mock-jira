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

  async function loadIssuesFor(projectId) {
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
    const defaultProject = BoardLogic.pickDefaultProject(projects, getLastSelectedKey());
    if (!defaultProject) {
      // Task 7 fills in the empty-state branch here.
      return;
    }
    board.hidden = false;
    renderSwitcher(projects, defaultProject.id);
    await loadIssuesFor(defaultProject.id);
  }

  window.BoardApp = {
    fetchJson, showError, clearError, renderSwitcher, renderColumns, renderBoardState,
    loadIssuesFor, init, getLastSelectedKey, setLastSelectedKey, onProjectSwitch,
  };

  document.addEventListener("DOMContentLoaded", init);
  document.getElementById("project-switcher").addEventListener("change", onProjectSwitch);
})();
