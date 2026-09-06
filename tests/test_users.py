def test_create_user_returns_201_with_full_representation(client):
    resp = client.post(
        "/users", json={"name": "Ana Costa", "email": "ana.costa@portwell.example", "role": "QA"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Ana Costa"
    assert body["email"] == "ana.costa@portwell.example"
    assert body["role"] == "QA"
    assert "id" in body


def test_create_user_duplicate_email_returns_409(client):
    client.post("/users", json={"name": "Ana Costa", "email": "ana.costa@portwell.example"})
    resp = client.post("/users", json={"name": "Someone Else", "email": "ana.costa@portwell.example"})
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "USER_EMAIL_DUPLICATE"
    assert "ana.costa@portwell.example" in body["message"]


def test_create_user_missing_name_returns_422_with_error_envelope(client):
    resp = client.post("/users", json={"email": "nobody@portwell.example"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "name" in body["message"]


def test_create_user_empty_name_returns_422_with_error_envelope(client):
    resp = client.post("/users", json={"name": ""})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "name" in body["message"]


def test_create_user_without_email_succeeds_and_never_collides(client):
    first = client.post("/users", json={"name": "No Email One"})
    second = client.post("/users", json={"name": "No Email Two"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["email"] is None
    assert second.json()["email"] is None


def test_create_user_allows_duplicate_names(client):
    first = client.post("/users", json={"name": "Same Name"})
    second = client.post("/users", json={"name": "Same Name"})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_list_users_returns_all_ordered_by_creation(client):
    client.post("/users", json={"name": "User One"})
    client.post("/users", json={"name": "User Two"})
    resp = client.get("/users")
    assert resp.status_code == 200
    names = [u["name"] for u in resp.json() if u["name"] in ("User One", "User Two")]
    assert names == ["User One", "User Two"]


def test_get_user_by_id_returns_200(client):
    created = client.post("/users", json={"name": "Findable User"}).json()
    resp = client.get(f"/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Findable User"


def test_get_user_unknown_id_returns_404(client):
    resp = client.get("/users/999999")
    assert resp.status_code == 404
    assert "999999" in resp.json()["message"]


def test_fresh_startup_seeds_real_users(client):
    # BEH-9: a fresh database (the `client` fixture's own temp DB) seeds a handful of real,
    # non-placeholder Users independently of Project/Issue seeding.
    users = client.get("/users").json()
    assert len(users) >= 4
    names = {u["name"] for u in users}
    assert {"Mei Tan", "Kofi Adjei", "Priya Nair", "Joao Pinto"}.issubset(names)
    for user in users:
        assert user["name"].strip() != ""
        assert "lorem" not in user["name"].lower()
