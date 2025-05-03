"""
API Schemas Module

This module defines the Pydantic models for API requests and responses.
These models are used for validation and serialization of API data.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Repository schemas
class RepositoryBase(BaseModel):
    """Base schema for repository data."""
    name: str = Field(..., description="Repository name")
    url: str = Field(..., description="Repository URL")
    description: Optional[str] = Field(None, description="Repository description")
    default_branch: str = Field("main", description="Default branch")

class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository."""
    create_snapshot: bool = Field(False, description="Whether to create an initial snapshot")
    analyze: bool = Field(False, description="Whether to analyze the repository after creation")
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")

class RepositoryResponse(RepositoryBase):
    """Schema for repository response."""
    id: int = Field(..., description="Repository ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# Snapshot schemas
class SnapshotBase(BaseModel):
    """Base schema for snapshot data."""
    repo_id: int = Field(..., description="Repository ID")
    commit_sha: Optional[str] = Field(None, description="Commit SHA")
    branch: Optional[str] = Field(None, description="Branch name")

class SnapshotCreate(SnapshotBase):
    """Schema for creating a snapshot."""
    analyze: bool = Field(False, description="Whether to analyze the snapshot after creation")
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")

class SnapshotResponse(BaseModel):
    """Schema for snapshot response."""
    id: int = Field(..., description="Snapshot ID")
    snapshot_id: str = Field(..., description="Unique snapshot identifier")
    repo_id: int = Field(..., description="Repository ID")
    commit_sha: Optional[str] = Field(None, description="Commit SHA")
    branch: Optional[str] = Field(None, description="Branch name")
    timestamp: datetime = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Snapshot metadata")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# File schemas
class FileBase(BaseModel):
    """Base schema for file data."""
    filepath: str = Field(..., description="File path")
    name: str = Field(..., description="File name")
    extension: Optional[str] = Field(None, description="File extension")

class FileResponse(FileBase):
    """Schema for file response."""
    id: int = Field(..., description="File ID")
    repo_id: int = Field(..., description="Repository ID")
    snapshot_id: int = Field(..., description="Snapshot ID")
    s3_key: Optional[str] = Field(None, description="S3 key for file content")
    content_hash: Optional[str] = Field(None, description="Content hash")
    line_count: Optional[int] = Field(None, description="Line count")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# Analysis schemas
class AnalysisRequest(BaseModel):
    """Schema for analysis request."""
    repo_id: int = Field(..., description="Repository ID")
    analysis_type: str = Field(..., description="Analysis type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")

class AnalysisResponse(BaseModel):
    """Schema for analysis response."""
    id: int = Field(..., description="Analysis ID")
    repo_id: int = Field(..., description="Repository ID")
    snapshot_id: int = Field(..., description="Snapshot ID")
    analysis_type: str = Field(..., description="Analysis type")
    timestamp: datetime = Field(..., description="Creation timestamp")
    summary: Optional[str] = Field(None, description="Analysis summary")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Analysis metrics")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

class AnalysisIssueBase(BaseModel):
    """Base schema for analysis issue data."""
    issue_type: str = Field(..., description="Issue type")
    severity: str = Field(..., description="Issue severity")
    message: str = Field(..., description="Issue message")
    file_path: Optional[str] = Field(None, description="File path")
    line_number: Optional[int] = Field(None, description="Line number")
    code_snippet: Optional[str] = Field(None, description="Code snippet")
    suggestion: Optional[str] = Field(None, description="Suggestion for fixing the issue")

class AnalysisIssueResponse(AnalysisIssueBase):
    """Schema for analysis issue response."""
    id: int = Field(..., description="Issue ID")
    analysis_result_id: int = Field(..., description="Analysis result ID")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# Job schemas
class AnalysisJobBase(BaseModel):
    """Base schema for analysis job data."""
    repo_id: int = Field(..., description="Repository ID")
    job_type: str = Field(..., description="Job type")
    status: str = Field(..., description="Job status")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")

class AnalysisJobResponse(AnalysisJobBase):
    """Schema for analysis job response."""
    id: int = Field(..., description="Job ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result_id: Optional[int] = Field(None, description="Analysis result ID")
    error_message: Optional[str] = Field(None, description="Error message")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# Webhook schemas
class WebhookBase(BaseModel):
    """Base schema for webhook data."""
    repo_id: int = Field(..., description="Repository ID")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to trigger the webhook")
    secret: Optional[str] = Field(None, description="Webhook secret")

class WebhookCreate(WebhookBase):
    """Schema for creating a webhook."""
    pass

class WebhookResponse(WebhookBase):
    """Schema for webhook response."""
    id: int = Field(..., description="Webhook ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_triggered: Optional[datetime] = Field(None, description="Last triggered timestamp")
    
    class Config:
        """Pydantic config."""
        orm_mode = True

# Comparison schemas
class ComparisonRequest(BaseModel):
    """Schema for comparison request."""
    snapshot1_id: str = Field(..., description="First snapshot ID")
    snapshot2_id: str = Field(..., description="Second snapshot ID")

class ComparisonResponse(BaseModel):
    """Schema for comparison response."""
    snapshot1_id: str = Field(..., description="First snapshot ID")
    snapshot2_id: str = Field(..., description="Second snapshot ID")
    files_added: List[str] = Field(..., description="Files added")
    files_removed: List[str] = Field(..., description="Files removed")
    files_modified: List[str] = Field(..., description="Files modified")
    metrics_diff: Dict[str, Any] = Field(..., description="Metrics difference")
"""

