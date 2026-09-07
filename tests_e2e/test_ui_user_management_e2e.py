def test_users_view_lists_seeded_users(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")
    page.wait_for_selector("#view-users:not([hidden])")

    page.wait_for_selector('#users-list .ledger-row:has-text("Mei Tan")')
    assert page.locator("#users-list .ledger-row").count() == 4  # BEH-1: 4 seeded Users
    row_text = page.locator('#users-list .ledger-row:has-text("Mei Tan")').inner_text()
    assert "mei.tan@portwell.example" in row_text
    assert "Head of Engineering" in row_text


def test_add_user_form_creates_and_refreshes_list(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")
    page.wait_for_selector("#view-users:not([hidden])")

    page.fill("#user-name", "E2E New User")
    page.fill("#user-email", "e2e-new-user@example.com")
    page.fill("#user-role", "QA")
    page.click("#create-user-form button[type=submit]")

    page.wait_for_selector('#users-list .ledger-row:has-text("E2E New User")')  # BEH-3
    assert page.input_value("#user-name") == ""  # form cleared on success


def test_add_user_form_blocks_whitespace_only_name(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")
    page.wait_for_selector("#view-users:not([hidden])")

    post_requests = []
    page.on(
        "request",
        lambda req: post_requests.append(req) if req.method == "POST" and "/users" in req.url else None,
    )

    # Whitespace-only satisfies the input's native `required` attribute (non-empty), so this
    # exercises the app's own trim-aware validateUserForm check, not the browser's HTML5
    # validation UI.
    page.fill("#user-name", "   ")
    page.click("#create-user-form button[type=submit]")

    page.wait_for_selector("#create-user-error:not([hidden])")  # BEH-4
    assert len(post_requests) == 0  # blocked client-side, no request sent


def test_duplicate_email_shows_real_api_error(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")
    page.wait_for_selector("#view-users:not([hidden])")

    page.fill("#user-name", "Duplicate Email Person")
    page.fill("#user-email", "mei.tan@portwell.example")  # a real seeded user's email
    page.click("#create-user-form button[type=submit]")

    page.wait_for_selector("#create-user-error:not([hidden])")
    error_text = page.locator("#create-user-error").inner_text()
    assert "already exists" in error_text  # BEH-5: the API's own message, not a generic one
    assert page.input_value("#user-name") == "Duplicate Email Person"  # input retained


def test_users_view_shows_error_on_fetch_failure(page, ui_board_server):
    page.route("**/users", lambda route: route.abort("failed"))

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")

    page.wait_for_selector("#users-view-error:not([hidden])")  # BEH-6
    error_text = page.locator("#users-view-error").inner_text()
    assert "Loading users failed" in error_text
    # the add-user form itself stays present/usable regardless of the list fetch outcome
    assert page.locator("#create-user-form").is_visible()
