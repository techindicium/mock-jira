import pytest

from mcp_server.config import get_api_base_url


def test_get_api_base_url_returns_configured_value(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000")
    assert get_api_base_url() == "http://localhost:8000"


def test_get_api_base_url_raises_clear_error_when_unset(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="API_BASE_URL"):
        get_api_base_url()
