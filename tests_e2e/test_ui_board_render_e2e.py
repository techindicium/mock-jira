def test_seeded_board_renders_with_issues_in_correct_columns(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    # Real DOM only — never board-logic.js's internal state or a mocked fetch response.
    assert page.locator("#col-todo .card").count() == 2
    assert page.locator("#col-in_progress .card").count() == 2
    assert page.locator("#col-done .card").count() == 2

    assert page.locator(
        '#col-todo .card:has-text("Investigate INCIDENT-01")'
    ).count() == 1
    assert page.locator(
        '#col-done .card:has-text("Publish pilot-expansion readiness checklist")'
    ).count() == 1
