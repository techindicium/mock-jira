def test_assignee_datalist_is_populated_from_seeded_users(page, ui_board_server):
    users_requests = []
    page.on("request", lambda req: users_requests.append(req) if "/users" in req.url else None)

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")
    page.wait_for_function(
        "document.getElementById('user-directory-options').options.length > 0"
    )
    option_values = page.eval_on_selector_all(
        "#user-directory-options option", "opts => opts.map(o => o.value)"
    )
    assert len(option_values) > 0  # BEH-1/BEH-2: real seeded Users populate the suggestion list

    # BEH-1: fetched exactly once — opening the edit form must not trigger a second /users call.
    page.click("#cancel-create-issue")
    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    assert len(users_requests) == 1


def test_users_fetched_once_even_across_a_create_project_reinit(page, ui_board_server):
    # BEH-1 regression guard: onCreateProjectSubmit calls init() again after a successful
    # create-project submission, in the same page load — loadUsers() must not re-fire there.
    users_requests = []
    page.on("request", lambda req: users_requests.append(req) if "/users" in req.url else None)

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.wait_for_function(
        "document.getElementById('user-directory-options').options.length > 0"
    )

    page.fill("#project-key", "UPK")
    page.fill("#project-name", "User Picker Regression Project")
    page.click("#create-project-form button[type=submit]")
    # Options inside a closed native <select> aren't "visible" to Playwright's locator engine,
    # so poll the DOM directly rather than waiting on a locator's visibility state.
    page.wait_for_function(
        "Array.from(document.querySelectorAll('#project-switcher option'))"
        ".some(o => o.textContent.includes('UPK'))"
    )

    assert len(users_requests) == 1


def test_picking_a_suggested_name_still_submits_as_free_text(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")
    page.wait_for_function(
        "document.getElementById('user-directory-options').options.length > 0"
    )
    picked_name = page.eval_on_selector(
        "#user-directory-options option", "o => o.value"
    )

    page.fill("#issue-summary", "e2e-picker issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "medium")
    page.fill("#issue-assignee", picked_name)  # BEH-4: typing the exact suggested value
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-picker issue")')
    card_text = page.locator('#col-todo .card:has-text("e2e-picker issue")').inner_text()
    assert picked_name in card_text  # BEH-4/BEH-5: submitted exactly as free text


def test_arbitrary_free_text_assignee_still_accepted(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.click("#open-create-issue")

    page.fill("#issue-summary", "e2e-freetext issue")
    page.select_option("#issue-type", "bug")
    page.select_option("#issue-priority", "low")
    page.fill("#issue-assignee", "Someone Not In The Directory")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-freetext issue")')
    card_text = page.locator('#col-todo .card:has-text("e2e-freetext issue")').inner_text()
    assert "Someone Not In The Directory" in card_text  # BEH-5: no directory-match validation


def test_edit_issue_assignee_also_offers_suggestions(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    list_attr = page.eval_on_selector("#edit-issue-assignee", "el => el.getAttribute('list')")
    assert list_attr == "user-directory-options"  # BEH-3


def test_user_directory_failure_degrades_gracefully(page, ui_board_server):
    # Real aborted request, matching the existing error-path e2e pattern — not a mocked fetch.
    page.route("**/users", lambda route: route.abort("failed"))

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator("#board-error").is_hidden()  # BEH-6: no board-error banner for this

    page.click("#open-create-issue")
    page.fill("#issue-summary", "e2e-degraded issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "high")
    page.fill("#issue-assignee", "Still Works")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-degraded issue")')
    # form/board remained fully functional despite the /users failure
