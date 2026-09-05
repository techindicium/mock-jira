def _create_project(client, key="SDLC", name="SDLC Track"):
    return client.post("/projects", json={"key": key, "name": name}).json()


def test_create_issue_returns_201_with_server_assigned_key_and_todo_status(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={
            "project_id": project["id"],
            "summary": "Fix login bug",
            "issue_type": "bug",
            "priority": "high",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"] == "SDLC-1"
    assert body["status"] == "todo"
    assert body["project_id"] == project["id"]
    assert body["summary"] == "Fix login bug"


def test_create_second_issue_in_same_project_increments_sequence(client):
    project = _create_project(client)
    client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "A", "issue_type": "task", "priority": "low"},
    )
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "B", "issue_type": "task", "priority": "low"},
    )
    assert resp.json()["key"] == "SDLC-2"


def test_create_issue_unknown_project_returns_404(client):
    resp = client.post(
        "/issues",
        json={"project_id": 999999, "summary": "X", "issue_type": "bug", "priority": "low"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "ISSUE_PROJECT_NOT_FOUND"
    assert "999999" in body["message"]


def test_create_issue_missing_summary_returns_422(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "issue_type": "bug", "priority": "low"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "summary" in body["message"]


def test_create_issue_invalid_issue_type_returns_422(client):
    project = _create_project(client)
    resp = client.post(
        "/issues",
        json={"project_id": project["id"], "summary": "X", "issue_type": "epic", "priority": "low"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "issue_type" in body["message"]
    # Error Cases table requires naming the allowed values, not just "field is required"
    assert "bug" in body["message"] and "task" in body["message"] and "story" in body["message"]
