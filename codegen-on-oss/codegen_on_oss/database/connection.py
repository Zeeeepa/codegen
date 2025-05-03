"""
Database connection management for the codegen-on-oss system.

This module provides functions for creating and managing database connections,
sessions, and engine configuration.
"""

import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from codegen_on_oss.config import settings
from codegen_on_oss.database.models import Base

logger = logging.getLogger(__name__)

# Global engine instance
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.
    
    Returns:
        Engine: The SQLAlchemy engine instance
    """
    global _engine
    
    if _engine is None:
        logger.info(f"Creating database engine with URL: {settings.db_url_safe}")
        
        connect_args = {}
        if settings.db_url.startswith('sqlite'):
            connect_args = {"check_same_thread": False}
        
        _engine = create_engine(
            settings.db_url,
            echo=settings.db_echo,
            pool_pre_ping=True,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            connect_args=connect_args
        )
        
        # Set up SQLite optimizations if using SQLite
        if settings.db_url.startswith('sqlite'):
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Get or create the SQLAlchemy session factory.
    
    Returns:
        sessionmaker: The SQLAlchemy session factory
    """
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    
    return _session_factory


@contextmanager
def get_db_session() -> Session:
    """
    Get a database session using a context manager.
    
    Yields:
        Session: A SQLAlchemy session
        
    Example:
        ```python
        with get_db_session() as session:
            results = session.query(MyModel).all()
        ```
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def init_db(create_tables: bool = False) -> None:
    """
    Initialize the database connection and optionally create tables.
    
    Args:
        create_tables: Whether to create all tables defined in models
    """
    engine = get_engine()
    
    if create_tables:
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=engine)
    
    # Initialize session factory
    get_session_factory()
    
    logger.info("Database initialized successfully")


def get_db() -> Session:
    """
    Dependency for FastAPI to get a database session.
    
    Returns:
        Session: A SQLAlchemy session
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
    finally:
        session.close()

