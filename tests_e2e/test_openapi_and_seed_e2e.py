import httpx

from tests_e2e.servers import start_issue_tracker_api


def test_openapi_json_lists_implemented_routes_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        doc = resp.json()
        assert "/projects" in doc["paths"]
        assert "/issues" in doc["paths"]
        assert "get" in doc["paths"]["/projects"]
        assert "post" in doc["paths"]["/issues"]


def test_seed_data_visible_on_fresh_server_start(tmp_path):
    # Deliberately NOT the shared `server` fixture: BEH-5 asserts a *fresh, empty*
    # database seeds exactly once, so this needs its own isolated server instance.
    with (
        start_issue_tracker_api(tmp_path) as base_url,
        httpx.Client(base_url=base_url, timeout=5) as client,
    ):
        projects = client.get("/projects").json()
        assert len(projects) == 1
        assert projects[0]["key"] == "ASSIST"

        issues = client.get("/issues", params={"project_id": projects[0]["id"]}).json()
        assert len(issues) == 6
