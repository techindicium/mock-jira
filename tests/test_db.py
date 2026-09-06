from app.db import create_schema, get_connection


def test_create_schema_creates_projects_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
    )
    assert cursor.fetchone() is not None

def test_create_schema_is_idempotent(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    create_schema(conn)  # second call must not raise or duplicate the table
    cursor = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='projects'"
    )
    assert cursor.fetchone()[0] == 1


def test_create_schema_creates_issues_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='issues'"
    )
    assert cursor.fetchone() is not None


def test_allocate_issue_key_increments_per_project_starting_at_one(tmp_path):
    from app.db import allocate_issue_key

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('SDLC', 'SDLC', '')")
    project_id = conn.execute("SELECT id FROM projects WHERE key='SDLC'").fetchone()["id"]

    assert allocate_issue_key(conn, project_id, "SDLC") == "SDLC-1"
    assert allocate_issue_key(conn, project_id, "SDLC") == "SDLC-2"


def test_create_schema_creates_users_table(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    assert cursor.fetchone() is not None


def test_users_table_allows_multiple_null_emails(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("INSERT INTO users (name, email, role) VALUES ('A', NULL, NULL)")
    conn.execute("INSERT INTO users (name, email, role) VALUES ('B', NULL, NULL)")
    conn.commit()
    count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    assert count == 2


def test_allocate_issue_key_sequences_are_independent_per_project(tmp_path):
    from app.db import allocate_issue_key

    db_path = tmp_path / "test.db"
    conn = get_connection(str(db_path))
    create_schema(conn)
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('SDLC', 'SDLC', '')")
    conn.execute("INSERT INTO projects (key, name, description) VALUES ('DDLC', 'DDLC', '')")
    sdlc_id = conn.execute("SELECT id FROM projects WHERE key='SDLC'").fetchone()["id"]
    ddlc_id = conn.execute("SELECT id FROM projects WHERE key='DDLC'").fetchone()["id"]

    assert allocate_issue_key(conn, sdlc_id, "SDLC") == "SDLC-1"
    assert allocate_issue_key(conn, ddlc_id, "DDLC") == "DDLC-1"
    assert allocate_issue_key(conn, sdlc_id, "SDLC") == "SDLC-2"
