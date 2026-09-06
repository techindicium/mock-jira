def test_create_issue_form_shows_new_card_without_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.evaluate("window.__e2eNoReloadMarker = true")

    page.click("#open-create-issue")
    page.fill("#issue-summary", "e2e-created issue")
    page.select_option("#issue-type", "task")
    page.select_option("#issue-priority", "medium")
    page.click("#create-issue-form button[type=submit]")

    page.wait_for_selector('#col-todo .card:has-text("e2e-created issue")')
    assert page.locator("#create-issue").is_hidden()
    # BEH-3: no page reload occurred — the marker set above survives.
    assert page.evaluate("window.__e2eNoReloadMarker") is True


def test_edit_issue_form_updates_visible_card_without_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.evaluate("window.__e2eNoReloadMarker = true")

    page.locator("#col-todo .card").first.click()
    page.wait_for_selector("#edit-issue:not([hidden])")

    page.fill("#edit-issue-summary", "e2e-edited summary")
    page.click("#edit-issue-form button[type=submit]")

    page.wait_for_selector('.card:has-text("e2e-edited summary")')
    assert page.locator("#edit-issue").is_hidden()
    # BEH-4: no page reload occurred — the marker set above survives.
    assert page.evaluate("window.__e2eNoReloadMarker") is True
