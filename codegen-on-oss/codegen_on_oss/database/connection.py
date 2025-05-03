"""
Database Connection Module

This module provides functionality for connecting to the database and managing sessions.
It includes configuration settings and session factories.
"""

import os
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen_on_oss.database.models import Base

class DatabaseSettings(BaseSettings):
    """Database connection settings."""
    model_config = SettingsConfigDict(env_prefix="DB_")
    
    dialect: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"  # noqa: S105
    database: str = "codegen_analysis"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    @computed_field
    def url(self) -> str:
        """Get the database connection URL."""
        return f"{self.dialect}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class DatabaseManager:
    """
    Database manager for handling connections and sessions.
    
    This class provides methods for creating and managing database connections,
    creating tables, and obtaining session factories.
    """
    
    def __init__(self, settings: Optional[DatabaseSettings] = None):
        """
        Initialize the database manager.
        
        Args:
            settings: Optional database settings. If not provided, default settings will be used.
        """
        self.settings = settings or DatabaseSettings()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _create_engine(self):
        """Create a SQLAlchemy engine with the configured settings."""
        return create_engine(
            self.settings.url,
            poolclass=QueuePool,
            pool_size=self.settings.pool_size,
            max_overflow=self.settings.max_overflow,
            pool_timeout=self.settings.pool_timeout,
            pool_recycle=self.settings.pool_recycle,
            echo=self.settings.echo
        )
    
    def create_tables(self):
        """Create all tables defined in the models."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables defined in the models."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        This context manager ensures that the session is properly closed and
        committed or rolled back as appropriate.
        
        Yields:
            A SQLAlchemy session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Create a global database manager instance
db_manager = DatabaseManager()

def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    This function is intended to be used as a dependency in FastAPI endpoints.
    
    Yields:
        A SQLAlchemy session
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
"""

