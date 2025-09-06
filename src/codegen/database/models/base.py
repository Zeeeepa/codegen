"""
Base database models and mixins for Codegen.

Provides common functionality and patterns used across all database models.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, Boolean, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True
    )


class BaseModel(Base, TimestampMixin):
    """
    Base model class that all other models inherit from.
    
    Provides:
    - UUID primary key
    - Timestamps (created_at, updated_at)
    - Common utility methods
    - JSON serialization support
    """
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )
    
    # Metadata fields for tracking and debugging
    metadata_json = Column(JSON, default=dict, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        result = {}
        
        # Include all column attributes
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif hasattr(value, '__dict__'):
                value = str(value)
            result[column.name] = value
        
        # Optionally include relationships
        if include_relationships:
            for relationship in self.__mapper__.relationships:
                value = getattr(self, relationship.key)
                if value is not None:
                    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        result[relationship.key] = [
                            item.to_dict() if hasattr(item, 'to_dict') else str(item)
                            for item in value
                        ]
                    else:
                        result[relationship.key] = (
                            value.to_dict() if hasattr(value, 'to_dict') else str(value)
                        )
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None) -> None:
        """Update model instance from dictionary."""
        exclude = exclude or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the model instance."""
        if self.metadata_json is None:
            self.metadata_json = {}
        self.metadata_json[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the model instance."""
        if self.metadata_json is None:
            return default
        return self.metadata_json.get(key, default)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """Mixin to add soft delete functionality to models."""
    
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    
    def soft_delete(self) -> None:
        """Mark the record as deleted without actually deleting it."""
        self.deleted_at = func.now()
        self.is_deleted = True
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None
        self.is_deleted = False


class AuditMixin:
    """Mixin to add audit trail functionality to models."""
    
    created_by_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    updated_by_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # IP address and user agent for audit trail
    created_from_ip = Column(String(45), nullable=True)  # IPv6 max length
    updated_from_ip = Column(String(45), nullable=True)
    
    # Additional context for the operation
    created_context = Column(JSON, default=dict, nullable=False)
    updated_context = Column(JSON, default=dict, nullable=False)


class VersionedMixin:
    """Mixin to add versioning functionality to models."""
    
    version = Column(Integer, default=1, nullable=False)
    
    def increment_version(self) -> None:
        """Increment the version number."""
        self.version += 1


class StatusMixin:
    """Mixin to add status tracking to models."""
    
    status = Column(String(50), nullable=False, default='active', index=True)
    status_message = Column(Text, nullable=True)
    status_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    def update_status(self, status: str, message: Optional[str] = None) -> None:
        """Update the status of the model."""
        self.status = status
        self.status_message = message
        self.status_updated_at = func.now()
