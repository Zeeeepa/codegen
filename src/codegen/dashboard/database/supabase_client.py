"""Supabase client for dashboard database operations."""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import json

try:
    from supabase import create_client, Client
    from postgrest import APIError
except ImportError:
    # Graceful fallback if supabase is not installed
    Client = None
    APIError = Exception

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """Supabase client for dashboard database operations."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """Initialize Supabase client.
        
        Args:
            url: Supabase URL (defaults to SUPABASE_URL env var)
            key: Supabase anon key (defaults to SUPABASE_ANON_KEY env var)
        """
        if Client is None:
            raise ImportError("supabase-py is required for database operations. Install with: pip install supabase")
        
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required. Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables.")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized", extra={"url": self.url})
    
    async def health_check(self) -> bool:
        """Check if the database connection is healthy."""
        try:
            # Simple query to test connection
            result = self.client.table("agent_runs_starred").select("count", count="exact").limit(1).execute()
            return True
        except Exception as e:
            logger.error("Database health check failed", extra={"error": str(e)})
            return False
    
    # Agent Run Starred Operations
    async def star_agent_run(self, user_id: str, org_id: int, agent_run_id: int, metadata: Optional[Dict] = None) -> Dict:
        """Star an agent run for a user."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "agent_run_id": agent_run_id,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("agent_runs_starred").upsert(data).execute()
            logger.info("Agent run starred", extra={"user_id": user_id, "agent_run_id": agent_run_id})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to star agent run", extra={"error": str(e), "agent_run_id": agent_run_id})
            raise
    
    async def unstar_agent_run(self, user_id: str, org_id: int, agent_run_id: int) -> bool:
        """Unstar an agent run for a user."""
        try:
            result = self.client.table("agent_runs_starred").delete().eq("user_id", user_id).eq("org_id", org_id).eq("agent_run_id", agent_run_id).execute()
            logger.info("Agent run unstarred", extra={"user_id": user_id, "agent_run_id": agent_run_id})
            return len(result.data) > 0
        except Exception as e:
            logger.error("Failed to unstar agent run", extra={"error": str(e), "agent_run_id": agent_run_id})
            raise
    
    async def get_starred_agent_runs(self, user_id: str, org_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get starred agent runs for a user."""
        try:
            result = self.client.table("agent_runs_starred").select("*").eq("user_id", user_id).eq("org_id", org_id).order("updated_at", desc=True).limit(limit).offset(offset).execute()
            return result.data
        except Exception as e:
            logger.error("Failed to get starred agent runs", extra={"error": str(e), "user_id": user_id})
            raise
    
    async def is_agent_run_starred(self, user_id: str, org_id: int, agent_run_id: int) -> bool:
        """Check if an agent run is starred by a user."""
        try:
            result = self.client.table("agent_runs_starred").select("id").eq("user_id", user_id).eq("org_id", org_id).eq("agent_run_id", agent_run_id).limit(1).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error("Failed to check if agent run is starred", extra={"error": str(e), "agent_run_id": agent_run_id})
            return False
    
    # Project Starred Operations
    async def star_project(self, user_id: str, org_id: int, repo_name: str, metadata: Optional[Dict] = None) -> Dict:
        """Star a project for a user."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "repo_name": repo_name,
                "metadata": metadata or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("projects_starred").upsert(data).execute()
            logger.info("Project starred", extra={"user_id": user_id, "repo_name": repo_name})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to star project", extra={"error": str(e), "repo_name": repo_name})
            raise
    
    async def unstar_project(self, user_id: str, org_id: int, repo_name: str) -> bool:
        """Unstar a project for a user."""
        try:
            result = self.client.table("projects_starred").delete().eq("user_id", user_id).eq("org_id", org_id).eq("repo_name", repo_name).execute()
            logger.info("Project unstarred", extra={"user_id": user_id, "repo_name": repo_name})
            return len(result.data) > 0
        except Exception as e:
            logger.error("Failed to unstar project", extra={"error": str(e), "repo_name": repo_name})
            raise
    
    async def get_starred_projects(self, user_id: str, org_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get starred projects for a user."""
        try:
            result = self.client.table("projects_starred").select("*").eq("user_id", user_id).eq("org_id", org_id).order("updated_at", desc=True).limit(limit).offset(offset).execute()
            return result.data
        except Exception as e:
            logger.error("Failed to get starred projects", extra={"error": str(e), "user_id": user_id})
            raise
    
    # User Preferences Operations
    async def get_user_preferences(self, user_id: str, org_id: int) -> Dict:
        """Get user preferences."""
        try:
            result = self.client.table("user_preferences").select("*").eq("user_id", user_id).eq("org_id", org_id).limit(1).execute()
            if result.data:
                return result.data[0]["preferences"]
            return {}
        except Exception as e:
            logger.error("Failed to get user preferences", extra={"error": str(e), "user_id": user_id})
            return {}
    
    async def update_user_preferences(self, user_id: str, org_id: int, preferences: Dict) -> Dict:
        """Update user preferences."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "preferences": preferences,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("user_preferences").upsert(data).execute()
            logger.info("User preferences updated", extra={"user_id": user_id})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to update user preferences", extra={"error": str(e), "user_id": user_id})
            raise
    
    # Notification Operations
    async def create_notification(self, user_id: str, org_id: int, title: str, message: str, 
                                notification_type: str = "info", metadata: Optional[Dict] = None) -> Dict:
        """Create a notification for a user."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "title": title,
                "message": message,
                "type": notification_type,
                "metadata": metadata or {},
                "read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("notifications").insert(data).execute()
            logger.info("Notification created", extra={"user_id": user_id, "title": title})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to create notification", extra={"error": str(e), "user_id": user_id})
            raise
    
    async def get_notifications(self, user_id: str, org_id: int, unread_only: bool = False, 
                              limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get notifications for a user."""
        try:
            query = self.client.table("notifications").select("*").eq("user_id", user_id).eq("org_id", org_id)
            
            if unread_only:
                query = query.eq("read", False)
            
            result = query.order("created_at", desc=True).limit(limit).offset(offset).execute()
            return result.data
        except Exception as e:
            logger.error("Failed to get notifications", extra={"error": str(e), "user_id": user_id})
            raise
    
    async def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read."""
        try:
            result = self.client.table("notifications").update({"read": True, "read_at": datetime.now(timezone.utc).isoformat()}).eq("id", notification_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error("Failed to mark notification as read", extra={"error": str(e), "notification_id": notification_id})
            raise
    
    # Validation Gates Operations
    async def create_validation_gate(self, user_id: str, org_id: int, repo_name: str, 
                                   gate_config: Dict, metadata: Optional[Dict] = None) -> Dict:
        """Create a validation gate for a repository."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "repo_name": repo_name,
                "gate_config": gate_config,
                "metadata": metadata or {},
                "active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("validation_gates").insert(data).execute()
            logger.info("Validation gate created", extra={"user_id": user_id, "repo_name": repo_name})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to create validation gate", extra={"error": str(e), "repo_name": repo_name})
            raise
    
    async def get_validation_gates(self, user_id: str, org_id: int, repo_name: Optional[str] = None) -> List[Dict]:
        """Get validation gates for a user/organization."""
        try:
            query = self.client.table("validation_gates").select("*").eq("user_id", user_id).eq("org_id", org_id).eq("active", True)
            
            if repo_name:
                query = query.eq("repo_name", repo_name)
            
            result = query.order("created_at", desc=True).execute()
            return result.data
        except Exception as e:
            logger.error("Failed to get validation gates", extra={"error": str(e), "user_id": user_id})
            raise
    
    # Dashboard Session Operations
    async def create_dashboard_session(self, user_id: str, org_id: int, session_data: Dict) -> Dict:
        """Create a dashboard session."""
        try:
            data = {
                "user_id": user_id,
                "org_id": org_id,
                "session_data": session_data,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.client.table("dashboard_sessions").insert(data).execute()
            logger.info("Dashboard session created", extra={"user_id": user_id})
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error("Failed to create dashboard session", extra={"error": str(e), "user_id": user_id})
            raise
    
    async def update_session_activity(self, session_id: str, user_id: str) -> bool:
        """Update session last activity timestamp."""
        try:
            result = self.client.table("dashboard_sessions").update({"last_activity": datetime.now(timezone.utc).isoformat()}).eq("id", session_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error("Failed to update session activity", extra={"error": str(e), "session_id": session_id})
            return False
    
    # Utility Methods
    async def execute_raw_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a raw SQL query (use with caution)."""
        try:
            # Note: This would require RLS policies to be properly configured
            result = self.client.rpc("execute_sql", {"query": query, "params": params or {}}).execute()
            return result.data
        except Exception as e:
            logger.error("Failed to execute raw query", extra={"error": str(e)})
            raise
    
    async def get_table_stats(self, table_name: str) -> Dict:
        """Get basic statistics for a table."""
        try:
            result = self.client.table(table_name).select("*", count="exact").limit(1).execute()
            return {"count": result.count, "table": table_name}
        except Exception as e:
            logger.error("Failed to get table stats", extra={"error": str(e), "table": table_name})
            return {"count": 0, "table": table_name}


# Global instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get the global Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


def init_supabase_client(url: str, key: str) -> SupabaseClient:
    """Initialize the global Supabase client with custom credentials."""
    global _supabase_client
    _supabase_client = SupabaseClient(url, key)
    return _supabase_client
