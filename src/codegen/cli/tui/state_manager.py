"""Centralized state management for Codegen Dashboard."""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from codegen.cli.auth.constants import CONFIG_DIR
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class StateManager:
    """Thread-safe state manager for dashboard data with persistence."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._state_file = Path(CONFIG_DIR) / "dashboard_state.json"
        self._cache_file = Path(CONFIG_DIR) / "dashboard_cache.json"
        
        # Initialize state structure
        self._state = {
            'starred_agents': set(),
            'starred_projects': set(),
            'notifications': [],
            'workflows': {},
            'prd_dialogs': {},
            'validation_gates': {},
            'preferences': {
                'auto_refresh_interval': 10,
                'notification_enabled': True,
                'theme': 'default',
                'max_notifications': 100,
            },
            'follow_up_rules': {},
            'last_activity': None,
        }
        
        # Cache for API responses
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = {
            'agent_runs': 30,      # 30 seconds for agent runs
            'projects': 300,       # 5 minutes for projects
            'tools': 600,          # 10 minutes for tools
            'user_info': 3600,     # 1 hour for user info
        }
        
        # Load persisted state
        self._load_state()
        self._load_cache()
        
        logger.info("State manager initialized", 
                   extra={"operation": "state.init", "state_file": str(self._state_file)})
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    
    def _load_state(self):
        """Load state from disk."""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                
                # Convert lists back to sets for starred items
                if 'starred_agents' in data:
                    data['starred_agents'] = set(data['starred_agents'])
                if 'starred_projects' in data:
                    data['starred_projects'] = set(data['starred_projects'])
                
                # Merge with default state
                self._state.update(data)
                
                logger.info("State loaded from disk", 
                           extra={"operation": "state.load", "starred_agents": len(self._state['starred_agents'])})
        except Exception as e:
            logger.warning(f"Failed to load state: {e}", extra={"operation": "state.load_error"})
    
    def _save_state(self):
        """Save state to disk."""
        try:
            self._ensure_config_dir()
            
            # Convert sets to lists for JSON serialization
            data = self._state.copy()
            data['starred_agents'] = list(data['starred_agents'])
            data['starred_projects'] = list(data['starred_projects'])
            data['last_activity'] = datetime.now().isoformat()
            
            with open(self._state_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug("State saved to disk", extra={"operation": "state.save"})
        except Exception as e:
            logger.error(f"Failed to save state: {e}", extra={"operation": "state.save_error"})
    
    def _load_cache(self):
        """Load cache from disk."""
        try:
            if self._cache_file.exists():
                with open(self._cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                self._cache = cache_data.get('cache', {})
                self._cache_timestamps = cache_data.get('timestamps', {})
                
                logger.debug("Cache loaded from disk", 
                           extra={"operation": "cache.load", "entries": len(self._cache)})
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}", extra={"operation": "cache.load_error"})
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            self._ensure_config_dir()
            
            cache_data = {
                'cache': self._cache,
                'timestamps': self._cache_timestamps,
                'saved_at': datetime.now().isoformat(),
            }
            
            with open(self._cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2, default=str)
            
            logger.debug("Cache saved to disk", extra={"operation": "cache.save"})
        except Exception as e:
            logger.error(f"Failed to save cache: {e}", extra={"operation": "cache.save_error"})
    
    # State management methods
    def get_state(self, key: str, default=None):
        """Get state value thread-safely."""
        with self._lock:
            return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any, persist: bool = True):
        """Set state value thread-safely."""
        with self._lock:
            self._state[key] = value
            if persist:
                self._save_state()
            
            logger.debug(f"State updated: {key}", 
                        extra={"operation": "state.set", "key": key, "persist": persist})
    
    def update_state(self, updates: Dict[str, Any], persist: bool = True):
        """Update multiple state values."""
        with self._lock:
            self._state.update(updates)
            if persist:
                self._save_state()
            
            logger.debug("State bulk updated", 
                        extra={"operation": "state.update", "keys": list(updates.keys())})
    
    # Starred agents management
    def star_agent(self, agent_id: str):
        """Star an agent run."""
        with self._lock:
            self._state['starred_agents'].add(agent_id)
            self._save_state()
            
            logger.info(f"Agent starred: {agent_id}", 
                       extra={"operation": "state.star_agent", "agent_id": agent_id})
    
    def unstar_agent(self, agent_id: str):
        """Unstar an agent run."""
        with self._lock:
            self._state['starred_agents'].discard(agent_id)
            self._save_state()
            
            logger.info(f"Agent unstarred: {agent_id}", 
                       extra={"operation": "state.unstar_agent", "agent_id": agent_id})
    
    def is_agent_starred(self, agent_id: str) -> bool:
        """Check if agent is starred."""
        with self._lock:
            return agent_id in self._state['starred_agents']
    
    def get_starred_agents(self) -> Set[str]:
        """Get all starred agent IDs."""
        with self._lock:
            return self._state['starred_agents'].copy()
    
    # Starred projects management
    def star_project(self, project_id: str):
        """Star a project."""
        with self._lock:
            self._state['starred_projects'].add(project_id)
            self._save_state()
            
            logger.info(f"Project starred: {project_id}", 
                       extra={"operation": "state.star_project", "project_id": project_id})
    
    def unstar_project(self, project_id: str):
        """Unstar a project."""
        with self._lock:
            self._state['starred_projects'].discard(project_id)
            self._save_state()
            
            logger.info(f"Project unstarred: {project_id}", 
                       extra={"operation": "state.unstar_project", "project_id": project_id})
    
    def is_project_starred(self, project_id: str) -> bool:
        """Check if project is starred."""
        with self._lock:
            return project_id in self._state['starred_projects']
    
    def get_starred_projects(self) -> Set[str]:
        """Get all starred project IDs."""
        with self._lock:
            return self._state['starred_projects'].copy()
    
    # Notifications management
    def add_notification(self, message: str, notification_type: str = "info", data: Optional[Dict] = None):
        """Add a notification."""
        with self._lock:
            notification = {
                'id': f"notif_{int(time.time() * 1000)}",
                'message': message,
                'type': notification_type,
                'timestamp': datetime.now().isoformat(),
                'data': data or {},
                'read': False,
            }
            
            self._state['notifications'].append(notification)
            
            # Keep only last N notifications
            max_notifications = self._state['preferences'].get('max_notifications', 100)
            if len(self._state['notifications']) > max_notifications:
                self._state['notifications'] = self._state['notifications'][-max_notifications:]
            
            self._save_state()
            
            logger.info(f"Notification added: {message}", 
                       extra={"operation": "state.add_notification", "type": notification_type})
            
            return notification['id']
    
    def mark_notification_read(self, notification_id: str):
        """Mark notification as read."""
        with self._lock:
            for notification in self._state['notifications']:
                if notification['id'] == notification_id:
                    notification['read'] = True
                    self._save_state()
                    break
    
    def get_notifications(self, unread_only: bool = False) -> List[Dict]:
        """Get notifications."""
        with self._lock:
            notifications = self._state['notifications'].copy()
            if unread_only:
                notifications = [n for n in notifications if not n.get('read', False)]
            return notifications
    
    def clear_notifications(self):
        """Clear all notifications."""
        with self._lock:
            self._state['notifications'] = []
            self._save_state()
            
            logger.info("Notifications cleared", extra={"operation": "state.clear_notifications"})
    
    # Preferences management
    def get_preference(self, key: str, default=None):
        """Get preference value."""
        with self._lock:
            return self._state['preferences'].get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """Set preference value."""
        with self._lock:
            self._state['preferences'][key] = value
            self._save_state()
            
            logger.debug(f"Preference updated: {key} = {value}", 
                        extra={"operation": "state.set_preference", "key": key})
    
    # Cache management
    def get_cache(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if expired
            cache_type = key.split('_')[0] if '_' in key else 'default'
            ttl = self._cache_ttl.get(cache_type, 300)  # Default 5 minutes
            
            if time.time() - self._cache_timestamps.get(key, 0) > ttl:
                # Expired, remove from cache
                del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
                return None
            
            return self._cache[key]
    
    def set_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value."""
        with self._lock:
            self._cache[key] = value
            self._cache_timestamps[key] = time.time()
            
            # Periodically save cache (every 10 cache operations)
            if len(self._cache) % 10 == 0:
                self._save_cache()
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        with self._lock:
            if pattern is None:
                # Clear all cache
                self._cache.clear()
                self._cache_timestamps.clear()
                logger.info("All cache invalidated", extra={"operation": "cache.invalidate_all"})
            else:
                # Clear matching entries
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self._cache[key]
                    if key in self._cache_timestamps:
                        del self._cache_timestamps[key]
                
                logger.info(f"Cache invalidated for pattern: {pattern}", 
                           extra={"operation": "cache.invalidate_pattern", "pattern": pattern, "count": len(keys_to_remove)})
    
    # Follow-up rules management
    def add_follow_up_rule(self, agent_id: str, query: str, conditions: Optional[Dict] = None):
        """Add follow-up rule for an agent."""
        with self._lock:
            if 'follow_up_rules' not in self._state:
                self._state['follow_up_rules'] = {}
            
            self._state['follow_up_rules'][agent_id] = {
                'query': query,
                'conditions': conditions or {'on_completion': True},
                'created_at': datetime.now().isoformat(),
                'executed': False,
            }
            
            self._save_state()
            
            logger.info(f"Follow-up rule added for agent: {agent_id}", 
                       extra={"operation": "state.add_followup", "agent_id": agent_id})
    
    def get_follow_up_rules(self, agent_id: Optional[str] = None) -> Dict:
        """Get follow-up rules."""
        with self._lock:
            rules = self._state.get('follow_up_rules', {})
            if agent_id:
                return {agent_id: rules.get(agent_id)} if agent_id in rules else {}
            return rules.copy()
    
    def mark_follow_up_executed(self, agent_id: str):
        """Mark follow-up rule as executed."""
        with self._lock:
            if agent_id in self._state.get('follow_up_rules', {}):
                self._state['follow_up_rules'][agent_id]['executed'] = True
                self._state['follow_up_rules'][agent_id]['executed_at'] = datetime.now().isoformat()
                self._save_state()
    
    # Cleanup methods
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
        
        with self._lock:
            # Clean old notifications
            original_count = len(self._state['notifications'])
            self._state['notifications'] = [
                n for n in self._state['notifications']
                if datetime.fromisoformat(n['timestamp']).timestamp() > cutoff_time
            ]
            
            # Clean old cache entries
            cache_keys_to_remove = []
            for key, timestamp in self._cache_timestamps.items():
                if timestamp < cutoff_time:
                    cache_keys_to_remove.append(key)
            
            for key in cache_keys_to_remove:
                del self._cache[key]
                del self._cache_timestamps[key]
            
            self._save_state()
            self._save_cache()
            
            logger.info(f"Cleanup completed: removed {original_count - len(self._state['notifications'])} notifications, {len(cache_keys_to_remove)} cache entries", 
                       extra={"operation": "state.cleanup", "days": days})


# Global state manager instance
_state_manager = None
_state_manager_lock = threading.Lock()


def get_state_manager() -> StateManager:
    """Get global state manager instance (singleton)."""
    global _state_manager
    
    if _state_manager is None:
        with _state_manager_lock:
            if _state_manager is None:
                _state_manager = StateManager()
    
    return _state_manager

