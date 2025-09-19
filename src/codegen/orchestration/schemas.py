"""
Schema definitions for the visual orchestration CI/CD system.

These schemas define the structure for pipelines, stages, tasks, and execution contexts
used throughout the orchestration system.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import json


class ExecutionStatus(str, Enum):
    """Status of pipeline/stage/task execution."""
    PENDING = "pending"
    RUNNING = "running" 
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TriggerType(str, Enum):
    """Types of pipeline triggers."""
    MANUAL = "manual"
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    GIT_PUSH = "git_push"
    GIT_PR = "git_pr" 
    GIT_TAG = "git_tag"


class StageType(str, Enum):
    """Types of pipeline stages."""
    AGENT_TASK = "agent_task"
    SHELL_COMMAND = "shell_command"
    DOCKER_RUN = "docker_run"
    DEPLOY = "deploy"
    TEST = "test"
    BUILD = "build"
    NOTIFICATION = "notification"
    PARALLEL_GROUP = "parallel_group"
    CONDITIONAL = "conditional"


@dataclass
class ResourceLimits:
    """Resource allocation limits for execution."""
    cpu_cores: Optional[float] = None
    memory_mb: Optional[int] = None
    max_execution_time: Optional[int] = None  # seconds
    max_parallel_tasks: Optional[int] = None


@dataclass
class WebhookConfig:
    """Webhook configuration for callbacks."""
    url: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    auth_token: Optional[str] = None
    retry_attempts: int = 3
    retry_delay: int = 5  # seconds
    timeout: int = 30  # seconds


@dataclass
class GitTriggerConfig:
    """Git-based trigger configuration."""
    repository: str
    branches: List[str] = field(default_factory=lambda: ["main", "develop"])
    paths: Optional[List[str]] = None  # File path filters
    ignore_paths: Optional[List[str]] = None
    webhook_secret: Optional[str] = None


@dataclass
class ScheduleTriggerConfig:
    """Schedule-based trigger configuration."""
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True


@dataclass
class AgentTaskConfig:
    """Configuration for agent-based tasks."""
    prompt: str
    agent_type: str = "default"
    timeout: Optional[int] = None
    org_id: Optional[str] = None
    api_token: Optional[str] = None
    base_url: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShellCommandConfig:
    """Configuration for shell command execution."""
    command: str
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    capture_output: bool = True
    timeout: Optional[int] = None


@dataclass
class DockerRunConfig:
    """Configuration for Docker container execution."""
    image: str
    command: Optional[str] = None
    working_directory: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)
    networks: List[str] = field(default_factory=list)
    timeout: Optional[int] = None


@dataclass
class ConditionalConfig:
    """Configuration for conditional execution."""
    condition: str  # Expression to evaluate
    if_true: Optional[str] = None  # Stage ID to execute if true
    if_false: Optional[str] = None  # Stage ID to execute if false


@dataclass
class StageDefinition:
    """Definition of a pipeline stage."""
    id: str
    name: str
    stage_type: StageType
    description: Optional[str] = None
    
    # Dependencies and execution flow
    depends_on: List[str] = field(default_factory=list)
    can_run_parallel: bool = True
    continue_on_failure: bool = False
    
    # Stage-specific configurations
    agent_config: Optional[AgentTaskConfig] = None
    shell_config: Optional[ShellCommandConfig] = None
    docker_config: Optional[DockerRunConfig] = None
    conditional_config: Optional[ConditionalConfig] = None
    
    # Resource and execution settings
    resource_limits: Optional[ResourceLimits] = None
    retry_attempts: int = 0
    retry_delay: int = 10  # seconds
    
    # Metadata and variables
    variables: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class PipelineDefinition:
    """Complete pipeline definition."""
    id: str
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Pipeline structure
    stages: List[StageDefinition] = field(default_factory=list)
    
    # Trigger configuration
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Global settings
    global_variables: Dict[str, Any] = field(default_factory=dict)
    global_resource_limits: Optional[ResourceLimits] = None
    
    # Webhook and notification settings
    webhooks: List[WebhookConfig] = field(default_factory=list)
    notifications: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Execution settings
    max_parallel_stages: int = 10
    max_execution_time: Optional[int] = None  # seconds
    cleanup_on_failure: bool = True


@dataclass
class TaskExecution:
    """Runtime execution information for a task."""
    id: str
    stage_id: str
    pipeline_id: str
    status: ExecutionStatus
    
    # Execution details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results and outputs
    result: Optional[Any] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    exit_code: Optional[int] = None
    
    # Resource usage
    cpu_usage: Optional[float] = None
    memory_usage: Optional[int] = None  # MB
    
    # Agent-specific information
    agent_run_id: Optional[str] = None
    agent_web_url: Optional[str] = None
    
    # Retry information
    attempt_number: int = 1
    max_attempts: int = 1
    
    # Context and metadata
    variables: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


@dataclass
class PipelineExecution:
    """Runtime execution information for an entire pipeline."""
    id: str
    pipeline_id: str
    pipeline_definition: PipelineDefinition
    status: ExecutionStatus
    
    # Execution details
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Task executions
    tasks: Dict[str, TaskExecution] = field(default_factory=dict)
    
    # Trigger information
    triggered_by: TriggerType
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    
    # Results and metrics
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    skipped_stages: int = 0
    
    # Resource usage
    total_cpu_usage: Optional[float] = None
    total_memory_usage: Optional[int] = None
    
    # Context and metadata
    variables: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    
    # Webhook delivery status
    webhook_deliveries: List[Dict[str, Any]] = field(default_factory=list)


# Type aliases for complex types
AgentTask = Union[TaskExecution, Dict[str, Any]]
PipelineContext = Dict[str, Any]
ExecutionResult = Dict[str, Any]