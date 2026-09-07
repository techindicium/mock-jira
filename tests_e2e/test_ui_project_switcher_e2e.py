import httpx


def test_switching_project_replaces_board_contents(page, ui_board_server):
    # This test is about switcher behavior itself, not project creation (creation is covered by
    # board-view.spec.md BEH-1/BEH-6 and project-management-screen.spec.md's own form) — create
    # a second, empty Project via a real, direct HTTP call so there is something distinct to
    # switch to/from. ASSIST is always the first-seeded Project (ORDER BY id ASC), so it stays
    # the default selection on load regardless of when this second Project is created.
    with httpx.Client(base_url=ui_board_server, timeout=5) as client:
        resp = client.post("/projects", json={"key": "E2ESWITCH", "name": "E2E Switch Project"})
        resp.raise_for_status()

    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.wait_for_selector('#col-todo .card:has-text("Investigate INCIDENT-01")')

    # BEH-6: select a different Project from the switcher control.
    page.select_option("#project-switcher", label="E2ESWITCH — E2E Switch Project")

    # The new project has no issues yet — every column should now be empty.
    page.wait_for_function(
        "document.getElementById('col-todo').querySelectorAll('.card').length === 0"
    )
    assert page.locator("#col-todo .card").count() == 0
    assert page.locator("#col-in_progress .card").count() == 0
    assert page.locator("#col-done .card").count() == 0

    # Switch back — the board fully replaces its contents again, never merging the two.
    page.select_option("#project-switcher", label="ASSIST — Portwell Assist Engineering")

    page.wait_for_selector('#col-todo .card:has-text("Investigate INCIDENT-01")')
    assert page.locator("#col-todo .card").count() == 2
    assert page.locator("#col-in_progress .card").count() == 2
    assert page.locator("#col-done .card").count() == 2
