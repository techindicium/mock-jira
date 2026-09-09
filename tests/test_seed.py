import pytest

from app.seed import (
    SEED_ISSUES,
    SEED_PROJECT,
    SEED_USERS,
    load_seed_data,
    SeedError,
    _validate_seed_data,
)

# The issue assignees and reporters: the people who touch the tracker.
_CANON_NAMES = {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto", "Ana Fialho",
                "Rui Bastos", "Gabriela Rocha", "Sofia Marques"}

# The user directory carries the whole roster, which is wider than the tracker's users.
_CANON_ROSTER = _CANON_NAMES | {"Inês Duarte", "Marta Oliveira", "Henrik Sole",
                                "Declan Byrne", "Lucia Ferreira", "Tomas Silva"}


def test_seed_project_key_and_name_are_not_placeholder_text():
    assert SEED_PROJECT["key"] == "PORTAL"
    assert SEED_PROJECT["name"] == "Help portal engineering"
    assert "lorem" not in SEED_PROJECT["description"].lower()


def test_seed_issues_use_real_canon_names():
    for issue in SEED_ISSUES:
        assert issue["assignee"] in _CANON_NAMES
        assert issue["reporter"] in _CANON_NAMES


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


def test_fresh_startup_seeds_both_projects_and_their_issues(client):
    projects = client.get("/projects").json()
    assert len(projects) == 2
    by_key = {p["key"]: p for p in projects}
    assert set(by_key) == {"PORTAL", "DATA"}

    project = by_key["PORTAL"]
    assert project["name"] == "Help portal engineering"

    issues = client.get("/issues", params={"project_id": project["id"]}).json()
    assert len(issues) == 6

    # DATA is deliberately sparse. Engineering adopted this tracker and other teams did not,
    # so it holds only the analytics requests that came from engineering.
    data_issues = client.get(
        "/issues", params={"project_id": by_key["DATA"]["id"]}
    ).json()
    assert len(data_issues) == 3

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


def test_seed_users_use_real_canon_names():
    assert len(SEED_USERS) >= 3
    for user in SEED_USERS:
        assert user["name"] in _CANON_ROSTER


def test_seed_users_if_empty_is_independent_of_project_seeding(tmp_path):
    from app.db import create_schema, get_connection
    from app.seed import seed_users_if_empty

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    # No Project/Issue seeding has run at all — User seeding must still work standalone.
    seed_users_if_empty(conn, str(db_path))
    users = conn.execute("SELECT * FROM users").fetchall()
    _, _, expected_users = load_seed_data()
    assert len(users) == len(expected_users)


def test_seed_users_if_empty_is_idempotent(tmp_path):
    from app.db import create_schema, get_connection
    from app.seed import seed_users_if_empty

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    seed_users_if_empty(conn, str(db_path))
    seed_users_if_empty(conn, str(db_path))  # second call must not duplicate
    users = conn.execute("SELECT * FROM users").fetchall()
    _, _, expected_users = load_seed_data()
    assert len(users) == len(expected_users)


def test_seeding_is_idempotent_across_restarts(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.main as main_module

    db_path = tmp_path / "restart.db"
    monkeypatch.setattr(main_module, "DB_PATH", str(db_path))

    with TestClient(main_module.app) as c1:
        first_projects = c1.get("/projects").json()

    with TestClient(main_module.app) as c2:
        second_projects = c2.get("/projects").json()
        issues = c2.get(
            "/issues", params={"project_id": second_projects[0]["id"]}
        ).json()

    assert len(first_projects) == 2
    assert len(second_projects) == 2
    assert first_projects[0]["id"] == second_projects[0]["id"]
    assert len(issues) == 6
