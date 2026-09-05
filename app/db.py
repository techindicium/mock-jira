import sqlite3


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            summary TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            issue_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'todo',
            priority TEXT NOT NULL,
            assignee TEXT NOT NULL DEFAULT '',
            reporter TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS project_issue_sequences (
            project_id INTEGER PRIMARY KEY REFERENCES projects(id),
            next_seq INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()


def allocate_issue_key(conn: sqlite3.Connection, project_id: int, project_key: str) -> str:
    """Durable per-project sequence: never decrements or reuses a number, even across deletes."""
    row = conn.execute(
        "SELECT next_seq FROM project_issue_sequences WHERE project_id = ?", (project_id,)
    ).fetchone()
    seq = row["next_seq"] if row else 1
    conn.execute(
        """
        INSERT INTO project_issue_sequences (project_id, next_seq) VALUES (?, ?)
        ON CONFLICT(project_id) DO UPDATE SET next_seq = excluded.next_seq
        """,
        (project_id, seq + 1),
    )
    conn.commit()
    return f"{project_key}-{seq}"
