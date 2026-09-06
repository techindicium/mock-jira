def test_drag_card_to_new_column_persists_after_reload(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    card = page.locator("#col-todo .card").first
    issue_id = card.get_attribute("data-issue-id")

    # Real drag event, not a direct call into board-logic.js's moveIssueStatus().
    card.drag_to(page.locator('.column[data-status="done"]'))

    page.wait_for_selector(f'#col-done .card[data-issue-id="{issue_id}"]')
    assert page.locator(f'#col-todo .card[data-issue-id="{issue_id}"]').count() == 0

    # BEH-2: verified by reloading the page in the same real browser.
    page.reload()
    page.wait_for_selector("#board:not([hidden])")
    assert page.locator(f'#col-done .card[data-issue-id="{issue_id}"]').count() == 1
    assert page.locator(f'#col-todo .card[data-issue-id="{issue_id}"]').count() == 0
