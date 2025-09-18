"""
Session Manager - Unified Session Management Across Services

This module implements comprehensive session management that maintains user context
and state across all services in the orchestration layer. It provides persistent
session storage, context preservation, and cross-service state synchronization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import uuid

from codegen.orchestration.config.unified_config import UnifiedConfig

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"

@dataclass
class UserPreferences:
    """User preferences and settings."""
    preferred_services: List[str] = field(default_factory=list)
    default_timeout: int = 300
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {
        "email": True,
        "desktop": True,
        "in_app": True
    })
    ui_settings: Dict[str, Any] = field(default_factory=dict)
    rate_limit_preferences: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPreferences':
        """Create from dictionary."""
        return cls(**data)

@dataclass
class ServiceState:
    """State information for a specific service within a session."""
    service_name: str
    last_interaction: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    authentication_info: Dict[str, Any] = field(default_factory=dict)
    operation_history: List[str] = field(default_factory=list)  # Operation IDs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['last_interaction'] = self.last_interaction.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceState':
        """Create from dictionary."""
        data = data.copy()
        data['last_interaction'] = datetime.fromisoformat(data['last_interaction'])
        return cls(**data)

@dataclass
class UnifiedSession:
    """
    Unified session that maintains state across all services.
    
    This class represents a user session that can span multiple services
    and maintain context, preferences, and state information.
    """
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    status: SessionStatus = SessionStatus.ACTIVE
    
    # Context and state
    global_context: Dict[str, Any] = field(default_factory=dict)
    service_states: Dict[str, ServiceState] = field(default_factory=dict)
    preferences: UserPreferences = field(default_factory=UserPreferences)
    
    # Session metadata
    client_info: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Expiration settings
    idle_timeout: int = 3600  # 1 hour
    max_lifetime: int = 86400  # 24 hours
    
    def __post_init__(self):
        """Initialize computed fields."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        now = datetime.utcnow()
        
        # Check idle timeout
        idle_duration = (now - self.last_activity).total_seconds()
        if idle_duration > self.idle_timeout:
            return True
        
        # Check max lifetime
        total_duration = (now - self.created_at).total_seconds()
        if total_duration > self.max_lifetime:
            return True
        
        return False
    
    @property
    def time_until_expiry(self) -> int:
        """Get seconds until session expires."""
        now = datetime.utcnow()
        
        # Calculate time until idle timeout
        idle_duration = (now - self.last_activity).total_seconds()
        idle_remaining = max(0, self.idle_timeout - idle_duration)
        
        # Calculate time until max lifetime
        total_duration = (now - self.created_at).total_seconds()
        lifetime_remaining = max(0, self.max_lifetime - total_duration)
        
        return int(min(idle_remaining, lifetime_remaining))
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        if self.status == SessionStatus.IDLE:
            self.status = SessionStatus.ACTIVE
    
    def get_service_state(self, service_name: str) -> Optional[ServiceState]:
        """Get state for a specific service."""
        return self.service_states.get(service_name)
    
    def update_service_state(self, service_name: str, context: Dict[str, Any]) -> None:
        """Update state for a specific service."""
        if service_name not in self.service_states:
            self.service_states[service_name] = ServiceState(
                service_name=service_name,
                last_interaction=datetime.utcnow()
            )
        
        service_state = self.service_states[service_name]
        service_state.context.update(context)
        service_state.last_interaction = datetime.utcnow()
        self.update_activity()
    
    def add_operation_to_service(self, service_name: str, operation_id: str) -> None:
        """Add an operation ID to a service's history."""
        if service_name not in self.service_states:
            self.service_states[service_name] = ServiceState(
                service_name=service_name,
                last_interaction=datetime.utcnow()
            )
        
        service_state = self.service_states[service_name]
        service_state.operation_history.append(operation_id)
        
        # Keep only last 100 operations per service
        if len(service_state.operation_history) > 100:
            service_state.operation_history = service_state.operation_history[-100:]
        
        service_state.last_interaction = datetime.utcnow()
        self.update_activity()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        data = {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'status': self.status.value,
            'global_context': self.global_context,
            'service_states': {
                name: state.to_dict() 
                for name, state in self.service_states.items()
            },
            'preferences': self.preferences.to_dict(),
            'client_info': self.client_info,
            'tags': self.tags,
            'metadata': self.metadata,
            'idle_timeout': self.idle_timeout,
            'max_lifetime': self.max_lifetime
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedSession':
        """Create session from dictionary."""
        data = data.copy()
        
        # Parse datetime fields
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        data['status'] = SessionStatus(data['status'])
        
        # Parse service states
        service_states = {}
        for name, state_data in data.get('service_states', {}).items():
            service_states[name] = ServiceState.from_dict(state_data)
        data['service_states'] = service_states
        
        # Parse preferences
        if 'preferences' in data:
            data['preferences'] = UserPreferences.from_dict(data['preferences'])
        
        return cls(**data)

class SessionManager:
    """
    Unified session manager for the orchestration layer.
    
    This class manages user sessions across all services, providing persistent
    storage, context preservation, and automatic cleanup of expired sessions.
    """
    
    def __init__(self, config: UnifiedConfig):
        """Initialize the session manager."""
        self.config = config
        self._sessions: Dict[str, UnifiedSession] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self._lock = threading.RLock()
        self._initialized = False
        
        # Configuration
        self._storage_backend = config.get_session_storage_backend()
        self._cleanup_interval = config.get_session_cleanup_interval()
        self._default_idle_timeout = config.get_default_session_idle_timeout()
        self._default_max_lifetime = config.get_default_session_max_lifetime()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        logger.info("SessionManager initialized")
    
    async def initialize(self) -> None:
        """Initialize the session manager."""
        with self._lock:
            if self._initialized:
                return
            
            logger.info("Initializing session manager...")
            
            # Load existing sessions from storage
            await self._load_sessions_from_storage()
            
            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self._initialized = True
            logger.info("Session manager initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the session manager."""
        logger.info("Shutting down session manager...")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for cleanup task to complete
        if self._cleanup_task:
            await self._cleanup_task
        
        # Save all sessions to storage
        await self._save_sessions_to_storage()
        
        with self._lock:
            self._sessions.clear()
            self._user_sessions.clear()
            self._initialized = False
        
        logger.info("Session manager shutdown complete")
    
    async def create_session(
        self,
        user_id: str,
        client_info: Optional[Dict[str, str]] = None,
        preferences: Optional[UserPreferences] = None,
        idle_timeout: Optional[int] = None,
        max_lifetime: Optional[int] = None
    ) -> UnifiedSession:
        """
        Create a new session for a user.
        
        Args:
            user_id: User identifier
            client_info: Optional client information
            preferences: Optional user preferences
            idle_timeout: Optional custom idle timeout
            max_lifetime: Optional custom max lifetime
            
        Returns:
            New UnifiedSession instance
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = UnifiedSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now,
            client_info=client_info or {},
            preferences=preferences or UserPreferences(),
            idle_timeout=idle_timeout or self._default_idle_timeout,
            max_lifetime=max_lifetime or self._default_max_lifetime
        )
        
        with self._lock:
            self._sessions[session_id] = session
            
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[UnifiedSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            UnifiedSession if found and not expired, None otherwise
        """
        with self._lock:
            session = self._sessions.get(session_id)
            
            if not session:
                return None
            
            # Check if session is expired
            if session.is_expired:
                await self._expire_session(session_id)
                return None
            
            # Update activity
            session.update_activity()
            return session
    
    async def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: str,
        **kwargs
    ) -> UnifiedSession:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            user_id: User identifier
            **kwargs: Additional arguments for session creation
            
        Returns:
            UnifiedSession instance
        """
        if session_id:
            session = await self.get_session(session_id)
            if session:
                return session
        
        # Create new session
        return await self.create_session(user_id, **kwargs)
    
    async def update_session_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        service_name: Optional[str] = None
    ) -> bool:
        """
        Update session context.
        
        Args:
            session_id: Session identifier
            context: Context data to update
            service_name: Optional service name for service-specific context
            
        Returns:
            True if update was successful, False if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        if service_name:
            session.update_service_state(service_name, context)
        else:
            session.global_context.update(context)
            session.update_activity()
        
        logger.debug(f"Updated context for session {session_id}")
        return True
    
    async def add_operation_to_session(
        self,
        session_id: str,
        operation_id: str,
        service_name: str
    ) -> bool:
        """
        Add an operation to a session's history.
        
        Args:
            session_id: Session identifier
            operation_id: Operation identifier
            service_name: Service that executed the operation
            
        Returns:
            True if addition was successful, False if session not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.add_operation_to_service(service_name, operation_id)
        logger.debug(f"Added operation {operation_id} to session {session_id}")
        return True
    
    async def get_user_sessions(self, user_id: str) -> List[UnifiedSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of active UnifiedSession instances
        """
        with self._lock:
            session_ids = self._user_sessions.get(user_id, [])
            sessions = []
            
            for session_id in session_ids[:]:  # Copy list to avoid modification during iteration
                session = self._sessions.get(session_id)
                if session and not session.is_expired:
                    sessions.append(session)
                else:
                    # Clean up expired or missing session
                    self._user_sessions[user_id].remove(session_id)
                    if session_id in self._sessions:
                        del self._sessions[session_id]
            
            return sessions
    
    async def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if termination was successful, False if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.status = SessionStatus.TERMINATED
            
            # Remove from user sessions
            user_sessions = self._user_sessions.get(session.user_id, [])
            if session_id in user_sessions:
                user_sessions.remove(session_id)
            
            # Remove from active sessions
            del self._sessions[session_id]
            
            logger.info(f"Terminated session {session_id}")
            return True
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = []
        
        with self._lock:
            for session_id, session in list(self._sessions.items()):
                if session.is_expired:
                    expired_sessions.append(session_id)
        
        # Clean up expired sessions
        for session_id in expired_sessions:
            await self._expire_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    async def get_session_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive session metrics.
        
        Returns:
            Dictionary of session metrics
        """
        with self._lock:
            total_sessions = len(self._sessions)
            active_sessions = len([s for s in self._sessions.values() if s.status == SessionStatus.ACTIVE])
            idle_sessions = len([s for s in self._sessions.values() if s.status == SessionStatus.IDLE])
            
            # User statistics
            total_users = len(self._user_sessions)
            users_with_multiple_sessions = len([
                user_id for user_id, sessions in self._user_sessions.items()
                if len(sessions) > 1
            ])
            
            # Session age statistics
            now = datetime.utcnow()
            session_ages = [
                (now - session.created_at).total_seconds()
                for session in self._sessions.values()
            ]
            
            avg_session_age = sum(session_ages) / len(session_ages) if session_ages else 0
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "idle_sessions": idle_sessions,
                "total_users": total_users,
                "users_with_multiple_sessions": users_with_multiple_sessions,
                "average_session_age_seconds": avg_session_age,
                "storage_backend": self._storage_backend
            }
    
    # Private methods
    
    async def _expire_session(self, session_id: str) -> None:
        """Mark a session as expired and clean it up."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = SessionStatus.EXPIRED
                
                # Remove from user sessions
                user_sessions = self._user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
                
                # Remove from active sessions
                del self._sessions[session_id]
                
                logger.debug(f"Expired session {session_id}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cleaning up expired sessions."""
        while not self._shutdown_event.is_set():
            try:
                await self.cleanup_expired_sessions()
                await asyncio.sleep(self._cleanup_interval)
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(self._cleanup_interval * 2)  # Back off on error
    
    async def _load_sessions_from_storage(self) -> None:
        """Load sessions from persistent storage."""
        # TODO: Implement persistent storage loading
        # This would load sessions from SQLite, Redis, or file storage
        # depending on the configured storage backend
        logger.debug("Loading sessions from storage (not implemented)")
    
    async def _save_sessions_to_storage(self) -> None:
        """Save sessions to persistent storage."""
        # TODO: Implement persistent storage saving
        # This would save sessions to SQLite, Redis, or file storage
        # depending on the configured storage backend
        logger.debug("Saving sessions to storage (not implemented)")

