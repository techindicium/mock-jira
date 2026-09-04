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
