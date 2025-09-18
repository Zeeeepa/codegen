"""Data models for Codegen Dashboard."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback for basic functionality without pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(**kwargs):
        return kwargs.get('default', None)


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    IDLE = "idle"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StarredAgent(BaseModel):
    """Model for starred agent runs."""
    agent_id: str
    starred_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DashboardStats(BaseModel):
    """Model for dashboard statistics."""
    total_agents: int = 0
    running_agents: int = 0
    completed_agents: int = 0
    failed_agents: int = 0
    starred_agents: int = 0
    
    total_projects: int = 0
    starred_projects: int = 0
    
    unread_notifications: int = 0
    total_notifications: int = 0
    
    last_updated: datetime = Field(default_factory=datetime.now)

