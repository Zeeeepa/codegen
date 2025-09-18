"""Local database storage for Codegen Dashboard."""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from codegen.cli.auth.constants import CONFIG_DIR
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class DashboardDB:
    """SQLite-based local storage for dashboard data."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path(CONFIG_DIR) / "dashboard.db")
        self._lock = threading.Lock()
        self._ensure_config_dir()
        self._init_database()
        
        logger.info(f"Dashboard database initialized: {self.db_path}", 
                   extra={"operation": "db.init", "db_path": self.db_path})
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                
                # Starred agents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS starred_agents (
                        agent_id TEXT PRIMARY KEY,
                        starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Starred projects table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS starred_projects (
                        project_id TEXT PRIMARY KEY,
                        project_name TEXT,
                        starred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata TEXT DEFAULT '{}'
                    )
                ''')
                
                # Notifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        message TEXT NOT NULL,
                        type TEXT DEFAULT 'info',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        read_at TIMESTAMP NULL,
                        data TEXT DEFAULT '{}'
                    )
                ''')
                
                # Preferences table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.debug("Database schema initialized", extra={"operation": "db.schema_init"})
                
            finally:
                conn.close()
    
    def _execute_query(self, query: str, params: Tuple = (), fetch: bool = False) -> Any:
        """Execute SQL query with proper error handling."""
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetch:
                    if 'SELECT' in query.upper():
                        return cursor.fetchall()
                    else:
                        return cursor.fetchone()
                else:
                    conn.commit()
                    return cursor.rowcount
                    
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}", extra={"operation": "db.error", "query": query[:100]})
                conn.rollback()
                raise
            finally:
                conn.close()
    
    # Starred agents methods
    def star_agent(self, agent_id: str, metadata: Optional[Dict] = None) -> bool:
        """Star an agent run."""
        try:
            metadata_json = json.dumps(metadata or {})
            self._execute_query(
                "INSERT OR REPLACE INTO starred_agents (agent_id, metadata, starred_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (agent_id, metadata_json)
            )
            logger.info(f"Agent starred: {agent_id}", extra={"operation": "db.star_agent", "agent_id": agent_id})
            return True
        except Exception as e:
            logger.error(f"Failed to star agent {agent_id}: {e}", extra={"operation": "db.star_agent_error"})
            return False
    
    def unstar_agent(self, agent_id: str) -> bool:
        """Unstar an agent run."""
        try:
            rows_affected = self._execute_query("DELETE FROM starred_agents WHERE agent_id = ?", (agent_id,))
            logger.info(f"Agent unstarred: {agent_id}", extra={"operation": "db.unstar_agent", "agent_id": agent_id})
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to unstar agent {agent_id}: {e}", extra={"operation": "db.unstar_agent_error"})
            return False
    
    def is_agent_starred(self, agent_id: str) -> bool:
        """Check if agent is starred."""
        try:
            result = self._execute_query("SELECT 1 FROM starred_agents WHERE agent_id = ?", (agent_id,), fetch=True)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Failed to check if agent {agent_id} is starred: {e}", extra={"operation": "db.check_starred_error"})
            return False
    
    def get_starred_agents(self) -> List[Dict]:
        """Get all starred agents."""
        try:
            rows = self._execute_query("SELECT * FROM starred_agents ORDER BY starred_at DESC", fetch=True)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get starred agents: {e}", extra={"operation": "db.get_starred_agents_error"})
            return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            stats = {}
            tables = ['starred_agents', 'starred_projects', 'notifications', 'preferences']
            
            for table in tables:
                rows = self._execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch=True)
                stats[table] = rows[0]['count'] if rows else 0
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}", extra={"operation": "db.get_stats_error"})
            return {}


# Global database instance
_dashboard_db = None
_db_lock = threading.Lock()


def get_dashboard_db() -> DashboardDB:
    """Get global dashboard database instance (singleton)."""
    global _dashboard_db
    
    if _dashboard_db is None:
        with _db_lock:
            if _dashboard_db is None:
                _dashboard_db = DashboardDB()
    
    return _dashboard_db

