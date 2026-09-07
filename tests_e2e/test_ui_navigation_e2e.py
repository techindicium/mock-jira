def test_board_is_active_view_by_default(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    assert page.locator("#view-board").is_visible()
    assert page.locator("#view-users").is_hidden()
    assert page.locator("#view-projects").is_hidden()
    assert "active" in (page.get_attribute("#nav-board", "class") or "")  # BEH-1/BEH-4


def test_clicking_users_nav_shows_users_view_and_hides_board(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    page.click("#nav-users")

    page.wait_for_selector("#view-users:not([hidden])")
    assert page.locator("#view-board").is_hidden()
    assert page.locator("#view-projects").is_hidden()
    assert "active" in (page.get_attribute("#nav-users", "class") or "")  # BEH-2/BEH-4


def test_clicking_projects_nav_shows_projects_view_and_hides_others(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    page.click("#nav-projects")

    page.wait_for_selector("#view-projects:not([hidden])")
    assert page.locator("#view-board").is_hidden()
    assert page.locator("#view-users").is_hidden()  # BEH-2


def test_returning_to_board_shows_prior_state_without_refetch(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-users")
    page.wait_for_selector("#view-users:not([hidden])")

    issues_requests = []
    page.on("request", lambda req: issues_requests.append(req) if "/issues" in req.url else None)

    page.click("#nav-board")

    page.wait_for_selector("#view-board:not([hidden])")
    assert page.locator("#board").is_visible()
    assert len(issues_requests) == 0  # BEH-3: switching back never re-fetches board data


def test_nav_items_are_keyboard_focusable(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    page.locator("#nav-users").focus()
    assert page.evaluate("document.activeElement.id") == "nav-users"  # BEH-5
