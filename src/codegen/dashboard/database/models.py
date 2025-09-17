"""Pydantic models for dashboard database operations."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    AGENT_COMPLETE = "agent_complete"
    AGENT_FAILED = "agent_failed"
    PR_CREATED = "pr_created"
    VALIDATION_FAILED = "validation_failed"


class AgentRunStarred(BaseModel):
    """Model for starred agent runs."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    agent_run_id: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProjectStarred(BaseModel):
    """Model for starred projects."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    repo_name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPreferences(BaseModel):
    """Model for user preferences."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Notification(BaseModel):
    """Model for notifications."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    metadata: Dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ValidationGate(BaseModel):
    """Model for validation gates."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    repo_name: str
    gate_config: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PRDDialog(BaseModel):
    """Model for PRD dialogs."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    repo_name: str
    title: str
    content: str
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkflowTemplate(BaseModel):
    """Model for workflow templates."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    name: str
    description: str
    template_config: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DashboardSession(BaseModel):
    """Model for dashboard sessions."""
    id: Optional[str] = None
    user_id: str
    org_id: int
    session_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Request/Response Models for API endpoints

class StarAgentRunRequest(BaseModel):
    """Request model for starring an agent run."""
    agent_run_id: int
    metadata: Optional[Dict[str, Any]] = None


class StarProjectRequest(BaseModel):
    """Request model for starring a project."""
    repo_name: str
    metadata: Optional[Dict[str, Any]] = None


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    metadata: Optional[Dict[str, Any]] = None


class UpdatePreferencesRequest(BaseModel):
    """Request model for updating user preferences."""
    preferences: Dict[str, Any]


class CreateValidationGateRequest(BaseModel):
    """Request model for creating a validation gate."""
    repo_name: str
    gate_config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class CreatePRDDialogRequest(BaseModel):
    """Request model for creating a PRD dialog."""
    repo_name: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class CreateWorkflowTemplateRequest(BaseModel):
    """Request model for creating a workflow template."""
    name: str
    description: str
    template_config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


# Response Models

class PaginatedResponse(BaseModel):
    """Generic paginated response model."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class StarredAgentRunsResponse(BaseModel):
    """Response model for starred agent runs."""
    items: List[AgentRunStarred]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class StarredProjectsResponse(BaseModel):
    """Response model for starred projects."""
    items: List[ProjectStarred]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool


class NotificationsResponse(BaseModel):
    """Response model for notifications."""
    items: List[Notification]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    unread_count: int


class ValidationGatesResponse(BaseModel):
    """Response model for validation gates."""
    items: List[ValidationGate]
    total: int


class DatabaseHealthResponse(BaseModel):
    """Response model for database health check."""
    healthy: bool
    timestamp: datetime
    tables: Dict[str, int]  # table_name -> record_count


# Database Schema SQL (for reference and migrations)
DATABASE_SCHEMA_SQL = """
-- Agent Runs Starred Table
CREATE TABLE IF NOT EXISTS agent_runs_starred (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    agent_run_id INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id, agent_run_id)
);

-- Projects Starred Table
CREATE TABLE IF NOT EXISTS projects_starred (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id, repo_name)
);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validation Gates Table
CREATE TABLE IF NOT EXISTS validation_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    gate_config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PRD Dialogs Table
CREATE TABLE IF NOT EXISTS prd_dialogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow Templates Table
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dashboard Sessions Table
CREATE TABLE IF NOT EXISTS dashboard_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_runs_starred_user_org ON agent_runs_starred(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_projects_starred_user_org ON projects_starred(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_org ON notifications(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, org_id, read) WHERE read = FALSE;
CREATE INDEX IF NOT EXISTS idx_validation_gates_user_org ON validation_gates(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_validation_gates_repo ON validation_gates(repo_name, active);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_user ON dashboard_sessions(user_id, org_id);

-- Row Level Security (RLS) Policies
ALTER TABLE agent_runs_starred ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects_starred ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_gates ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_dialogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can access their own starred agent runs" ON agent_runs_starred
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own starred projects" ON projects_starred
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own preferences" ON user_preferences
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own notifications" ON notifications
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own validation gates" ON validation_gates
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own PRD dialogs" ON prd_dialogs
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own workflow templates" ON workflow_templates
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own dashboard sessions" ON dashboard_sessions
    FOR ALL USING (auth.uid()::text = user_id);
"""
