from tests.test_issues import _create_project


def _create_issue(client, project_id, summary="Fix bug"):
    return client.post(
        "/issues",
        json={"project_id": project_id, "summary": summary, "issue_type": "bug", "priority": "low"},
    ).json()


def test_create_comment_returns_201_with_created_comment(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    resp = client.post(f"/issues/{issue['id']}/comments", json={"body": "Looks good to me."})
    assert resp.status_code == 201
    body = resp.json()
    assert body["issue_id"] == issue["id"]
    assert body["body"] == "Looks good to me."
    assert "id" in body and "created_at" in body

def test_create_comment_empty_body_is_422(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    resp = client.post(f"/issues/{issue['id']}/comments", json={"body": ""})
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"

def test_create_comment_on_missing_issue_is_404(client):
    resp = client.post("/issues/999999/comments", json={"body": "x"})
    assert resp.status_code == 404
    assert resp.json()["code"] == "ISSUE_NOT_FOUND"

def test_list_comments_returns_chronological_order(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    client.post(f"/issues/{issue['id']}/comments", json={"body": "first"})
    client.post(f"/issues/{issue['id']}/comments", json={"body": "second"})
    resp = client.get(f"/issues/{issue['id']}/comments")
    assert resp.status_code == 200
    bodies = [c["body"] for c in resp.json()]
    assert bodies == ["first", "second"]

def test_deleting_issue_deletes_its_comments(client):
    # Real cascade proof: query the comments table directly via the TestClient's own db
    # connection (client.app.state.db_conn, set by app.main's startup handler) rather than
    # relying on the 404-on-deleted-issue side effect, which would pass even if the
    # cascade-delete implementation step were skipped entirely.
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    created = client.post(f"/issues/{issue['id']}/comments", json={"body": "will be cascaded"}).json()
    client.delete(f"/issues/{issue['id']}")
    conn = client.app.state.db_conn
    row = conn.execute("SELECT * FROM comments WHERE id = ?", (created["id"],)).fetchone()
    assert row is None
