from fastapi import APIRouter, HTTPException, Request

from app.db import allocate_issue_key
from app.models import CommentCreate, CommentRead, IssueCreate, IssuePatch, IssueRead

router = APIRouter()


def _row_to_issue_read(row) -> IssueRead:
    return IssueRead(
        id=row["id"], key=row["key"], project_id=row["project_id"], summary=row["summary"],
        description=row["description"], issue_type=row["issue_type"], status=row["status"],
        priority=row["priority"], assignee=row["assignee"], reporter=row["reporter"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


@router.post("/issues", response_model=IssueRead, status_code=201)
def create_issue(payload: IssueCreate, request: Request):
    conn = request.app.state.db_conn
    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (payload.project_id,)
    ).fetchone()
    if project is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Project {payload.project_id} not found",
                "code": "ISSUE_PROJECT_NOT_FOUND",
            },
        )

    key = allocate_issue_key(conn, project["id"], project["key"])
    cursor = conn.execute(
        """
        INSERT INTO issues
            (key, project_id, summary, description, issue_type, status, priority, assignee, reporter)
        VALUES (?, ?, ?, ?, ?, 'todo', ?, ?, ?)
        """,
        (
            key, project["id"], payload.summary, payload.description or "", payload.issue_type,
            payload.priority, payload.assignee or "", payload.reporter or "",
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_issue_read(row)


@router.get("/issues", response_model=list[IssueRead])
def list_issues(request: Request, project_id: int | None = None, status: str | None = None):
    conn = request.app.state.db_conn
    query = "SELECT * FROM issues WHERE 1=1"
    params: list = []
    if project_id is not None:
        query += " AND project_id = ?"
        params.append(project_id)
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_issue_read(r) for r in rows]


@router.get("/issues/{issue_id}", response_model=IssueRead)
def get_issue(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    return _row_to_issue_read(row)


def _row_to_comment_read(row) -> CommentRead:
    return CommentRead(
        id=row["id"], issue_id=row["issue_id"], body=row["body"],
        author=row["author"], created_at=row["created_at"],
    )


def _require_issue(conn, issue_id: int):
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    return row


@router.post("/issues/{issue_id}/comments", response_model=CommentRead, status_code=201)
def create_comment(issue_id: int, payload: CommentCreate, request: Request):
    conn = request.app.state.db_conn
    _require_issue(conn, issue_id)
    if not payload.body or not payload.body.strip():
        raise HTTPException(
            status_code=422,
            detail={"message": "body is required", "code": "VALIDATION_ERROR"},
        )
    cursor = conn.execute(
        "INSERT INTO comments (issue_id, body, author) VALUES (?, ?, ?)",
        (issue_id, payload.body, payload.author or ""),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_comment_read(row)


@router.get("/issues/{issue_id}/comments", response_model=list[CommentRead])
def list_comments(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    _require_issue(conn, issue_id)
    rows = conn.execute(
        "SELECT * FROM comments WHERE issue_id = ? ORDER BY id ASC", (issue_id,)
    ).fetchall()
    return [_row_to_comment_read(r) for r in rows]


_PATCHABLE_FIELDS = ("summary", "description", "issue_type", "priority", "assignee", "reporter", "status")


@router.patch("/issues/{issue_id}", response_model=IssueRead)
def patch_issue(issue_id: int, payload: IssuePatch, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )

    updates = payload.model_dump(exclude_unset=True)
    set_clauses = [f"{field} = ?" for field in _PATCHABLE_FIELDS if field in updates]
    values = [updates[field] for field in _PATCHABLE_FIELDS if field in updates]
    if set_clauses:
        # Sub-second precision: schema's `created_at`/`updated_at` defaults use
        # datetime('now') (1-second granularity), so a patch landing in the same
        # wall-clock second as creation would otherwise produce an identical
        # updated_at, silently violating BEH-7's "bumps updated_at" contract.
        set_clauses.append("updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')")
        conn.execute(
            f"UPDATE issues SET {', '.join(set_clauses)} WHERE id = ?",
            (*values, issue_id),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    return _row_to_issue_read(row)


@router.delete("/issues/{issue_id}", status_code=204)
def delete_issue(issue_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM issues WHERE id = ?", (issue_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Issue {issue_id} not found", "code": "ISSUE_NOT_FOUND"},
        )
    conn.execute("DELETE FROM comments WHERE issue_id = ?", (issue_id,))
    conn.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    conn.commit()
