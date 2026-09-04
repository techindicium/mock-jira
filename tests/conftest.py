import pytest
from fastapi.testclient import TestClient

import app.main as main_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(main_module, "DB_PATH", str(db_path))
    with TestClient(main_module.app) as c:
        yield c
