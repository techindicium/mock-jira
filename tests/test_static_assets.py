def test_root_serves_board_shell(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert 'id="col-todo"' in body
    assert 'id="col-in_progress"' in body
    assert 'id="col-done"' in body
    assert 'id="project-switcher"' in body


def test_static_css_is_served(client):
    resp = client.get("/static/css/board.css")
    assert resp.status_code == 200
