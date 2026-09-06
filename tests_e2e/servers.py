"""Reusable real-server-process fixture for e2e suites.

Launches `uvicorn app.main:app` as its own OS process (never imported in-process),
on an ephemeral local port, with DATABASE_PATH pointed at a fresh temp file. Polls
GET / (the app's existing root route — there is no dedicated /health endpoint,
same convention as this repo's docker-compose.yml healthcheck) until it answers,
then yields the base URL. Terminates the process on exit.

Reused by this repo's own tests_e2e/conftest.py `server` fixture, and intended for
direct reuse (no pytest dependency) by kanban-ui's ui-e2e and mcp-server's mcp-e2e
sibling specs, which will start this same API as their upstream test dependency.
"""
import contextlib
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx

_STARTUP_TIMEOUT_SECONDS = 10.0
_POLL_INTERVAL_SECONDS = 0.1


class E2EServerStartTimeout(RuntimeError):
    """Raised when the server subprocess doesn't answer GET / within the startup timeout."""


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def start_issue_tracker_api(tmp_path: Path) -> Iterator[str]:
    """Start the real issue-tracker-api server as a subprocess; yield its base_url.

    Args:
        tmp_path: a directory to place this run's SQLite DB file in. Callers control
            scope (function- or session-level) by choosing what Path they pass in
            (e.g. pytest's `tmp_path` vs. `tmp_path_factory.mktemp(...)`).

    Yields:
        The base URL (e.g. "http://127.0.0.1:54231") once the server answers GET /.

    Raises:
        E2EServerStartTimeout: the process didn't answer GET / within the startup
            timeout. The exception message names the timeout and the last-seen
            process output (E2E_SERVER_START_TIMEOUT in api-e2e.spec.md).
    """
    port = _free_port()
    db_path = Path(tmp_path) / "e2e.db"
    base_url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "DATABASE_PATH": str(db_path)}
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--host", "127.0.0.1", "--port", str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                last_output = proc.stdout.read() if proc.stdout else ""
                raise E2EServerStartTimeout(
                    f"server process exited early (code {proc.returncode}) before "
                    f"answering GET {base_url}/ within the {_STARTUP_TIMEOUT_SECONDS}s "
                    f"startup timeout. Last output:\n{last_output}"
                )
            try:
                resp = httpx.get(base_url + "/", timeout=1)
                if resp.status_code == 200:
                    break
            except httpx.TransportError:
                pass
            time.sleep(_POLL_INTERVAL_SECONDS)
        else:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            last_output = proc.stdout.read() if proc.stdout else ""
            raise E2EServerStartTimeout(
                f"server did not answer GET {base_url}/ within the "
                f"{_STARTUP_TIMEOUT_SECONDS}s startup timeout. Last output:\n{last_output}"
            )
        yield base_url
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
