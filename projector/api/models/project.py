"""
Pydantic models for the Projector API.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str
    git_url: str
    slack_channel: Optional[str] = None
    max_parallel_tasks: int = 2

class ProjectCreate(ProjectBase):
    """Model for creating a new project."""
    pass

class ProjectUpdate(BaseModel):
    """Model for updating a project."""
    name: Optional[str] = None
    git_url: Optional[str] = None
    slack_channel: Optional[str] = None
    max_parallel_tasks: Optional[int] = None
    documents: Optional[List[str]] = None
    features: Optional[Dict[str, Any]] = None
    implementation_plan: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    """Model for a task in the implementation plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    status: str = "pending"
    dependencies: List[str] = []
    completed_at: Optional[float] = None

class ImplementationPlan(BaseModel):
    """Model for an implementation plan."""
    description: Optional[str] = None
    tasks: List[Task] = []

class Project(ProjectBase):
    """Complete project model with all fields."""
    id: str
    documents: List[str] = []
    features: Dict[str, Any] = {}
    implementation_plan: Optional[ImplementationPlan] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True