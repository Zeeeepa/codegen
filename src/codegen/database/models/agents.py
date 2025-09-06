"""
Agent-related database models.

Models for agent runs, logs, states, and tasks.
"""

from typing import List, Optional
from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped

from .base import BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin, VersionedMixin


class AgentRun(BaseModel, SoftDeleteMixin, AuditMixin, StatusMixin, VersionedMixin):
    """
    Agent run model representing a single agent execution.
    
    Maps to API endpoints: 
    - POST /v1/organizations/{org_id}/agent/run
    - GET /v1/organizations/{org_id}/agent/run/{agent_run_id}
    - GET /v1/organizations/{org_id}/agent/runs
    
    UI Data Flow: Agent run dashboard, execution monitoring, run history
    """
    
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    created_by_user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    repository_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("repository.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Agent run identification
    external_id = Column(Integer, nullable=True, index=True)  # External system ID
    run_number = Column(Integer, nullable=True, index=True)   # Sequential number per org
    
    # Agent run content
    prompt = Column(Text, nullable=False)
    images = Column(JSON, default=list, nullable=False)  # List of image URLs/data
    
    # Source information
    source_type = Column(String(50), nullable=False, index=True)  # API, SLACK, GITHUB, etc.
    source_metadata = Column(JSON, default=dict, nullable=False)
    
    # Execution details
    agent_type = Column(String(100), default='default', nullable=False)
    agent_version = Column(String(50), nullable=True)
    
    # Timing information
    started_at = Column(String(255), nullable=True)  # ISO datetime string
    completed_at = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Execution status
    execution_status = Column(String(50), default='pending', nullable=False, index=True)
    # pending, running, completed, failed, cancelled, timeout
    
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    
    # Results and outputs
    result_summary = Column(Text, nullable=True)
    output_files = Column(JSON, default=list, nullable=False)
    artifacts = Column(JSON, default=dict, nullable=False)
    
    # Resource usage
    tokens_used = Column(Integer, default=0, nullable=False)
    api_calls_made = Column(Integer, default=0, nullable=False)
    memory_peak_mb = Column(Float, nullable=True)
    cpu_time_seconds = Column(Float, nullable=True)
    
    # Configuration
    timeout_seconds = Column(Integer, default=3600, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Flags
    is_test_run = Column(Boolean, default=False, nullable=False)
    is_debug_mode = Column(Boolean, default=False, nullable=False)
    is_priority = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", 
        back_populates="agent_runs"
    )
    
    created_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        back_populates="created_agent_runs",
        foreign_keys=[created_by_user_id]
    )
    
    repository: Mapped[Optional["Repository"]] = relationship(
        "Repository", 
        back_populates="agent_runs"
    )
    
    logs: Mapped[List["AgentRunLog"]] = relationship(
        "AgentRunLog", 
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="AgentRunLog.created_at"
    )
    
    states: Mapped[List["AgentRunState"]] = relationship(
        "AgentRunState", 
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="AgentRunState.created_at"
    )
    
    tasks: Mapped[List["AgentTask"]] = relationship(
        "AgentTask", 
        back_populates="agent_run",
        cascade="all, delete-orphan"
    )
    
    def is_running(self) -> bool:
        """Check if the agent run is currently running."""
        return self.execution_status in ['pending', 'running']
    
    def is_completed(self) -> bool:
        """Check if the agent run has completed (successfully or with error)."""
        return self.execution_status in ['completed', 'failed', 'cancelled', 'timeout']
    
    def is_successful(self) -> bool:
        """Check if the agent run completed successfully."""
        return self.execution_status == 'completed'
    
    def can_retry(self) -> bool:
        """Check if the agent run can be retried."""
        return (
            self.execution_status in ['failed', 'timeout'] and 
            self.retry_count < self.max_retries
        )
    
    def add_log(self, message: str, level: str = 'info', tool_name: str = None) -> "AgentRunLog":
        """Add a log entry to this agent run."""
        log = AgentRunLog(
            agent_run_id=self.id,
            message=message,
            level=level,
            tool_name=tool_name
        )
        self.logs.append(log)
        return log
    
    def update_state(self, state: str, data: dict = None) -> "AgentRunState":
        """Update the agent run state."""
        state_entry = AgentRunState(
            agent_run_id=self.id,
            state=state,
            state_data=data or {}
        )
        self.states.append(state_entry)
        return state_entry


class AgentRunLog(BaseModel):
    """
    Agent run log entries.
    
    Maps to API endpoint: GET /v1/alpha/organizations/{org_id}/agent/run/{agent_run_id}/logs
    UI Data Flow: Log viewer, debugging interface, execution timeline
    """
    
    agent_run_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("agent_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Log content
    message = Column(Text, nullable=False)
    level = Column(String(20), default='info', nullable=False, index=True)
    # debug, info, warning, error, critical
    
    # Tool information
    tool_name = Column(String(100), nullable=True, index=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    
    # Message type and context
    message_type = Column(String(50), nullable=True, index=True)
    thought = Column(Text, nullable=True)
    observation = Column(JSON, nullable=True)
    
    # Timing
    timestamp = Column(String(255), nullable=True)  # ISO datetime string
    duration_ms = Column(Integer, nullable=True)
    
    # Metadata
    sequence_number = Column(Integer, nullable=True, index=True)
    parent_log_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Relationships
    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun", 
        back_populates="logs"
    )


class AgentRunState(BaseModel):
    """
    Agent run state tracking.
    
    UI Data Flow: State machine visualization, progress tracking, debugging
    """
    
    agent_run_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("agent_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # State information
    state = Column(String(100), nullable=False, index=True)
    previous_state = Column(String(100), nullable=True)
    
    # State data
    state_data = Column(JSON, default=dict, nullable=False)
    transition_reason = Column(Text, nullable=True)
    
    # Timing
    entered_at = Column(String(255), nullable=True)  # ISO datetime string
    duration_ms = Column(Integer, nullable=True)
    
    # Relationships
    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun", 
        back_populates="states"
    )


class AgentTask(BaseModel, StatusMixin, VersionedMixin):
    """
    Individual tasks within an agent run.
    
    UI Data Flow: Task breakdown view, progress tracking, task management
    """
    
    agent_run_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("agent_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Task identification
    task_name = Column(String(255), nullable=False)
    task_type = Column(String(100), nullable=False, index=True)
    task_description = Column(Text, nullable=True)
    
    # Task hierarchy
    parent_task_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    depth_level = Column(Integer, default=0, nullable=False)
    
    # Task execution
    execution_status = Column(String(50), default='pending', nullable=False, index=True)
    # pending, running, completed, failed, skipped, blocked
    
    started_at = Column(String(255), nullable=True)
    completed_at = Column(String(255), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Task configuration
    task_config = Column(JSON, default=dict, nullable=False)
    input_data = Column(JSON, default=dict, nullable=False)
    output_data = Column(JSON, default=dict, nullable=False)
    
    # Dependencies
    depends_on = Column(JSON, default=list, nullable=False)  # List of task IDs
    blocks = Column(JSON, default=list, nullable=False)      # List of task IDs
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0, nullable=False)
    progress_message = Column(Text, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Relationships
    agent_run: Mapped["AgentRun"] = relationship(
        "AgentRun", 
        back_populates="tasks"
    )
    
    def is_ready_to_run(self) -> bool:
        """Check if task is ready to run (all dependencies completed)."""
        if not self.depends_on:
            return True
        
        # Check if all dependencies are completed
        # This would require a database query in practice
        return self.execution_status == 'pending'
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.execution_status == 'failed' and 
            self.retry_count < self.max_retries
        )
    
    def mark_completed(self, output_data: dict = None) -> None:
        """Mark task as completed."""
        self.execution_status = 'completed'
        self.progress_percentage = 100.0
        if output_data:
            self.output_data = output_data
        
        from datetime import datetime
        self.completed_at = datetime.utcnow().isoformat() + 'Z'
    
    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed."""
        self.execution_status = 'failed'
        self.error_message = error_message
        
        from datetime import datetime
        self.completed_at = datetime.utcnow().isoformat() + 'Z'
