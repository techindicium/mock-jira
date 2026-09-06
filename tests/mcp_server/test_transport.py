import mcp_server.server as server_module


def test_main_runs_stdio_by_default(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    calls = []
    monkeypatch.setattr(server_module.mcp, "run", lambda *a, **kw: calls.append((a, kw)))
    server_module.main()
    assert calls == [((), {})]


def test_main_runs_streamable_http_when_port_is_set(monkeypatch):
    monkeypatch.setenv("PORT", "8001")
    calls = []
    monkeypatch.setattr(server_module.mcp, "run", lambda *a, **kw: calls.append((a, kw)))
    server_module.main()
    assert calls == [((), {"transport": "streamable-http", "host": "0.0.0.0", "port": 8001})]
