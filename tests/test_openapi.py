def test_openapi_json_lists_project_routes(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    doc = resp.json()
    assert "/projects" in doc["paths"]
    assert "post" in doc["paths"]["/projects"]
    assert "get" in doc["paths"]["/projects"]
    assert "/projects/{project_id}" in doc["paths"]
    assert "get" in doc["paths"]["/projects/{project_id}"]
