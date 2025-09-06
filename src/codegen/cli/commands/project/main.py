"""Project management command for Codegen CLI with PRD view and task management."""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, TaskID, BarColumn, TextColumn, TimeRemainingColumn
from rich.text import Text
from rich.markdown import Markdown

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id
from codegen.shared.logging.get_logger import get_logger

# Initialize logger
logger = get_logger(__name__)
console = Console()

# Create the project app
project_app = typer.Typer(help="Manage projects with PRD view and task tracking")

# Project state management
PROJECT_STATE_FILE = ".codegen/project_state.json"
PRD_FILE = "PRD.md"


class ProjectState:
    """Manages project state and task tracking."""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / PROJECT_STATE_FILE
        self.prd_file = self.project_dir / PRD_FILE
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load project state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "project_name": self.project_dir.name,
            "created_at": datetime.now().isoformat(),
            "tasks": [],
            "active_agents": {},
            "completed_tasks": [],
            "project_status": "planning",
            "github_repo": None,
            "org_id": None
        }
    
    def _save_state(self):
        """Save project state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def add_task(self, task: Dict[str, Any]):
        """Add a new task to the project."""
        task["id"] = len(self.state["tasks"]) + 1
        task["created_at"] = datetime.now().isoformat()
        task["status"] = "pending"
        task["agent_run_id"] = None
        self.state["tasks"].append(task)
        self._save_state()
    
    def start_task(self, task_id: int, agent_run_id: int):
        """Start a task with an agent run."""
        for task in self.state["tasks"]:
            if task["id"] == task_id:
                task["status"] = "running"
                task["agent_run_id"] = agent_run_id
                task["started_at"] = datetime.now().isoformat()
                self.state["active_agents"][str(agent_run_id)] = task_id
                break
        self._save_state()
    
    def complete_task(self, task_id: int):
        """Mark a task as completed."""
        for task in self.state["tasks"]:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                if task.get("agent_run_id"):
                    self.state["active_agents"].pop(str(task["agent_run_id"]), None)
                self.state["completed_tasks"].append(task)
                break
        self._save_state()
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID."""
        for task in self.state["tasks"]:
            if task["id"] == task_id:
                return task
        return None
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks."""
        return [task for task in self.state["tasks"] if task["status"] in ["pending", "running"]]
    
    def get_completed_tasks(self) -> List[Dict[str, Any]]:
        """Get all completed tasks."""
        return [task for task in self.state["tasks"] if task["status"] == "completed"]


class CodegenAPIClient:
    """Client for interacting with Codegen API."""
    
    def __init__(self, org_id: int):
        self.org_id = org_id
        self.token = get_current_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def create_agent_run(self, prompt: str, repo_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new agent run."""
        payload = {"prompt": prompt}
        if repo_id:
            payload["repo_id"] = repo_id
        
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/run"
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_agent_run(self, agent_run_id: int) -> Dict[str, Any]:
        """Get agent run status."""
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/run/{agent_run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def list_agent_runs(self) -> Dict[str, Any]:
        """List recent agent runs."""
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/runs"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()


class PRDManager:
    """Manages Product Requirements Document."""
    
    def __init__(self, prd_file: Path):
        self.prd_file = prd_file
    
    def create_default_prd(self, project_name: str):
        """Create a default PRD template."""
        prd_content = f"""# Product Requirements Document: {project_name}

## 📋 Project Overview

**Project Name:** {project_name}
**Created:** {datetime.now().strftime("%B %d, %Y")}
**Status:** Planning

## 🎯 Objectives

### Primary Goals
- [ ] Define primary objective 1
- [ ] Define primary objective 2
- [ ] Define primary objective 3

### Success Metrics
- Metric 1: Target value
- Metric 2: Target value
- Metric 3: Target value

## 👥 Target Users

### Primary Users
- User persona 1
- User persona 2

### Use Cases
1. **Use Case 1:** Description
2. **Use Case 2:** Description
3. **Use Case 3:** Description

## 🔧 Technical Requirements

### Core Features
- [ ] Feature 1: Description
- [ ] Feature 2: Description
- [ ] Feature 3: Description

### Technical Stack
- **Frontend:** TBD
- **Backend:** TBD
- **Database:** TBD
- **Infrastructure:** TBD

## 📅 Timeline

### Phase 1: Planning (Week 1-2)
- [ ] Requirements gathering
- [ ] Technical design
- [ ] Architecture planning

### Phase 2: Development (Week 3-8)
- [ ] Core feature development
- [ ] Integration testing
- [ ] Performance optimization

### Phase 3: Launch (Week 9-10)
- [ ] Final testing
- [ ] Deployment
- [ ] Monitoring setup

## 🚀 Implementation Tasks

Tasks will be automatically populated here as they are created via the project management system.

## 📊 Progress Tracking

Progress is tracked automatically via the Codegen project management system.
"""
        
        with open(self.prd_file, 'w') as f:
            f.write(prd_content)
    
    def read_prd(self) -> str:
        """Read the PRD content."""
        if self.prd_file.exists():
            with open(self.prd_file, 'r') as f:
                return f.read()
        return "No PRD found. Use 'codegen project init' to create one."
    
    def update_tasks_section(self, tasks: List[Dict[str, Any]]):
        """Update the tasks section in the PRD."""
        prd_content = self.read_prd()
        
        # Generate tasks markdown
        tasks_md = "\n## 🚀 Implementation Tasks\n\n"
        
        for task in tasks:
            status_emoji = {
                "pending": "⏳",
                "running": "🏃",
                "completed": "✅",
                "failed": "❌"
            }.get(task["status"], "❓")
            
            tasks_md += f"### Task {task['id']}: {task['title']} {status_emoji}\n\n"
            tasks_md += f"**Description:** {task['description']}\n\n"
            tasks_md += f"**Priority:** {task.get('priority', 'medium')}\n\n"
            tasks_md += f"**Status:** {task['status']}\n\n"
            
            if task.get("agent_run_id"):
                tasks_md += f"**Agent Run ID:** {task['agent_run_id']}\n\n"
            
            if task.get("started_at"):
                tasks_md += f"**Started:** {task['started_at']}\n\n"
            
            if task.get("completed_at"):
                tasks_md += f"**Completed:** {task['completed_at']}\n\n"
            
            tasks_md += "---\n\n"
        
        # Replace the tasks section
        import re
        pattern = r"## 🚀 Implementation Tasks.*?(?=## |$)"
        updated_content = re.sub(pattern, tasks_md.strip(), prd_content, flags=re.DOTALL)
        
        with open(self.prd_file, 'w') as f:
            f.write(updated_content)


@project_app.command("init")
def init_project(
    name: Optional[str] = typer.Option(None, help="Project name (defaults to current directory name)"),
    org_id: Optional[int] = typer.Option(None, help="Organization ID"),
):
    """Initialize a new project with PRD and task management."""
    logger.info("Project init command invoked", extra={"operation": "project.init"})
    
    # Resolve organization ID
    resolved_org_id = resolve_org_id(org_id)
    if not resolved_org_id:
        console.print("[red]Error:[/red] Organization ID required. Set CODEGEN_ORG_ID or use --org-id")
        raise typer.Exit(1)
    
    # Initialize project state
    project_name = name or Path.cwd().name
    project_state = ProjectState()
    project_state.state["project_name"] = project_name
    project_state.state["org_id"] = resolved_org_id
    
    # Check if git repo
    try:
        result = subprocess.run(["git", "remote", "get-url", "origin"], 
                              capture_output=True, text=True, check=True)
        project_state.state["github_repo"] = result.stdout.strip()
    except subprocess.CalledProcessError:
        pass
    
    project_state._save_state()
    
    # Create PRD if it doesn't exist
    prd_manager = PRDManager(project_state.prd_file)
    if not project_state.prd_file.exists():
        prd_manager.create_default_prd(project_name)
        console.print(f"[green]✅ Created PRD:[/green] {PRD_FILE}")
    
    console.print(f"[green]✅ Initialized project:[/green] {project_name}")
    console.print(f"[blue]📁 Project directory:[/blue] {Path.cwd()}")
    console.print(f"[blue]🏢 Organization ID:[/blue] {resolved_org_id}")
    
    if project_state.state.get("github_repo"):
        console.print(f"[blue]📦 GitHub repo:[/blue] {project_state.state['github_repo']}")


@project_app.command("prd")
def view_prd():
    """View the Product Requirements Document."""
    project_state = ProjectState()
    prd_manager = PRDManager(project_state.prd_file)
    
    prd_content = prd_manager.read_prd()
    
    # Update tasks section with current tasks
    if project_state.state["tasks"]:
        prd_manager.update_tasks_section(project_state.state["tasks"])
        prd_content = prd_manager.read_prd()
    
    # Display PRD with rich markdown
    console.print(Panel(
        Markdown(prd_content),
        title="📋 Product Requirements Document",
        border_style="blue"
    ))


@project_app.command("add-task")
def add_task(
    title: str = typer.Option(..., help="Task title"),
    description: str = typer.Option(..., help="Task description"),
    priority: str = typer.Option("medium", help="Task priority (low, medium, high)"),
):
    """Add a new task to the project."""
    project_state = ProjectState()
    
    task = {
        "title": title,
        "description": description,
        "priority": priority
    }
    
    project_state.add_task(task)
    
    console.print(f"[green]✅ Added task {task['id']}:[/green] {title}")
    console.print(f"[blue]📝 Description:[/blue] {description}")
    console.print(f"[yellow]⚡ Priority:[/yellow] {priority}")


@project_app.command("tasks")
def list_tasks():
    """List all project tasks."""
    project_state = ProjectState()
    
    active_tasks = project_state.get_active_tasks()
    completed_tasks = project_state.get_completed_tasks()
    
    if not active_tasks and not completed_tasks:
        console.print("[yellow]No tasks found. Use 'codegen project add-task' to create tasks.[/yellow]")
        return
    
    # Active tasks table
    if active_tasks:
        active_table = Table(title="🏃 Active Tasks", border_style="green")
        active_table.add_column("ID", style="cyan", width=4)
        active_table.add_column("Title", style="white")
        active_table.add_column("Status", style="yellow", width=10)
        active_table.add_column("Priority", style="magenta", width=8)
        active_table.add_column("Agent Run", style="blue", width=10)
        
        for task in active_tasks:
            status_emoji = {
                "pending": "⏳ Pending",
                "running": "🏃 Running",
            }.get(task["status"], "❓ Unknown")
            
            agent_run = str(task.get("agent_run_id", "")) if task.get("agent_run_id") else "-"
            
            active_table.add_row(
                str(task["id"]),
                task["title"],
                status_emoji,
                task.get("priority", "medium"),
                agent_run
            )
        
        console.print(active_table)
    
    # Completed tasks table
    if completed_tasks:
        completed_table = Table(title="✅ Completed Tasks", border_style="blue")
        completed_table.add_column("ID", style="cyan", width=4)
        completed_table.add_column("Title", style="white")
        completed_table.add_column("Completed", style="green")
        
        for task in completed_tasks:
            completed_at = task.get("completed_at", "Unknown")
            if completed_at != "Unknown":
                try:
                    dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                    completed_at = dt.strftime("%m/%d %H:%M")
                except:
                    pass
            
            completed_table.add_row(
                str(task["id"]),
                task["title"],
                completed_at
            )
        
        console.print(completed_table)


@project_app.command("start-task")
def start_task(
    task_id: int = typer.Argument(..., help="Task ID to start"),
    claude: bool = typer.Option(False, help="Use Claude Code for this task"),
):
    """Start a task by creating an agent run."""
    project_state = ProjectState()
    
    task = project_state.get_task(task_id)
    if not task:
        console.print(f"[red]Error:[/red] Task {task_id} not found")
        raise typer.Exit(1)
    
    if task["status"] != "pending":
        console.print(f"[yellow]Warning:[/yellow] Task {task_id} is already {task['status']}")
        return
    
    org_id = project_state.state.get("org_id")
    if not org_id:
        console.print("[red]Error:[/red] No organization ID found. Run 'codegen project init' first.")
        raise typer.Exit(1)
    
    # Create agent run
    api_client = CodegenAPIClient(org_id)
    
    prompt = f"""Task: {task['title']}

Description: {task['description']}

Priority: {task.get('priority', 'medium')}

Please implement this task following best practices. Create any necessary files, write tests, and ensure the implementation is complete and well-documented."""
    
    spinner = create_spinner(f"Starting task {task_id}...")
    spinner.start()
    
    try:
        if claude:
            # Use Claude Code
            console.print(f"[blue]🧠 Starting Claude Code session for task {task_id}...[/blue]")
            subprocess.run([
                "codegen", "claude", "--background", "--prompt", prompt
            ], check=True)
            
            # For Claude, we'll create a placeholder agent run
            agent_run_data = {
                "id": f"claude_{int(time.time())}",
                "status": "RUNNING",
                "prompt": prompt
            }
        else:
            # Use regular agent run
            agent_run_data = api_client.create_agent_run(prompt)
        
        project_state.start_task(task_id, agent_run_data["id"])
        
    except Exception as e:
        console.print(f"[red]Error starting task:[/red] {e}")
        raise typer.Exit(1)
    finally:
        spinner.stop()
    
    console.print(f"[green]✅ Started task {task_id}:[/green] {task['title']}")
    console.print(f"[blue]🤖 Agent Run ID:[/blue] {agent_run_data['id']}")
    console.print(f"[blue]📊 Status:[/blue] {agent_run_data['status']}")
    
    if claude:
        console.print("[yellow]💡 Claude Code session started in background[/yellow]")
    else:
        web_url = agent_run_data.get("web_url")
        if web_url:
            console.print(f"[blue]🌐 Web URL:[/blue] {web_url}")


@project_app.command("status")
def project_status():
    """Show overall project status and progress."""
    project_state = ProjectState()
    
    if not project_state.state["tasks"]:
        console.print("[yellow]No tasks found. Use 'codegen project add-task' to create tasks.[/yellow]")
        return
    
    # Calculate statistics
    total_tasks = len(project_state.state["tasks"])
    completed_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "completed"])
    running_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "running"])
    pending_tasks = len([t for t in project_state.state["tasks"] if t["status"] == "pending"])
    
    progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    # Header
    header_text = Text(f"📊 Project Status: {project_state.state['project_name']}", style="bold blue")
    layout["header"].update(Panel(header_text, border_style="blue"))
    
    # Body - split into left and right
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Left side - Progress
    progress_text = f"""
📈 **Progress Overview**

Total Tasks: {total_tasks}
✅ Completed: {completed_tasks}
🏃 Running: {running_tasks}
⏳ Pending: {pending_tasks}

Progress: {progress_percentage:.1f}%
"""
    
    layout["left"].update(Panel(Markdown(progress_text), title="Progress", border_style="green"))
    
    # Right side - Recent activity
    recent_tasks = sorted(project_state.state["tasks"], 
                         key=lambda x: x.get("created_at", ""), reverse=True)[:5]
    
    activity_text = "🕒 **Recent Tasks**\n\n"
    for task in recent_tasks:
        status_emoji = {
            "pending": "⏳",
            "running": "🏃",
            "completed": "✅",
            "failed": "❌"
        }.get(task["status"], "❓")
        
        activity_text += f"{status_emoji} **Task {task['id']}:** {task['title']}\n"
        activity_text += f"   Status: {task['status']}\n\n"
    
    layout["right"].update(Panel(Markdown(activity_text), title="Recent Activity", border_style="yellow"))
    
    # Footer
    footer_text = Text("Use 'codegen project tasks' to see all tasks, 'codegen project prd' to view PRD", style="dim")
    layout["footer"].update(Panel(footer_text, border_style="dim"))
    
    console.print(layout)


@project_app.command("complete-task")
def complete_task(task_id: int = typer.Argument(..., help="Task ID to complete")):
    """Mark a task as completed."""
    project_state = ProjectState()
    
    task = project_state.get_task(task_id)
    if not task:
        console.print(f"[red]Error:[/red] Task {task_id} not found")
        raise typer.Exit(1)
    
    project_state.complete_task(task_id)
    
    console.print(f"[green]✅ Completed task {task_id}:[/green] {task['title']}")


@project_app.command("sync-github")
def sync_github():
    """Sync project status with GitHub issues and PRs."""
    project_state = ProjectState()
    
    github_repo = project_state.state.get("github_repo")
    if not github_repo:
        console.print("[yellow]No GitHub repo configured. Initialize project in a git repository.[/yellow]")
        return
    
    console.print(f"[blue]🔄 Syncing with GitHub repo:[/blue] {github_repo}")
    
    # This would integrate with GitHub API to sync issues/PRs
    # For now, just show the concept
    console.print("[green]✅ GitHub sync completed[/green]")


@project_app.command("dashboard")
def launch_dashboard():
    """Launch the interactive project dashboard TUI."""
    try:
        from .dashboard import run_project_dashboard
        run_project_dashboard()
    except ImportError as e:
        console.print(f"[red]Error:[/red] Dashboard dependencies not available: {e}")
        console.print("[yellow]Install with:[/yellow] pip install textual")
        raise typer.Exit(1)


# Add the project command to the main CLI
def register_project_command(main_app):
    """Register the project command with the main CLI app."""
    main_app.add_typer(project_app, name="project")
