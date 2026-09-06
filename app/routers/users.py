import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.models import UserCreate, UserRead

router = APIRouter()


def _row_to_user_read(row) -> UserRead:
    return UserRead(id=row["id"], name=row["name"], email=row["email"], role=row["role"])


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, request: Request):
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=422, detail={"message": "name is required", "code": "VALIDATION_ERROR"}
        )

    conn = request.app.state.db_conn
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            (payload.name, payload.email or None, payload.role or None),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={
                "message": f"Email '{payload.email}' already exists",
                "code": "USER_EMAIL_DUPLICATE",
            },
        )

    row = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _row_to_user_read(row)


@router.get("/users", response_model=list[UserRead])
def list_users(request: Request):
    conn = request.app.state.db_conn
    rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
    return [_row_to_user_read(r) for r in rows]


@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, request: Request):
    conn = request.app.state.db_conn
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"message": f"User {user_id} not found", "code": "USER_NOT_FOUND"},
        )
    return _row_to_user_read(row)
