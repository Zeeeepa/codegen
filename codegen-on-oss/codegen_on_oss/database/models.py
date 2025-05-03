"""
Database models for the codegen-on-oss system.

This module defines the SQLAlchemy models that represent the database schema
for storing analysis data, snapshots, and metrics.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Table, JSON, Text, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

Base = declarative_base()

# Association tables for many-to-many relationships
snapshot_tag_association = Table(
    'snapshot_tag_association',
    Base.metadata,
    Column('snapshot_id', UUID(as_uuid=True), ForeignKey('snapshots.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
)

file_analysis_tag_association = Table(
    'file_analysis_tag_association',
    Base.metadata,
    Column('file_analysis_id', Integer, ForeignKey('file_analyses.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
)


class AnalysisBase(Base):
    """Base model for all analysis data"""
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id"), index=True)


class Tag(Base):
    """Tags for categorizing snapshots and analyses"""
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    snapshots = relationship("CodebaseSnapshot", secondary=snapshot_tag_association, back_populates="tags")
    file_analyses = relationship("FileAnalysis", secondary=file_analysis_tag_association, back_populates="tags")


class CodebaseSnapshot(Base):
    """Snapshot model with metadata and relationships"""
    __tablename__ = "snapshots"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository: Mapped[str] = mapped_column(String(255), index=True)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40), index=True, nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    metadata: Mapped[Dict] = mapped_column(JSONB, default={})
    manifest_hash: Mapped[str] = mapped_column(String(64), index=True)
    
    # Relationships
    code_metrics = relationship("CodeMetrics", back_populates="snapshot", cascade="all, delete-orphan")
    file_analyses = relationship("FileAnalysis", back_populates="snapshot", cascade="all, delete-orphan")
    dependency_analyses = relationship("DependencyAnalysis", back_populates="snapshot", cascade="all, delete-orphan")
    security_analyses = relationship("SecurityAnalysis", back_populates="snapshot", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=snapshot_tag_association, back_populates="snapshots")
    
    __table_args__ = (
        UniqueConstraint('repository', 'commit_sha', name='uq_repo_commit'),
        Index('idx_snapshot_repo_commit', 'repository', 'commit_sha'),
    )


class FileManifest(Base):
    """File manifest for a snapshot, tracking files and their hashes"""
    __tablename__ = "file_manifests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id"), index=True)
    file_path: Mapped[str] = mapped_column(String(1024), index=True)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    file_size: Mapped[int] = mapped_column(Integer)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_stored: Mapped[bool] = mapped_column(Boolean, default=False)
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Relationship
    snapshot = relationship("CodebaseSnapshot", backref="file_manifests")
    
    __table_args__ = (
        UniqueConstraint('snapshot_id', 'file_path', name='uq_snapshot_file_path'),
    )


class CodeMetrics(AnalysisBase):
    """Code quality metrics for a snapshot"""
    __tablename__ = "code_metrics"
    
    total_lines: Mapped[int] = mapped_column(Integer)
    code_lines: Mapped[int] = mapped_column(Integer)
    comment_lines: Mapped[int] = mapped_column(Integer)
    blank_lines: Mapped[int] = mapped_column(Integer)
    complexity: Mapped[float] = mapped_column(Float)
    maintainability_index: Mapped[float] = mapped_column(Float)
    test_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duplication_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language_breakdown: Mapped[Dict] = mapped_column(JSONB)
    
    # Relationship
    snapshot = relationship("CodebaseSnapshot", back_populates="code_metrics")


class FileAnalysis(AnalysisBase):
    """Analysis of individual files"""
    __tablename__ = "file_analyses"
    
    file_path: Mapped[str] = mapped_column(String(1024), index=True)
    language: Mapped[str] = mapped_column(String(50), index=True)
    lines: Mapped[int] = mapped_column(Integer)
    complexity: Mapped[float] = mapped_column(Float)
    issues_count: Mapped[int] = mapped_column(Integer, default=0)
    analysis_data: Mapped[Dict] = mapped_column(JSONB)
    
    # Relationships
    snapshot = relationship("CodebaseSnapshot", back_populates="file_analyses")
    issues = relationship("CodeIssue", back_populates="file_analysis", cascade="all, delete-orphan")
    functions = relationship("FunctionAnalysis", back_populates="file_analysis", cascade="all, delete-orphan")
    classes = relationship("ClassAnalysis", back_populates="file_analysis", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=file_analysis_tag_association, back_populates="file_analyses")


class CodeIssue(Base):
    """Code issues identified during analysis"""
    __tablename__ = "code_issues"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_analyses.id"), index=True)
    line_number: Mapped[int] = mapped_column(Integer)
    column: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_type: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    message: Mapped[str] = mapped_column(Text)
    rule_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationship
    file_analysis = relationship("FileAnalysis", back_populates="issues")


class FunctionAnalysis(Base):
    """Analysis of individual functions"""
    __tablename__ = "function_analyses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_analyses.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    complexity: Mapped[float] = mapped_column(Float)
    parameters: Mapped[List] = mapped_column(JSONB)
    return_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    file_analysis = relationship("FileAnalysis", back_populates="functions")


class ClassAnalysis(Base):
    """Analysis of individual classes"""
    __tablename__ = "class_analyses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("file_analyses.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    methods_count: Mapped[int] = mapped_column(Integer)
    attributes_count: Mapped[int] = mapped_column(Integer)
    inheritance: Mapped[List] = mapped_column(JSONB)
    docstring: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    file_analysis = relationship("FileAnalysis", back_populates="classes")


class DependencyAnalysis(AnalysisBase):
    """Analysis of project dependencies"""
    __tablename__ = "dependency_analyses"
    
    dependencies_count: Mapped[int] = mapped_column(Integer)
    direct_dependencies: Mapped[List] = mapped_column(JSONB)
    transitive_dependencies: Mapped[List] = mapped_column(JSONB)
    outdated_dependencies: Mapped[List] = mapped_column(JSONB)
    vulnerable_dependencies: Mapped[List] = mapped_column(JSONB)
    
    # Relationship
    snapshot = relationship("CodebaseSnapshot", back_populates="dependency_analyses")


class SecurityAnalysis(AnalysisBase):
    """Security analysis results"""
    __tablename__ = "security_analyses"
    
    vulnerabilities_count: Mapped[int] = mapped_column(Integer)
    high_severity_count: Mapped[int] = mapped_column(Integer)
    medium_severity_count: Mapped[int] = mapped_column(Integer)
    low_severity_count: Mapped[int] = mapped_column(Integer)
    analysis_data: Mapped[Dict] = mapped_column(JSONB)
    
    # Relationship
    snapshot = relationship("CodebaseSnapshot", back_populates="security_analyses")


class AnalysisJob(Base):
    """Analysis job tracking"""
    __tablename__ = "analysis_jobs"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("snapshots.id"), nullable=True, index=True)
    repository: Mapped[str] = mapped_column(String(255), index=True)
    commit_sha: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    analysis_types: Mapped[List] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result_data: Mapped[Dict] = mapped_column(JSONB, default={})
    
    # Relationship
    snapshot = relationship("CodebaseSnapshot", backref="analysis_jobs")


class ParseMetrics(Base):
    """Parse metrics from the existing system, maintained for compatibility"""
    __tablename__ = "parse_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[str] = mapped_column(String, index=True)
    language: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    codegen_version: Mapped[str] = mapped_column(String, index=True)
    delta_time: Mapped[float] = mapped_column(Float, index=True)
    cumulative_time: Mapped[float] = mapped_column(Float, index=True)
    cpu_time: Mapped[float] = mapped_column(Float, index=True)
    memory_usage: Mapped[int] = mapped_column(Integer, index=True)
    memory_delta: Mapped[int] = mapped_column(Integer, index=True)
    error: Mapped[str] = mapped_column(String, index=True)
    modal_function_call_id: Mapped[str] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint(
            "repo",
            "revision",
            "action",
            "codegen_version",
            name="uq_repo_revision_action_codegen_version",
        ),
    )


class SWEBenchResult(Base):
    """SWEBench results from the existing system, maintained for compatibility"""
    __tablename__ = "swebench_output"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codegen_version: Mapped[str] = mapped_column(String, index=True)
    submitted: Mapped[int] = mapped_column(Integer)
    completed_instances: Mapped[int] = mapped_column(Integer)
    resolved_instances: Mapped[int] = mapped_column(Integer)
    unresolved_instances: Mapped[int] = mapped_column(Integer)
    empty_patches: Mapped[int] = mapped_column(Integer)
    error_instances: Mapped[int] = mapped_column(Integer)
    modal_function_call_id: Mapped[str] = mapped_column(String)

