import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.models import ProjectCreate, ProjectRead

router = APIRouter()


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(payload: ProjectCreate, request: Request):
    if not payload.key or not payload.key.strip():
        raise HTTPException(status_code=422, detail={"message": "key is required", "code": "VALIDATION_ERROR"})
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=422, detail={"message": "name is required", "code": "VALIDATION_ERROR"})

    conn = request.app.state.db_conn
    try:
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description) VALUES (?, ?, ?)",
            (payload.key, payload.name, payload.description or ""),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={"message": f"Project key '{payload.key}' already exists", "code": "PROJECT_KEY_DUPLICATE"},
        )

    row = conn.execute("SELECT * FROM projects WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return ProjectRead(id=row["id"], key=row["key"], name=row["name"], description=row["description"])
