"""
Main Codegen Dashboard application with AI-powered chat interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from .config import get_config
from .models import DashboardState, ChatSession, ChatMessage, ChatMessageType
from .ui.main_window import MainWindow
from .services.codegen_client import CodegenClient
from .services.chat_service import ChatService
from .services.state_manager import StateManager
from .services.notification_service import NotificationService
from .storage.database_manager import DatabaseManager
from .utils.logger import setup_logger


class CodegenDashboard:
    """
    Main Codegen Dashboard application with comprehensive AI integration.
    
    Features:
    - Real-time agent run monitoring
    - AI-powered chat interface with RepoMaster + Z.AI
    - Project visualization with graph-sitter analysis
    - PRD validation and automated follow-up agents
    - Validation gates and workflow orchestration
    """
    
    def __init__(self):
        """Initialize the Codegen Dashboard."""
        self.config = get_config()
        self.logger = setup_logger(__name__)
        
        # Initialize core services
        self.database_manager = DatabaseManager(self.config)
        self.state_manager = StateManager()
        self.notification_service = NotificationService(self.config)
        self.codegen_client = CodegenClient(self.config)
        self.chat_service = ChatService(self.config, self.codegen_client)
        
        # Initialize UI
        self.root = None
        self.main_window = None
        
        # Runtime state
        self.running = False
        self.background_tasks = []
        self.current_chat_session: Optional[ChatSession] = None
        
        self.logger.info("Codegen Dashboard initialized")
    
    def start(self):
        """Start the dashboard application."""
        try:
            self.logger.info("Starting Codegen Dashboard...")
            
            # Validate configuration
            config_issues = self.config.validate()
            if config_issues:
                self.logger.warning(f"Configuration issues found: {config_issues}")
                # Show configuration dialog if critical issues exist
                if any("API key" in issue for issue in config_issues):
                    self._show_config_dialog()
            
            # Initialize database
            self.database_manager.initialize()
            
            # Create main window
            self.root = tk.Tk()
            self.root.title("Codegen Dashboard")
            self.root.geometry(f"{self.config.ui.window_width}x{self.config.ui.window_height}")
            
            # Set window icon and properties
            self.root.resizable(True, True)
            self.root.minsize(800, 600)
            
            # Apply theme
            self._apply_theme()
            
            # Create main window
            self.main_window = MainWindow(
                self.root,
                self.config,
                self.state_manager,
                self.codegen_client,
                self.chat_service,
                self.notification_service,
                self.database_manager
            )
            
            # Set up event handlers
            self._setup_event_handlers()
            
            # Start background services
            self._start_background_services()
            
            # Load initial data
            self._load_initial_data()
            
            self.running = True
            self.logger.info("Dashboard started successfully")
            
            # Start the main event loop
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"Failed to start dashboard: {e}")
            messagebox.showerror("Startup Error", f"Failed to start dashboard: {e}")
            raise
    
    def stop(self):
        """Stop the dashboard application."""
        try:
            self.logger.info("Stopping Codegen Dashboard...")
            self.running = False
            
            # Stop background services
            self._stop_background_services()
            
            # Save current state
            self._save_current_state()
            
            # Close database connections
            if self.database_manager:
                self.database_manager.close()
            
            # Destroy UI
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            self.logger.info("Dashboard stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping dashboard: {e}")
    
    def _apply_theme(self):
        """Apply the selected theme to the application."""
        style = ttk.Style()
        
        if self.config.ui.theme == "dark":
            # Dark theme configuration
            style.theme_use("clam")
            style.configure(".", background="#2b2b2b", foreground="#ffffff")
            style.configure("TLabel", background="#2b2b2b", foreground="#ffffff")
            style.configure("TButton", background="#404040", foreground="#ffffff")
            style.configure("TEntry", background="#404040", foreground="#ffffff")
            style.configure("TText", background="#404040", foreground="#ffffff")
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TNotebook", background="#2b2b2b")
            style.configure("TNotebook.Tab", background="#404040", foreground="#ffffff")
            
            # Configure root window
            self.root.configure(bg="#2b2b2b")
        else:
            # Light theme (default)
            style.theme_use("default")
    
    def _setup_event_handlers(self):
        """Set up event handlers for the application."""
        # Window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # State change events
        self.state_manager.subscribe("agent_run_updated", self._on_agent_run_updated)
        self.state_manager.subscribe("project_updated", self._on_project_updated)
        self.state_manager.subscribe("notification_created", self._on_notification_created)
        
        # Chat events
        self.chat_service.on_message_received = self._on_chat_message_received
        self.chat_service.on_agent_run_created = self._on_agent_run_created_from_chat
        self.chat_service.on_prd_validation_completed = self._on_prd_validation_completed
    
    def _start_background_services(self):
        """Start background monitoring and polling services."""
        if self.config.monitoring.auto_refresh:
            # Start agent run monitoring
            if self.config.monitoring.poll_running_agents:
                self._start_agent_monitoring()
            
            # Start PR monitoring
            if self.config.monitoring.poll_prs:
                self._start_pr_monitoring()
            
            # Start general state refresh
            self._start_state_refresh()
    
    def _stop_background_services(self):
        """Stop all background services."""
        for task in self.background_tasks:
            if hasattr(task, 'cancel'):
                task.cancel()
        self.background_tasks.clear()
    
    def _start_agent_monitoring(self):
        """Start background agent run monitoring."""
        def monitor_agents():
            while self.running:
                try:
                    # Fetch current agent runs
                    runs = self.codegen_client.get_agent_runs()
                    
                    # Update state
                    for run in runs:
                        self.state_manager.update_agent_run(run)
                    
                    # Check for completed runs that need PRD validation
                    self._check_prd_validation_needed()
                    
                except Exception as e:
                    self.logger.error(f"Error monitoring agents: {e}")
                
                # Wait for next poll
                import time
                time.sleep(self.config.monitoring.agent_poll_interval)
        
        thread = threading.Thread(target=monitor_agents, daemon=True)
        thread.start()
        self.background_tasks.append(thread)
    
    def _start_pr_monitoring(self):
        """Start background PR monitoring."""
        def monitor_prs():
            while self.running:
                try:
                    # Get starred projects
                    starred_projects = self.state_manager.get_starred_projects()
                    
                    for project in starred_projects:
                        # Fetch PRs for project
                        prs = self.codegen_client.get_project_prs(project.id)
                        
                        # Check for new or updated PRs
                        for pr in prs:
                            if self._is_pr_new_or_updated(pr):
                                self.state_manager.update_pr(pr)
                                
                                # Trigger validation gates if configured
                                self._trigger_validation_gates(project, pr)
                    
                except Exception as e:
                    self.logger.error(f"Error monitoring PRs: {e}")
                
                # Wait for next poll
                import time
                time.sleep(self.config.monitoring.pr_poll_interval)
        
        thread = threading.Thread(target=monitor_prs, daemon=True)
        thread.start()
        self.background_tasks.append(thread)
    
    def _start_state_refresh(self):
        """Start general state refresh."""
        def refresh_state():
            while self.running:
                try:
                    # Update dashboard state
                    state = self._calculate_dashboard_state()
                    self.state_manager.update_dashboard_state(state)
                    
                    # Refresh UI if needed
                    if self.main_window:
                        self.main_window.refresh_state()
                    
                except Exception as e:
                    self.logger.error(f"Error refreshing state: {e}")
                
                # Wait for next refresh
                import time
                time.sleep(self.config.ui.refresh_interval)
        
        thread = threading.Thread(target=refresh_state, daemon=True)
        thread.start()
        self.background_tasks.append(thread)
    
    def _load_initial_data(self):
        """Load initial data for the dashboard."""
        try:
            # Load agent runs
            runs = self.codegen_client.get_agent_runs()
            for run in runs:
                self.state_manager.add_agent_run(run)
            
            # Load projects
            projects = self.codegen_client.get_projects()
            for project in projects:
                self.state_manager.add_project(project)
            
            # Load chat sessions
            chat_sessions = self.database_manager.get_chat_sessions()
            for session in chat_sessions:
                self.state_manager.add_chat_session(session)
            
            # Create default chat session if none exist
            if not chat_sessions:
                self._create_default_chat_session()
            
            # Update dashboard state
            state = self._calculate_dashboard_state()
            self.state_manager.update_dashboard_state(state)
            
            self.logger.info("Initial data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            messagebox.showwarning("Data Loading", f"Some data could not be loaded: {e}")
    
    def _create_default_chat_session(self):
        """Create a default chat session."""
        session = ChatSession(
            id=f"session_{datetime.now().timestamp()}",
            title="Welcome Chat",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add welcome message
        welcome_message = ChatMessage(
            id=f"msg_{datetime.now().timestamp()}",
            type=ChatMessageType.SYSTEM,
            content="Welcome to Codegen Dashboard! I'm your AI assistant powered by RepoMaster and Z.AI. I can help you:\n\n• Analyze your codebase with intelligent context detection\n• Create and manage Codegen agent runs\n• Validate PRD requirements automatically\n• Visualize project dependencies and structure\n\nHow can I help you today?",
            timestamp=datetime.now(),
            user_id="system"
        )
        
        session.messages.append(welcome_message)
        self.state_manager.add_chat_session(session)
        self.current_chat_session = session
        
        # Save to database
        self.database_manager.save_chat_session(session)
    
    def _calculate_dashboard_state(self) -> DashboardState:
        """Calculate current dashboard state."""
        agent_runs = self.state_manager.get_agent_runs()
        projects = self.state_manager.get_projects()
        notifications = self.state_manager.get_notifications()
        chat_sessions = self.state_manager.get_chat_sessions()
        
        return DashboardState(
            running_instances=len([r for r in agent_runs if r.status.value == "running"]),
            total_runs=len(agent_runs),
            starred_runs=len([r for r in agent_runs if r.starred]),
            active_projects=len([p for p in projects if p.status.value == "active"]),
            starred_projects=len([p for p in projects if p.starred]),
            unread_notifications=len([n for n in notifications if not n.read]),
            active_workflows=0,  # TODO: Implement workflow tracking
            active_chat_sessions=len(chat_sessions),
            total_memory_entries=self.database_manager.get_memory_count(),
            ai_insights_count=0,  # TODO: Implement AI insights
            last_updated=datetime.now()
        )
    
    def _check_prd_validation_needed(self):
        """Check if any completed agent runs need PRD validation."""
        if not self.config.ai.prd_validation_enabled:
            return
        
        completed_runs = [
            r for r in self.state_manager.get_agent_runs()
            if r.status.value == "completed" and r.prd_validation_result is None
        ]
        
        for run in completed_runs:
            if run.project_id:
                project = self.state_manager.get_project(run.project_id)
                if project and project.prd_content:
                    # Trigger PRD validation
                    self._validate_prd_for_run(run, project)
    
    def _validate_prd_for_run(self, agent_run, project):
        """Validate PRD requirements for a completed agent run."""
        def validate():
            try:
                result = self.chat_service.validate_prd(
                    agent_run, project.prd_content
                )
                
                # Update agent run with validation result
                agent_run.prd_validation_result = result.validation_result
                self.state_manager.update_agent_run(agent_run)
                
                # Create follow-up agent if validation failed
                if (result.validation_result.value in ["failed", "partial"] and
                    self.config.ai.auto_create_followup):
                    self._create_followup_agent(agent_run, result)
                
            except Exception as e:
                self.logger.error(f"Error validating PRD for run {agent_run.id}: {e}")
        
        thread = threading.Thread(target=validate, daemon=True)
        thread.start()
    
    def _create_followup_agent(self, original_run, validation_result):
        """Create a follow-up agent run based on PRD validation results."""
        try:
            followup_prompt = self.chat_service.generate_followup_prompt(
                original_run, validation_result
            )
            
            # Create new agent run
            followup_run = self.codegen_client.create_agent_run(
                prompt=followup_prompt,
                project_id=original_run.project_id,
                parent_run_id=original_run.id
            )
            
            self.state_manager.add_agent_run(followup_run)
            
            # Create notification
            self.notification_service.create_notification(
                type="followup_agent_created",
                title="Follow-up Agent Created",
                message=f"Created follow-up agent for {original_run.title}",
                related_agent_run_id=followup_run.id
            )
            
            self.logger.info(f"Created follow-up agent {followup_run.id} for {original_run.id}")
            
        except Exception as e:
            self.logger.error(f"Error creating follow-up agent: {e}")
    
    def _trigger_validation_gates(self, project, pr):
        """Trigger validation gates for a project PR."""
        # TODO: Implement validation gates
        pass
    
    def _is_pr_new_or_updated(self, pr) -> bool:
        """Check if a PR is new or has been updated."""
        existing_pr = self.state_manager.get_pr(pr.id)
        if not existing_pr:
            return True
        return pr.updated_at > existing_pr.updated_at
    
    def _save_current_state(self):
        """Save current application state."""
        try:
            # Save chat sessions
            for session in self.state_manager.get_chat_sessions():
                self.database_manager.save_chat_session(session)
            
            # Save starred items
            starred_runs = [r for r in self.state_manager.get_agent_runs() if r.starred]
            starred_projects = [p for p in self.state_manager.get_projects() if p.starred]
            
            self.database_manager.save_starred_items(starred_runs, starred_projects)
            
            self.logger.info("Current state saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving current state: {e}")
    
    def _show_config_dialog(self):
        """Show configuration dialog for missing settings."""
        # TODO: Implement configuration dialog
        messagebox.showwarning(
            "Configuration Required",
            "Please configure your Codegen API key in the settings to use all features."
        )
    
    # Event handlers
    def _on_window_close(self):
        """Handle window close event."""
        self.stop()
    
    def _on_agent_run_updated(self, agent_run):
        """Handle agent run update event."""
        if self.main_window:
            self.main_window.refresh_agent_runs()
    
    def _on_project_updated(self, project):
        """Handle project update event."""
        if self.main_window:
            self.main_window.refresh_projects()
    
    def _on_notification_created(self, notification):
        """Handle notification creation event."""
        if self.main_window:
            self.main_window.show_notification(notification)
    
    def _on_chat_message_received(self, message: ChatMessage):
        """Handle new chat message."""
        if self.current_chat_session:
            self.current_chat_session.messages.append(message)
            self.current_chat_session.updated_at = datetime.now()
            
            if self.main_window:
                self.main_window.refresh_chat()
    
    def _on_agent_run_created_from_chat(self, agent_run, chat_message: ChatMessage):
        """Handle agent run created from chat."""
        self.state_manager.add_agent_run(agent_run)
        
        # Link chat message to agent run
        chat_message.agent_run_id = agent_run.id
        
        if self.main_window:
            self.main_window.refresh_agent_runs()
            self.main_window.refresh_chat()
    
    def _on_prd_validation_completed(self, validation_result):
        """Handle PRD validation completion."""
        # Update UI with validation results
        if self.main_window:
            self.main_window.show_prd_validation_result(validation_result)


def main():
    """Main entry point for the dashboard application."""
    try:
        dashboard = CodegenDashboard()
        dashboard.start()
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    except Exception as e:
        print(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
