"""
Codegen Workflow Server

HTTP server for serving validation workflows as web services.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import workflows-py components
from workflows.server import WorkflowServer
from workflows import Context

from .validator import CodegenValidationWorkflow, ValidationConfig
from .events import ValidationStatus
from ..database.events import get_event_emitter
from ..database.middleware import get_database_middleware

logger = logging.getLogger(__name__)


class CodegenWorkflowServer:
    """
    HTTP server for Codegen validation workflows.
    
    Provides REST API endpoints for:
    - Starting validation workflows
    - Checking validation status
    - Streaming validation events
    - Managing workflow configurations
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        enable_cors: bool = True,
        middleware: Optional[List] = None,
    ):
        self.host = host
        self.port = port
        self.enable_cors = enable_cors
        self.middleware = middleware or []
        
        # Initialize workflow server
        self.server = WorkflowServer(middleware=self.middleware)
        self._setup_workflows()
        
        # Database integration
        self.db_middleware = get_database_middleware()
        self.event_emitter = get_event_emitter()
        
        # Active workflows tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    def _setup_workflows(self):
        """Setup validation workflows."""
        if not self.server:
            return
        
        # Default validation workflow
        default_workflow = CodegenValidationWorkflow()
        self.server.add_workflow("validation", default_workflow)
        
        # Custom validation workflows for different scenarios
        
        # Fast validation (code quality only)
        fast_config = ValidationConfig(
            enable_security_scan=False,
            enable_deployment_validation=False,
            parallel_execution=True,
            timeout_minutes=5,
        )
        fast_workflow = CodegenValidationWorkflow(fast_config)
        self.server.add_workflow("fast-validation", fast_workflow)
        
        # Security-focused validation
        security_config = ValidationConfig(
            enable_code_quality=False,
            enable_deployment_validation=False,
            parallel_execution=True,
            timeout_minutes=15,
        )
        security_workflow = CodegenValidationWorkflow(security_config)
        self.server.add_workflow("security-validation", security_workflow)
        
        # Full validation with deployment
        full_config = ValidationConfig(
            enable_code_quality=True,
            enable_security_scan=True,
            enable_deployment_validation=True,
            parallel_execution=True,
            timeout_minutes=30,
            notification_channels=["slack", "email"],
        )
        full_workflow = CodegenValidationWorkflow(full_config)
        self.server.add_workflow("full-validation", full_workflow)
    
    async def start_validation(
        self,
        agent_run_id: str,
        organization_id: str,
        workflow_type: str = "validation",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a validation workflow for an agent run.
        
        Args:
            agent_run_id: ID of the agent run to validate
            organization_id: Organization ID
            workflow_type: Type of validation workflow to run
            **kwargs: Additional parameters for the workflow
            
        Returns:
            Dictionary with workflow execution details
        """
        try:
            # Get agent run details from database
            from ..database.models.agents import AgentRun
            agent_run = self.db_middleware.get_by_id(AgentRun, agent_run_id)
            
            if not agent_run:
                raise ValueError(f"Agent run {agent_run_id} not found")
            
            # Prepare workflow input
            workflow_input = {
                "agent_run_id": agent_run_id,
                "organization_id": organization_id,
                "repository_id": str(agent_run.repository_id) if agent_run.repository_id else None,
                "pr_number": kwargs.get("pr_number"),
                "commit_sha": kwargs.get("commit_sha"),
                "agent_type": agent_run.agent_type,
                "prompt": agent_run.prompt,
                "source_type": agent_run.source_type,
                "execution_status": agent_run.execution_status,
                "result_summary": agent_run.result_summary,
                "output_files": agent_run.output_files or [],
                "tokens_used": agent_run.tokens_used,
                "api_calls_made": agent_run.api_calls_made,
                **kwargs
            }
            
            # Start workflow execution
            workflow_id = f"validation-{agent_run_id}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Track active workflow
            self.active_workflows[workflow_id] = {
                "agent_run_id": agent_run_id,
                "organization_id": organization_id,
                "workflow_type": workflow_type,
                "status": ValidationStatus.RUNNING.value,
                "started_at": datetime.utcnow().isoformat(),
                "input": workflow_input,
            }
            
            # Emit workflow started event
            self.event_emitter.emit(
                event_type="validation.workflow.started",
                data={
                    "workflow_id": workflow_id,
                    "agent_run_id": agent_run_id,
                    "organization_id": organization_id,
                    "workflow_type": workflow_type,
                },
                organization_id=organization_id,
            )
            
            # Start workflow asynchronously
            asyncio.create_task(
                self._execute_workflow(workflow_id, workflow_type, workflow_input)
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "started",
                "agent_run_id": agent_run_id,
                "workflow_type": workflow_type,
                "started_at": self.active_workflows[workflow_id]["started_at"],
            }
            
        except Exception as e:
            logger.error(f"Failed to start validation workflow: {e}")
            raise
    
    async def _execute_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        workflow_input: Dict[str, Any]
    ):
        """Execute a validation workflow."""
        try:
            # Get workflow
            workflow = self.server._workflows.get(workflow_type)
            if not workflow:
                raise ValueError(f"Workflow type '{workflow_type}' not found")
            
            # Create context
            ctx = Context(workflow)
            
            # Run workflow
            result = await workflow.run(ctx=ctx, **workflow_input)
            
            # Update workflow status
            self.active_workflows[workflow_id].update({
                "status": ValidationStatus.PASSED.value if result.get("status") == "passed" else ValidationStatus.FAILED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result,
            })
            
            # Emit workflow completed event
            self.event_emitter.emit(
                event_type="validation.workflow.completed",
                data={
                    "workflow_id": workflow_id,
                    "agent_run_id": workflow_input["agent_run_id"],
                    "organization_id": workflow_input["organization_id"],
                    "status": self.active_workflows[workflow_id]["status"],
                    "result": result,
                },
                organization_id=workflow_input["organization_id"],
            )
            
            logger.info(f"Workflow {workflow_id} completed with status: {self.active_workflows[workflow_id]['status']}")
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {e}")
            
            # Update workflow status
            self.active_workflows[workflow_id].update({
                "status": ValidationStatus.FAILED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "error": str(e),
            })
            
            # Emit workflow failed event
            self.event_emitter.emit(
                event_type="validation.workflow.failed",
                data={
                    "workflow_id": workflow_id,
                    "agent_run_id": workflow_input["agent_run_id"],
                    "organization_id": workflow_input["organization_id"],
                    "error": str(e),
                },
                organization_id=workflow_input["organization_id"],
            )
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a validation workflow."""
        return self.active_workflows.get(workflow_id)
    
    def list_active_workflows(self, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active validation workflows."""
        workflows = list(self.active_workflows.values())
        
        if organization_id:
            workflows = [w for w in workflows if w["organization_id"] == organization_id]
        
        return workflows
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running validation workflow."""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        
        if workflow["status"] not in [ValidationStatus.RUNNING.value, ValidationStatus.PENDING.value]:
            return False
        
        # Update status
        workflow.update({
            "status": ValidationStatus.CANCELLED.value,
            "cancelled_at": datetime.utcnow().isoformat(),
        })
        
        # Emit cancellation event
        self.event_emitter.emit(
            event_type="validation.workflow.cancelled",
            data={
                "workflow_id": workflow_id,
                "agent_run_id": workflow["agent_run_id"],
                "organization_id": workflow["organization_id"],
            },
            organization_id=workflow["organization_id"],
        )
        
        logger.info(f"Workflow {workflow_id} cancelled")
        return True
    
    async def serve(self) -> None:
        """Start the workflow server."""
        logger.info(f"Starting Codegen Workflow Server at http://{self.host}:{self.port}")
        
        await self.server.serve(
            host=self.host,
            port=self.port,
            uvicorn_config={
                "log_level": "info",
                "access_log": True,
            }
        )
    
    def add_custom_workflow(self, name: str, workflow: CodegenValidationWorkflow) -> None:
        """Add a custom validation workflow."""
        if self.server:
            self.server.add_workflow(name, workflow)
    
    def get_workflow_metrics(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Get validation workflow metrics."""
        workflows = self.list_active_workflows(organization_id)
        
        total_workflows = len(workflows)
        running_workflows = len([w for w in workflows if w["status"] == ValidationStatus.RUNNING.value])
        completed_workflows = len([w for w in workflows if w["status"] in [ValidationStatus.PASSED.value, ValidationStatus.FAILED.value]])
        failed_workflows = len([w for w in workflows if w["status"] == ValidationStatus.FAILED.value])
        
        success_rate = (completed_workflows - failed_workflows) / completed_workflows * 100 if completed_workflows > 0 else 0
        
        return {
            "total_workflows": total_workflows,
            "running_workflows": running_workflows,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "success_rate": round(success_rate, 2),
            "organization_id": organization_id,
        }


# Integration with Codegen database events
class WorkflowEventHandler:
    """Handle database events and trigger validation workflows."""
    
    def __init__(self, workflow_server: CodegenWorkflowServer):
        self.workflow_server = workflow_server
        self.event_emitter = get_event_emitter()
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register event handlers for automatic workflow triggering."""
        
        # Trigger validation when agent run completes
        self.event_emitter.on("agentrun.completed", self._handle_agent_run_completed)
        
        # Trigger validation when PR is created/updated
        self.event_emitter.on("pullrequest.created", self._handle_pr_created)
        self.event_emitter.on("pullrequest.updated", self._handle_pr_updated)
        
        # Handle GitHub check suite events
        self.event_emitter.on("github.check_suite.requested", self._handle_check_suite_requested)
    
    async def _handle_agent_run_completed(self, event):
        """Handle agent run completion event."""
        try:
            agent_run_id = event.data.get("id")
            organization_id = event.organization_id
            
            if not agent_run_id or not organization_id:
                return
            
            logger.info(f"Triggering validation workflow for completed agent run: {agent_run_id}")
            
            # Start validation workflow
            await self.workflow_server.start_validation(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type="validation",
                triggered_by="agent_run_completion",
            )
            
        except Exception as e:
            logger.error(f"Failed to handle agent run completed event: {e}")
    
    async def _handle_pr_created(self, event):
        """Handle PR creation event."""
        try:
            pr_data = event.data
            organization_id = event.organization_id
            
            # Check if this PR was created by an agent run
            agent_run_id = pr_data.get("agent_run_id")
            if not agent_run_id:
                return
            
            logger.info(f"Triggering validation workflow for PR creation: {pr_data.get('number')}")
            
            # Start validation workflow
            await self.workflow_server.start_validation(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type="full-validation",
                pr_number=pr_data.get("number"),
                commit_sha=pr_data.get("head_sha"),
                triggered_by="pr_creation",
            )
            
        except Exception as e:
            logger.error(f"Failed to handle PR created event: {e}")
    
    async def _handle_pr_updated(self, event):
        """Handle PR update event."""
        try:
            pr_data = event.data
            organization_id = event.organization_id
            
            # Check if this is a significant update that requires validation
            if pr_data.get("action") not in ["synchronize", "opened"]:
                return
            
            agent_run_id = pr_data.get("agent_run_id")
            if not agent_run_id:
                return
            
            logger.info(f"Triggering validation workflow for PR update: {pr_data.get('number')}")
            
            # Start fast validation for PR updates
            await self.workflow_server.start_validation(
                agent_run_id=agent_run_id,
                organization_id=organization_id,
                workflow_type="fast-validation",
                pr_number=pr_data.get("number"),
                commit_sha=pr_data.get("head_sha"),
                triggered_by="pr_update",
            )
            
        except Exception as e:
            logger.error(f"Failed to handle PR updated event: {e}")
    
    async def _handle_check_suite_requested(self, event):
        """Handle GitHub check suite requested event."""
        try:
            check_suite_data = event.data
            organization_id = event.organization_id
            
            # Find associated agent run
            commit_sha = check_suite_data.get("head_sha")
            if not commit_sha:
                return
            
            # Query database for agent run with this commit
            from ..database.models.agents import AgentRun
            agent_runs = self.workflow_server.db_middleware.list_with_filters(
                AgentRun,
                filters={"organization_id": organization_id},
                limit=1
            )
            
            if not agent_runs:
                return
            
            agent_run = agent_runs[0]
            
            logger.info(f"Triggering validation workflow for check suite: {check_suite_data.get('id')}")
            
            # Start security-focused validation for check suites
            await self.workflow_server.start_validation(
                agent_run_id=str(agent_run.id),
                organization_id=organization_id,
                workflow_type="security-validation",
                commit_sha=commit_sha,
                check_suite_id=check_suite_data.get("id"),
                triggered_by="check_suite_request",
            )
            
        except Exception as e:
            logger.error(f"Failed to handle check suite requested event: {e}")


# Factory function for easy server creation
def create_workflow_server(
    host: str = "localhost",
    port: int = 8080,
    enable_auto_triggers: bool = True,
    **kwargs
) -> CodegenWorkflowServer:
    """
    Create a Codegen workflow server with optional automatic triggers.
    
    Args:
        host: Server host
        port: Server port
        enable_auto_triggers: Whether to enable automatic workflow triggers
        **kwargs: Additional server configuration
        
    Returns:
        Configured CodegenWorkflowServer instance
    """
    server = CodegenWorkflowServer(host=host, port=port, **kwargs)
    
    if enable_auto_triggers:
        # Set up automatic workflow triggers
        WorkflowEventHandler(server)
    
    return server
