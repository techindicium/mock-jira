import httpx
import pytest

from tests_e2e.servers import E2EServerStartTimeout, start_issue_tracker_api


def test_start_issue_tracker_api_yields_reachable_base_url(tmp_path):
    with start_issue_tracker_api(tmp_path) as base_url:
        resp = httpx.get(base_url + "/", timeout=5)
        assert resp.status_code == 200


def test_start_issue_tracker_api_tears_down_process_on_exit(tmp_path):
    with start_issue_tracker_api(tmp_path) as base_url:
        pass
    with httpx.Client(timeout=1) as client:
        try:
            client.get(base_url + "/")
            assert False, "expected connection to be refused after teardown"
        except httpx.ConnectError:
            pass


def test_start_issue_tracker_api_raises_e2e_server_start_timeout_on_unhealthy_startup(tmp_path):
    # Deliberate misuse: pass a *file* where the fixture expects a directory to place
    # the DB under. `app.main`'s on_startup catches the resulting sqlite3.OperationalError
    # ("unable to open database file") and raises RuntimeError, which fails uvicorn's
    # startup event — so the subprocess exits almost immediately, exercising the
    # "process exited early" branch of E2E_SERVER_START_TIMEOUT without waiting out
    # the full startup timeout.
    not_a_dir = tmp_path / "not_a_directory"
    not_a_dir.write_text("this is a file, not a directory, so app startup fails fast")

    with pytest.raises(E2EServerStartTimeout) as exc_info, start_issue_tracker_api(not_a_dir):
        pass  # pragma: no cover - should never be reached

    message = str(exc_info.value)
    assert "startup timeout" in message  # names the timeout
    assert "Last output" in message      # names the last-seen process output
