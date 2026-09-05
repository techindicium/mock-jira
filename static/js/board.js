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

  window.BoardApp = { fetchJson, showError, clearError };
})();
