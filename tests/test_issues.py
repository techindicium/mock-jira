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


def test_list_issues_unfiltered_returns_all(client):
    project = _create_project(client)
    client.post("/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"})
    client.post("/issues", json={"project_id": project["id"], "summary": "B", "issue_type": "task", "priority": "low"})
    resp = client.get("/issues")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_issues_filtered_by_project_id(client):
    p1 = _create_project(client, key="SDLC", name="SDLC")
    p2 = _create_project(client, key="DDLC", name="DDLC")
    client.post("/issues", json={"project_id": p1["id"], "summary": "A", "issue_type": "bug", "priority": "low"})
    client.post("/issues", json={"project_id": p2["id"], "summary": "B", "issue_type": "bug", "priority": "low"})
    resp = client.get(f"/issues?project_id={p1['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["project_id"] == p1["id"]


def test_get_issue_by_id_returns_200(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.get(f"/issues/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["key"] == "SDLC-1"


def test_get_issue_unknown_id_returns_404(client):
    resp = client.get("/issues/999999")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == "ISSUE_NOT_FOUND"
    assert "999999" in body["message"]


def test_patch_issue_updates_given_fields_and_returns_200(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(
        f"/issues/{created['id']}",
        json={"summary": "Updated summary", "status": "in_progress", "assignee": "dana"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"] == "Updated summary"
    assert body["status"] == "in_progress"
    assert body["assignee"] == "dana"
    assert body["updated_at"] != created["updated_at"]


def test_patch_issue_ignores_id_key_and_project_id_in_body(client):
    p1 = _create_project(client, key="SDLC", name="SDLC")
    p2 = _create_project(client, key="DDLC", name="DDLC")
    created = client.post(
        "/issues", json={"project_id": p1["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(
        f"/issues/{created['id']}",
        json={"id": 999, "key": "DDLC-1", "project_id": p2["id"], "summary": "still SDLC"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["key"] == created["key"]
    assert body["project_id"] == p1["id"]
    assert body["summary"] == "still SDLC"


def test_patch_issue_invalid_status_returns_422_and_persists_no_change(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(f"/issues/{created['id']}", json={"status": "blocked"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    # Error Cases table requires naming the invalid field and its allowed values (Task 2's
    # literal_error branch in app/errors.py, reused here unchanged for the status field)
    assert "status" in body["message"]
    assert "todo" in body["message"] and "in_progress" in body["message"] and "done" in body["message"]
    unchanged = client.get(f"/issues/{created['id']}").json()
    assert unchanged["status"] == "todo"


def test_patch_issue_invalid_issue_type_returns_422(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.patch(f"/issues/{created['id']}", json={"issue_type": "epic"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "issue_type" in body["message"]


def test_patch_issue_unknown_id_returns_404(client):
    resp = client.patch("/issues/999999", json={"summary": "x"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"


def test_list_issues_filtered_by_status(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    client.patch(f"/issues/{created['id']}", json={"status": "in_progress"})
    resp = client.get("/issues?status=in_progress")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["status"] == "in_progress"


def test_delete_issue_returns_204_and_removes_it(client):
    project = _create_project(client)
    created = client.post(
        "/issues", json={"project_id": project["id"], "summary": "A", "issue_type": "bug", "priority": "low"}
    ).json()
    resp = client.delete(f"/issues/{created['id']}")
    assert resp.status_code == 204
    assert resp.content == b""

    follow_up = client.get(f"/issues/{created['id']}")
    assert follow_up.status_code == 404

    listing = client.get("/issues")
    assert created["id"] not in [i["id"] for i in listing.json()]


def test_delete_issue_unknown_id_returns_404(client):
    resp = client.delete("/issues/999999")
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"
