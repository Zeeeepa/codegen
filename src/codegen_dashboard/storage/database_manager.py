"""
Database Manager for the Codegen Dashboard.

Handles local SQLite database for storing dashboard data including
agent runs, starred items, notifications, and user preferences.
"""

import sqlite3
import logging
import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager


class DatabaseManager:
    """
    Manages the local SQLite database for dashboard data.
    
    Provides methods for:
    - Database initialization and schema management
    - Agent run data storage and retrieval
    - Starred items management
    - Notification history
    - User preferences and settings
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the database manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database file location
        db_dir = os.path.expanduser("~/.codegen/dashboard")
        os.makedirs(db_dir, exist_ok=True)
        self.db_path = os.path.join(db_dir, "dashboard.db")
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Agent runs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS agent_runs (
                        id INTEGER PRIMARY KEY,
                        status TEXT NOT NULL,
                        result TEXT,
                        web_url TEXT,
                        created_at TIMESTAMP NOT NULL,
                        last_updated TIMESTAMP NOT NULL,
                        is_starred BOOLEAN DEFAULT FALSE,
                        follow_up_prompt TEXT,
                        auto_follow_up BOOLEAN DEFAULT FALSE,
                        metadata TEXT  -- JSON for additional data
                    )
                ''')
                
                # Projects table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        is_starred BOOLEAN DEFAULT FALSE,
                        pr_monitoring_enabled BOOLEAN DEFAULT FALSE,
                        validation_gates TEXT,  -- JSON array
                        last_pr_check TIMESTAMP,
                        metadata TEXT  -- JSON for additional data
                    )
                ''')
                
                # Notifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS notifications (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        message TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        is_read BOOLEAN DEFAULT FALSE,
                        related_agent_run_id INTEGER,
                        related_project_id INTEGER,
                        metadata TEXT  -- JSON for additional data
                    )
                ''')
                
                # User preferences table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                ''')
                
                # Workflow templates table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS workflow_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        template_data TEXT NOT NULL,  -- JSON
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                ''')
                
                # PRD documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS prd_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        project_id INTEGER,
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_runs_starred ON agent_runs(is_starred)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_starred ON projects(is_starred)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def save_agent_run(self, agent_run_data: Dict[str, Any]) -> bool:
        """Save or update an agent run."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if agent run exists
                cursor.execute('SELECT id FROM agent_runs WHERE id = ?', (agent_run_data['id'],))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing
                    cursor.execute('''
                        UPDATE agent_runs 
                        SET status = ?, result = ?, web_url = ?, last_updated = ?,
                            metadata = ?
                        WHERE id = ?
                    ''', (
                        agent_run_data['status'],
                        agent_run_data.get('result'),
                        agent_run_data.get('web_url'),
                        datetime.now(),
                        json.dumps(agent_run_data.get('metadata', {})),
                        agent_run_data['id']
                    ))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO agent_runs 
                        (id, status, result, web_url, created_at, last_updated, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        agent_run_data['id'],
                        agent_run_data['status'],
                        agent_run_data.get('result'),
                        agent_run_data.get('web_url'),
                        datetime.fromisoformat(agent_run_data['created_at']) if agent_run_data.get('created_at') else datetime.now(),
                        datetime.now(),
                        json.dumps(agent_run_data.get('metadata', {}))
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save agent run: {e}")
            return False
    
    def get_agent_runs(self, limit: int = 50, offset: int = 0, 
                      status_filter: Optional[str] = None,
                      starred_only: bool = False) -> List[Dict[str, Any]]:
        """Get agent runs with optional filtering."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM agent_runs WHERE 1=1'
                params = []
                
                if status_filter:
                    query += ' AND status = ?'
                    params.append(status_filter)
                
                if starred_only:
                    query += ' AND is_starred = TRUE'
                
                query += ' ORDER BY last_updated DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get agent runs: {e}")
            return []
    
    def star_agent_run(self, agent_run_id: int, starred: bool = True) -> bool:
        """Star or unstar an agent run."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE agent_runs SET is_starred = ? WHERE id = ?',
                    (starred, agent_run_id)
                )
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to star agent run: {e}")
            return False
    
    def set_follow_up_prompt(self, agent_run_id: int, prompt: str, auto_follow_up: bool = False) -> bool:
        """Set follow-up prompt for an agent run."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE agent_runs 
                    SET follow_up_prompt = ?, auto_follow_up = ?
                    WHERE id = ?
                ''', (prompt, auto_follow_up, agent_run_id))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to set follow-up prompt: {e}")
            return False
    
    def save_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Save a notification."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO notifications
                    (id, type, title, message, created_at, is_read, 
                     related_agent_run_id, related_project_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification_data['id'],
                    notification_data['type'],
                    notification_data['title'],
                    notification_data['message'],
                    notification_data['created_at'],
                    notification_data.get('is_read', False),
                    notification_data.get('related_agent_run_id'),
                    notification_data.get('related_project_id'),
                    json.dumps(notification_data.get('metadata', {}))
                ))
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save notification: {e}")
            return False
    
    def get_notifications(self, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get notifications."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM notifications'
                params = []
                
                if unread_only:
                    query += ' WHERE is_read = FALSE'
                
                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get notifications: {e}")
            return []
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE notifications SET is_read = TRUE WHERE id = ?',
                    (notification_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def save_user_preference(self, key: str, value: Any) -> bool:
        """Save a user preference."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO user_preferences (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, json.dumps(value), datetime.now()))
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save user preference: {e}")
            return False
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM user_preferences WHERE key = ?', (key,))
                row = cursor.fetchone()
                
                if row:
                    return json.loads(row['value'])
                return default
                
        except Exception as e:
            self.logger.error(f"Failed to get user preference: {e}")
            return default
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """Clean up old data to keep database size manageable."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cutoff_date = datetime.now().replace(day=datetime.now().day - days)
                
                # Clean up old notifications
                cursor.execute(
                    'DELETE FROM notifications WHERE created_at < ? AND is_read = TRUE',
                    (cutoff_date,)
                )
                
                # Clean up old agent runs (keep starred ones)
                cursor.execute(
                    'DELETE FROM agent_runs WHERE last_updated < ? AND is_starred = FALSE',
                    (cutoff_date,)
                )
                
                conn.commit()
                self.logger.info(f"Cleaned up data older than {days} days")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['agent_runs', 'projects', 'notifications', 'user_preferences']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[table] = cursor.fetchone()[0]
                
                # Additional stats
                cursor.execute('SELECT COUNT(*) FROM agent_runs WHERE is_starred = TRUE')
                stats['starred_agent_runs'] = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM notifications WHERE is_read = FALSE')
                stats['unread_notifications'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {}
    
    def close(self):
        """Close database connections and cleanup."""
        self.logger.info("Database manager closed")
