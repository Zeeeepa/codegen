"""
Database middleware for Codegen.

Provides high-level database operations, caching, and business logic.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import IntegrityError, NoResultFound

from .connection import db_session_scope, get_db_session
from .models.base import BaseModel
from .events import EventEmitter

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class DatabaseMiddleware:
    """
    High-level database operations middleware.
    
    Provides:
    - CRUD operations with event emission
    - Query building and optimization
    - Caching integration
    - Business logic enforcement
    - Transaction management
    """
    
    def __init__(self, event_emitter: Optional[EventEmitter] = None):
        self.event_emitter = event_emitter or EventEmitter()
    
    # CREATE operations
    
    def create(
        self, 
        model_class: Type[T], 
        data: Dict[str, Any],
        session: Optional[Session] = None,
        emit_event: bool = True
    ) -> T:
        """Create a new model instance."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            # Create instance
            instance = model_class(**data)
            
            # Add audit information if available
            if hasattr(instance, 'created_by_id') and 'created_by_id' in data:
                instance.created_by_id = data['created_by_id']
            
            use_session.add(instance)
            use_session.flush()  # Get the ID without committing
            
            # Emit event
            if emit_event:
                self.event_emitter.emit(
                    event_type=f"{model_class.__name__.lower()}.created",
                    data={
                        'id': str(instance.id),
                        'model': model_class.__name__,
                        'data': instance.to_dict()
                    }
                )
            
            if close_session:
                use_session.commit()
            
            logger.info(f"Created {model_class.__name__} with ID: {instance.id}")
            return instance
            
        except Exception as e:
            if close_session:
                use_session.rollback()
            logger.error(f"Failed to create {model_class.__name__}: {e}")
            raise
        finally:
            if close_session:
                use_session.close()
    
    def bulk_create(
        self, 
        model_class: Type[T], 
        data_list: List[Dict[str, Any]],
        session: Optional[Session] = None,
        emit_events: bool = True
    ) -> List[T]:
        """Create multiple model instances in bulk."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            instances = []
            for data in data_list:
                instance = model_class(**data)
                instances.append(instance)
                use_session.add(instance)
            
            use_session.flush()  # Get IDs without committing
            
            # Emit events
            if emit_events:
                for instance in instances:
                    self.event_emitter.emit(
                        event_type=f"{model_class.__name__.lower()}.created",
                        data={
                            'id': str(instance.id),
                            'model': model_class.__name__,
                            'data': instance.to_dict()
                        }
                    )
            
            if close_session:
                use_session.commit()
            
            logger.info(f"Created {len(instances)} {model_class.__name__} instances")
            return instances
            
        except Exception as e:
            if close_session:
                use_session.rollback()
            logger.error(f"Failed to bulk create {model_class.__name__}: {e}")
            raise
        finally:
            if close_session:
                use_session.close()
    
    # READ operations
    
    def get_by_id(
        self, 
        model_class: Type[T], 
        id: Union[str, UUID],
        session: Optional[Session] = None,
        relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """Get a model instance by ID."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            query = use_session.query(model_class)
            
            # Load relationships if specified
            if relationships:
                for rel in relationships:
                    if hasattr(model_class, rel):
                        query = query.options(joinedload(getattr(model_class, rel)))
            
            instance = query.filter(model_class.id == id).first()
            
            if instance and hasattr(instance, 'is_deleted') and instance.is_deleted:
                return None
            
            return instance
            
        finally:
            if close_session:
                use_session.close()
    
    def get_by_field(
        self, 
        model_class: Type[T], 
        field: str, 
        value: Any,
        session: Optional[Session] = None
    ) -> Optional[T]:
        """Get a model instance by a specific field."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            query = use_session.query(model_class)
            
            if hasattr(model_class, 'is_deleted'):
                query = query.filter(model_class.is_deleted == False)
            
            instance = query.filter(getattr(model_class, field) == value).first()
            return instance
            
        finally:
            if close_session:
                use_session.close()
    
    def list_with_filters(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        session: Optional[Session] = None,
        relationships: Optional[List[str]] = None
    ) -> List[T]:
        """List model instances with filters and pagination."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            query = use_session.query(model_class)
            
            # Apply soft delete filter
            if hasattr(model_class, 'is_deleted'):
                query = query.filter(model_class.is_deleted == False)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        if isinstance(value, list):
                            query = query.filter(getattr(model_class, field).in_(value))
                        else:
                            query = query.filter(getattr(model_class, field) == value)
            
            # Apply ordering
            if order_by and hasattr(model_class, order_by):
                order_field = getattr(model_class, order_by)
                if order_desc:
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
            
            # Load relationships if specified
            if relationships:
                for rel in relationships:
                    if hasattr(model_class, rel):
                        query = query.options(joinedload(getattr(model_class, rel)))
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
            
        finally:
            if close_session:
                use_session.close()
    
    def count_with_filters(
        self,
        model_class: Type[T],
        filters: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> int:
        """Count model instances with filters."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            query = use_session.query(func.count(model_class.id))
            
            # Apply soft delete filter
            if hasattr(model_class, 'is_deleted'):
                query = query.filter(model_class.is_deleted == False)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        if isinstance(value, list):
                            query = query.filter(getattr(model_class, field).in_(value))
                        else:
                            query = query.filter(getattr(model_class, field) == value)
            
            return query.scalar()
            
        finally:
            if close_session:
                use_session.close()
    
    # UPDATE operations
    
    def update(
        self, 
        instance: T, 
        data: Dict[str, Any],
        session: Optional[Session] = None,
        emit_event: bool = True
    ) -> T:
        """Update a model instance."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            # Store old data for event
            old_data = instance.to_dict() if emit_event else None
            
            # Update instance
            instance.update_from_dict(data)
            
            # Add audit information if available
            if hasattr(instance, 'updated_by_id') and 'updated_by_id' in data:
                instance.updated_by_id = data['updated_by_id']
            
            use_session.add(instance)
            use_session.flush()
            
            # Emit event
            if emit_event:
                self.event_emitter.emit(
                    event_type=f"{instance.__class__.__name__.lower()}.updated",
                    data={
                        'id': str(instance.id),
                        'model': instance.__class__.__name__,
                        'old_data': old_data,
                        'new_data': instance.to_dict(),
                        'changes': data
                    }
                )
            
            if close_session:
                use_session.commit()
            
            logger.info(f"Updated {instance.__class__.__name__} with ID: {instance.id}")
            return instance
            
        except Exception as e:
            if close_session:
                use_session.rollback()
            logger.error(f"Failed to update {instance.__class__.__name__}: {e}")
            raise
        finally:
            if close_session:
                use_session.close()
    
    def update_by_id(
        self, 
        model_class: Type[T], 
        id: Union[str, UUID], 
        data: Dict[str, Any],
        session: Optional[Session] = None,
        emit_event: bool = True
    ) -> Optional[T]:
        """Update a model instance by ID."""
        instance = self.get_by_id(model_class, id, session)
        if instance:
            return self.update(instance, data, session, emit_event)
        return None
    
    # DELETE operations
    
    def delete(
        self, 
        instance: T,
        session: Optional[Session] = None,
        soft_delete: bool = True,
        emit_event: bool = True
    ) -> bool:
        """Delete a model instance."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            if soft_delete and hasattr(instance, 'soft_delete'):
                instance.soft_delete()
                use_session.add(instance)
            else:
                use_session.delete(instance)
            
            use_session.flush()
            
            # Emit event
            if emit_event:
                self.event_emitter.emit(
                    event_type=f"{instance.__class__.__name__.lower()}.deleted",
                    data={
                        'id': str(instance.id),
                        'model': instance.__class__.__name__,
                        'soft_delete': soft_delete,
                        'data': instance.to_dict()
                    }
                )
            
            if close_session:
                use_session.commit()
            
            logger.info(f"Deleted {instance.__class__.__name__} with ID: {instance.id}")
            return True
            
        except Exception as e:
            if close_session:
                use_session.rollback()
            logger.error(f"Failed to delete {instance.__class__.__name__}: {e}")
            raise
        finally:
            if close_session:
                use_session.close()
    
    def delete_by_id(
        self, 
        model_class: Type[T], 
        id: Union[str, UUID],
        session: Optional[Session] = None,
        soft_delete: bool = True,
        emit_event: bool = True
    ) -> bool:
        """Delete a model instance by ID."""
        instance = self.get_by_id(model_class, id, session)
        if instance:
            return self.delete(instance, session, soft_delete, emit_event)
        return False
    
    # TRANSACTION operations
    
    def execute_in_transaction(self, operations: List[callable]) -> List[Any]:
        """Execute multiple operations in a single transaction."""
        with db_session_scope() as session:
            results = []
            for operation in operations:
                result = operation(session)
                results.append(result)
            return results
    
    # UTILITY operations
    
    def exists(
        self, 
        model_class: Type[T], 
        filters: Dict[str, Any],
        session: Optional[Session] = None
    ) -> bool:
        """Check if a model instance exists with given filters."""
        use_session = session or get_db_session()
        close_session = session is None
        
        try:
            query = use_session.query(model_class.id)
            
            # Apply soft delete filter
            if hasattr(model_class, 'is_deleted'):
                query = query.filter(model_class.is_deleted == False)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.filter(getattr(model_class, field) == value)
            
            return query.first() is not None
            
        finally:
            if close_session:
                use_session.close()


# Global middleware instance
_middleware: Optional[DatabaseMiddleware] = None


def get_database_middleware() -> DatabaseMiddleware:
    """Get the global database middleware instance."""
    global _middleware
    if _middleware is None:
        _middleware = DatabaseMiddleware()
    return _middleware
