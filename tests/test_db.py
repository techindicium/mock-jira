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
