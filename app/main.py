from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import create_schema, get_connection
from app.errors import http_exception_handler, validation_exception_handler
from app.routers.projects import router as projects_router

DB_PATH = "mock_jira.db"

app = FastAPI(title="mock-jira", version="0.1.0")

app.include_router(projects_router)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection(DB_PATH)
    create_schema(conn)
    app.state.db_conn = conn  # kept open for the process lifetime; sqlite3 handles serialization
