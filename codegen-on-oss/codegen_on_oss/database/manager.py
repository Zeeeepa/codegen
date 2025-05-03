"""
Database Manager for Codegen-on-OSS

This module provides a database manager for handling database operations,
including connection management, session creation, and transaction handling.
"""

import os
import logging
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen_on_oss.database.models import Base

logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    dialect: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"  # noqa: S105
    database: str = "codegen_oss"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    echo: bool = False
    
    @property
    def url(self) -> str:
        """Get the database URL."""
        return f"{self.dialect}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseManager:
    """
    Database manager for handling database operations.
    
    This class provides methods for creating database sessions, executing
    transactions, and managing database connections.
    """
    
    def __init__(self, settings: Optional[DatabaseSettings] = None):
        """
        Initialize the database manager.
        
        Args:
            settings: Database connection settings. If None, default settings are used.
        """
        self.settings = settings or DatabaseSettings()
        self.engine = create_engine(
            self.settings.url,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            pool_timeout=self.settings.pool_timeout,
            pool_recycle=self.settings.pool_recycle,
            echo=self.settings.echo,
            poolclass=QueuePool
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # Set up connection pool logging
        if self.settings.echo:
            event.listen(self.engine, 'checkout', self._checkout_listener)
    
    def create_tables(self):
        """Create all tables defined in the models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all tables defined in the models."""
        Base.metadata.drop_all(self.engine)
        logger.info("Database tables dropped")
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        Yields:
            Session: A SQLAlchemy session.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction error: {e}")
            raise
        finally:
            session.close()
    
    def _checkout_listener(self, dbapi_connection, connection_record, connection_proxy):
        """Log when a connection is checked out from the pool."""
        logger.debug(f"Connection checkout: {id(dbapi_connection)}")


# Singleton instance of DatabaseManager
_db_manager: Optional[DatabaseManager] = None

def get_db_manager() -> DatabaseManager:
    """
    Get the singleton instance of DatabaseManager.
    
    Returns:
        DatabaseManager: The database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get a database session from the singleton DatabaseManager.
    
    Yields:
        Session: A SQLAlchemy session.
    """
    db_manager = get_db_manager()
    with db_manager.session_scope() as session:
        yield session

