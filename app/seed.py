import json
from pathlib import Path

from app.models import ISSUE_PRIORITIES, ISSUE_STATUSES, ISSUE_TYPES

# Reserved identifier prefixes from ../course-shared/canon/identifiers.md — read once, at
# plan-authoring time, and copied by value here. Never re-read at runtime: the constitution
# ("no inbound dependencies") forbids this repo from opening any file outside itself.
_CANON_RESERVED_PREFIXES = (
    "ACCOUNT-", "TICKET-", "ARTICLE-", "PROPOSAL-", "INCIDENT-",
    "POLICY-", "OPPORTUNITY-", "EXPERIMENT-", "P-",
)

SEED_PROJECT = {
    "key": "PORTAL",
    "name": "Help portal engineering",
    "description": "Change tracking for the customer help portal and the WMS modules it serves."
}

# 6 Issues: exactly 2 of each status (todo/in_progress/done), 2 of each issue_type
# (bug/task/story), 2 of each priority (low/medium/high) — per BEH-1 as tightened by review.
SEED_ISSUES = [
    {
        "summary": "Answers on integrations topics are sent without review",
        "description": "Raised after INCIDENT-02. Integrations is a consequential area and the routing rules do not treat it as one, so an answer reaches an Enterprise account with nobody having read it.",
        "issue_type": "bug",
        "status": "todo",
        "priority": "high",
        "assignee": "Kofi Adjei",
        "reporter": "Priya Nair"
    },
    {
        "summary": "Two refund windows in one answer",
        "description": "A billing answer quoted 30 and 60 days in the same reply. Both articles are published and one supersedes the other; nothing at the point of retrieval says so.",
        "issue_type": "bug",
        "status": "todo",
        "priority": "medium",
        "assignee": "Kofi Adjei",
        "reporter": "Joao Pinto"
    },
    {
        "summary": "Articles with no reviewer are being used",
        "description": "POLICY-02 says an article without a source and a reviewer is not eligible. ARTICLE-0131 has neither and is the only cycle-count article, so it answers alone.",
        "issue_type": "task",
        "status": "in_progress",
        "priority": "high",
        "assignee": "Kofi Adjei",
        "reporter": "Ana Fialho"
    },
    {
        "summary": "Password reset answer is out of date",
        "description": "Self-service reset shipped in June. The article still describes the old process and tells the operator to raise a ticket.",
        "issue_type": "bug",
        "status": "in_progress",
        "priority": "low",
        "assignee": "Joao Pinto",
        "reporter": "Joao Pinto"
    },
    {
        "summary": "Match score is not calibrated",
        "description": "The relevance score is word overlap with a floor. It ranks a close title match above a better body match, which is how a superseded article reaches the top of a result list.",
        "issue_type": "story",
        "status": "done",
        "priority": "medium",
        "assignee": "Kofi Adjei",
        "reporter": "Kofi Adjei"
    },
    {
        "summary": "Restore the article index integration test",
        "description": "It was stubbed on a branch to unblock a release and never restored. The test now builds its own two-article index, so its assertions pass against data written to satisfy them.",
        "issue_type": "task",
        "status": "done",
        "priority": "low",
        "assignee": "Kofi Adjei",
        "reporter": "Kofi Adjei"
    }
]


# 4 Users: the "Assist engineering" roster already referenced by name (never by id — the User
# directory is additive, not a foreign key) as Issue assignee/reporter above. Same sourcing rule
# BEH-3 established: real names/roles from course-shared/canon/company.md's Named People table,
# never invented placeholders.
SEED_USERS = [
    {
        "name": "Inês Duarte",
        "role": "Founder and CEO"
    },
    {
        "name": "Mei Tan",
        "role": "Head of Engineering"
    },
    {
        "name": "Ana Fialho",
        "role": "VP Product"
    },
    {
        "name": "Gabriela Rocha",
        "role": "Customer Success Director"
    },
    {
        "name": "Sofia Marques",
        "role": "Analytics Lead"
    },
    {
        "name": "Marta Oliveira",
        "role": "Commercial Director"
    },
    {
        "name": "Henrik Sole",
        "role": "Operations and Finance"
    },
    {
        "name": "Rui Bastos",
        "role": "Support Manager"
    },
    {
        "name": "Lucia Ferreira",
        "role": "Service Delivery Manager"
    },
    {
        "name": "Kofi Adjei",
        "role": "Staff Engineer, help portal"
    },
    {
        "name": "Declan Byrne",
        "role": "Data Engineer"
    },
    {
        "name": "Priya Nair",
        "role": "Solution Consultant"
    },
    {
        "name": "Joao Pinto",
        "role": "Support Engineer, Tier 2"
    },
    {
        "name": "Tomas Silva",
        "role": "Legal and Data Protection"
    }
]


class SeedError(RuntimeError):
    """Raised when startup seeding cannot proceed. Carries a stable `code` for operators."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


_FIXTURE = Path(__file__).parent / "fixtures" / "seed_reference.json"


def load_seed_data() -> tuple[dict, list[dict], list[dict]]:
    """Project, issues and users, from the canon-generated fixture when it is present.

    Generated by course-shared/tools/seed_mocks.py and committed here, so nothing outside this
    repository is opened at runtime. The literals above stay as the fallback, which keeps this
    repo standing alone if the fixture is ever absent.
    """
    if not _FIXTURE.exists():
        return SEED_PROJECT, SEED_ISSUES, SEED_USERS
    data = json.loads(_FIXTURE.read_text())
    return data["project"], data["issues"], data["users"]


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

    project, issues, _ = load_seed_data()
    _validate_seed_data(project, issues)  # a failure here is a bug in the seed data

    import sqlite3

    from app.db import allocate_issue_key

    try:
        cursor = conn.execute(
            "INSERT INTO projects (key, name, description) VALUES (?, ?, ?)",
            (project["key"], project["name"], project["description"]),
        )
        project_id = cursor.lastrowid
        for issue in issues:
            key = allocate_issue_key(conn, project_id, project["key"])
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


def _validate_seed_users(users: list[dict]) -> None:
    for i, user in enumerate(users):
        if not user.get("name") or not user["name"].strip():
            raise SeedError("SEED_DATA_INVALID", f"Seed user {i} is missing a name")


def seed_users_if_empty(conn, db_path: str) -> None:
    """Seed the User directory on first run only. No-op if any User already exists.

    Independent of `seed_if_empty` (Project/Issue seeding): the User directory is an additive,
    unrelated resource (no foreign key to Issue/Project — see charter Out of Scope), so it gets
    its own emptiness check rather than being folded into the Project/Issue seeding transaction.
    """
    existing = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if existing["n"] > 0:
        return

    _, _, users = load_seed_data()
    _validate_seed_users(users)

    import sqlite3

    try:
        for user in users:
            conn.execute(
                "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
                (user["name"], user.get("email"), user.get("role")),
            )
        conn.commit()
    except sqlite3.OperationalError as exc:
        raise SeedError(
            "SEED_DB_NOT_WRITABLE", f"Cannot write seed users to database at '{db_path}': {exc}"
        ) from exc
