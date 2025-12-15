"""Workflow Management UI for Controller Dashboard."""

import sys
from datetime import datetime
from typing import Optional

from codegen.cli.tui.controller_dashboard import (
    ControllerDashboard,
    WorkflowConfig,
    WorkflowStatus,
    SandboxInstance,
    SandboxStatus
)
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class WorkflowManagementUI:
    """Interactive UI for workflow management."""

    def __init__(self, controller: ControllerDashboard):
        """Initialize Workflow Management UI."""
        self.controller = controller
        self.selected_index = 0
        self.show_action_menu = False
        self.action_menu_selection = 0
        self.running = True
        
        # View modes
        self.view_mode = "list"  # list, detail, monitoring, create
        self.current_workflow_id: Optional[str] = None
        
        logger.info("Workflow Management UI initialized")

    def render_workflow_list(self) -> str:
        """Render list of all workflows with status."""
        output = []
        output.append("\n" + "=" * 80)
        output.append("🎯 WORKFLOW MANAGEMENT DASHBOARD")
        output.append("=" * 80 + "\n")
        
        # Summary stats
        summary = self.controller.get_dashboard_summary()
        output.append(f"📊 Summary:")
        output.append(f"   Total Workflows: {summary['workflows']['total']}")
        output.append(f"   Enabled: {summary['workflows']['enabled']} | Disabled: {summary['workflows']['disabled']}")
        output.append(f"   Currently Running: {summary['workflows']['running']}")
        output.append(f"\n   Active Sandboxes: {summary['sandboxes']['active']} | Total: {summary['sandboxes']['total']}")
        output.append("")
        
        if not self.controller.workflows:
            output.append("   No workflows configured.")
            output.append("\n   Press 'n' to create a new workflow")
        else:
            output.append("Workflows:")
            output.append("-" * 80)
            
            for idx, (wf_id, workflow) in enumerate(self.controller.workflows.items()):
                # Highlight selected
                prefix = "➤ " if idx == self.selected_index else "  "
                
                # Status indicator
                status_icon = self._get_status_icon(workflow.status)
                enabled_icon = "✓" if workflow.enabled else "✗"
                
                # Format line
                line = f"{prefix}[{idx+1}] {status_icon} {workflow.name}"
                line += f"  [{enabled_icon}]"
                line += f"  (Updated: {workflow.updated_at.strftime('%H:%M:%S')})"
                
                output.append(line)
                
                # Show description for selected
                if idx == self.selected_index:
                    output.append(f"       📝 {workflow.description}")
                    if workflow.schedule:
                        output.append(f"       ⏰ Schedule: {workflow.schedule}")
                    if workflow.dependencies:
                        output.append(f"       🔗 Dependencies: {', '.join(workflow.dependencies)}")
        
        output.append("")
        output.append("-" * 80)
        output.append("Commands: [↑↓] Navigate | [Enter] Details | [Space] Toggle | [r] Run | [m] Monitor | [n] New | [q] Quit")
        
        return "\n".join(output)

    def render_workflow_detail(self, workflow_id: str) -> str:
        """Render detailed view of a specific workflow."""
        workflow = self.controller.workflows.get(workflow_id)
        if not workflow:
            return "Workflow not found"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append(f"📋 WORKFLOW DETAILS: {workflow.name}")
        output.append("=" * 80 + "\n")
        
        # Basic info
        output.append(f"ID: {workflow.id}")
        output.append(f"Status: {self._get_status_icon(workflow.status)} {workflow.status.value}")
        output.append(f"Enabled: {'✓ Yes' if workflow.enabled else '✗ No'}")
        output.append(f"Description: {workflow.description}")
        output.append(f"Created: {workflow.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"Updated: {workflow.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        
        # Configuration
        output.append("Configuration:")
        output.append(f"  • Parallel Execution: {'Enabled' if workflow.parallel_execution else 'Disabled'}")
        output.append(f"  • Max Instances: {workflow.max_instances}")
        output.append(f"  • Schedule: {workflow.schedule or 'Not scheduled'}")
        output.append(f"  • Tags: {', '.join(workflow.tags) if workflow.tags else 'None'}")
        output.append("")
        
        # Dependencies
        if workflow.dependencies:
            output.append("Dependencies:")
            for dep in workflow.dependencies:
                output.append(f"  • {dep}")
            output.append("")
        
        # Retry policy
        if workflow.retry_policy:
            output.append("Retry Policy:")
            for key, value in workflow.retry_policy.items():
                output.append(f"  • {key}: {value}")
            output.append("")
        
        # Active executions
        active_sandboxes = self.controller.get_parallel_executions(workflow_id)
        if active_sandboxes:
            output.append(f"Active Executions ({len(active_sandboxes)}):")
            for sandbox in active_sandboxes:
                output.append(f"  • Sandbox {sandbox.id}")
                output.append(f"    Status: {sandbox.status.value}")
                output.append(f"    Started: {sandbox.started_at.strftime('%H:%M:%S')}")
                if sandbox.run_id:
                    output.append(f"    Run ID: {sandbox.run_id}")
        else:
            output.append("No active executions")
        
        output.append("")
        output.append("-" * 80)
        output.append("Commands: [Space] Toggle | [r] Run | [t] Terminate All | [b] Back | [q] Quit")
        
        return "\n".join(output)

    def render_sandbox_monitoring(self, sandbox_id: str) -> str:
        """Render real-time sandbox monitoring view."""
        sandbox = self.controller.sandboxes.get(sandbox_id)
        if not sandbox:
            return "Sandbox not found"
        
        output = []
        output.append("\n" + "=" * 80)
        output.append(f"🔍 SANDBOX MONITORING: {sandbox.id}")
        output.append("=" * 80 + "\n")
        
        # Status
        output.append(f"Status: {self._get_sandbox_status_icon(sandbox.status)} {sandbox.status.value}")
        output.append(f"Workflow: {sandbox.workflow_id}")
        output.append(f"Run ID: {sandbox.run_id or 'N/A'}")
        output.append(f"Created: {sandbox.created_at.strftime('%H:%M:%S')}")
        if sandbox.started_at:
            output.append(f"Started: {sandbox.started_at.strftime('%H:%M:%S')}")
        if sandbox.completed_at:
            output.append(f"Completed: {sandbox.completed_at.strftime('%H:%M:%S')}")
            duration = (sandbox.completed_at - sandbox.started_at).total_seconds()
            output.append(f"Duration: {duration:.2f}s")
        output.append("")
        
        # Metrics
        if sandbox.metrics:
            output.append("Metrics:")
            for key, value in sandbox.metrics.items():
                output.append(f"  • {key}: {value}")
            output.append("")
        
        # Resource usage
        if sandbox.resource_usage:
            output.append("Resource Usage:")
            for key, value in sandbox.resource_usage.items():
                output.append(f"  • {key}: {value}")
            output.append("")
        
        # Recent logs
        if sandbox.logs:
            output.append("Recent Logs (last 10):")
            for log in sandbox.logs[-10:]:
                timestamp = log.get("timestamp", "")
                level = log.get("level", "INFO")
                message = log.get("message", "")
                output.append(f"  [{timestamp}] {level}: {message}")
        else:
            output.append("No logs available")
        
        output.append("")
        output.append("-" * 80)
        output.append("Commands: [r] Refresh | [t] Terminate | [b] Back | [q] Quit")
        
        return "\n".join(output)

    def render_create_workflow(self) -> str:
        """Render workflow creation form."""
        output = []
        output.append("\n" + "=" * 80)
        output.append("➕ CREATE NEW WORKFLOW")
        output.append("=" * 80 + "\n")
        
        output.append("Enter workflow details:")
        output.append("")
        output.append("Name: [Enter workflow name]")
        output.append("Description: [Enter description]")
        output.append("Schedule (optional): [cron format or 'manual']")
        output.append("Parallel Execution: [y/n]")
        output.append("Max Instances: [number]")
        output.append("")
        output.append("-" * 80)
        output.append("Commands: [Enter] Create | [Esc] Cancel")
        
        return "\n".join(output)

    def render_action_menu(self) -> str:
        """Render action menu for selected workflow."""
        actions = [
            "Toggle Enable/Disable",
            "Run Workflow",
            "Schedule Workflow",
            "View Details",
            "Monitor Executions",
            "Edit Configuration",
            "Delete Workflow",
            "Cancel"
        ]
        
        output = []
        output.append("\n" + "-" * 40)
        output.append("Actions:")
        for idx, action in enumerate(actions):
            prefix = "➤ " if idx == self.action_menu_selection else "  "
            output.append(f"{prefix}{action}")
        output.append("-" * 40)
        
        return "\n".join(output)

    def _get_status_icon(self, status: WorkflowStatus) -> str:
        """Get icon for workflow status."""
        icons = {
            WorkflowStatus.ENABLED: "✓",
            WorkflowStatus.DISABLED: "✗",
            WorkflowStatus.RUNNING: "▶",
            WorkflowStatus.PAUSED: "⏸",
            WorkflowStatus.SCHEDULED: "⏰",
            WorkflowStatus.FAILED: "✗",
            WorkflowStatus.COMPLETED: "✓"
        }
        return icons.get(status, "?")

    def _get_sandbox_status_icon(self, status: SandboxStatus) -> str:
        """Get icon for sandbox status."""
        icons = {
            SandboxStatus.IDLE: "○",
            SandboxStatus.INITIALIZING: "◐",
            SandboxStatus.RUNNING: "●",
            SandboxStatus.TERMINATING: "◑",
            SandboxStatus.ERROR: "✗"
        }
        return icons.get(status, "?")

    def handle_key(self, key: str) -> bool:
        """Handle keyboard input."""
        if key == 'q':
            self.running = False
            return False
        
        if self.view_mode == "list":
            return self._handle_list_view_key(key)
        elif self.view_mode == "detail":
            return self._handle_detail_view_key(key)
        elif self.view_mode == "monitoring":
            return self._handle_monitoring_view_key(key)
        
        return True

    def _handle_list_view_key(self, key: str) -> bool:
        """Handle keys in list view."""
        if key == 'up':
            self.selected_index = max(0, self.selected_index - 1)
        elif key == 'down':
            self.selected_index = min(len(self.controller.workflows) - 1, self.selected_index + 1)
        elif key == ' ':  # Space to toggle
            workflow_ids = list(self.controller.workflows.keys())
            if workflow_ids:
                self.controller.toggle_workflow(workflow_ids[self.selected_index])
        elif key == '\r':  # Enter for details
            workflow_ids = list(self.controller.workflows.keys())
            if workflow_ids:
                self.current_workflow_id = workflow_ids[self.selected_index]
                self.view_mode = "detail"
        elif key == 'r':  # Run workflow
            workflow_ids = list(self.controller.workflows.keys())
            if workflow_ids:
                workflow_id = workflow_ids[self.selected_index]
                self.controller.execute_workflow_in_sandbox(workflow_id)
        elif key == 'm':  # Start monitoring
            self.controller.start_monitoring()
        elif key == 'n':  # Create new workflow
            self.view_mode = "create"
        
        return True

    def _handle_detail_view_key(self, key: str) -> bool:
        """Handle keys in detail view."""
        if key == 'b':
            self.view_mode = "list"
            self.current_workflow_id = None
        elif key == ' ' and self.current_workflow_id:
            self.controller.toggle_workflow(self.current_workflow_id)
        elif key == 'r' and self.current_workflow_id:
            self.controller.execute_workflow_in_sandbox(self.current_workflow_id)
        elif key == 't' and self.current_workflow_id:
            # Terminate all active executions
            active_sandboxes = self.controller.get_parallel_executions(self.current_workflow_id)
            for sandbox in active_sandboxes:
                self.controller.terminate_sandbox(sandbox.id)
        
        return True

    def _handle_monitoring_view_key(self, key: str) -> bool:
        """Handle keys in monitoring view."""
        if key == 'b':
            self.view_mode = "list"
        elif key == 'r':
            # Refresh monitoring data
            pass
        
        return True

    def run(self):
        """Run the workflow management UI."""
        while self.running:
            # Clear screen
            sys.stdout.write("\033[2J\033[H")
            
            # Render appropriate view
            if self.view_mode == "list":
                output = self.render_workflow_list()
            elif self.view_mode == "detail" and self.current_workflow_id:
                output = self.render_workflow_detail(self.current_workflow_id)
            elif self.view_mode == "create":
                output = self.render_create_workflow()
            else:
                output = "Invalid view mode"
            
            print(output)
            
            # Get input (simplified for now)
            try:
                import time
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.running = False


def run_workflow_management_ui():
    """Entry point for workflow management UI."""
    controller = ControllerDashboard()
    ui = WorkflowManagementUI(controller)
    ui.run()

