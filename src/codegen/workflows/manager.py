"""
Codegen Workflow Manager

High-level manager for orchestrating validation workflows across the Codegen platform.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .server import CodegenWorkflowServer, create_workflow_server
from .validator import CodegenValidationWorkflow, ValidationConfig
from .events import ValidationStatus, ValidationSeverity
from ..database.events import get_event_emitter
from ..database.middleware import get_database_middleware

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPolicy:
    """Policy configuration for workflow execution."""
    
    # Trigger conditions
    trigger_on_agent_completion: bool = True
    trigger_on_pr_creation: bool = True
    trigger_on_pr_update: bool = True
    trigger_on_check_suite: bool = True
    
    # Workflow selection
    default_workflow_type: str = "validation"
    pr_workflow_type: str = "full-validation"
    update_workflow_type: str = "fast-validation"
    check_suite_workflow_type: str = "security-validation"
    
    # Execution limits
    max_concurrent_workflows: int = 10
    max_retries: int = 3
    timeout_minutes: int = 30
    
    # Quality gates
    required_validations: Set[str] = field(default_factory=lambda: {"code_quality", "security"})
    blocking_severities: Set[ValidationSeverity] = field(default_factory=lambda: {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL})
    
    # Notifications
    notify_on_failure: bool = True
    notify_on_success: bool = False
    notification_channels: List[str] = field(default_factory=list)


class WorkflowManager:
    """
    High-level manager for Codegen validation workflows.
    
    Provides:
    - Policy-based workflow orchestration
    - Resource management and throttling
    - Quality gate enforcement
    - Metrics collection and reporting
    - Integration with Codegen database and events
    """
    
    def __init__(
        self,
        policy: Optional[WorkflowPolicy] = None,
        server_config: Optional[Dict[str, Any]] = None,
    ):
        self.policy = policy or WorkflowPolicy()
        self.server_config = server_config or {}
        
        # Initialize workflow server
        self.server = create_workflow_server(
            enable_auto_triggers=False,  # We'll handle triggers manually
            **self.server_config
        )
        
        # Database integration
        self.db_middleware = get_database_middleware()
        self.event_emitter = get_event_emitter()
        
        # State tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_queue: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_duration": 0.0,
            "quality_gate_failures": 0,
        }
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Start background tasks
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _setup_event_handlers(self):
        """Setup event handlers for automatic workflow triggering."""
        
        if self.policy.trigger_on_agent_completion:
            self.event_emitter.on("agentrun.completed", self._handle_agent_run_completed)
        
        if self.policy.trigger_on_pr_creation:
            self.event_emitter.on("pullrequest.created", self._handle_pr_created)
        
        if self.policy.trigger_on_pr_update:
            self.event_emitter.on("pullrequest.updated", self._handle_pr_updated)
        
        if self.policy.trigger_on_check_suite:
            self.event_emitter.on("github.check_suite.requested", self._handle_check_suite_requested)
    
    def _start_background_tasks(self):
        """Start background tasks for workflow management."""
        
        # Workflow queue processor
        self._background_tasks.append(
            asyncio.create_task(self._process_workflow_queue())
        )
        
        # Metrics collector
        self._background_tasks.append(
            asyncio.create_task(self._collect_metrics())
        )
        
        # Cleanup task
        self._background_tasks.append(
            asyncio.create_task(self._cleanup_completed_workflows())
        )
    
    async def start_validation_workflow(
        self,
        agent_run_id: str,
        organization_id: str,
        workflow_type: Optional[str] = None,
        priority: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a validation workflow with policy enforcement.
        
        Args:
            agent_run_id: ID of the agent run to validate
            organization_id: Organization ID
            workflow_type: Type of workflow to run (uses policy default if None)
            priority: Workflow priority (1-10, higher is more important)
            **kwargs: Additional workflow parameters
            
        Returns:
            Dictionary with workflow execution details
        """
        workflow_type = workflow_type or self.policy.default_workflow_type
        
        # Check resource limits
        if len(self.active_workflows) >= self.policy.max_concurrent_workflows:
            # Queue the workflow
            workflow_request = {
                "agent_run_id": agent_run_id,
                "organization_id": organization_id,
                "workflow_type": workflow_type,
                "priority": priority,
                "requested_at": datetime.utcnow().isoformat(),
                "kwargs": kwargs,
            }
            
            # Insert in priority order
            self.workflow_queue.append(workflow_request)
            self.workflow_queue.sort(key=lambda x: x["priority"], reverse=True)
            
            logger.info(f"Workflow queued for agent run {agent_run_id} (queue size: {len(self.workflow_queue)})")
            
            return {
                "status": "queued",
                "agent_run_id": agent_run_id,
                "workflow_type": workflow_type,
                "queue_position": len(self.workflow_queue),
            }
        
        # Start workflow immediately
        return await self._execute_workflow(
            agent_run_id=agent_run_id,
            organization_id=organization_id,
            workflow_type=workflow_type,
            **kwargs
        )
    
    async def _execute_workflow(
        self,
        agent_run_id: str,
        organization_id: str,
        workflow_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a validation workflow."""
        try:
            # Start workflow via server
            result = await self.server.start_validation(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type=workflow_type,
                **kwargs
            )
            
            workflow_id = result["workflow_id"]
            
            # Track in active workflows
            self.active_workflows[workflow_id] = {
                **result,
                "started_by_manager": True,
                "retry_count": 0,
            }
            
            # Update metrics
            self.metrics["total_workflows"] += 1
            
            logger.info(f"Started workflow {workflow_id} for agent run {agent_run_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute workflow for agent run {agent_run_id}: {e}")
            raise
    
    async def _process_workflow_queue(self):
        """Process queued workflows when resources become available."""
        while True:
            try:
                # Check if we can process more workflows
                if (len(self.active_workflows) < self.policy.max_concurrent_workflows 
                    and self.workflow_queue):
                    
                    # Get highest priority workflow
                    workflow_request = self.workflow_queue.pop(0)
                    
                    logger.info(f"Processing queued workflow for agent run {workflow_request['agent_run_id']}")
                    
                    # Execute workflow
                    await self._execute_workflow(**workflow_request, **workflow_request["kwargs"])
                
                # Wait before checking again
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing workflow queue: {e}")
                await asyncio.sleep(10)
    
    async def _collect_metrics(self):
        """Collect and update workflow metrics."""
        while True:
            try:
                # Collect metrics from server
                server_metrics = self.server.get_workflow_metrics()
                
                # Update our metrics
                self.metrics.update({
                    "active_workflows": len(self.active_workflows),
                    "queued_workflows": len(self.workflow_queue),
                    "server_metrics": server_metrics,
                    "last_updated": datetime.utcnow().isoformat(),
                })
                
                # Emit metrics event
                self.event_emitter.emit(
                    event_type="validation.metrics.updated",
                    data=self.metrics,
                )
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_completed_workflows(self):
        """Clean up completed workflows from tracking."""
        while True:
            try:
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                workflows_to_remove = []
                
                for workflow_id, workflow_data in self.active_workflows.items():
                    # Get current status from server
                    current_status = self.server.get_workflow_status(workflow_id)
                    
                    if not current_status:
                        workflows_to_remove.append(workflow_id)
                        continue
                    
                    # Check if workflow is completed and old enough
                    if (current_status.get("status") in [ValidationStatus.PASSED.value, ValidationStatus.FAILED.value, ValidationStatus.CANCELLED.value]
                        and "completed_at" in current_status):
                        
                        completed_at = datetime.fromisoformat(current_status["completed_at"])
                        if completed_at < cutoff_time:
                            workflows_to_remove.append(workflow_id)
                
                # Remove old workflows
                for workflow_id in workflows_to_remove:
                    del self.active_workflows[workflow_id]
                    logger.debug(f"Cleaned up completed workflow: {workflow_id}")
                
                # Wait before next cleanup
                await asyncio.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Error during workflow cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def enforce_quality_gates(
        self,
        workflow_id: str,
        validation_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Enforce quality gates based on validation results.
        
        Args:
            workflow_id: ID of the workflow
            validation_results: List of validation results
            
        Returns:
            Quality gate enforcement result
        """
        try:
            # Check required validations
            completed_validations = {result.get("step_type") for result in validation_results}
            missing_validations = self.policy.required_validations - completed_validations
            
            if missing_validations:
                return {
                    "passed": False,
                    "reason": f"Missing required validations: {missing_validations}",
                    "missing_validations": list(missing_validations),
                }
            
            # Check for blocking severities
            blocking_issues = []
            for result in validation_results:
                severity = result.get("severity")
                if severity in [s.value for s in self.policy.blocking_severities]:
                    if result.get("status") == ValidationStatus.FAILED.value:
                        blocking_issues.append({
                            "step": result.get("step_name"),
                            "severity": severity,
                            "message": result.get("message"),
                        })
            
            if blocking_issues:
                self.metrics["quality_gate_failures"] += 1
                
                return {
                    "passed": False,
                    "reason": f"Found {len(blocking_issues)} blocking issues",
                    "blocking_issues": blocking_issues,
                }
            
            # Quality gates passed
            return {
                "passed": True,
                "reason": "All quality gates passed",
                "validations_completed": list(completed_validations),
            }
            
        except Exception as e:
            logger.error(f"Error enforcing quality gates for workflow {workflow_id}: {e}")
            return {
                "passed": False,
                "reason": f"Quality gate enforcement failed: {e}",
                "error": str(e),
            }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive workflow status including manager metadata."""
        server_status = self.server.get_workflow_status(workflow_id)
        manager_status = self.active_workflows.get(workflow_id, {})
        
        if not server_status:
            return None
        
        return {
            **server_status,
            **manager_status,
            "managed": True,
        }
    
    def get_organization_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get workflow metrics for a specific organization."""
        org_workflows = [
            w for w in self.active_workflows.values()
            if w.get("organization_id") == organization_id
        ]
        
        server_metrics = self.server.get_workflow_metrics(organization_id)
        
        return {
            **server_metrics,
            "active_workflows": len(org_workflows),
            "queued_workflows": len([
                w for w in self.workflow_queue
                if w.get("organization_id") == organization_id
            ]),
            "organization_id": organization_id,
        }
    
    def update_policy(self, policy_updates: Dict[str, Any]) -> None:
        """Update workflow policy configuration."""
        for key, value in policy_updates.items():
            if hasattr(self.policy, key):
                setattr(self.policy, key, value)
                logger.info(f"Updated policy {key} to {value}")
            else:
                logger.warning(f"Unknown policy key: {key}")
        
        # Emit policy update event
        self.event_emitter.emit(
            event_type="validation.policy.updated",
            data=policy_updates,
        )
    
    async def shutdown(self):
        """Shutdown the workflow manager gracefully."""
        logger.info("Shutting down workflow manager...")
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cancel active workflows
        for workflow_id in list(self.active_workflows.keys()):
            self.server.cancel_workflow(workflow_id)
        
        logger.info("Workflow manager shutdown complete")
    
    # Event handlers
    
    async def _handle_agent_run_completed(self, event):
        """Handle agent run completion event."""
        try:
            agent_run_id = event.data.get("id")
            organization_id = event.organization_id
            
            if not agent_run_id or not organization_id:
                return
            
            logger.info(f"Manager triggering validation for completed agent run: {agent_run_id}")
            
            await self.start_validation_workflow(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type=self.policy.default_workflow_type,
                triggered_by="agent_run_completion",
                priority=7,  # High priority for completed runs
            )
            
        except Exception as e:
            logger.error(f"Failed to handle agent run completed event: {e}")
    
    async def _handle_pr_created(self, event):
        """Handle PR creation event."""
        try:
            pr_data = event.data
            organization_id = event.organization_id
            
            agent_run_id = pr_data.get("agent_run_id")
            if not agent_run_id:
                return
            
            logger.info(f"Manager triggering validation for PR creation: {pr_data.get('number')}")
            
            await self.start_validation_workflow(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type=self.policy.pr_workflow_type,
                pr_number=pr_data.get("number"),
                commit_sha=pr_data.get("head_sha"),
                triggered_by="pr_creation",
                priority=8,  # Higher priority for PR creation
            )
            
        except Exception as e:
            logger.error(f"Failed to handle PR created event: {e}")
    
    async def _handle_pr_updated(self, event):
        """Handle PR update event."""
        try:
            pr_data = event.data
            organization_id = event.organization_id
            
            if pr_data.get("action") not in ["synchronize", "opened"]:
                return
            
            agent_run_id = pr_data.get("agent_run_id")
            if not agent_run_id:
                return
            
            logger.info(f"Manager triggering validation for PR update: {pr_data.get('number')}")
            
            await self.start_validation_workflow(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type=self.policy.update_workflow_type,
                pr_number=pr_data.get("number"),
                commit_sha=pr_data.get("head_sha"),
                triggered_by="pr_update",
                priority=6,  # Medium priority for updates
            )
            
        except Exception as e:
            logger.error(f"Failed to handle PR updated event: {e}")
    
    async def _handle_check_suite_requested(self, event):
        """Handle GitHub check suite requested event."""
        try:
            check_suite_data = event.data
            organization_id = event.organization_id
            
            commit_sha = check_suite_data.get("head_sha")
            if not commit_sha:
                return
            
            # Find associated agent run
            from ..database.models.agents import AgentRun
            agent_runs = self.db_middleware.list_with_filters(
                AgentRun,
                filters={"organization_id": organization_id},
                limit=1
            )
            
            if not agent_runs:
                return
            
            agent_run = agent_runs[0]
            
            logger.info(f"Manager triggering validation for check suite: {check_suite_data.get('id')}")
            
            await self.start_validation_workflow(
                agent_run_id=str(agent_run.id),
                organization_id=organization_id,
                workflow_type=self.policy.check_suite_workflow_type,
                commit_sha=commit_sha,
                check_suite_id=check_suite_data.get("id"),
                triggered_by="check_suite_request",
                priority=9,  # Highest priority for check suites
            )
            
        except Exception as e:
            logger.error(f"Failed to handle check suite requested event: {e}")


# Factory function for easy manager creation
def create_workflow_manager(
    policy: Optional[WorkflowPolicy] = None,
    server_config: Optional[Dict[str, Any]] = None,
) -> WorkflowManager:
    """
    Create a Codegen workflow manager with policy-based orchestration.
    
    Args:
        policy: Workflow policy configuration
        server_config: Server configuration options
        
    Returns:
        Configured WorkflowManager instance
    """
    return WorkflowManager(policy=policy, server_config=server_config)
