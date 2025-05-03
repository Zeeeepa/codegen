"""
Database Manager for Codegen-on-OSS

This module provides a central manager for database operations.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Type, TypeVar, Generic

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.pool import QueuePool

from .models import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)

class DatabaseManager:
    """
    Manages database connections and operations.
    
    This class provides a unified interface for all database operations,
    including connection management, transaction handling, and CRUD operations.
    """
    
    def __init__(self, db_url: Optional[str] = None, echo: bool = False):
        """
        Initialize the DatabaseManager.
        
        Args:
            db_url: SQLAlchemy database URL. If None, uses the DATABASE_URL environment variable.
            echo: Whether to echo SQL statements.
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL', 'sqlite:///codegen_oss.db')
        self.engine = create_engine(
            self.db_url,
            echo=echo,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        
    def create_tables(self):
        """Create all tables defined in the models."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
        
    def drop_tables(self):
        """Drop all tables defined in the models."""
        Base.metadata.drop_all(self.engine)
        logger.info("Database tables dropped")
        
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
    
    def close_session(self, session: Session):
        """Close a database session."""
        session.close()
        
    def commit_session(self, session: Session):
        """Commit changes in a session."""
        session.commit()
        
    def rollback_session(self, session: Session):
        """Rollback changes in a session."""
        session.rollback()
        
    def create(self, model: T) -> T:
        """
        Create a new record in the database.
        
        Args:
            model: The model instance to create
            
        Returns:
            The created model instance
        """
        session = self.get_session()
        try:
            session.add(model)
            session.commit()
            return model
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating record: {e}")
            raise
        finally:
            session.close()
            
    def get_by_id(self, model_class: Type[T], id: str) -> Optional[T]:
        """
        Get a record by its ID.
        
        Args:
            model_class: The model class to query
            id: The ID of the record to retrieve
            
        Returns:
            The model instance if found, None otherwise
        """
        session = self.get_session()
        try:
            return session.query(model_class).filter(model_class.id == id).first()
        except Exception as e:
            logger.error(f"Error getting record by ID: {e}")
            raise
        finally:
            session.close()
            
    def get_all(self, model_class: Type[T], **filters) -> List[T]:
        """
        Get all records of a model class, optionally filtered.
        
        Args:
            model_class: The model class to query
            **filters: Optional filters to apply
            
        Returns:
            A list of model instances
        """
        session = self.get_session()
        try:
            query = session.query(model_class)
            for attr, value in filters.items():
                if hasattr(model_class, attr):
                    query = query.filter(getattr(model_class, attr) == value)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting all records: {e}")
            raise
        finally:
            session.close()
            
    def update(self, model: T) -> T:
        """
        Update a record in the database.
        
        Args:
            model: The model instance to update
            
        Returns:
            The updated model instance
        """
        session = self.get_session()
        try:
            session.merge(model)
            session.commit()
            return model
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating record: {e}")
            raise
        finally:
            session.close()
            
    def delete(self, model: T) -> bool:
        """
        Delete a record from the database.
        
        Args:
            model: The model instance to delete
            
        Returns:
            True if the record was deleted, False otherwise
        """
        session = self.get_session()
        try:
            session.delete(model)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting record: {e}")
            raise
        finally:
            session.close()
            
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query.
        
        Args:
            query: The SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            A list of dictionaries containing the query results
        """
        session = self.get_session()
        try:
            result = session.execute(query, params or {})
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            session.close()
            
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name: The name of the table to check
            
        Returns:
            True if the table exists, False otherwise
        """
        return inspect(self.engine).has_table(table_name)
    
    def __enter__(self):
        """Context manager entry point."""
        self.session = self.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

