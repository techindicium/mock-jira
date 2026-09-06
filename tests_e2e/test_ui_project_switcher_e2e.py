def test_switching_project_replaces_board_contents(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")

    # Create a second, empty Project via the real create-project form so there is
    # something distinct to switch to/from.
    page.fill("#project-key", "E2ESWITCH")
    page.fill("#project-name", "E2E Switch Project")
    page.click("#create-project-form button[type=submit]")

    page.wait_for_function(
        "() => document.getElementById('project-switcher')"
        ".selectedOptions[0]?.dataset.key === 'E2ESWITCH'"
    )
    # The new project has no issues yet — every column should now be empty.
    assert page.locator("#col-todo .card").count() == 0
    assert page.locator("#col-in_progress .card").count() == 0
    assert page.locator("#col-done .card").count() == 0

    # BEH-6: select a different Project from the switcher control.
    page.select_option("#project-switcher", label="ASSIST — Portwell Assist Engineering")

    page.wait_for_selector('#col-todo .card:has-text("Investigate INCIDENT-01")')
    assert page.locator("#col-todo .card").count() == 2
    assert page.locator("#col-in_progress .card").count() == 2
    assert page.locator("#col-done .card").count() == 2
