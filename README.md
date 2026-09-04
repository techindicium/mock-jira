# mock-jira

A standalone mock of a JIRA-shaped issue-tracking API for the adev course tracks to consume as
an external system dependency. Required by the `portwell-assist` (SDLC) and `portwell-analytics`
(DDLC) tracks.

Independent repo: no dependency on `course-shared`, the other `mock-*` repos, or any track repo.
Tracks that need it pull it in as a service dependency; this repo never depends on them back.

Not yet scoped. Run `/adev:brainstorm` here to charter what the mock API surface needs to cover
before implementing it.
