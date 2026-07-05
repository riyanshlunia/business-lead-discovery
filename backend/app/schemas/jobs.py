from datetime import datetime

from pydantic import BaseModel, Field


class JobCreateRequest(BaseModel):
    industry: str = Field(min_length=2, max_length=255)
    location: str = Field(min_length=2, max_length=255)
    limit: int = Field(default=100, ge=1, le=1000)
    project_name: str | None = Field(default=None, max_length=255)


class JobCreateResponse(BaseModel):
    job_id: int
    status: str
    query: str


class JobRead(BaseModel):
    id: int
    project_id: int
    status: str
    industry: str
    location: str
    query: str
    target_limit: int
    progress: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
