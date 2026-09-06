import httpx

from tests_e2e.servers import start_issue_tracker_api


def test_created_user_is_visible_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        create_resp = client.post(
            "/users",
            json={"name": "E2E Test User", "email": "e2e.user@portwell.example", "role": "QA"},
        )
        assert create_resp.status_code == 201
        created = create_resp.json()

        list_resp = client.get("/users")
        assert list_resp.status_code == 200
        names = [u["name"] for u in list_resp.json()]
        assert "E2E Test User" in names
        assert any(u["id"] == created["id"] for u in list_resp.json())

        get_resp = client.get(f"/users/{created['id']}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "E2E Test User"


def test_duplicate_user_email_returns_409_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        client.post("/users", json={"name": "First", "email": "e2edup@portwell.example"})
        resp = client.post("/users", json={"name": "Second", "email": "e2edup@portwell.example"})
        assert resp.status_code == 409
        assert resp.json()["code"] == "USER_EMAIL_DUPLICATE"


def test_unknown_user_id_returns_404_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/users/999999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "USER_NOT_FOUND"


def test_openapi_json_lists_user_routes_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        doc = resp.json()
        assert "/users" in doc["paths"]
        assert "post" in doc["paths"]["/users"]
        assert "get" in doc["paths"]["/users"]
        assert "/users/{user_id}" in doc["paths"]


def test_seed_users_visible_on_fresh_server_start(tmp_path):
    # Deliberately NOT the shared `server` fixture: needs a fresh, empty database to prove
    # BEH-9's seed-on-startup behavior end to end, over a real HTTP connection.
    with (
        start_issue_tracker_api(tmp_path) as base_url,
        httpx.Client(base_url=base_url, timeout=5) as client,
    ):
        users = client.get("/users").json()
        assert len(users) >= 4
        names = {u["name"] for u in users}
        assert {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto"}.issubset(names)
