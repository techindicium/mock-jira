from app.models import ISSUE_PRIORITIES, ISSUE_STATUSES, ISSUE_TYPES

# Reserved identifier prefixes from ../course-shared/canon/identifiers.md — read once, at
# plan-authoring time, and copied by value here. Never re-read at runtime: the constitution
# ("no inbound dependencies") forbids this repo from opening any file outside itself.
_CANON_RESERVED_PREFIXES = (
    "ACCOUNT-", "TICKET-", "ARTICLE-", "PROPOSAL-", "INCIDENT-",
    "POLICY-", "OPPORTUNITY-", "EXPERIMENT-", "P-",
)

SEED_PROJECT = {
    "key": "ASSIST",
    "name": "Portwell Assist Engineering",
    "description": (
        "Engineering tracker for Portwell Assist, the AI-assisted support-ticket triage pilot."
    ),
}

# 6 Issues: exactly 2 of each status (todo/in_progress/done), 2 of each issue_type
# (bug/task/story), 2 of each priority (low/medium/high) — per BEH-1 as tightened by review.
SEED_ISSUES = [
    {
        "summary": "Investigate INCIDENT-01: proposal quoted a superseded refund window",
        "description": (
            "A billing proposal cited an out-of-date refund-window policy instead of the "
            "current one. Trace which article version the retriever returned for ACCOUNT-1001 "
            "and confirm the index only serves published, current articles."
        ),
        "issue_type": "bug", "status": "todo", "priority": "high",
        "assignee": "Kofi Adjei", "reporter": "Joao Pinto",
    },
    {
        "summary": "Design review-queue triage rules for pilot expansion",
        "description": (
            "Support engineers flagged the review queue, not answer quality, as the pilot's "
            "real bottleneck. Propose a triage rule set so low-confidence proposals reach a "
            "reviewer faster without adding headcount."
        ),
        "issue_type": "story", "status": "todo", "priority": "medium",
        "assignee": "Mei Tan", "reporter": "Priya Nair",
    },
    {
        "summary": "Add webhook-retry safeguard after INCIDENT-02",
        "description": (
            "An integrations proposal told an account to disable a webhook retry its EDI feed "
            "depended on. Add a guard so the proposal generator never recommends disabling "
            "retries on a webhook flagged as EDI-critical."
        ),
        "issue_type": "task", "status": "in_progress", "priority": "low",
        "assignee": "Joao Pinto", "reporter": "Mei Tan",
    },
    {
        "summary": "Fix stale-article lookup in the proposal generator",
        "description": (
            "The retriever can still surface a superseded article version. Filter the article "
            "index to `status: published` only and drop anything a newer article's "
            "`supersedes` list names."
        ),
        "issue_type": "bug", "status": "in_progress", "priority": "medium",
        "assignee": "Priya Nair", "reporter": "Kofi Adjei",
    },
    {
        "summary": "Publish pilot-expansion readiness checklist",
        "description": (
            "One side wants to expand the pilot; the other wants review capacity solved "
            "first. Publish a checklist covering both positions so Product can decide with "
            "the tradeoffs visible."
        ),
        "issue_type": "story", "status": "done", "priority": "high",
        "assignee": "Kofi Adjei", "reporter": "Mei Tan",
    },
    {
        "summary": "Document review-capacity findings from the pilot",
        "description": (
            "Write up the pilot's review-queue bottleneck finding for the engineering team's "
            "retro, referencing the 22-minute median response time on proposal-sent tickets."
        ),
        "issue_type": "task", "status": "done", "priority": "low",
        "assignee": "Mei Tan", "reporter": "Joao Pinto",
    },
]


class SeedError(RuntimeError):
    """Raised when startup seeding cannot proceed. Carries a stable `code` for operators."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _validate_seed_data(project: dict, issues: list[dict]) -> None:
    if not project.get("key") or not project["key"].strip():
        raise SeedError("SEED_DATA_INVALID", "Seed project is missing a key")
    if any(project["key"].startswith(p) for p in _CANON_RESERVED_PREFIXES):
        raise SeedError(
            "SEED_DATA_INVALID",
            f"Seed project key '{project['key']}' collides with a canon-reserved prefix",
        )
    if not project.get("name") or not project["name"].strip():
        raise SeedError("SEED_DATA_INVALID", "Seed project is missing a name")

    if len(issues) != 6:
        raise SeedError("SEED_DATA_INVALID", f"Expected 6 seed issues, found {len(issues)}")

    for i, issue in enumerate(issues):
        if issue.get("issue_type") not in ISSUE_TYPES:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Seed issue {i} has invalid issue_type '{issue.get('issue_type')}'",
            )
        if issue.get("status") not in ISSUE_STATUSES:
            raise SeedError(
                "SEED_DATA_INVALID", f"Seed issue {i} has invalid status '{issue.get('status')}'"
            )
        if issue.get("priority") not in ISSUE_PRIORITIES:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Seed issue {i} has invalid priority '{issue.get('priority')}'",
            )
        if not issue.get("summary") or not issue["summary"].strip():
            raise SeedError("SEED_DATA_INVALID", f"Seed issue {i} is missing a summary")
        if not issue.get("assignee") or not issue.get("reporter"):
            raise SeedError("SEED_DATA_INVALID", f"Seed issue {i} is missing assignee or reporter")

    statuses = [issue["status"] for issue in issues]
    for status in ISSUE_STATUSES:
        count = statuses.count(status)
        if count != 2:
            raise SeedError(
                "SEED_DATA_INVALID",
                f"Expected exactly 2 seed issues with status '{status}', found {count}",
            )


def seed_if_empty(conn, db_path: str) -> None:
    """Seed one Project and six Issues on first run only. No-op if any Project already exists.

    Runs synchronously during app startup, before Uvicorn begins serving requests — no request
    can observe a partially-seeded state, and no concurrent writer can interleave with it.
    """
    existing = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()
    if existing["n"] > 0:
        return  # BEH-2: already seeded (or real data present) — never touch it

    _validate_seed_data(SEED_PROJECT, SEED_ISSUES)  # hardcoded data; a failure here is a code bug

    import sqlite3

    from app.db import allocate_issue_key

    try:
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description) VALUES (?, ?, ?)",
            (SEED_PROJECT["key"], SEED_PROJECT["name"], SEED_PROJECT["description"]),
        )
        project_id = cursor.lastrowid
        for issue in SEED_ISSUES:
            key = allocate_issue_key(conn, project_id, SEED_PROJECT["key"])
            conn.execute(
                """
                INSERT INTO issues
                    (key, project_id, summary, description, issue_type, status, priority,
                     assignee, reporter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key, project_id, issue["summary"], issue["description"], issue["issue_type"],
                    issue["status"], issue["priority"], issue["assignee"], issue["reporter"],
                ),
            )
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise SeedError(
            "SEED_DB_NOT_WRITABLE", f"Cannot write seed data to database at '{db_path}': {exc}"
        ) from exc
