import pytest

from app.seed import SEED_ISSUES, SEED_PROJECT, SeedError, _validate_seed_data

_CANON_ASSIST_NAMES = {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto"}


def test_seed_project_key_and_name_are_not_placeholder_text():
    assert SEED_PROJECT["key"] == "ASSIST"
    assert SEED_PROJECT["name"] == "Portwell Assist Engineering"
    assert "lorem" not in SEED_PROJECT["description"].lower()


def test_seed_issues_use_real_canon_names():
    for issue in SEED_ISSUES:
        assert issue["assignee"] in _CANON_ASSIST_NAMES
        assert issue["reporter"] in _CANON_ASSIST_NAMES


def test_validate_seed_data_passes_for_shipped_fixture():
    _validate_seed_data(SEED_PROJECT, SEED_ISSUES)  # must not raise


def test_validate_seed_data_rejects_canon_reserved_key_prefix():
    bad_project = {**SEED_PROJECT, "key": "ACCOUNT-1"}
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(bad_project, SEED_ISSUES)
    assert exc_info.value.code == "SEED_DATA_INVALID"


def test_validate_seed_data_rejects_invalid_status():
    bad_issues = [dict(SEED_ISSUES[0], status="blocked")] + SEED_ISSUES[1:]
    with pytest.raises(SeedError) as exc_info:
        _validate_seed_data(SEED_PROJECT, bad_issues)
    assert exc_info.value.code == "SEED_DATA_INVALID"


def test_fresh_startup_seeds_one_project_and_six_issues(client):
    projects = client.get("/projects").json()
    assert len(projects) == 1
    project = projects[0]
    assert project["key"] == "ASSIST"
    assert project["name"] == "Portwell Assist Engineering"

    issues = client.get("/issues", params={"project_id": project["id"]}).json()
    assert len(issues) == 6

    statuses = [i["status"] for i in issues]
    assert statuses.count("todo") == 2
    assert statuses.count("in_progress") == 2
    assert statuses.count("done") == 2

    assert {i["issue_type"] for i in issues} == {"bug", "task", "story"}
    assert {i["priority"] for i in issues} == {"low", "medium", "high"}

    for issue in issues:
        assert issue["summary"].strip() != ""
        assert "lorem" not in issue["summary"].lower()
        assert "lorem" not in issue["description"].lower()
        assert not issue["key"].startswith((
            "ACCOUNT-", "TICKET-", "ARTICLE-", "PROPOSAL-", "INCIDENT-",
            "POLICY-", "OPPORTUNITY-", "EXPERIMENT-", "P-",
        ))


def test_seed_if_empty_raises_seed_db_not_writable_when_connection_is_read_only(tmp_path):
    from app.db import create_schema, get_connection
    from app.seed import seed_if_empty

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("PRAGMA query_only = ON")  # simulate an unwritable database, no chmod needed

    with pytest.raises(SeedError) as exc_info:
        seed_if_empty(conn, str(db_path))
    assert exc_info.value.code == "SEED_DB_NOT_WRITABLE"
    assert str(db_path) in str(exc_info.value)
