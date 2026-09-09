from tests.test_issues import _create_project


def _create_issue(client, project_id):
    return client.post(
        "/issues",
        json={"project_id": project_id, "summary": "x", "issue_type": "task", "priority": "low"},
    ).json()


def test_new_issue_starts_unsprinted_even_if_sprint_id_is_supplied(client):
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    resp = client.post(
        "/issues",
        json={
            "project_id": project["id"], "summary": "x", "issue_type": "task", "priority": "low",
            "sprint_id": sprint["id"],
        },
    )
    assert resp.json()["sprint_id"] is None


def test_assign_issue_to_sprint(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    assert resp.json()["sprint_id"] == sprint["id"]


def test_assign_issue_to_sprint_from_different_project_is_422(client):
    p1 = _create_project(client, key="A")
    p2 = _create_project(client, key="B")
    issue = _create_issue(client, p1["id"])
    other_sprint = client.post(f"/projects/{p2['id']}/sprints", json={"name": "S"}).json()
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": other_sprint["id"]})
    assert resp.status_code == 422
    assert resp.json()["code"] == "SPRINT_PROJECT_MISMATCH"


def test_assign_issue_to_closed_sprint_is_409(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_CLOSED"


def test_unassign_issue_from_sprint(client):
    project = _create_project(client)
    issue = _create_issue(client, project["id"])
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/issues/{issue['id']}", json={"sprint_id": sprint["id"]})
    resp = client.patch(f"/issues/{issue['id']}", json={"sprint_id": None})
    assert resp.json()["sprint_id"] is None
