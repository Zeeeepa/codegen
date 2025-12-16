"""Controller Dashboard for Workflow Management and Sandboxed Execution."""

import asyncio
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Workflow execution status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    RUNNING = "running"
    PAUSED = "paused"
    SCHEDULED = "scheduled"
    FAILED = "failed"
    COMPLETED = "completed"


class SandboxStatus(Enum):
    """Sandbox execution environment status."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    TERMINATING = "terminating"
    ERROR = "error"


@dataclass
class WorkflowConfig:
    """Workflow configuration and metadata."""
    id: str
    name: str
    description: str
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime
    enabled: bool = True
    parallel_execution: bool = False
    max_instances: int = 1
    retry_policy: dict = field(default_factory=dict)
    schedule: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class SandboxInstance:
    """Sandboxed execution instance."""
    id: str
    workflow_id: str
    status: SandboxStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    run_id: Optional[str] = None
    logs: list[dict] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    resource_usage: dict = field(default_factory=dict)


class ControllerDashboard:
    """Main Controller Dashboard for managing workflows and sandbox execution."""

    def __init__(self):
        """Initialize Controller Dashboard."""
        logger.info("Initializing Controller Dashboard", extra={"component": "controller_dashboard"})
        
        # Authentication
        self.token = get_current_token()
        self.org_id = resolve_org_id() if self.token else None
        
        # Workflow management
        self.workflows: dict[str, WorkflowConfig] = {}
        self.workflow_states: dict[str, dict] = {}
        
        # Sandbox management
        self.sandboxes: dict[str, SandboxInstance] = {}
        self.active_executions: set[str] = set()
        
        # UI state
        self.current_view = "workflows"  # workflows, sandboxes, monitoring, projects, prds
        self.selected_workflow_id: Optional[str] = None
        self.selected_sandbox_id: Optional[str] = None
        
        # Real-time monitoring
        self.monitoring_active = False
        self.metrics_history: dict[str, list] = {}
        
        # Background threads
        self._refresh_lock = threading.Lock()
        self._monitoring_thread: Optional[threading.Thread] = None
        
        logger.info("Controller Dashboard initialized", extra={
            "org_id": self.org_id,
            "authenticated": bool(self.token)
        })

    def toggle_workflow(self, workflow_id: str) -> bool:
        """Toggle workflow enabled/disabled state with persistence."""
        if workflow_id not in self.workflows:
            logger.error(f"Workflow not found: {workflow_id}")
            return False
        
        workflow = self.workflows[workflow_id]
        workflow.enabled = not workflow.enabled
        workflow.status = WorkflowStatus.ENABLED if workflow.enabled else WorkflowStatus.DISABLED
        workflow.updated_at = datetime.now()
        
        # Persist state
        self._persist_workflow_state(workflow)
        
        logger.info(f"Workflow toggled", extra={
            "workflow_id": workflow_id,
            "enabled": workflow.enabled,
            "status": workflow.status.value
        })
        
        return True

    def create_sandbox(self, workflow_id: str, config: Optional[dict] = None) -> Optional[str]:
        """Create isolated sandbox for workflow execution."""
        if workflow_id not in self.workflows:
            logger.error(f"Cannot create sandbox: workflow {workflow_id} not found")
            return None
        
        workflow = self.workflows[workflow_id]
        
        # Check max instances
        active_count = sum(1 for s in self.sandboxes.values() 
                          if s.workflow_id == workflow_id and 
                          s.status == SandboxStatus.RUNNING)
        
        if active_count >= workflow.max_instances:
            logger.warning(f"Max instances reached for workflow {workflow_id}")
            return None
        
        sandbox_id = f"sandbox-{workflow_id}-{int(time.time())}"
        sandbox = SandboxInstance(
            id=sandbox_id,
            workflow_id=workflow_id,
            status=SandboxStatus.INITIALIZING,
            created_at=datetime.now()
        )
        
        self.sandboxes[sandbox_id] = sandbox
        
        logger.info(f"Sandbox created", extra={
            "sandbox_id": sandbox_id,
            "workflow_id": workflow_id,
            "status": sandbox.status.value
        })
        
        return sandbox_id

    def execute_workflow_in_sandbox(self, workflow_id: str, params: Optional[dict] = None) -> Optional[str]:
        """Execute workflow in isolated sandbox with parallel support."""
        workflow = self.workflows.get(workflow_id)
        if not workflow or not workflow.enabled:
            logger.error(f"Workflow {workflow_id} not available for execution")
            return None
        
        # Create sandbox
        sandbox_id = self.create_sandbox(workflow_id)
        if not sandbox_id:
            return None
        
        sandbox = self.sandboxes[sandbox_id]
        
        try:
            # Update sandbox status
            sandbox.status = SandboxStatus.RUNNING
            sandbox.started_at = datetime.now()
            self.active_executions.add(sandbox_id)
            
            # Execute via API
            headers = {"Authorization": f"Bearer {self.token}"}
            payload = {
                "workflow_id": workflow_id,
                "sandbox_id": sandbox_id,
                "org_id": self.org_id,
                "params": params or {}
            }
            
            response = requests.post(
                f"{API_ENDPOINT}/workflows/execute",
                headers=headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                sandbox.run_id = result.get("run_id")
                
                logger.info(f"Workflow execution started", extra={
                    "workflow_id": workflow_id,
                    "sandbox_id": sandbox_id,
                    "run_id": sandbox.run_id
                })
                
                return sandbox.run_id
            else:
                sandbox.status = SandboxStatus.ERROR
                logger.error(f"Workflow execution failed: {response.status_code}")
                return None
                
        except Exception as e:
            sandbox.status = SandboxStatus.ERROR
            logger.error(f"Workflow execution exception", extra={"error": str(e)})
            return None

    def monitor_sandbox(self, sandbox_id: str) -> dict:
        """Monitor sandbox execution in real-time."""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return {}
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{API_ENDPOINT}/sandboxes/{sandbox_id}/status",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Update sandbox metrics
                sandbox.metrics = status_data.get("metrics", {})
                sandbox.resource_usage = status_data.get("resource_usage", {})
                
                # Update logs
                new_logs = status_data.get("logs", [])
                if new_logs:
                    sandbox.logs.extend(new_logs)
                
                # Check for completion
                if status_data.get("completed"):
                    sandbox.status = SandboxStatus.IDLE
                    sandbox.completed_at = datetime.now()
                    self.active_executions.discard(sandbox_id)
                
                return status_data
            
        except Exception as e:
            logger.error(f"Sandbox monitoring error", extra={
                "sandbox_id": sandbox_id,
                "error": str(e)
            })
        
        return {}

    def terminate_sandbox(self, sandbox_id: str) -> bool:
        """Terminate sandbox execution gracefully."""
        sandbox = self.sandboxes.get(sandbox_id)
        if not sandbox:
            return False
        
        sandbox.status = SandboxStatus.TERMINATING
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{API_ENDPOINT}/sandboxes/{sandbox_id}/terminate",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                sandbox.status = SandboxStatus.IDLE
                sandbox.completed_at = datetime.now()
                self.active_executions.discard(sandbox_id)
                
                logger.info(f"Sandbox terminated", extra={"sandbox_id": sandbox_id})
                return True
                
        except Exception as e:
            logger.error(f"Sandbox termination error", extra={
                "sandbox_id": sandbox_id,
                "error": str(e)
            })
        
        return False

    def get_parallel_executions(self, workflow_id: str) -> list[SandboxInstance]:
        """Get all parallel sandbox executions for a workflow."""
        return [
            sandbox for sandbox in self.sandboxes.values()
            if sandbox.workflow_id == workflow_id and
            sandbox.status == SandboxStatus.RUNNING
        ]

    def start_monitoring(self):
        """Start real-time monitoring of all active sandboxes."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        logger.info("Real-time monitoring started")

    def stop_monitoring(self):
        """Stop real-time monitoring."""
        self.monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=2)
        
        logger.info("Real-time monitoring stopped")

    def _monitoring_loop(self):
        """Background monitoring loop for active sandboxes."""
        while self.monitoring_active:
            try:
                active_sandbox_ids = list(self.active_executions)
                
                for sandbox_id in active_sandbox_ids:
                    status_data = self.monitor_sandbox(sandbox_id)
                    
                    # Store metrics history
                    if sandbox_id not in self.metrics_history:
                        self.metrics_history[sandbox_id] = []
                    
                    self.metrics_history[sandbox_id].append({
                        "timestamp": datetime.now().isoformat(),
                        "metrics": status_data.get("metrics", {}),
                        "resource_usage": status_data.get("resource_usage", {})
                    })
                
                time.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)

    def _persist_workflow_state(self, workflow: WorkflowConfig):
        """Persist workflow state to storage."""
        state_data = {
            "id": workflow.id,
            "enabled": workflow.enabled,
            "status": workflow.status.value,
            "updated_at": workflow.updated_at.isoformat()
        }
        
        self.workflow_states[workflow.id] = state_data
        
        # In production, this would write to database/file
        logger.debug(f"Workflow state persisted", extra={"workflow_id": workflow.id})

    def get_dashboard_summary(self) -> dict:
        """Get comprehensive dashboard summary."""
        return {
            "workflows": {
                "total": len(self.workflows),
                "enabled": sum(1 for w in self.workflows.values() if w.enabled),
                "disabled": sum(1 for w in self.workflows.values() if not w.enabled),
                "running": sum(1 for w in self.workflows.values() if w.status == WorkflowStatus.RUNNING)
            },
            "sandboxes": {
                "total": len(self.sandboxes),
                "active": len(self.active_executions),
                "idle": sum(1 for s in self.sandboxes.values() if s.status == SandboxStatus.IDLE),
                "error": sum(1 for s in self.sandboxes.values() if s.status == SandboxStatus.ERROR)
            },
            "monitoring": {
                "active": self.monitoring_active,
                "tracked_sandboxes": len(self.metrics_history)
            }
        }


def create_controller_dashboard() -> ControllerDashboard:
    """Factory function to create Controller Dashboard instance."""
    return ControllerDashboard()

