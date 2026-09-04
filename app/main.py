from fastapi import FastAPI

from app.db import create_schema, get_connection

DB_PATH = "mock_jira.db"

app = FastAPI(title="mock-jira", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    conn = get_connection(DB_PATH)
    create_schema(conn)
    conn.close()
