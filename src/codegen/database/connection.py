"""
Database connection management for Codegen.

Provides connection pooling, session management, and database configuration.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
from urllib.parse import urlparse

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import QueuePool

from .models.base import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration management."""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.pool_size = int(os.getenv('DB_POOL_SIZE', '10'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '20'))
        self.pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
        self.pool_recycle = int(os.getenv('DB_POOL_RECYCLE', '3600'))
        self.echo = os.getenv('DB_ECHO', 'false').lower() == 'true'
        self.echo_pool = os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables."""
        # Try different environment variable names
        url = (
            os.getenv('DATABASE_URL') or
            os.getenv('DB_URL') or
            os.getenv('CODEGEN_DATABASE_URL')
        )
        
        if not url:
            # Construct from individual components
            host = os.getenv('DB_HOST', 'localhost')
            port = os.getenv('DB_PORT', '5432')
            name = os.getenv('DB_NAME', 'codegen')
            user = os.getenv('DB_USER', 'codegen')
            password = os.getenv('DB_PASSWORD', 'codegen')
            
            url = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        
        # Handle postgres:// URLs (convert to postgresql://)
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        
        return url
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        return {
            'poolclass': QueuePool,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'pool_pre_ping': True,  # Validate connections before use
            'echo': self.echo,
            'echo_pool': self.echo_pool,
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'codegen-app',
            }
        }


class DatabaseManager:
    """
    Database manager for handling connections and sessions.
    
    Provides:
    - Connection pooling
    - Session management
    - Health monitoring
    - Migration support
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        
    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
        return self._session_factory
    
    @property
    def scoped_session_factory(self) -> scoped_session:
        """Get or create the scoped session factory."""
        if self._scoped_session is None:
            self._scoped_session = scoped_session(self.session_factory)
        return self._scoped_session
    
    def _create_engine(self) -> Engine:
        """Create and configure the database engine."""
        logger.info(f"Creating database engine for: {self._mask_url(self.config.database_url)}")
        
        engine = create_engine(
            self.config.database_url,
            **self.config.get_engine_kwargs()
        )
        
        # Add event listeners
        self._setup_event_listeners(engine)
        
        return engine
    
    def _setup_event_listeners(self, engine: Engine) -> None:
        """Setup database event listeners for monitoring and logging."""
        
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas if using SQLite."""
            if 'sqlite' in str(engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout."""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin."""
            logger.debug("Connection checked in to pool")
        
        @event.listens_for(engine, "connect")
        def set_postgresql_search_path(dbapi_connection, connection_record):
            """Set PostgreSQL search path."""
            if 'postgresql' in str(engine.url):
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public")
    
    def _mask_url(self, url: str) -> str:
        """Mask sensitive information in database URL."""
        try:
            parsed = urlparse(url)
            if parsed.password:
                masked = url.replace(parsed.password, '***')
                return masked
            return url
        except Exception:
            return url
    
    def create_all_tables(self) -> None:
        """Create all database tables."""
        logger.info("Creating all database tables")
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all_tables(self) -> None:
        """Drop all database tables."""
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()
    
    def get_scoped_session(self) -> Session:
        """Get a scoped database session."""
        return self.scoped_session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db_manager.session_scope() as session:
                # Do database operations
                session.add(model_instance)
                # Commit happens automatically
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
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a database health check."""
        try:
            with self.session_scope() as session:
                # Simple query to test connection
                result = session.execute("SELECT 1 as health_check")
                row = result.fetchone()
                
                # Get pool status
                pool_status = {
                    'size': self.engine.pool.size(),
                    'checked_in': self.engine.pool.checkedin(),
                    'checked_out': self.engine.pool.checkedout(),
                    'overflow': self.engine.pool.overflow(),
                    'invalid': self.engine.pool.invalid(),
                }
                
                return {
                    'status': 'healthy',
                    'database_url': self._mask_url(self.config.database_url),
                    'pool_status': pool_status,
                    'health_check_result': row[0] if row else None,
                }
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': self._mask_url(self.config.database_url),
            }
    
    def close(self) -> None:
        """Close all database connections."""
        if self._scoped_session:
            self._scoped_session.remove()
        
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db_session() -> Session:
    """Get a database session (convenience function)."""
    return get_database_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """Get a database session with automatic transaction management."""
    with get_database_manager().session_scope() as session:
        yield session


def init_database(drop_existing: bool = False) -> None:
    """Initialize the database with all tables."""
    db_manager = get_database_manager()
    
    if drop_existing:
        db_manager.drop_all_tables()
    
    db_manager.create_all_tables()
    logger.info("Database initialized successfully")


def close_database() -> None:
    """Close all database connections."""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
