"""Project Dashboard TUI for real-time project monitoring and task management."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Button, Footer, Header, Static, DataTable, ProgressBar, 
    Label, Input, Select, TextArea, Tabs, TabPane
)
from textual.screen import Screen
from textual.reactive import reactive
from textual.timer import Timer

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from .main import ProjectState, CodegenAPIClient, PRDManager


class TaskCreateModal(Screen):
    """Modal for creating new tasks."""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save Task"),
    ]
    
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        with Container(id="task-modal"):
            yield Static("Create New Task", id="modal-title")
            yield Label("Title:")
            yield Input(placeholder="Enter task title...", id="task-title")
            yield Label("Description:")
            yield TextArea(placeholder="Enter task description...", id="task-description")
            yield Label("Priority:")
            yield Select([
                ("Low", "low"),
                ("Medium", "medium"),
                ("High", "high")
            ], value="medium", id="task-priority")
            
            with Horizontal():
                yield Button("Save Task", variant="primary", id="save-task")
                yield Button("Cancel", variant="default", id="cancel-task")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-task":
            self.action_save()
        elif event.button.id == "cancel-task":
            self.action_cancel()
    
    def action_save(self) -> None:
        title = self.query_one("#task-title", Input).value
        description = self.query_one("#task-description", TextArea).text
        priority = self.query_one("#task-priority", Select).value
        
        if not title.strip():
            return
        
        task_data = {
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority
        }
        
        self.callback(task_data)
        self.dismiss()
    
    def action_cancel(self) -> None:
        self.dismiss()


class ProjectDashboard(App):
    """Main project dashboard TUI application."""
    
    CSS = """
    #project-header {
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
    }
    
    #stats-container {
        height: 8;
        border: solid $primary;
    }
    
    #tasks-container {
        border: solid $secondary;
    }
    
    #prd-container {
        border: solid $accent;
    }
    
    #task-modal {
        align: center middle;
        width: 60;
        height: 20;
        background: $surface;
        border: solid $primary;
    }
    
    #modal-title {
        text-align: center;
        text-style: bold;
        color: $primary;
    }
    
    .task-pending {
        background: $warning 20%;
    }
    
    .task-running {
        background: $success 20%;
    }
    
    .task-completed {
        background: $primary 20%;
    }
    
    .priority-high {
        color: $error;
        text-style: bold;
    }
    
    .priority-medium {
        color: $warning;
    }
    
    .priority-low {
        color: $success;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "new_task", "New Task"),
        Binding("s", "start_task", "Start Task"),
        Binding("c", "complete_task", "Complete Task"),
        Binding("p", "view_prd", "View PRD"),
        Binding("g", "sync_github", "Sync GitHub"),
    ]
    
    project_name = reactive("Unknown Project")
    total_tasks = reactive(0)
    completed_tasks = reactive(0)
    running_tasks = reactive(0)
    pending_tasks = reactive(0)
    progress_percentage = reactive(0.0)
    
    def __init__(self):
        super().__init__()
        self.project_state = ProjectState()
        self.api_client = None
        self.refresh_timer: Optional[Timer] = None
        self.selected_task_id = None
        
        # Initialize API client if org_id is available
        org_id = self.project_state.state.get("org_id")
        if org_id:
            try:
                self.api_client = CodegenAPIClient(org_id)
            except Exception:
                pass
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical():
            # Project header
            yield Static(f"📊 Project Dashboard: {self.project_name}", id="project-header")
            
            # Statistics section
            with Container(id="stats-container"):
                yield Static("📈 Project Statistics", classes="section-title")
                with Horizontal():
                    yield Static(f"Total: {self.total_tasks}", id="stat-total")
                    yield Static(f"✅ Completed: {self.completed_tasks}", id="stat-completed")
                    yield Static(f"🏃 Running: {self.running_tasks}", id="stat-running")
                    yield Static(f"⏳ Pending: {self.pending_tasks}", id="stat-pending")
                
                yield ProgressBar(total=100, show_eta=False, id="progress-bar")
                yield Static(f"Progress: {self.progress_percentage:.1f}%", id="progress-text")
            
            # Main content tabs
            with Tabs():
                with TabPane("Tasks", id="tasks-tab"):
                    with Container(id="tasks-container"):
                        yield Static("🚀 Active Tasks", classes="section-title")
                        yield DataTable(id="tasks-table")
                        
                        with Horizontal():
                            yield Button("New Task", variant="primary", id="new-task-btn")
                            yield Button("Start Task", variant="success", id="start-task-btn")
                            yield Button("Complete Task", variant="default", id="complete-task-btn")
                            yield Button("Refresh", variant="default", id="refresh-btn")
                
                with TabPane("PRD", id="prd-tab"):
                    with Container(id="prd-container"):
                        yield Static("📋 Product Requirements Document", classes="section-title")
                        yield ScrollableContainer(
                            Static("Loading PRD...", id="prd-content"),
                            id="prd-scroll"
                        )
                
                with TabPane("Agent Runs", id="agents-tab"):
                    with Container(id="agents-container"):
                        yield Static("🤖 Active Agent Runs", classes="section-title")
                        yield DataTable(id="agents-table")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the dashboard when mounted."""
        self.refresh_data()
        self.setup_tables()
        
        # Set up auto-refresh timer (every 30 seconds)
        self.refresh_timer = self.set_interval(30.0, self.refresh_data)
    
    def setup_tables(self) -> None:
        """Set up the data tables."""
        # Tasks table
        tasks_table = self.query_one("#tasks-table", DataTable)
        tasks_table.add_columns("ID", "Title", "Status", "Priority", "Agent Run")
        tasks_table.cursor_type = "row"
        
        # Agents table
        agents_table = self.query_one("#agents-table", DataTable)
        agents_table.add_columns("ID", "Status", "Created", "Summary")
        agents_table.cursor_type = "row"
    
    def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        # Reload project state
        self.project_state = ProjectState()
        
        # Update reactive variables
        self.project_name = self.project_state.state.get("project_name", "Unknown Project")
        
        tasks = self.project_state.state.get("tasks", [])
        self.total_tasks = len(tasks)
        self.completed_tasks = len([t for t in tasks if t["status"] == "completed"])
        self.running_tasks = len([t for t in tasks if t["status"] == "running"])
        self.pending_tasks = len([t for t in tasks if t["status"] == "pending"])
        
        if self.total_tasks > 0:
            self.progress_percentage = (self.completed_tasks / self.total_tasks) * 100
        else:
            self.progress_percentage = 0.0
        
        # Update UI elements
        self.update_statistics()
        self.update_tasks_table()
        self.update_prd_content()
        
        if self.api_client:
            self.update_agents_table()
    
    def update_statistics(self) -> None:
        """Update the statistics display."""
        try:
            self.query_one("#stat-total", Static).update(f"Total: {self.total_tasks}")
            self.query_one("#stat-completed", Static).update(f"✅ Completed: {self.completed_tasks}")
            self.query_one("#stat-running", Static).update(f"🏃 Running: {self.running_tasks}")
            self.query_one("#stat-pending", Static).update(f"⏳ Pending: {self.pending_tasks}")
            
            progress_bar = self.query_one("#progress-bar", ProgressBar)
            progress_bar.update(progress=self.progress_percentage)
            
            self.query_one("#progress-text", Static).update(f"Progress: {self.progress_percentage:.1f}%")
            
            # Update header
            self.query_one("#project-header", Static).update(f"📊 Project Dashboard: {self.project_name}")
        except Exception:
            pass  # Ignore if widgets not found
    
    def update_tasks_table(self) -> None:
        """Update the tasks table."""
        try:
            tasks_table = self.query_one("#tasks-table", DataTable)
            tasks_table.clear()
            
            for task in self.project_state.state.get("tasks", []):
                status_display = {
                    "pending": "⏳ Pending",
                    "running": "🏃 Running",
                    "completed": "✅ Completed",
                    "failed": "❌ Failed"
                }.get(task["status"], "❓ Unknown")
                
                priority_display = task.get("priority", "medium").title()
                agent_run = str(task.get("agent_run_id", "")) if task.get("agent_run_id") else "-"
                
                # Add row with styling based on status
                row_key = tasks_table.add_row(
                    str(task["id"]),
                    task["title"],
                    status_display,
                    priority_display,
                    agent_run
                )
                
                # Apply styling based on status
                if task["status"] == "pending":
                    tasks_table.set_row_style(row_key, "task-pending")
                elif task["status"] == "running":
                    tasks_table.set_row_style(row_key, "task-running")
                elif task["status"] == "completed":
                    tasks_table.set_row_style(row_key, "task-completed")
        except Exception:
            pass
    
    def update_prd_content(self) -> None:
        """Update the PRD content."""
        try:
            prd_manager = PRDManager(self.project_state.prd_file)
            prd_content = prd_manager.read_prd()
            
            # Update tasks section if needed
            if self.project_state.state["tasks"]:
                prd_manager.update_tasks_section(self.project_state.state["tasks"])
                prd_content = prd_manager.read_prd()
            
            self.query_one("#prd-content", Static).update(prd_content)
        except Exception:
            pass
    
    def update_agents_table(self) -> None:
        """Update the agents table with API data."""
        if not self.api_client:
            return
        
        try:
            agents_data = self.api_client.list_agent_runs()
            agents_table = self.query_one("#agents-table", DataTable)
            agents_table.clear()
            
            for agent_run in agents_data.get("items", [])[:10]:  # Show last 10
                created_at = agent_run.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_display = dt.strftime("%m/%d %H:%M")
                    except:
                        created_display = created_at
                else:
                    created_display = "Unknown"
                
                summary = agent_run.get("summary", "No summary")[:50] + "..." if len(agent_run.get("summary", "")) > 50 else agent_run.get("summary", "No summary")
                
                agents_table.add_row(
                    str(agent_run.get("id", "")),
                    agent_run.get("status", "Unknown"),
                    created_display,
                    summary
                )
        except Exception:
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "new-task-btn":
            self.action_new_task()
        elif event.button.id == "start-task-btn":
            self.action_start_task()
        elif event.button.id == "complete-task-btn":
            self.action_complete_task()
        elif event.button.id == "refresh-btn":
            self.action_refresh()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle task selection."""
        if event.data_table.id == "tasks-table":
            row_data = event.data_table.get_row(event.row_key)
            self.selected_task_id = int(row_data[0])  # First column is task ID
    
    def action_new_task(self) -> None:
        """Create a new task."""
        def on_task_created(task_data):
            self.project_state.add_task(task_data)
            self.refresh_data()
        
        self.push_screen(TaskCreateModal(on_task_created))
    
    def action_start_task(self) -> None:
        """Start the selected task."""
        if not self.selected_task_id:
            return
        
        task = self.project_state.get_task(self.selected_task_id)
        if not task or task["status"] != "pending":
            return
        
        if not self.api_client:
            return
        
        # Create agent run
        prompt = f"""Task: {task['title']}

Description: {task['description']}

Priority: {task.get('priority', 'medium')}

Please implement this task following best practices."""
        
        try:
            agent_run_data = self.api_client.create_agent_run(prompt)
            self.project_state.start_task(self.selected_task_id, agent_run_data["id"])
            self.refresh_data()
        except Exception:
            pass
    
    def action_complete_task(self) -> None:
        """Complete the selected task."""
        if not self.selected_task_id:
            return
        
        self.project_state.complete_task(self.selected_task_id)
        self.refresh_data()
    
    def action_refresh(self) -> None:
        """Refresh the dashboard data."""
        self.refresh_data()
    
    def action_view_prd(self) -> None:
        """Switch to PRD tab."""
        tabs = self.query_one(Tabs)
        tabs.active = "prd-tab"
    
    def action_sync_github(self) -> None:
        """Sync with GitHub (placeholder)."""
        # This would implement GitHub sync functionality
        pass


def run_project_dashboard():
    """Run the project dashboard TUI."""
    app = ProjectDashboard()
    app.run()


if __name__ == "__main__":
    run_project_dashboard()

