def test_create_project_returns_201_with_full_representation(client):
    resp = client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"] == "SDLC"
    assert body["name"] == "SDLC Track"
    assert body["description"] == ""
    assert "id" in body


def test_create_project_duplicate_key_returns_409(client):
    client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    resp = client.post("/projects", json={"key": "SDLC", "name": "Another"})
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "PROJECT_KEY_DUPLICATE"
    assert "SDLC" in body["message"]


def test_create_project_missing_name_returns_422_with_error_envelope(client):
    # Field entirely absent from the body -> Pydantic/FastAPI raises RequestValidationError,
    # not our manual check. Must still surface the same VALIDATION_ERROR envelope.
    resp = client.post("/projects", json={"key": "SDLC"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "name" in body["message"]


def test_create_project_empty_key_returns_422_with_error_envelope(client):
    resp = client.post("/projects", json={"key": "", "name": "SDLC Track"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "key" in body["message"]


def test_create_project_malformed_json_returns_400(client):
    resp = client.post(
        "/projects",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json()["code"] == "MALFORMED_JSON"


def test_list_projects_returns_all_ordered_by_creation(client):
    client.post("/projects", json={"key": "SDLC", "name": "SDLC Track"})
    client.post("/projects", json={"key": "DDLC", "name": "DDLC Track"})
    resp = client.get("/projects")
    assert resp.status_code == 200
    keys = [p["key"] for p in resp.json()]
    assert keys == ["SDLC", "DDLC"]
