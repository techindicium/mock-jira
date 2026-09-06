import pytest

from tests_e2e.servers import start_issue_tracker_api


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
