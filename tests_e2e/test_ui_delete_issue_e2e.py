def test_delete_issue_removes_card_confirmed_after_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    card = page.locator("#col-todo .card").first
    issue_id = card.get_attribute("data-issue-id")

    # onDeleteIssueClick uses a native window.confirm() dialog — accept it for real.
    page.on("dialog", lambda dialog: dialog.accept())

    card.click()
    page.wait_for_selector("#edit-issue:not([hidden])")
    page.click("#delete-issue")

    page.wait_for_selector(f'.card[data-issue-id="{issue_id}"]', state="detached")
    assert page.locator(f'.card[data-issue-id="{issue_id}"]').count() == 0

    # BEH-5: verified by reloading the page and confirming it does not reappear.
    page.reload()
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator(f'.card[data-issue-id="{issue_id}"]').count() == 0
