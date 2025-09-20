"""
Codegen Workflow Events

Event definitions for the CI/CD validation workflow system.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ValidationStatus(str, Enum):
    """Validation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationResult(BaseModel):
    """Result of a validation step."""
    status: ValidationStatus
    severity: ValidationSeverity = ValidationSeverity.INFO
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None
    artifacts: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None


# Base Event Classes (using workflows-py Event pattern)
try:
    from workflows.events import Event
except ImportError:
    # Fallback if workflows-py not available
    from pydantic import BaseModel as Event


class CodegenValidationEvent(Event):
    """Base class for all Codegen validation events."""
    agent_run_id: str
    organization_id: str
    repository_id: Optional[str] = None
    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    triggered_by: str = "system"
    metadata: Optional[Dict[str, Any]] = None


class AgentRunValidationEvent(CodegenValidationEvent):
    """Event triggered when an agent run needs validation."""
    agent_type: str
    prompt: str
    source_type: str
    execution_status: str
    result_summary: Optional[str] = None
    output_files: Optional[List[str]] = None
    tokens_used: Optional[int] = None
    api_calls_made: Optional[int] = None


class CodeQualityValidationEvent(CodegenValidationEvent):
    """Event for code quality validation."""
    changed_files: List[str]
    language: str
    test_coverage_required: bool = True
    lint_rules: Optional[Dict[str, Any]] = None
    complexity_threshold: Optional[int] = None


class SecurityValidationEvent(CodegenValidationEvent):
    """Event for security validation."""
    scan_types: List[str] = Field(default_factory=lambda: ["secrets", "vulnerabilities", "dependencies"])
    severity_threshold: ValidationSeverity = ValidationSeverity.WARNING
    exclude_patterns: Optional[List[str]] = None


class DeploymentValidationEvent(CodegenValidationEvent):
    """Event for deployment validation."""
    environment: str
    deployment_type: str
    health_checks: List[str] = Field(default_factory=list)
    rollback_enabled: bool = True
    timeout_minutes: int = 30


class ValidationCompleteEvent(CodegenValidationEvent):
    """Event emitted when all validations are complete."""
    overall_status: ValidationStatus
    validation_results: List[ValidationResult]
    total_duration_seconds: float
    passed_count: int
    failed_count: int
    skipped_count: int
    summary: str


class ValidationStepEvent(CodegenValidationEvent):
    """Event for individual validation step completion."""
    step_name: str
    step_type: str
    result: ValidationResult


class ValidationErrorEvent(CodegenValidationEvent):
    """Event for validation errors."""
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    recovery_suggestions: Optional[List[str]] = None


class ValidationRetryEvent(CodegenValidationEvent):
    """Event for validation retry attempts."""
    step_name: str
    retry_count: int
    max_retries: int
    delay_seconds: float
    reason: str


class ValidationCancelledEvent(CodegenValidationEvent):
    """Event when validation is cancelled."""
    cancelled_by: str
    reason: str
    partial_results: Optional[List[ValidationResult]] = None


class ValidationTimeoutEvent(CodegenValidationEvent):
    """Event when validation times out."""
    timeout_seconds: float
    completed_steps: List[str]
    pending_steps: List[str]


# Workflow Control Events
class PauseValidationEvent(CodegenValidationEvent):
    """Event to pause validation workflow."""
    reason: str
    resume_conditions: Optional[List[str]] = None


class ResumeValidationEvent(CodegenValidationEvent):
    """Event to resume paused validation."""
    resume_reason: str
    skip_completed: bool = True


class ValidationConfigUpdateEvent(CodegenValidationEvent):
    """Event to update validation configuration."""
    config_changes: Dict[str, Any]
    apply_immediately: bool = False


# Integration Events
class GitHubCheckSuiteEvent(CodegenValidationEvent):
    """Event from GitHub check suite."""
    check_suite_id: str
    check_run_id: Optional[str] = None
    action: str  # requested, rerequested, completed
    conclusion: Optional[str] = None
    head_branch: str
    head_sha: str


class LinearIssueEvent(CodegenValidationEvent):
    """Event from Linear issue updates."""
    issue_id: str
    issue_title: str
    issue_status: str
    assignee_id: Optional[str] = None
    labels: Optional[List[str]] = None


class SlackNotificationEvent(CodegenValidationEvent):
    """Event for Slack notifications."""
    channel: str
    message: str
    thread_ts: Optional[str] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    mention_users: Optional[List[str]] = None


# Metrics and Monitoring Events
class ValidationMetricsEvent(CodegenValidationEvent):
    """Event for validation metrics collection."""
    metrics: Dict[str, Any]
    timestamp: str
    tags: Optional[Dict[str, str]] = None


class ValidationHealthCheckEvent(CodegenValidationEvent):
    """Event for validation system health checks."""
    component: str
    status: str
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    last_success: Optional[str] = None
