"""
Unified Storage Manager

Simple storage manager following KISS principles. Provides basic storage
capabilities with in-memory implementation and plans for future expansion.

This implementation focuses on simplicity and functionality over complexity,
following the YAGNI principle by implementing only what's needed now.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedStorageManager:
    """
    Simple unified storage manager for session data and orchestration state.
    
    Currently implements in-memory storage with plans for future expansion
    to persistent storage backends as needed.
    """
    
    def __init__(self):
        """Initialize the unified storage manager."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # In-memory storage (simple implementation following KISS)
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.orchestration_state: Dict[str, Any] = {}
        
        # Storage statistics
        self.storage_stats = {
            "sessions_stored": 0,
            "state_updates": 0,
            "total_operations": 0
        }
        
        self.logger.info("Unified Storage Manager initialized")
    
    async def initialize(self) -> None:
        """Initialize the storage manager."""
        try:
            # For now, just log initialization
            # Future: Initialize SQLite, Redis connections, etc.
            
            self.logger.info("Unified Storage Manager initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize storage manager: {e}")
            raise
    
    async def store_session_data(
        self, 
        session_id: str, 
        session_data: Dict[str, Any]
    ) -> None:
        """
        Store session data.
        
        Args:
            session_id: Unique session identifier
            session_data: Session data to store
        """
        try:
            self.session_data[session_id] = {
                **session_data,
                "stored_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            self.storage_stats["sessions_stored"] += 1
            self.storage_stats["total_operations"] += 1
            
            self.logger.debug(f"Stored session data for session: {session_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store session data for {session_id}: {e}")
            raise
    
    async def load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        try:
            session_data = self.session_data.get(session_id)
            
            self.storage_stats["total_operations"] += 1
            
            if session_data:
                self.logger.debug(f"Loaded session data for session: {session_id}")
            else:
                self.logger.debug(f"No session data found for session: {session_id}")
            
            return session_data
            
        except Exception as e:
            self.logger.error(f"Failed to load session data for {session_id}: {e}")
            return None
    
    async def update_session_data(
        self, 
        session_id: str, 
        updates: Dict[str, Any]
    ) -> None:
        """
        Update existing session data.
        
        Args:
            session_id: Session identifier
            updates: Updates to apply to session data
        """
        try:
            if session_id in self.session_data:
                self.session_data[session_id].update(updates)
                self.session_data[session_id]["updated_at"] = datetime.now()
                
                self.storage_stats["total_operations"] += 1
                
                self.logger.debug(f"Updated session data for session: {session_id}")
            else:
                self.logger.warning(f"Attempted to update non-existent session: {session_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to update session data for {session_id}: {e}")
            raise
    
    async def delete_session_data(self, session_id: str) -> None:
        """
        Delete session data.
        
        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self.session_data:
                del self.session_data[session_id]
                
                self.storage_stats["total_operations"] += 1
                
                self.logger.debug(f"Deleted session data for session: {session_id}")
            else:
                self.logger.warning(f"Attempted to delete non-existent session: {session_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to delete session data for {session_id}: {e}")
            raise
    
    async def store_orchestration_state(
        self, 
        key: str, 
        state_data: Dict[str, Any]
    ) -> None:
        """
        Store orchestration state data.
        
        Args:
            key: State key
            state_data: State data to store
        """
        try:
            self.orchestration_state[key] = {
                **state_data,
                "stored_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            self.storage_stats["state_updates"] += 1
            self.storage_stats["total_operations"] += 1
            
            self.logger.debug(f"Stored orchestration state for key: {key}")
            
        except Exception as e:
            self.logger.error(f"Failed to store orchestration state for {key}: {e}")
            raise
    
    async def load_orchestration_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load orchestration state data.
        
        Args:
            key: State key
            
        Returns:
            State data or None if not found
        """
        try:
            state_data = self.orchestration_state.get(key)
            
            self.storage_stats["total_operations"] += 1
            
            if state_data:
                self.logger.debug(f"Loaded orchestration state for key: {key}")
            else:
                self.logger.debug(f"No orchestration state found for key: {key}")
            
            return state_data
            
        except Exception as e:
            self.logger.error(f"Failed to load orchestration state for {key}: {e}")
            return None
    
    async def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all stored session data.
        
        Returns:
            Dictionary of all session data
        """
        try:
            self.storage_stats["total_operations"] += 1
            return self.session_data.copy()
            
        except Exception as e:
            self.logger.error(f"Failed to get all sessions: {e}")
            return {}
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics
        """
        return {
            **self.storage_stats,
            "total_sessions": len(self.session_data),
            "total_state_keys": len(self.orchestration_state),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old session data.
        
        Args:
            max_age_hours: Maximum age of sessions to keep in hours
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            sessions_to_delete = []
            
            for session_id, session_data in self.session_data.items():
                stored_at = session_data.get("stored_at")
                if stored_at and stored_at.timestamp() < cutoff_time:
                    sessions_to_delete.append(session_id)
            
            # Delete old sessions
            for session_id in sessions_to_delete:
                del self.session_data[session_id]
            
            if sessions_to_delete:
                self.logger.info(f"Cleaned up {len(sessions_to_delete)} old sessions")
            
            return len(sessions_to_delete)
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old sessions: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the storage manager."""
        try:
            # Simple health check - verify storage is accessible
            test_key = "health_check_test"
            test_data = {"test": True, "timestamp": datetime.now().isoformat()}
            
            # Test session storage
            await self.store_session_data(test_key, test_data)
            loaded_data = await self.load_session_data(test_key)
            await self.delete_session_data(test_key)
            
            # Test orchestration state storage
            await self.store_orchestration_state(test_key, test_data)
            loaded_state = await self.load_orchestration_state(test_key)
            
            # Verify operations worked
            storage_healthy = (
                loaded_data is not None and 
                loaded_state is not None and
                loaded_data.get("test") is True and
                loaded_state.get("test") is True
            )
            
            return {
                "status": "healthy" if storage_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "storage_stats": await self.get_storage_stats(),
                "test_operations": "passed" if storage_healthy else "failed"
            }
            
        except Exception as e:
            self.logger.error(f"Storage health check failed: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the storage manager."""
        self.logger.info("Shutting down Unified Storage Manager")
        
        try:
            # For in-memory storage, just clear data
            # Future: Close database connections, flush caches, etc.
            
            session_count = len(self.session_data)
            state_count = len(self.orchestration_state)
            
            self.session_data.clear()
            self.orchestration_state.clear()
            
            self.logger.info(
                f"Unified Storage Manager shutdown complete. "
                f"Cleared {session_count} sessions and {state_count} state entries."
            )
            
        except Exception as e:
            self.logger.error(f"Error during storage manager shutdown: {e}")
            raise
