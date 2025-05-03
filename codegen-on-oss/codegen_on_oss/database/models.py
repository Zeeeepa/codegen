"""
Database models for codegen-on-oss.

This module defines SQLAlchemy models for storing analysis results, snapshots,
and other data in a relational database.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Table, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

# Association tables for many-to-many relationships
snapshot_file_association = Table(
    'snapshot_file_association', 
    Base.metadata,
    Column('snapshot_id', String(36), ForeignKey('snapshots.id')),
    Column('file_id', String(36), ForeignKey('files.id')),
)

snapshot_function_association = Table(
    'snapshot_function_association', 
    Base.metadata,
    Column('snapshot_id', String(36), ForeignKey('snapshots.id')),
    Column('function_id', String(36), ForeignKey('functions.id')),
)

snapshot_class_association = Table(
    'snapshot_class_association', 
    Base.metadata,
    Column('snapshot_id', String(36), ForeignKey('snapshots.id')),
    Column('class_id', String(36), ForeignKey('classes.id')),
)

function_dependency_association = Table(
    'function_dependency_association', 
    Base.metadata,
    Column('function_id', String(36), ForeignKey('functions.id')),
    Column('dependency_id', String(36), ForeignKey('functions.id')),
)

class_dependency_association = Table(
    'class_dependency_association', 
    Base.metadata,
    Column('class_id', String(36), ForeignKey('classes.id')),
    Column('dependency_id', String(36), ForeignKey('classes.id')),
)

file_import_association = Table(
    'file_import_association', 
    Base.metadata,
    Column('file_id', String(36), ForeignKey('files.id')),
    Column('import_id', String(36), ForeignKey('imports.id')),
)

class Repository(Base):
    """Repository model for storing information about code repositories."""
    
    __tablename__ = 'repositories'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_branch = Column(String(255), default='main')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("Snapshot", back_populates="repository")
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}')>"


class Snapshot(Base):
    """Snapshot model for storing codebase snapshots."""
    
    __tablename__ = 'snapshots'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey('repositories.id'), nullable=False)
    commit_sha = Column(String(40), nullable=True)
    branch = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="snapshots")
    files = relationship("File", secondary=snapshot_file_association, back_populates="snapshots")
    functions = relationship("Function", secondary=snapshot_function_association, back_populates="snapshots")
    classes = relationship("Class", secondary=snapshot_class_association, back_populates="snapshots")
    analysis_results = relationship("AnalysisResult", back_populates="snapshot")
    
    # Indexes
    __table_args__ = (
        Index('idx_snapshot_repo_commit', 'repository_id', 'commit_sha'),
        Index('idx_snapshot_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Snapshot(id='{self.id}', commit_sha='{self.commit_sha}')>"


class File(Base):
    """File model for storing information about source code files."""
    
    __tablename__ = 'files'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filepath = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    content_hash = Column(String(64), nullable=False)
    line_count = Column(Integer, default=0)
    content = Column(Text, nullable=True)  # Optional: store file content
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    snapshots = relationship("Snapshot", secondary=snapshot_file_association, back_populates="files")
    functions = relationship("Function", back_populates="file")
    classes = relationship("Class", back_populates="file")
    imports = relationship("Import", secondary=file_import_association, back_populates="files")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_file_content_hash', 'content_hash'),
        Index('idx_file_filepath', 'filepath'),
    )
    
    def __repr__(self):
        return f"<File(filepath='{self.filepath}', content_hash='{self.content_hash}')>"


class Function(Base):
    """Function model for storing information about functions/methods."""
    
    __tablename__ = 'functions'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(255), nullable=False)
    file_id = Column(String(36), ForeignKey('files.id'), nullable=True)
    source = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    parameters = Column(JSON, nullable=True)
    return_type = Column(String(255), nullable=True)
    cyclomatic_complexity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    file = relationship("File", back_populates="functions")
    snapshots = relationship("Snapshot", secondary=snapshot_function_association, back_populates="functions")
    dependencies = relationship(
        "Function",
        secondary=function_dependency_association,
        primaryjoin=id==function_dependency_association.c.function_id,
        secondaryjoin=id==function_dependency_association.c.dependency_id,
        backref="dependents"
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_function_qualified_name', 'qualified_name'),
        Index('idx_function_file_id', 'file_id'),
    )
    
    def __repr__(self):
        return f"<Function(qualified_name='{self.qualified_name}')>"


class Class(Base):
    """Class model for storing information about classes."""
    
    __tablename__ = 'classes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(255), nullable=False)
    file_id = Column(String(36), ForeignKey('files.id'), nullable=True)
    source = Column(Text, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    parent_classes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    file = relationship("File", back_populates="classes")
    snapshots = relationship("Snapshot", secondary=snapshot_class_association, back_populates="classes")
    dependencies = relationship(
        "Class",
        secondary=class_dependency_association,
        primaryjoin=id==class_dependency_association.c.class_id,
        secondaryjoin=id==class_dependency_association.c.dependency_id,
        backref="dependents"
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_class_qualified_name', 'qualified_name'),
        Index('idx_class_file_id', 'file_id'),
    )
    
    def __repr__(self):
        return f"<Class(qualified_name='{self.qualified_name}')>"


class Import(Base):
    """Import model for storing information about imports."""
    
    __tablename__ = 'imports'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_name = Column(String(255), nullable=False)
    imported_symbol = Column(String(255), nullable=True)
    alias = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = relationship("File", secondary=file_import_association, back_populates="imports")
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_import_module_name', 'module_name'),
        UniqueConstraint('module_name', 'imported_symbol', 'alias', name='uq_import'),
    )
    
    def __repr__(self):
        return f"<Import(module_name='{self.module_name}', imported_symbol='{self.imported_symbol}')>"


class AnalysisResult(Base):
    """Analysis result model for storing analysis results."""
    
    __tablename__ = 'analysis_results'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id = Column(String(36), ForeignKey('snapshots.id'), nullable=False)
    analysis_type = Column(String(255), nullable=False)
    result = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    snapshot = relationship("Snapshot", back_populates="analysis_results")
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_snapshot_type', 'snapshot_id', 'analysis_type'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(id='{self.id}', analysis_type='{self.analysis_type}')>"


class Issue(Base):
    """Issue model for storing code issues found during analysis."""
    
    __tablename__ = 'issues'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_result_id = Column(String(36), ForeignKey('analysis_results.id'), nullable=False)
    file_id = Column(String(36), ForeignKey('files.id'), nullable=True)
    issue_type = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)
    column_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_result = relationship("AnalysisResult", backref=backref("issues", cascade="all, delete-orphan"))
    file = relationship("File")
    
    # Indexes
    __table_args__ = (
        Index('idx_issue_analysis_result', 'analysis_result_id'),
        Index('idx_issue_file', 'file_id'),
        Index('idx_issue_type_severity', 'issue_type', 'severity'),
    )
    
    def __repr__(self):
        return f"<Issue(issue_type='{self.issue_type}', severity='{self.severity}')>"


class UserPreference(Base):
    """User preference model for storing user preferences."""
    
    __tablename__ = 'user_preferences'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(255), nullable=False)
    preference_key = Column(String(255), nullable=False)
    preference_value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uq_user_preference'),
    )
    
    def __repr__(self):
        return f"<UserPreference(user_id='{self.user_id}', key='{self.preference_key}')>"


class WebhookConfig(Base):
    """Webhook configuration model for storing webhook configurations."""
    
    __tablename__ = 'webhook_configs'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey('repositories.id'), nullable=False)
    url = Column(String(255), nullable=False)
    secret = Column(String(255), nullable=True)
    events = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    
    # Relationships
    repository = relationship("Repository", backref=backref("webhook_configs", cascade="all, delete-orphan"))
    
    # Indexes
    __table_args__ = (
        Index('idx_webhook_repository', 'repository_id'),
    )
    
    def __repr__(self):
        return f"<WebhookConfig(id='{self.id}', url='{self.url}')>"

