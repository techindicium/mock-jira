import httpx


def test_unknown_project_id_returns_404(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/projects/999999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "PROJECT_NOT_FOUND"


def test_unknown_issue_id_returns_404(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        resp = client.get("/issues/999999")
        assert resp.status_code == 404
        assert resp.json()["code"] == "ISSUE_NOT_FOUND"


def test_duplicate_project_key_returns_409(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        client.post("/projects", json={"key": "E2EDUP", "name": "First"})
        resp = client.post("/projects", json={"key": "E2EDUP", "name": "Second"})
        assert resp.status_code == 409
        assert resp.json()["code"] == "PROJECT_KEY_DUPLICATE"


def test_invalid_issue_type_enum_returns_422(server):
    with httpx.Client(base_url=server, timeout=5) as client:
        project = client.post(
            "/projects", json={"key": "E2EENUM", "name": "Enum Project"}
        ).json()
        resp = client.post(
            "/issues",
            json={
                "project_id": project["id"], "summary": "bad enum",
                "issue_type": "not-a-real-type", "priority": "medium",
            },
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "VALIDATION_ERROR"
