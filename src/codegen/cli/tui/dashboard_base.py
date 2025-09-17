"""Dashboard base architecture for Codegen TUI."""

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class DashboardState:
    """Centralized state management for dashboard data."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {
            'starred_agents': set(),
            'starred_projects': set(),
            'notifications': [],
            'workflows': {},
            'prd_dialogs': {},
            'validation_gates': {},
            'cache': {},
            'last_refresh': {},
        }
        
        logger.info("Dashboard state initialized", extra={"operation": "dashboard.state.init"})
    
    def get(self, key: str, default=None):
        """Thread-safe get operation."""
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Thread-safe set operation."""
        with self._lock:
            self._data[key] = value
            logger.debug(f"Dashboard state updated: {key}", extra={"operation": "dashboard.state.set", "key": key})
    
    def update(self, updates: Dict[str, Any]):
        """Thread-safe bulk update operation."""
        with self._lock:
            self._data.update(updates)
            logger.debug(f"Dashboard state bulk updated", extra={"operation": "dashboard.state.update", "keys": list(updates.keys())})
    
    def add_to_set(self, key: str, value: Any):
        """Thread-safe add to set operation."""
        with self._lock:
            if key not in self._data:
                self._data[key] = set()
            if isinstance(self._data[key], set):
                self._data[key].add(value)
                logger.debug(f"Added to set {key}: {value}", extra={"operation": "dashboard.state.add_set", "key": key, "value": str(value)})
    
    def remove_from_set(self, key: str, value: Any):
        """Thread-safe remove from set operation."""
        with self._lock:
            if key in self._data and isinstance(self._data[key], set):
                self._data[key].discard(value)
                logger.debug(f"Removed from set {key}: {value}", extra={"operation": "dashboard.state.remove_set", "key": key, "value": str(value)})
    
    def is_in_set(self, key: str, value: Any) -> bool:
        """Thread-safe check if value is in set."""
        with self._lock:
            return key in self._data and isinstance(self._data[key], set) and value in self._data[key]


class DashboardCache:
    """Intelligent caching system for API responses."""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default TTL
        self.default_ttl = default_ttl
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.Lock()
        
        logger.info("Dashboard cache initialized", extra={"operation": "dashboard.cache.init", "default_ttl": default_ttl})
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if expired
            if time.time() - self._timestamps[key] > self.default_ttl:
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Cache expired for key: {key}", extra={"operation": "dashboard.cache.expired", "key": key})
                return None
            
            logger.debug(f"Cache hit for key: {key}", extra={"operation": "dashboard.cache.hit", "key": key})
            return self._cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value with TTL."""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            effective_ttl = ttl or self.default_ttl
            logger.debug(f"Cache set for key: {key}", extra={"operation": "dashboard.cache.set", "key": key, "ttl": effective_ttl})
    
    def invalidate(self, key: str):
        """Invalidate specific cache key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Cache invalidated for key: {key}", extra={"operation": "dashboard.cache.invalidate", "key": key})
    
    def clear(self):
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("Cache cleared", extra={"operation": "dashboard.cache.clear"})


class DashboardTab:
    """Base class for dashboard tabs."""
    
    def __init__(self, name: str, state: DashboardState, cache: DashboardCache):
        self.name = name
        self.state = state
        self.cache = cache
        self.is_active = False
        self.needs_refresh = True
        
        logger.debug(f"Dashboard tab initialized: {name}", extra={"operation": "dashboard.tab.init", "tab": name})
    
    def activate(self):
        """Called when tab becomes active."""
        self.is_active = True
        if self.needs_refresh:
            self.refresh()
        logger.debug(f"Dashboard tab activated: {self.name}", extra={"operation": "dashboard.tab.activate", "tab": self.name})
    
    def deactivate(self):
        """Called when tab becomes inactive."""
        self.is_active = False
        logger.debug(f"Dashboard tab deactivated: {self.name}", extra={"operation": "dashboard.tab.deactivate", "tab": self.name})
    
    def refresh(self):
        """Refresh tab data."""
        self.needs_refresh = False
        logger.debug(f"Dashboard tab refreshed: {self.name}", extra={"operation": "dashboard.tab.refresh", "tab": self.name})
    
    def render(self) -> List[str]:
        """Render tab content as list of strings."""
        return [f"Tab: {self.name}"]
    
    def handle_keypress(self, key: str) -> bool:
        """Handle keypress for this tab. Return True if handled."""
        return False


class StarredAgentsTab(DashboardTab):
    """Tab for managing starred agent runs."""
    
    def __init__(self, state: DashboardState, cache: DashboardCache):
        super().__init__("starred", state, cache)
        self.selected_index = 0
    
    def refresh(self):
        """Refresh starred agents data."""
        super().refresh()
        # This will be implemented to fetch starred agent details
        starred_ids = self.state.get('starred_agents', set())
        logger.info(f"Refreshing starred agents: {len(starred_ids)} starred", 
                   extra={"operation": "dashboard.starred.refresh", "count": len(starred_ids)})
    
    def render(self) -> List[str]:
        """Render starred agents list."""
        lines = ["🌟 Starred Agent Runs", ""]
        
        starred_ids = self.state.get('starred_agents', set())
        if not starred_ids:
            lines.append("No starred agent runs yet.")
            lines.append("Press 's' on any agent run to star it.")
        else:
            lines.append(f"Found {len(starred_ids)} starred agent runs:")
            for i, agent_id in enumerate(sorted(starred_ids)):
                marker = "→" if i == self.selected_index else " "
                lines.append(f"{marker} Agent #{agent_id}")
        
        return lines
    
    def handle_keypress(self, key: str) -> bool:
        """Handle keypress for starred agents tab."""
        starred_ids = list(sorted(self.state.get('starred_agents', set())))
        
        if key == 'j' and starred_ids:  # Move down
            self.selected_index = min(self.selected_index + 1, len(starred_ids) - 1)
            return True
        elif key == 'k' and starred_ids:  # Move up
            self.selected_index = max(self.selected_index - 1, 0)
            return True
        elif key == 'u' and starred_ids:  # Unstar selected
            if 0 <= self.selected_index < len(starred_ids):
                agent_id = starred_ids[self.selected_index]
                self.state.remove_from_set('starred_agents', agent_id)
                self.selected_index = min(self.selected_index, len(starred_ids) - 2)
                logger.info(f"Unstarred agent: {agent_id}", extra={"operation": "dashboard.starred.unstar", "agent_id": agent_id})
            return True
        
        return False


class ProjectsTab(DashboardTab):
    """Tab for managing projects."""
    
    def __init__(self, state: DashboardState, cache: DashboardCache):
        super().__init__("projects", state, cache)
        self.selected_index = 0
        self.projects = []
    
    def refresh(self):
        """Refresh projects data."""
        super().refresh()
        # This will be implemented to fetch projects from API
        logger.info("Refreshing projects data", extra={"operation": "dashboard.projects.refresh"})
    
    def render(self) -> List[str]:
        """Render projects list."""
        lines = ["📁 Projects", ""]
        
        starred_projects = self.state.get('starred_projects', set())
        if not self.projects:
            lines.append("Loading projects...")
        else:
            lines.append(f"Found {len(self.projects)} projects ({len(starred_projects)} starred):")
            for i, project in enumerate(self.projects):
                marker = "→" if i == self.selected_index else " "
                star = "⭐" if project.get('id') in starred_projects else " "
                lines.append(f"{marker}{star} {project.get('name', 'Unknown')}")
        
        return lines


class WorkflowsTab(DashboardTab):
    """Tab for managing workflows."""
    
    def __init__(self, state: DashboardState, cache: DashboardCache):
        super().__init__("workflows", state, cache)
        self.selected_index = 0
    
    def render(self) -> List[str]:
        """Render workflows list."""
        lines = ["⚙️ Workflows", ""]
        
        workflows = self.state.get('workflows', {})
        if not workflows:
            lines.append("No workflows configured.")
            lines.append("Create workflows to automate your CICD processes.")
        else:
            lines.append(f"Found {len(workflows)} workflows:")
            for i, (workflow_id, workflow) in enumerate(workflows.items()):
                marker = "→" if i == self.selected_index else " "
                status = workflow.get('status', 'idle')
                lines.append(f"{marker} {workflow.get('name', workflow_id)} [{status}]")
        
        return lines


class NotificationsTab(DashboardTab):
    """Tab for managing notifications."""
    
    def __init__(self, state: DashboardState, cache: DashboardCache):
        super().__init__("notifications", state, cache)
        self.selected_index = 0
    
    def render(self) -> List[str]:
        """Render notifications list."""
        lines = ["🔔 Notifications", ""]
        
        notifications = self.state.get('notifications', [])
        if not notifications:
            lines.append("No notifications.")
        else:
            lines.append(f"Found {len(notifications)} notifications:")
            for i, notification in enumerate(notifications[-10:]):  # Show last 10
                marker = "→" if i == self.selected_index else " "
                timestamp = notification.get('timestamp', 'Unknown')
                message = notification.get('message', 'No message')
                lines.append(f"{marker} [{timestamp}] {message}")
        
        return lines


class DashboardTabManager:
    """Manages dashboard tabs and navigation."""
    
    def __init__(self, state: DashboardState, cache: DashboardCache):
        self.state = state
        self.cache = cache
        self.current_tab_index = 0
        
        # Initialize dashboard tabs
        self.tabs = [
            StarredAgentsTab(state, cache),
            ProjectsTab(state, cache),
            WorkflowsTab(state, cache),
            NotificationsTab(state, cache),
        ]
        
        # Activate first tab
        if self.tabs:
            self.tabs[0].activate()
        
        logger.info(f"Dashboard tab manager initialized with {len(self.tabs)} tabs", 
                   extra={"operation": "dashboard.tabs.init", "tab_count": len(self.tabs)})
    
    def get_current_tab(self) -> Optional[DashboardTab]:
        """Get currently active tab."""
        if 0 <= self.current_tab_index < len(self.tabs):
            return self.tabs[self.current_tab_index]
        return None
    
    def switch_tab(self, direction: int):
        """Switch to next/previous tab."""
        if not self.tabs:
            return
        
        # Deactivate current tab
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.deactivate()
        
        # Switch tab
        self.current_tab_index = (self.current_tab_index + direction) % len(self.tabs)
        
        # Activate new tab
        new_tab = self.get_current_tab()
        if new_tab:
            new_tab.activate()
            logger.info(f"Switched to tab: {new_tab.name}", 
                       extra={"operation": "dashboard.tabs.switch", "tab": new_tab.name})
    
    def handle_keypress(self, key: str) -> bool:
        """Handle keypress, delegate to current tab if not handled globally."""
        # Global tab navigation
        if key == '\t':  # Tab key
            self.switch_tab(1)
            return True
        elif key == 'KEY_BTAB':  # Shift+Tab
            self.switch_tab(-1)
            return True
        
        # Delegate to current tab
        current_tab = self.get_current_tab()
        if current_tab:
            return current_tab.handle_keypress(key)
        
        return False
    
    def render_tabs(self) -> List[str]:
        """Render tab headers."""
        tab_headers = []
        for i, tab in enumerate(self.tabs):
            if i == self.current_tab_index:
                tab_headers.append(f"[{tab.name.upper()}]")
            else:
                tab_headers.append(f" {tab.name} ")
        
        return [" | ".join(tab_headers), ""]
    
    def render_current_tab(self) -> List[str]:
        """Render current tab content."""
        current_tab = self.get_current_tab()
        if current_tab:
            return current_tab.render()
        return ["No active tab"]

