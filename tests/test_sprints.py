from tests.test_issues import _create_project


def test_create_sprint_returns_201_planned_status(client):
    project = _create_project(client)
    resp = client.post(f"/projects/{project['id']}/sprints", json={"name": "Sprint 1"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "planned"
    assert body["project_id"] == project["id"]

def test_create_sprint_status_field_is_ignored_at_creation(client):
    project = _create_project(client)
    resp = client.post(f"/projects/{project['id']}/sprints", json={"name": "S", "status": "active"})
    assert resp.json()["status"] == "planned"

def test_create_sprint_end_before_start_is_422(client):
    project = _create_project(client)
    resp = client.post(
        f"/projects/{project['id']}/sprints",
        json={"name": "S", "start_date": "2026-02-01", "end_date": "2026-01-01"},
    )
    assert resp.status_code == 422

def test_list_sprints_missing_project_is_404(client):
    resp = client.get("/projects/999999/sprints")
    assert resp.status_code == 404
    assert resp.json()["code"] == "SPRINT_PROJECT_NOT_FOUND"

def test_activate_sprint_while_another_is_active_is_rejected(client):
    project = _create_project(client)
    s1 = client.post(f"/projects/{project['id']}/sprints", json={"name": "S1"}).json()
    s2 = client.post(f"/projects/{project['id']}/sprints", json={"name": "S2"}).json()
    client.patch(f"/sprints/{s1['id']}", json={"status": "active"})
    resp = client.patch(f"/sprints/{s2['id']}", json={"status": "active"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_ALREADY_ACTIVE"

def test_closing_sprint_then_reactivating_is_rejected(client):
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_CLOSED"

def test_reverting_an_active_sprint_to_planned_is_rejected(client):
    # Postcondition: a Sprint's status only ever moves forward (planned -> active ->
    # closed); no code path may set it backward.
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    resp = client.patch(f"/sprints/{sprint['id']}", json={"status": "planned"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "SPRINT_STATUS_BACKWARD"
    # and the sprint's actual status was not mutated
    still = client.get(f"/projects/{project['id']}/sprints").json()
    assert still[0]["status"] == "active"

def test_renaming_a_closed_sprint_is_allowed(client):
    # A closed Sprint rejects status changes, but name/date edits are NOT a status change
    # and must still succeed.
    project = _create_project(client)
    sprint = client.post(f"/projects/{project['id']}/sprints", json={"name": "S"}).json()
    client.patch(f"/sprints/{sprint['id']}", json={"status": "active"})
    client.patch(f"/sprints/{sprint['id']}", json={"status": "closed"})
    resp = client.patch(f"/sprints/{sprint['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
