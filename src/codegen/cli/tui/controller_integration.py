"""Integration of Controller Dashboard into main TUI."""

from typing import Any

from codegen.cli.tui.controller_dashboard import ControllerDashboard, WorkflowConfig, WorkflowStatus
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ControllerTUIIntegration:
    """Integrates Controller Dashboard functionality into existing TUI."""

    def __init__(self, tui_instance):
        """Initialize controller integration."""
        self.tui = tui_instance
        self.controller = ControllerDashboard()
        
        # Add new tabs to existing TUI
        self._enhance_tui_tabs()
        
        # Initialize sample workflows
        self._initialize_sample_workflows()
        
        logger.info("Controller Dashboard integrated into TUI")

    def _enhance_tui_tabs(self):
        """Add controller dashboard tabs to TUI."""
        # Add new tabs: workflows, projects, prds, sandboxes, monitoring
        new_tabs = ["workflows", "projects", "prds", "sandboxes", "monitoring"]
        
        # Insert after existing tabs
        for tab in new_tabs:
            if tab not in self.tui.tabs:
                self.tui.tabs.append(tab)
        
        logger.info(f"Enhanced TUI with controller tabs: {new_tabs}")

    def _initialize_sample_workflows(self):
        """Initialize sample workflows for demonstration."""
        from datetime import datetime
        
        sample_workflows = [
            WorkflowConfig(
                id="wf-code-review",
                name="Automated Code Review",
                description="AI-powered code review with security and style checks",
                status=WorkflowStatus.ENABLED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                enabled=True,
                parallel_execution=True,
                max_instances=3,
                tags=["code-quality", "security", "automated"],
                schedule="0 */4 * * *"  # Every 4 hours
            ),
            WorkflowConfig(
                id="wf-pr-generator",
                name="PR Generator",
                description="Generate PRs from task descriptions with tests",
                status=WorkflowStatus.ENABLED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                enabled=True,
                parallel_execution=False,
                max_instances=1,
                tags=["pr", "automation", "testing"]
            ),
            WorkflowConfig(
                id="wf-doc-sync",
                name="Documentation Sync",
                description="Keep documentation in sync with codebase changes",
                status=WorkflowStatus.DISABLED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                enabled=False,
                parallel_execution=True,
                max_instances=2,
                tags=["documentation", "sync"],
                schedule="0 2 * * *"  # Daily at 2 AM
            ),
            WorkflowConfig(
                id="wf-test-generator",
                name="Test Suite Generator",
                description="Generate comprehensive test suites for new code",
                status=WorkflowStatus.ENABLED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                enabled=True,
                parallel_execution=True,
                max_instances=5,
                tags=["testing", "automation", "quality"]
            ),
            WorkflowConfig(
                id="wf-security-scan",
                name="Security Scanner",
                description="Automated security vulnerability scanning",
                status=WorkflowStatus.ENABLED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                enabled=True,
                parallel_execution=True,
                max_instances=2,
                tags=["security", "scanning", "compliance"],
                schedule="0 */6 * * *"  # Every 6 hours
            )
        ]
        
        for workflow in sample_workflows:
            self.controller.workflows[workflow.id] = workflow
        
        logger.info(f"Initialized {len(sample_workflows)} sample workflows")

    def render_workflows_tab(self) -> str:
        """Render workflows management tab."""
        output = []
        output.append("\n╔════════════════════════════════════════════════════════════════════════════╗")
        output.append("║                    🎯 WORKFLOW CONTROLLER DASHBOARD                         ║")
        output.append("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        summary = self.controller.get_dashboard_summary()
        
        # Summary section
        output.append("📊 SUMMARY")
        output.append("─" * 80)
        output.append(f"Total Workflows: {summary['workflows']['total']} | "
                     f"Enabled: {summary['workflows']['enabled']} | "
                     f"Disabled: {summary['workflows']['disabled']} | "
                     f"Running: {summary['workflows']['running']}")
        output.append(f"Active Sandboxes: {summary['sandboxes']['active']} | "
                     f"Total Sandboxes: {summary['sandboxes']['total']}")
        output.append("")
        
        # Workflows list
        output.append("📋 WORKFLOWS")
        output.append("─" * 80)
        
        if not self.controller.workflows:
            output.append("No workflows configured. Press [n] to create a new workflow.")
        else:
            for idx, (wf_id, workflow) in enumerate(self.controller.workflows.items()):
                status_icon = self._get_status_indicator(workflow)
                enabled_text = "✓ ENABLED" if workflow.enabled else "✗ DISABLED"
                
                output.append(f"{idx+1}. {status_icon} {workflow.name}")
                output.append(f"   {enabled_text} | Status: {workflow.status.value}")
                output.append(f"   {workflow.description}")
                
                if workflow.schedule:
                    output.append(f"   ⏰ Schedule: {workflow.schedule}")
                
                # Show active executions
                active_sandboxes = self.controller.get_parallel_executions(wf_id)
                if active_sandboxes:
                    output.append(f"   🔄 Active Executions: {len(active_sandboxes)}")
                
                output.append("")
        
        output.append("─" * 80)
        output.append("Commands: [Space] Toggle | [Enter] Details | [r] Run | [m] Monitor | [n] New | [q] Quit")
        
        return "\n".join(output)

    def render_sandboxes_tab(self) -> str:
        """Render sandboxes monitoring tab."""
        output = []
        output.append("\n╔════════════════════════════════════════════════════════════════════════════╗")
        output.append("║                    🔬 SANDBOX EXECUTION MONITOR                             ║")
        output.append("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        summary = self.controller.get_dashboard_summary()
        
        output.append("📊 SANDBOX STATUS")
        output.append("─" * 80)
        output.append(f"Active: {summary['sandboxes']['active']} | "
                     f"Idle: {summary['sandboxes']['idle']} | "
                     f"Error: {summary['sandboxes']['error']}")
        output.append("")
        
        if not self.controller.sandboxes:
            output.append("No sandboxes created yet.")
        else:
            output.append("🔍 ACTIVE SANDBOXES")
            output.append("─" * 80)
            
            for sandbox_id, sandbox in self.controller.sandboxes.items():
                if sandbox_id in self.controller.active_executions:
                    output.append(f"● {sandbox_id}")
                    output.append(f"  Workflow: {sandbox.workflow_id}")
                    output.append(f"  Status: {sandbox.status.value}")
                    output.append(f"  Started: {sandbox.started_at.strftime('%H:%M:%S') if sandbox.started_at else 'N/A'}")
                    
                    if sandbox.metrics:
                        output.append(f"  Metrics: {', '.join(f'{k}={v}' for k, v in list(sandbox.metrics.items())[:3])}")
                    
                    output.append("")
        
        output.append("─" * 80)
        output.append("Commands: [r] Refresh | [t] Terminate Selected | [Enter] Details | [q] Quit")
        
        return "\n".join(output)

    def render_monitoring_tab(self) -> str:
        """Render real-time monitoring tab."""
        output = []
        output.append("\n╔════════════════════════════════════════════════════════════════════════════╗")
        output.append("║                    📈 REAL-TIME MONITORING DASHBOARD                        ║")
        output.append("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        monitoring_status = "🟢 ACTIVE" if self.controller.monitoring_active else "🔴 INACTIVE"
        output.append(f"Monitoring Status: {monitoring_status}")
        output.append("")
        
        if not self.controller.metrics_history:
            output.append("No metrics collected yet. Start monitoring to see real-time data.")
        else:
            output.append("📊 METRICS HISTORY")
            output.append("─" * 80)
            
            for sandbox_id, history in list(self.controller.metrics_history.items())[:5]:
                output.append(f"\n{sandbox_id}:")
                if history:
                    latest = history[-1]
                    output.append(f"  Latest Update: {latest['timestamp']}")
                    if latest['metrics']:
                        output.append(f"  Metrics: {latest['metrics']}")
                    if latest['resource_usage']:
                        output.append(f"  Resources: {latest['resource_usage']}")
        
        output.append("")
        output.append("─" * 80)
        
        if self.controller.monitoring_active:
            output.append("Commands: [s] Stop Monitoring | [r] Refresh | [q] Quit")
        else:
            output.append("Commands: [s] Start Monitoring | [r] Refresh | [q] Quit")
        
        return "\n".join(output)

    def render_projects_tab(self) -> str:
        """Render projects management tab."""
        output = []
        output.append("\n╔════════════════════════════════════════════════════════════════════════════╗")
        output.append("║                    📁 PROJECTS MANAGEMENT                                   ║")
        output.append("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        output.append("🚧 Projects Management - Coming Soon")
        output.append("")
        output.append("This tab will allow you to:")
        output.append("  • View and manage all projects")
        output.append("  • Create new projects with templates")
        output.append("  • Configure project settings")
        output.append("  • Link projects to workflows")
        output.append("  • Track project status and metrics")
        output.append("")
        output.append("─" * 80)
        output.append("Commands: [n] New Project | [q] Quit")
        
        return "\n".join(output)

    def render_prds_tab(self) -> str:
        """Render PRDs management tab."""
        output = []
        output.append("\n╔════════════════════════════════════════════════════════════════════════════╗")
        output.append("║                    📄 PRODUCT REQUIREMENTS DOCUMENTS (PRDs)                 ║")
        output.append("╚════════════════════════════════════════════════════════════════════════════╝\n")
        
        output.append("🚧 PRD Management - Coming Soon")
        output.append("")
        output.append("This tab will allow you to:")
        output.append("  • Create and edit PRDs")
        output.append("  • Link PRDs to projects")
        output.append("  • Generate implementation tasks from PRDs")
        output.append("  • Track PRD version history")
        output.append("  • Collaborate on requirements")
        output.append("")
        output.append("─" * 80)
        output.append("Commands: [n] New PRD | [q] Quit")
        
        return "\n".join(output)

    def _get_status_indicator(self, workflow: WorkflowConfig) -> str:
        """Get colored status indicator for workflow."""
        if workflow.status == WorkflowStatus.RUNNING:
            return "🟢"
        elif workflow.status == WorkflowStatus.ENABLED:
            return "🟢"
        elif workflow.status == WorkflowStatus.DISABLED:
            return "🔴"
        elif workflow.status == WorkflowStatus.PAUSED:
            return "🟡"
        elif workflow.status == WorkflowStatus.FAILED:
            return "🔴"
        elif workflow.status == WorkflowStatus.COMPLETED:
            return "✅"
        else:
            return "⚪"

    def handle_workflows_tab_key(self, key: str) -> bool:
        """Handle keyboard input for workflows tab."""
        if key == ' ':  # Toggle workflow
            workflow_ids = list(self.controller.workflows.keys())
            if workflow_ids and hasattr(self.tui, 'selected_index'):
                idx = min(self.tui.selected_index, len(workflow_ids) - 1)
                self.controller.toggle_workflow(workflow_ids[idx])
                return True
        elif key == 'r':  # Run workflow
            workflow_ids = list(self.controller.workflows.keys())
            if workflow_ids and hasattr(self.tui, 'selected_index'):
                idx = min(self.tui.selected_index, len(workflow_ids) - 1)
                self.controller.execute_workflow_in_sandbox(workflow_ids[idx])
                return True
        elif key == 'm':  # Toggle monitoring
            if self.controller.monitoring_active:
                self.controller.stop_monitoring()
            else:
                self.controller.start_monitoring()
            return True
        
        return False

    def handle_sandboxes_tab_key(self, key: str) -> bool:
        """Handle keyboard input for sandboxes tab."""
        if key == 't':  # Terminate sandbox
            active_sandboxes = list(self.controller.active_executions)
            if active_sandboxes and hasattr(self.tui, 'selected_index'):
                idx = min(self.tui.selected_index, len(active_sandboxes) - 1)
                self.controller.terminate_sandbox(active_sandboxes[idx])
                return True
        
        return False

    def handle_monitoring_tab_key(self, key: str) -> bool:
        """Handle keyboard input for monitoring tab."""
        if key == 's':  # Toggle monitoring
            if self.controller.monitoring_active:
                self.controller.stop_monitoring()
            else:
                self.controller.start_monitoring()
            return True
        
        return False


def integrate_controller_dashboard(tui_instance) -> ControllerTUIIntegration:
    """Integrate controller dashboard into existing TUI instance."""
    return ControllerTUIIntegration(tui_instance)

