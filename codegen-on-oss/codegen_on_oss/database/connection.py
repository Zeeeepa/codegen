"""
Database connection management for codegen-on-oss.

This module provides utilities for connecting to the database and managing sessions.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

from codegen_on_oss.database.models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database connection manager for codegen-on-oss.
    
    This class provides methods for connecting to the database, creating tables,
    and managing sessions.
    """
    
    def __init__(
        self, 
        connection_string: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False
    ):
        """
        Initialize the database manager.
        
        Args:
            connection_string: SQLAlchemy connection string. If None, will use the
                CODEGEN_DB_URL environment variable or default to SQLite.
            pool_size: Connection pool size.
            max_overflow: Maximum number of connections to create beyond pool_size.
            pool_timeout: Seconds to wait before giving up on getting a connection.
            pool_recycle: Seconds after which a connection is automatically recycled.
            echo: If True, log all SQL statements.
        """
        self.connection_string = connection_string or os.environ.get(
            'CODEGEN_DB_URL', 'sqlite:///codegen_on_oss.db'
        )
        self.engine = create_engine(
            self.connection_string,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=echo
        )
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self) -> None:
        """Create all tables defined in the models module."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all tables defined in the models module."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.session_scope() as session:
                session.add(some_object)
                session.add(some_other_object)
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error in database session: {e}")
            raise
        finally:
            session.close()
    
    def get_session(self) -> Session:
        """Get a new session."""
        return self.Session()
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string.
            params: Query parameters.
            
        Returns:
            Query result.
        """
        with self.session_scope() as session:
            result = session.execute(query, params or {})
            return result
    
    def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if the connection is healthy, False otherwise.
        """
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager

def initialize_db(connection_string: Optional[str] = None) -> DatabaseManager:
    """
    Initialize the database.
    
    Args:
        connection_string: SQLAlchemy connection string.
        
    Returns:
        DatabaseManager instance.
    """
    global db_manager
    db_manager = DatabaseManager(connection_string)
    db_manager.create_tables()
    return db_manager

