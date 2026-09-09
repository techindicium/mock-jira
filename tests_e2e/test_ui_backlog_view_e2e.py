"""Real-browser e2e coverage for the Backlog list view and its filters (backlog-view.spec.md).

Covers BEH-2 (Backlog reads the same selected Project as Board), BEH-7 (filters persist across
Project switches), and BEH-6/BEH-5 (zero-match empty state and clearing filters restores Issues)
— all cross-view, stateful behaviors that the pure-function unit tests in Tasks 1-6 cannot
exercise. Uses the real seeded Projects: PORTAL (default-selected, 6 Issues) and DATA (3 Issues).
"""


def test_switching_project_updates_backlog_and_board_data(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 6"
    )

    # BEH-2: the switcher lives in Board's header (the only place it's rendered) — switch
    # Project from there and confirm both Board and Backlog pick up the new selection.
    page.select_option("#project-switcher", label="DATA — Analytics requests")

    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 3"
    )
    assert page.locator("#col-todo .card").count() == 2  # DATA: task/todo/high, bug/todo/high
    assert page.locator("#col-in_progress .card").count() == 1  # DATA: task/in_progress/medium
    assert page.locator("#col-done .card").count() == 0

    # Backlog, switched to afterward with no further switcher interaction, shows the same
    # Project's data — proof the two views share one selection rather than each tracking its own.
    page.click("#nav-backlog")
    page.wait_for_selector("#view-backlog:not([hidden])")
    assert page.locator("#backlog-rows tr").count() == 3  # DATA: 3 seeded issues


def test_filters_persist_across_project_switch(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 6"
    )

    page.select_option("#filter-issue-type", value="bug")

    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 3"
    )
    assert page.locator("#col-todo .card").count() == 2  # PORTAL bugs: todo/high, todo/medium
    assert page.locator("#col-in_progress .card").count() == 1  # PORTAL bug: in_progress/low
    assert page.locator("#col-done .card").count() == 0

    # BEH-7: switching Project must not silently reset the active filter back to "All".
    page.select_option("#project-switcher", label="DATA — Analytics requests")

    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 1"
    )
    assert page.locator("#filter-issue-type").input_value() == "bug"
    assert page.locator("#col-todo .card").count() == 1  # DATA's only bug: todo/high
    assert page.locator("#col-in_progress .card").count() == 0
    assert page.locator("#col-done .card").count() == 0


def test_zero_match_filter_shows_empty_state_and_clearing_restores_issues(page, ui_board_server):
    page.goto(ui_board_server)
    page.wait_for_selector("#board:not([hidden])")
    page.wait_for_function(
        "document.querySelectorAll('#col-todo .card, #col-in_progress .card, "
        "#col-done .card').length === 6"
    )
    assert page.locator("#filter-empty-state").is_hidden()

    # BEH-6: priority=high + issue-type=story is a guaranteed zero-match combination against
    # PORTAL's seeded issues — PORTAL's only story Issue is priority=medium.
    page.select_option("#filter-priority", value="high")
    page.select_option("#filter-issue-type", value="story")

    page.wait_for_selector("#filter-empty-state:not([hidden])")
    assert page.locator("#filter-empty-state").inner_text() == "No issues match the current filters."
    assert page.locator("#col-todo .card").count() == 0
    assert page.locator("#col-in_progress .card").count() == 0
    assert page.locator("#col-done .card").count() == 0

    # BEH-5: clearing one filter (back to "All") restores the previously-excluded Issues and
    # hides the zero-match message.
    page.select_option("#filter-issue-type", value="")

    page.wait_for_selector("#filter-empty-state", state="hidden")
    assert page.locator("#col-todo .card").count() == 1  # PORTAL: bug/todo/high
    assert page.locator("#col-in_progress .card").count() == 1  # PORTAL: task/in_progress/high
    assert page.locator("#col-done .card").count() == 0
