def test_projects_view_lists_seeded_project(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-projects")
    page.wait_for_selector("#view-projects:not([hidden])")

    page.wait_for_selector('#projects-list .ledger-row:has-text("ASSIST")')  # BEH-1
    row_text = page.locator('#projects-list .ledger-row:has-text("ASSIST")').inner_text()
    assert "Portwell Assist Engineering" in row_text


def test_add_project_form_creates_and_refreshes_list(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-projects")
    page.wait_for_selector("#view-projects:not([hidden])")

    page.fill("#mgmt-project-key", "E2EMGMT")
    page.fill("#mgmt-project-name", "E2E Management Project")
    page.fill("#mgmt-project-description", "Created via the projects management screen")
    page.click("#mgmt-create-project-form button[type=submit]")

    page.wait_for_selector('#projects-list .ledger-row:has-text("E2EMGMT")')  # BEH-3
    assert page.input_value("#mgmt-project-key") == ""  # form cleared on success


def test_add_project_form_blocks_whitespace_only_key(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-projects")
    page.wait_for_selector("#view-projects:not([hidden])")

    post_requests = []
    page.on(
        "request",
        lambda req: post_requests.append(req) if req.method == "POST" and "/projects" in req.url else None,
    )

    # Whitespace-only satisfies the input's native `required` attribute (non-empty), so this
    # exercises the app's own trim-aware validateProjectForm check, not the browser's HTML5
    # validation UI.
    page.fill("#mgmt-project-key", "   ")
    page.fill("#mgmt-project-name", "Missing Key Project")
    page.click("#mgmt-create-project-form button[type=submit]")

    page.wait_for_selector("#mgmt-create-project-error:not([hidden])")  # BEH-4
    assert len(post_requests) == 0  # blocked client-side, no request sent


def test_duplicate_project_key_shows_real_api_error(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-projects")
    page.wait_for_selector("#view-projects:not([hidden])")

    page.fill("#mgmt-project-key", "ASSIST")  # the real seeded project's key
    page.fill("#mgmt-project-name", "Duplicate Key Attempt")
    page.click("#mgmt-create-project-form button[type=submit]")

    page.wait_for_selector("#mgmt-create-project-error:not([hidden])")
    error_text = page.locator("#mgmt-create-project-error").inner_text()
    assert "already exists" in error_text  # BEH-5: the API's own message, not a generic one
    assert page.input_value("#mgmt-project-key") == "ASSIST"  # input retained


def test_project_created_via_management_screen_appears_in_switcher_after_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#nav-projects")
    page.wait_for_selector("#view-projects:not([hidden])")

    page.fill("#mgmt-project-key", "E2ESWITCHCHK")
    page.fill("#mgmt-project-name", "Switcher Check Project")
    page.click("#mgmt-create-project-form button[type=submit]")
    page.wait_for_selector('#projects-list .ledger-row:has-text("E2ESWITCHCHK")')

    page.reload()
    page.wait_for_selector("#board:not([hidden])")
    options = page.locator("#project-switcher option").all_inner_texts()
    assert any("E2ESWITCHCHK" in o for o in options)  # BEH-7


def test_projects_view_shows_error_on_fetch_failure(page, ui_board_server):
    page.route("**/projects", lambda route: route.abort("failed"))

    page.goto(ui_board_server)
    page.wait_for_selector("#nav-projects")  # nav renders even though board's own load also fails
    page.click("#nav-projects")

    page.wait_for_selector("#projects-view-error:not([hidden])")  # BEH-6
    error_text = page.locator("#projects-view-error").inner_text()
    assert "Loading projects failed" in error_text
    assert page.locator("#mgmt-create-project-form").is_visible()
