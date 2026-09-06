import httpx


def test_created_project_is_visible_over_real_http(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        create_resp = client.post(
            "/projects",
            json={"key": "E2ECRUD", "name": "E2E CRUD Project"},
        )
        assert create_resp.status_code == 201
        created = create_resp.json()

        list_resp = client.get("/projects")
        assert list_resp.status_code == 200
        keys = [p["key"] for p in list_resp.json()]
        assert "E2ECRUD" in keys
        assert any(p["id"] == created["id"] for p in list_resp.json())
