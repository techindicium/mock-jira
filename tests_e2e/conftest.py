import socket

import pytest

from tests_e2e.browser import launch_chromium
from tests_e2e.servers import start_issue_tracker_api, start_mcp_server


@pytest.fixture(scope="session")
def server(tmp_path_factory) -> str:
    """Session-scoped real server, shared across this repo's own e2e tests.

    Uses tmp_path_factory (not the function-scoped tmp_path fixture) so the DB
    file is fresh once per test session, per api-e2e.spec.md Preconditions.
    Tests that need a truly empty/fresh database (e.g. BEH-5 seed-on-startup)
    must NOT use this shared fixture — call start_issue_tracker_api directly
    with their own tmp_path instead.
    """
    tmp_path = tmp_path_factory.mktemp("issue-tracker-api-e2e")
    with start_issue_tracker_api(tmp_path) as base_url:
        yield base_url


@pytest.fixture(scope="session")
def mcp_dual_server(tmp_path_factory) -> tuple[str, str]:
    """Session-scoped real issue-tracker-api + real mcp-server pair, wired via API_BASE_URL.

    Shared across BEH-1 through BEH-4 (all tests that need a live, reachable upstream). Tests
    use unique project/issue keys per test to avoid cross-test collisions in the shared
    database, matching the existing `server` fixture's convention. NOT used by BEH-5, which
    needs mcp-server running with no reachable upstream at all — see mcp_server_unreachable.

    Yields:
        (api_base_url, mcp_base_url)
    """
    tmp_path = tmp_path_factory.mktemp("mcp-e2e-dual-server")
    with start_issue_tracker_api(tmp_path) as api_base_url, start_mcp_server(api_base_url) as mcp_base_url:
        yield api_base_url, mcp_base_url


@pytest.fixture
def mcp_server_unreachable() -> str:
    """Function-scoped: real mcp-server alone, API_BASE_URL pointed at a port nothing listens on.

    Deliberately NOT mcp_dual_server (per BEH-5's own dedicated-fixture requirement — no
    issue-tracker-api process is started at all here). Function-scoped since only the error-path
    tests need this topology; no shared-database concerns apply since no upstream API exists to
    hold state.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        dead_port = probe.getsockname()[1]
    dead_api_base_url = f"http://127.0.0.1:{dead_port}"
    with start_mcp_server(dead_api_base_url) as mcp_base_url:
        yield mcp_base_url


@pytest.fixture(scope="session")
def browser():
    """Session-scoped real Chromium browser, shared across all ui-e2e tests."""
    with launch_chromium() as browser:
        yield browser


@pytest.fixture
def page(browser):
    """Function-scoped browser context/tab — a fresh, isolated page per test."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def ui_board_server(tmp_path) -> str:
    """Function-scoped real server, isolated from the shared session-scoped `server` fixture.

    Deliberately NOT `server` above: ui-e2e's BEH-1 asserts the *seeded* board (exactly 2 issues
    per column) renders correctly, and BEH-2/BEH-5 verify persistence by reloading in the same
    browser — both are sensitive to any other e2e test's writes landing in a shared database.
    A fresh function-scoped server (per review note SA-1) keeps each ui-e2e test's seeded
    starting state deterministic and independent of api-e2e's tests in the same run.
    """
    with start_issue_tracker_api(tmp_path) as base_url:
        yield base_url
