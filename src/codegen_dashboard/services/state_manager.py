"""
State Manager Service

Manages the global state of the dashboard including agent runs,
starred items, notifications, and user preferences.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
import json
import os


@dataclass
class AgentRunState:
    """State information for an agent run."""
    id: int
    status: str
    result: Optional[str]
    web_url: Optional[str]
    created_at: datetime
    last_updated: datetime
    is_starred: bool = False
    follow_up_prompt: Optional[str] = None
    auto_follow_up: bool = False


@dataclass
class ProjectState:
    """State information for a project."""
    id: int
    name: str
    description: Optional[str]
    is_starred: bool = False
    pr_monitoring_enabled: bool = False
    validation_gates: List[str] = field(default_factory=list)
    last_pr_check: Optional[datetime] = None


@dataclass
class NotificationState:
    """State information for a notification."""
    id: str
    type: str
    title: str
    message: str
    created_at: datetime
    is_read: bool = False
    related_agent_run_id: Optional[int] = None
    related_project_id: Optional[int] = None


class StateManager:
    """
    Manages the global state of the dashboard.
    
    Provides centralized state management for:
    - Agent runs and their status
    - Starred items (runs and projects)
    - Notifications and alerts
    - User preferences and settings
    - Real-time updates and synchronization
    """
    
    def __init__(self):
        """Initialize the state manager."""
        self.logger = logging.getLogger(__name__)
        
        # Core state
        self.agent_runs: Dict[int, AgentRunState] = {}
        self.projects: Dict[int, ProjectState] = {}
        self.notifications: Dict[str, NotificationState] = {}
        
        # Starred items
        self.starred_agent_runs: Set[int] = set()
        self.starred_projects: Set[int] = set()
        
        # Running instances tracking
        self.running_agent_runs: Set[int] = set()
        
        # State change callbacks
        self.state_change_callbacks = []
        
        # Persistence
        self.state_file = os.path.expanduser("~/.codegen/dashboard_state.json")
        self._ensure_state_directory()
        self._load_state()
        
    def _ensure_state_directory(self):
        """Ensure the state directory exists."""
        state_dir = os.path.dirname(self.state_file)
        os.makedirs(state_dir, exist_ok=True)
    
    def _load_state(self):
        """Load state from persistent storage."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Load starred items
                self.starred_agent_runs = set(data.get('starred_agent_runs', []))
                self.starred_projects = set(data.get('starred_projects', []))
                
                # Load agent runs
                for run_data in data.get('agent_runs', []):
                    run_state = AgentRunState(
                        id=run_data['id'],
                        status=run_data['status'],
                        result=run_data.get('result'),
                        web_url=run_data.get('web_url'),
                        created_at=datetime.fromisoformat(run_data['created_at']),
                        last_updated=datetime.fromisoformat(run_data['last_updated']),
                        is_starred=run_data.get('is_starred', False),
                        follow_up_prompt=run_data.get('follow_up_prompt'),
                        auto_follow_up=run_data.get('auto_follow_up', False)
                    )
                    self.agent_runs[run_state.id] = run_state
                
                # Load projects
                for project_data in data.get('projects', []):
                    project_state = ProjectState(
                        id=project_data['id'],
                        name=project_data['name'],
                        description=project_data.get('description'),
                        is_starred=project_data.get('is_starred', False),
                        pr_monitoring_enabled=project_data.get('pr_monitoring_enabled', False),
                        validation_gates=project_data.get('validation_gates', []),
                        last_pr_check=datetime.fromisoformat(project_data['last_pr_check']) if project_data.get('last_pr_check') else None
                    )
                    self.projects[project_state.id] = project_state
                
                self.logger.info("State loaded successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save state to persistent storage."""
        try:
            data = {
                'starred_agent_runs': list(self.starred_agent_runs),
                'starred_projects': list(self.starred_projects),
                'agent_runs': [
                    {
                        'id': run.id,
                        'status': run.status,
                        'result': run.result,
                        'web_url': run.web_url,
                        'created_at': run.created_at.isoformat(),
                        'last_updated': run.last_updated.isoformat(),
                        'is_starred': run.is_starred,
                        'follow_up_prompt': run.follow_up_prompt,
                        'auto_follow_up': run.auto_follow_up
                    }
                    for run in self.agent_runs.values()
                ],
                'projects': [
                    {
                        'id': project.id,
                        'name': project.name,
                        'description': project.description,
                        'is_starred': project.is_starred,
                        'pr_monitoring_enabled': project.pr_monitoring_enabled,
                        'validation_gates': project.validation_gates,
                        'last_pr_check': project.last_pr_check.isoformat() if project.last_pr_check else None
                    }
                    for project in self.projects.values()
                ]
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.logger.debug("State saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def update_agent_run(self, agent_run_data: Dict[str, Any]):
        """Update agent run state."""
        agent_id = agent_run_data['id']
        
        if agent_id in self.agent_runs:
            # Update existing
            run_state = self.agent_runs[agent_id]
            run_state.status = agent_run_data['status']
            run_state.result = agent_run_data.get('result')
            run_state.web_url = agent_run_data.get('web_url')
            run_state.last_updated = datetime.now()
        else:
            # Create new
            run_state = AgentRunState(
                id=agent_id,
                status=agent_run_data['status'],
                result=agent_run_data.get('result'),
                web_url=agent_run_data.get('web_url'),
                created_at=datetime.fromisoformat(agent_run_data['created_at']) if agent_run_data.get('created_at') else datetime.now(),
                last_updated=datetime.now(),
                is_starred=agent_id in self.starred_agent_runs
            )
            self.agent_runs[agent_id] = run_state
        
        # Update running instances
        if run_state.status in ['running', 'queued']:
            self.running_agent_runs.add(agent_id)
        else:
            self.running_agent_runs.discard(agent_id)
        
        self._save_state()
        self._notify_state_change('agent_run_updated', {'agent_run': run_state})
    
    def star_agent_run(self, agent_run_id: int):
        """Star an agent run."""
        self.starred_agent_runs.add(agent_run_id)
        if agent_run_id in self.agent_runs:
            self.agent_runs[agent_run_id].is_starred = True
        
        self._save_state()
        self._notify_state_change('agent_run_starred', {'agent_run_id': agent_run_id})
    
    def unstar_agent_run(self, agent_run_id: int):
        """Unstar an agent run."""
        self.starred_agent_runs.discard(agent_run_id)
        if agent_run_id in self.agent_runs:
            self.agent_runs[agent_run_id].is_starred = False
        
        self._save_state()
        self._notify_state_change('agent_run_unstarred', {'agent_run_id': agent_run_id})
    
    def star_project(self, project_id: int):
        """Star a project."""
        self.starred_projects.add(project_id)
        if project_id in self.projects:
            self.projects[project_id].is_starred = True
        
        self._save_state()
        self._notify_state_change('project_starred', {'project_id': project_id})
    
    def unstar_project(self, project_id: int):
        """Unstar a project."""
        self.starred_projects.discard(project_id)
        if project_id in self.projects:
            self.projects[project_id].is_starred = False
        
        self._save_state()
        self._notify_state_change('project_unstarred', {'project_id': project_id})
    
    def set_follow_up_prompt(self, agent_run_id: int, prompt: str, auto_follow_up: bool = False):
        """Set a follow-up prompt for an agent run."""
        if agent_run_id in self.agent_runs:
            self.agent_runs[agent_run_id].follow_up_prompt = prompt
            self.agent_runs[agent_run_id].auto_follow_up = auto_follow_up
            self._save_state()
            self._notify_state_change('follow_up_set', {
                'agent_run_id': agent_run_id,
                'prompt': prompt,
                'auto_follow_up': auto_follow_up
            })
    
    def add_notification(self, notification: NotificationState):
        """Add a new notification."""
        self.notifications[notification.id] = notification
        self._notify_state_change('notification_added', {'notification': notification})
    
    def mark_notification_read(self, notification_id: str):
        """Mark a notification as read."""
        if notification_id in self.notifications:
            self.notifications[notification_id].is_read = True
            self._notify_state_change('notification_read', {'notification_id': notification_id})
    
    def get_running_count(self) -> int:
        """Get the count of currently running agent runs."""
        return len(self.running_agent_runs)
    
    def get_running_agent_runs(self) -> List[AgentRunState]:
        """Get all currently running agent runs."""
        return [
            self.agent_runs[agent_id] 
            for agent_id in self.running_agent_runs 
            if agent_id in self.agent_runs
        ]
    
    def get_starred_agent_runs(self) -> List[AgentRunState]:
        """Get all starred agent runs."""
        return [
            run for run in self.agent_runs.values() 
            if run.is_starred
        ]
    
    def get_starred_projects(self) -> List[ProjectState]:
        """Get all starred projects."""
        return [
            project for project in self.projects.values() 
            if project.is_starred
        ]
    
    def get_unread_notifications(self) -> List[NotificationState]:
        """Get all unread notifications."""
        return [
            notification for notification in self.notifications.values() 
            if not notification.is_read
        ]
    
    def register_state_change_callback(self, callback):
        """Register a callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def _notify_state_change(self, event_type: str, data: Dict[str, Any]):
        """Notify all registered callbacks of state changes."""
        for callback in self.state_change_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                self.logger.error(f"Error in state change callback: {e}")
    
    def cleanup(self):
        """Cleanup resources."""
        self._save_state()
        self.logger.info("State manager cleaned up")
