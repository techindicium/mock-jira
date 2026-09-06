import pytest

import app.main as main_module


def test_db_path_defaults_to_env_var_database_path(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", "/tmp/from-env.db")
    # DB_PATH is resolved at import time; re-derive via the same helper the
    # module uses so the test exercises real resolution logic, not a literal.
    assert main_module.resolve_db_path() == "/tmp/from-env.db"


def test_db_path_falls_back_to_default_when_unset(monkeypatch):
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    assert main_module.resolve_db_path() == "mock_jira.db"


def test_startup_raises_clear_error_naming_the_path_when_unwritable(monkeypatch, tmp_path):
    unwritable_dir = tmp_path / "no-such-parent" / "db.sqlite"
    monkeypatch.setattr(main_module, "DB_PATH", str(unwritable_dir))
    with pytest.raises(RuntimeError, match=str(unwritable_dir)):
        main_module.on_startup()
