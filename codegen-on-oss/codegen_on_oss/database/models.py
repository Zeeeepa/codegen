"""
Database Models for Codegen OSS

This module defines the unified database schema for the codegen-oss system,
connecting repositories, snapshots, analysis results, and code entities.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, 
    JSON, String, Table, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

Base = declarative_base()

# Association tables for many-to-many relationships
snapshot_entity_association = Table(
    'snapshot_entity_association',
    Base.metadata,
    Column('snapshot_id', UUID(as_uuid=True), ForeignKey('snapshots.id')),
    Column('entity_id', UUID(as_uuid=True), ForeignKey('code_entities.id')),
)

analysis_entity_association = Table(
    'analysis_entity_association',
    Base.metadata,
    Column('analysis_id', UUID(as_uuid=True), ForeignKey('analyses.id')),
    Column('entity_id', UUID(as_uuid=True), ForeignKey('code_entities.id')),
)

entity_dependency_association = Table(
    'entity_dependency_association',
    Base.metadata,
    Column('entity_id', UUID(as_uuid=True), ForeignKey('code_entities.id')),
    Column('dependency_id', UUID(as_uuid=True), ForeignKey('code_entities.id')),
)


class Repository(Base):
    """Repository model representing a code repository."""
    
    __tablename__ = 'repositories'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_branch = Column(String(255), nullable=False, default='main')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    
    # Relationships
    snapshots = relationship("Snapshot", back_populates="repository", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}')>"


class Snapshot(Base):
    """Snapshot model representing a point-in-time capture of a codebase."""
    
    __tablename__ = 'snapshots'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'), nullable=False)
    commit_sha = Column(String(40), nullable=True)
    branch = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSONB, nullable=True)
    parent_snapshot_id = Column(UUID(as_uuid=True), ForeignKey('snapshots.id'), nullable=True)
    is_incremental = Column(Boolean, default=False)
    storage_path = Column(String(512), nullable=True)  # Path in S3 or other storage
    
    # Relationships
    repository = relationship("Repository", back_populates="snapshots")
    parent_snapshot = relationship("Snapshot", remote_side=[id], backref="child_snapshots")
    entities = relationship("CodeEntity", secondary=snapshot_entity_association, back_populates="snapshots")
    analyses = relationship("Analysis", back_populates="snapshot", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('repository_id', 'commit_sha', name='uq_repo_commit'),
    )
    
    def __repr__(self):
        return f"<Snapshot(repository='{self.repository.name if self.repository else None}', commit_sha='{self.commit_sha}')>"


class CodeEntity(Base):
    """Base model for code entities (files, functions, classes, etc.)."""
    
    __tablename__ = 'code_entities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(512), nullable=False)
    entity_type = Column(String(50), nullable=False)  # 'file', 'function', 'class', etc.
    filepath = Column(String(512), nullable=True)
    content_hash = Column(String(64), nullable=True)  # MD5 or other hash of content
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("Snapshot", secondary=snapshot_entity_association, back_populates="entities")
    analyses = relationship("Analysis", secondary=analysis_entity_association, back_populates="entities")
    dependencies = relationship(
        "CodeEntity",
        secondary=entity_dependency_association,
        primaryjoin=id==entity_dependency_association.c.entity_id,
        secondaryjoin=id==entity_dependency_association.c.dependency_id,
        backref="dependents"
    )
    
    __mapper_args__ = {
        'polymorphic_on': entity_type,
        'polymorphic_identity': 'entity'
    }
    
    def __repr__(self):
        return f"<CodeEntity(type='{self.entity_type}', name='{self.name}')>"


class FileEntity(CodeEntity):
    """Model for file entities."""
    
    __tablename__ = 'file_entities'
    
    id = Column(UUID(as_uuid=True), ForeignKey('code_entities.id'), primary_key=True)
    line_count = Column(Integer, nullable=True)
    language = Column(String(50), nullable=True)
    
    __mapper_args__ = {
        'polymorphic_identity': 'file'
    }


class FunctionEntity(CodeEntity):
    """Model for function entities."""
    
    __tablename__ = 'function_entities'
    
    id = Column(UUID(as_uuid=True), ForeignKey('code_entities.id'), primary_key=True)
    line_count = Column(Integer, nullable=True)
    parameter_count = Column(Integer, nullable=True)
    return_statement_count = Column(Integer, nullable=True)
    cyclomatic_complexity = Column(Integer, nullable=True)
    parent_class_id = Column(UUID(as_uuid=True), ForeignKey('class_entities.id'), nullable=True)
    
    # Relationships
    parent_class = relationship("ClassEntity", back_populates="methods")
    
    __mapper_args__ = {
        'polymorphic_identity': 'function'
    }


class ClassEntity(CodeEntity):
    """Model for class entities."""
    
    __tablename__ = 'class_entities'
    
    id = Column(UUID(as_uuid=True), ForeignKey('code_entities.id'), primary_key=True)
    line_count = Column(Integer, nullable=True)
    parent_class_names = Column(JSONB, nullable=True)  # List of parent class names
    
    # Relationships
    methods = relationship("FunctionEntity", back_populates="parent_class")
    
    __mapper_args__ = {
        'polymorphic_identity': 'class'
    }


class Analysis(Base):
    """Model for analysis results."""
    
    __tablename__ = 'analyses'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'), nullable=False)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey('snapshots.id'), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # 'dependency', 'complexity', 'security', etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="analyses")
    snapshot = relationship("Snapshot", back_populates="analyses")
    entities = relationship("CodeEntity", secondary=analysis_entity_association, back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis(type='{self.analysis_type}', status='{self.status}')>"


class AnalysisMetrics(Base):
    """Model for storing performance metrics of analysis runs."""
    
    __tablename__ = 'analysis_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationship
    analysis = relationship("Analysis")
    
    def __repr__(self):
        return f"<AnalysisMetrics(analysis_id='{self.analysis_id}', duration='{self.duration_seconds}s')>"


class EventLog(Base):
    """Model for logging system events."""
    
    __tablename__ = 'event_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSONB, nullable=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey('repositories.id'), nullable=True)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey('snapshots.id'), nullable=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey('analyses.id'), nullable=True)
    
    # Relationships
    repository = relationship("Repository")
    snapshot = relationship("Snapshot")
    analysis = relationship("Analysis")
    
    def __repr__(self):
        return f"<EventLog(type='{self.event_type}', timestamp='{self.timestamp}')>"

