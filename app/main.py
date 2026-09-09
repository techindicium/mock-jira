import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import create_schema, get_connection
from app.errors import http_exception_handler, validation_exception_handler
from app.routers.issues import router as issues_router
from app.routers.projects import router as projects_router
from app.routers.sprints import router as sprints_router
from app.routers.users import router as users_router
from app.seed import seed_if_empty, seed_users_if_empty


def resolve_db_path() -> str:
    return os.environ.get("DATABASE_PATH", "mock_jira.db")


DB_PATH = resolve_db_path()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="mock-jira", version="0.1.0")

app.include_router(projects_router)
app.include_router(issues_router)
app.include_router(users_router)
app.include_router(sprints_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_board() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.on_event("startup")
def on_startup() -> None:
    try:
        conn = get_connection(DB_PATH)
        create_schema(conn)
    except sqlite3.OperationalError as exc:
        raise RuntimeError(
            f"DATABASE_PATH '{DB_PATH}' is not writable: {exc}"
        ) from exc
    seed_if_empty(conn, DB_PATH)
    seed_users_if_empty(conn, DB_PATH)
    app.state.db_conn = conn  # kept open for the process lifetime; sqlite3 handles serialization
