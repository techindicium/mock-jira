from typing import Literal

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    key: str
    name: str
    description: str | None = None  # optional per review note SA-1; defaults to "" on create


class ProjectRead(BaseModel):
    id: int
    key: str
    name: str
    description: str


ISSUE_TYPES = ("bug", "task", "story")
ISSUE_STATUSES = ("todo", "in_progress", "done")
ISSUE_PRIORITIES = ("low", "medium", "high")


class IssueCreate(BaseModel):
    project_id: int
    summary: str
    issue_type: Literal["bug", "task", "story"]
    priority: Literal["low", "medium", "high"]
    description: str | None = None
    assignee: str | None = None
    reporter: str | None = None


class IssueRead(BaseModel):
    id: int
    key: str
    project_id: int
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: str
    reporter: str
    created_at: str
    updated_at: str
    sprint_id: int | None = None


class IssuePatch(BaseModel):
    summary: str | None = None
    description: str | None = None
    issue_type: Literal["bug", "task", "story"] | None = None
    priority: Literal["low", "medium", "high"] | None = None
    assignee: str | None = None
    reporter: str | None = None
    status: Literal["todo", "in_progress", "done"] | None = None
    sprint_id: int | None = None


class UserCreate(BaseModel):
    name: str
    email: str | None = None
    role: str | None = None


class UserRead(BaseModel):
    id: int
    name: str
    email: str | None = None
    role: str | None = None


class CommentCreate(BaseModel):
    body: str
    author: str | None = None


class CommentRead(BaseModel):
    id: int
    issue_id: int
    body: str
    author: str
    created_at: str


SPRINT_STATUSES = ("planned", "active", "closed")


class SprintCreate(BaseModel):
    name: str
    start_date: str | None = None
    end_date: str | None = None
    status: str | None = None  # accepted but ignored at creation time; always 'planned'


class SprintRead(BaseModel):
    id: int
    project_id: int
    name: str
    start_date: str | None = None
    end_date: str | None = None
    status: str


class SprintPatch(BaseModel):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    status: Literal["planned", "active", "closed"] | None = None
