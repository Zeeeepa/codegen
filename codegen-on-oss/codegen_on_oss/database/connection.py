"""
Database connection management for the codegen-on-oss system.

This module provides utilities for creating and managing database connections.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from codegen_on_oss.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager."""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the database manager.

        Args:
            db_url: Database URL. If not provided, it will be read from the environment.
        """
        self.db_url = db_url or os.environ.get(
            "CODEGEN_DB_URL", "sqlite:///./codegen_analysis.db"
        )
        self.engine: Optional[Engine] = None
        self.Session = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize the database engine and session factory."""
        try:
            # Create engine with appropriate configuration based on database type
            if self.db_url.startswith("sqlite"):
                # SQLite-specific configuration
                self.engine = create_engine(
                    self.db_url,
                    connect_args={"check_same_thread": False},
                    echo=False,
                )
            else:
                # PostgreSQL or other database configuration
                self.engine = create_engine(
                    self.db_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                    pool_recycle=1800,
                    echo=False,
                )

            # Create session factory
            self.Session = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            logger.info(f"Database connection initialized: {self.db_url}")
        except Exception as e:
            logger.error(f"Error initializing database connection: {e}")
            raise

    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        if not self.engine:
            self._initialize()

        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise

    def drop_tables(self) -> None:
        """Drop all tables defined in the models."""
        if not self.engine:
            self._initialize()

        try:
            Base.metadata.drop_all(self.engine)
            logger.info("Database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Yields:
            Session: Database session
        """
        if not self.Session:
            self._initialize()

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


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Session:
    """
    Get a database session.

    Returns:
        Session: Database session
    """
    session = db_manager.Session()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    db_manager.create_tables()

