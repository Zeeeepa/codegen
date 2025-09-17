"""
Enhanced data models for the Codegen Dashboard application with AI integration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import json


class RunStatus(Enum):
    """Status of an agent run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectStatus(Enum):
    """Status of a project."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PAUSED = "paused"


class NotificationType(Enum):
    """Types of notifications."""
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    PRD_VALIDATION_FAILED = "prd_validation_failed"
    FOLLOWUP_AGENT_CREATED = "followup_agent_created"


class ChatMessageType(Enum):
    """Types of chat messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT_CREATION = "agent_creation"
    PRD_VALIDATION = "prd_validation"


class ValidationResult(Enum):
    """Results of PRD validation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


@dataclass
class AgentRun:
    """Represents an agent run with enhanced AI integration."""
    id: str
    title: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    url: str
    description: str = ""
    starred: bool = False
    follow_up_query: str = ""
    auto_follow_up: bool = False
    project_id: Optional[str] = None
    parent_run_id: Optional[str] = None  # For follow-up runs
    prd_validation_result: Optional[ValidationResult] = None
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """Represents a Codegen project with graph-sitter analysis."""
    id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    url: str
    starred: bool = False
    pr_count: int = 0
    last_pr_at: Optional[datetime] = None
    validation_gates: List[str] = field(default_factory=list)
    prd_content: str = ""
    graph_analysis: Optional[Dict[str, Any]] = None  # Graph-sitter analysis results
    codebase_snapshot: Optional[str] = None  # Git hash or version
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """Represents a chat message in the AI interface."""
    id: str
    type: ChatMessageType
    content: str
    timestamp: datetime
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent_run_id: Optional[str] = None  # If message created an agent run
    context_used: List[str] = field(default_factory=list)  # Context sources used


@dataclass
class ChatSession:
    """Represents a chat session with context management."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)
    active_project_id: Optional[str] = None
    context_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_runs_created: List[str] = field(default_factory=list)


@dataclass
class CodeContext:
    """Represents code context from RepoMaster analysis."""
    project_id: str
    file_path: str
    content: str
    analysis_type: str  # "function", "class", "file", "dependency"
    symbols: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PRDValidation:
    """Represents PRD validation results."""
    id: str
    agent_run_id: str
    prd_content: str
    validation_result: ValidationResult
    validation_details: Dict[str, Any]
    confidence_score: float
    missing_requirements: List[str] = field(default_factory=list)
    follow_up_suggestions: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphVisualization:
    """Represents graph-sitter visualization data."""
    project_id: str
    visualization_type: str  # "blast_radius", "call_trace", "dependency_trace", "method_relationships"
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PullRequest:
    """Represents a pull request with enhanced tracking."""
    id: str
    number: int
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    url: str
    project_id: str
    author: str
    description: str = ""
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    agent_run_id: Optional[str] = None  # If created by an agent


@dataclass
class Notification:
    """Represents a notification with enhanced context."""
    id: str
    type: NotificationType
    title: str
    message: str
    created_at: datetime
    read: bool = False
    data: Dict[str, Any] = field(default_factory=dict)
    action_url: Optional[str] = None
    related_agent_run_id: Optional[str] = None


@dataclass
class ValidationGate:
    """Represents a validation gate with script execution."""
    id: str
    name: str
    description: str
    script_path: str
    enabled: bool = True
    project_ids: List[str] = field(default_factory=list)
    trigger_events: List[str] = field(default_factory=list)  # pr_created, pr_updated
    last_run: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    timeout_seconds: int = 300
    environment_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowTemplate:
    """Represents a workflow template with AI integration."""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    prd_template: str = ""
    context_requirements: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowExecution:
    """Represents a workflow execution with progress tracking."""
    id: str
    template_id: str
    name: str
    status: RunStatus
    current_step: int = 0
    total_steps: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    agent_runs: List[str] = field(default_factory=list)  # List of agent run IDs
    results: Dict[str, Any] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    context_snapshots: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AIInsight:
    """Represents AI-generated insights and recommendations."""
    id: str
    type: str  # "performance", "code_quality", "architecture", "optimization"
    title: str
    description: str
    confidence: float
    project_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryEntry:
    """Represents a memory entry for AI context persistence."""
    id: str
    type: str  # "conversation", "code_context", "error_pattern", "success_pattern"
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    project_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    relevance_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0


@dataclass
class DashboardState:
    """Represents the current state of the dashboard with AI metrics."""
    running_instances: int = 0
    total_runs: int = 0
    starred_runs: int = 0
    active_projects: int = 0
    starred_projects: int = 0
    unread_notifications: int = 0
    active_workflows: int = 0
    active_chat_sessions: int = 0
    total_memory_entries: int = 0
    ai_insights_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


# Utility functions for model serialization
def serialize_datetime(dt: datetime) -> str:
    """Serialize datetime to ISO format string."""
    return dt.isoformat()


def deserialize_datetime(dt_str: str) -> datetime:
    """Deserialize datetime from ISO format string."""
    return datetime.fromisoformat(dt_str)


def model_to_dict(model_instance) -> Dict[str, Any]:
    """Convert dataclass model to dictionary with datetime serialization."""
    result = {}
    for key, value in model_instance.__dict__.items():
        if isinstance(value, datetime):
            result[key] = serialize_datetime(value)
        elif isinstance(value, Enum):
            result[key] = value.value
        elif isinstance(value, list):
            result[key] = [
                item.value if isinstance(item, Enum) else 
                serialize_datetime(item) if isinstance(item, datetime) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def dict_to_model(model_class, data: Dict[str, Any]):
    """Convert dictionary to dataclass model with datetime deserialization."""
    # This is a simplified implementation - in practice, you'd want more robust handling
    processed_data = {}
    for key, value in data.items():
        if isinstance(value, str) and key.endswith('_at'):
            try:
                processed_data[key] = deserialize_datetime(value)
            except ValueError:
                processed_data[key] = value
        else:
            processed_data[key] = value
    
    return model_class(**processed_data)
