from fastapi import APIRouter, HTTPException, Request

from app.models import SprintCreate, SprintPatch, SprintRead

router = APIRouter()


def _row_to_sprint_read(row) -> SprintRead:
    return SprintRead(
        id=row["id"], project_id=row["project_id"], name=row["name"],
        start_date=row["start_date"], end_date=row["end_date"], status=row["status"],
    )


def _require_project(conn, project_id: int):
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Project {project_id} not found", "code": "SPRINT_PROJECT_NOT_FOUND"},
        )
    return row


@router.post("/projects/{project_id}/sprints", response_model=SprintRead, status_code=201)
def create_sprint(project_id: int, payload: SprintCreate, request: Request):
    conn = request.app.state.db_conn
    _require_project(conn, project_id)

    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=422, detail={"message": "name is required", "code": "VALIDATION_ERROR"})
    if payload.start_date and payload.end_date and payload.end_date < payload.start_date:
        raise HTTPException(
            status_code=422,
            detail={"message": "end_date must not precede start_date", "code": "VALIDATION_ERROR"},
        )

    cursor = conn.execute(
        """
        INSERT INTO sprints (project_id, name, start_date, end_date, status)
        VALUES (?, ?, ?, ?, 'planned')
        """,
        (project_id, payload.name, payload.start_date, payload.end_date),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_sprint_read(row)


@router.get("/projects/{project_id}/sprints", response_model=list[SprintRead])
def list_sprints(project_id: int, request: Request):
    conn = request.app.state.db_conn
    _require_project(conn, project_id)
    rows = conn.execute(
        "SELECT * FROM sprints WHERE project_id = ? ORDER BY id ASC", (project_id,)
    ).fetchall()
    return [_row_to_sprint_read(r) for r in rows]


_PATCHABLE_FIELDS = ("name", "start_date", "end_date", "status")


@router.patch("/sprints/{sprint_id}", response_model=SprintRead)
def patch_sprint(sprint_id: int, payload: SprintPatch, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"Sprint {sprint_id} not found", "code": "SPRINT_NOT_FOUND"},
        )

    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        if row["status"] == "closed":
            raise HTTPException(
                status_code=409,
                detail={"message": f"Sprint {sprint_id} is closed", "code": "SPRINT_CLOSED"},
            )
        if updates["status"] == "active":
            sibling = conn.execute(
                "SELECT id FROM sprints WHERE project_id = ? AND status = 'active' AND id != ?",
                (row["project_id"], sprint_id),
            ).fetchone()
            if sibling is not None:
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Project {row['project_id']} already has an active sprint",
                        "code": "SPRINT_ALREADY_ACTIVE",
                    },
                )

    set_clauses = [f"{field} = ?" for field in _PATCHABLE_FIELDS if field in updates]
    values = [updates[field] for field in _PATCHABLE_FIELDS if field in updates]
    if set_clauses:
        conn.execute(
            f"UPDATE sprints SET {', '.join(set_clauses)} WHERE id = ?",
            (*values, sprint_id),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM sprints WHERE id = ?", (sprint_id,)).fetchone()
    return _row_to_sprint_read(row)
