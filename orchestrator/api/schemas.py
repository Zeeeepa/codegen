from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# Projects
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Repositories
class RepositoryCreate(BaseModel):
    provider: str = "github"
    org: str
    name: str
    default_branch: str = "main"
    visibility: str = "private"


class RepositoryOut(BaseModel):
    id: int
    provider: str
    org: str
    name: str
    default_branch: str
    visibility: str

    class Config:
        from_attributes = True


class ProjectRepositoryLink(BaseModel):
    project_id: int
    repository_id: int


class PinCreate(BaseModel):
    project_id: int
    repository_id: int
    user_id: Optional[str] = None


class BranchCreate(BaseModel):
    repository_id: int
    name: str
    from_ref: Optional[str] = None  # default branch if None


class BranchOut(BaseModel):
    id: int
    repository_id: int
    name: str
    head_sha: Optional[str] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class PROpenRequest(BaseModel):
    repository_id: int
    head_branch: str
    base_branch: str
    title: str
    body: Optional[str] = None


class PROut(BaseModel):
    id: int
    repository_id: int
    number: int
    head_branch_id: int
    base_branch: str
    state: str
    checks_status: Optional[str] = None
    web_url: Optional[str] = None

    class Config:
        from_attributes = True


class AgentRunCreate(BaseModel):
    provider: str = "codegen"
    external_id: str
    repository_id: int
    branch_id: Optional[int] = None


class AgentRunOut(BaseModel):
    id: int
    provider: str
    external_id: str
    repository_id: int
    branch_id: Optional[int]
    status: str
    web_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisStart(BaseModel):
    repository_id: int
    branch_id: Optional[int] = None
    snapshot_id: Optional[int] = None


class AnalysisOut(BaseModel):
    id: int
    repository_id: int
    branch_id: Optional[int]
    snapshot_id: Optional[int]
    status: str

    class Config:
        from_attributes = True


class FindingOut(BaseModel):
    id: int
    analysis_id: int
    type: str
    file: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    symbol: Optional[str] = None
    context: Optional[str] = None
    confidence: Optional[float] = None
    status: str

    class Config:
        from_attributes = True

