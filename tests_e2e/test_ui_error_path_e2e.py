def test_network_failure_shows_visible_error_message(page, ui_board_server):
    # Simulate the real server becoming unreachable mid-load by aborting the
    # issues fetch at the network layer — no mocked fetch, a real aborted request.
    page.route("**/issues*", lambda route: route.abort("failed"))

    page.goto(ui_board_server)

    page.wait_for_selector("#board-error:not([hidden])")
    error_text = page.locator("#board-error").inner_text()
    assert "Loading issues failed" in error_text
