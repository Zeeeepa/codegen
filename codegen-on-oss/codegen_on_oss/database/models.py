"""
Database Models Module

This module defines the ORM models for the database schema, providing a unified
data model for storing analysis results, snapshots, and other artifacts.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Table, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

Base = declarative_base()

# Association tables for many-to-many relationships
file_issue_association = Table(
    'file_issue_association', 
    Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id')),
    Column('issue_id', Integer, ForeignKey('analysis_issues.id'))
)

function_issue_association = Table(
    'function_issue_association', 
    Base.metadata,
    Column('function_id', Integer, ForeignKey('functions.id')),
    Column('issue_id', Integer, ForeignKey('analysis_issues.id'))
)

class Repository(Base):
    """Repository model representing a code repository."""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_branch = Column(String, default="main")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    snapshots = relationship("Snapshot", back_populates="repository")
    analysis_results = relationship("AnalysisResult", back_populates="repository")
    files = relationship("File", back_populates="repository")
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}')>"

class Snapshot(Base):
    """Snapshot model representing a point-in-time capture of a codebase."""
    __tablename__ = "snapshots"
    
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String, nullable=False, unique=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    commit_sha = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="snapshots")
    analysis_results = relationship("AnalysisResult", back_populates="snapshot")
    files = relationship("File", back_populates="snapshot")
    
    def __repr__(self):
        return f"<Snapshot(snapshot_id='{self.snapshot_id}', commit_sha='{self.commit_sha}')>"

class AnalysisResult(Base):
    """Analysis result model representing the outcome of a code analysis."""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    analysis_type = Column(String, nullable=False)  # e.g., "commit", "pr", "repo"
    timestamp = Column(DateTime, default=datetime.now)
    summary = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="analysis_results")
    snapshot = relationship("Snapshot", back_populates="analysis_results")
    issues = relationship("AnalysisIssue", back_populates="analysis_result")
    file_metrics = relationship("FileMetric", back_populates="analysis_result")
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, analysis_type='{self.analysis_type}')>"

class AnalysisIssue(Base):
    """Analysis issue model representing a problem found during analysis."""
    __tablename__ = "analysis_issues"
    
    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"))
    issue_type = Column(String, nullable=False)  # e.g., "complexity", "security", "style"
    severity = Column(String, nullable=False)  # e.g., "high", "medium", "low"
    message = Column(Text, nullable=False)
    file_path = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    
    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="issues")
    files = relationship("File", secondary=file_issue_association, back_populates="issues")
    functions = relationship("Function", secondary=function_issue_association, back_populates="issues")
    
    def __repr__(self):
        return f"<AnalysisIssue(issue_type='{self.issue_type}', severity='{self.severity}')>"

class File(Base):
    """File model representing a source code file in a repository."""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"))
    filepath = Column(String, nullable=False)
    name = Column(String, nullable=False)
    extension = Column(String, nullable=True)
    s3_key = Column(String, nullable=True)  # Reference to file content in S3
    content_hash = Column(String, nullable=True)
    line_count = Column(Integer, nullable=True)
    
    # Relationships
    repository = relationship("Repository", back_populates="files")
    snapshot = relationship("Snapshot", back_populates="files")
    functions = relationship("Function", back_populates="file")
    classes = relationship("Class", back_populates="file")
    metrics = relationship("FileMetric", back_populates="file")
    issues = relationship("AnalysisIssue", secondary=file_issue_association, back_populates="files")
    
    __table_args__ = (
        UniqueConstraint('snapshot_id', 'filepath', name='uq_snapshot_filepath'),
    )
    
    def __repr__(self):
        return f"<File(filepath='{self.filepath}')>"

class Function(Base):
    """Function model representing a function or method in a source file."""
    __tablename__ = "functions"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    name = Column(String, nullable=False)
    qualified_name = Column(String, nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    parameters = Column(JSON, nullable=True)
    return_type = Column(String, nullable=True)
    source = Column(Text, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="functions")
    metrics = relationship("FunctionMetric", back_populates="function")
    issues = relationship("AnalysisIssue", secondary=function_issue_association, back_populates="functions")
    
    def __repr__(self):
        return f"<Function(name='{self.name}', qualified_name='{self.qualified_name}')>"

class Class(Base):
    """Class model representing a class in a source file."""
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    name = Column(String, nullable=False)
    qualified_name = Column(String, nullable=False)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    parent_classes = Column(JSON, nullable=True)
    source = Column(Text, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="classes")
    metrics = relationship("ClassMetric", back_populates="class_")
    
    def __repr__(self):
        return f"<Class(name='{self.name}', qualified_name='{self.qualified_name}')>"

class FileMetric(Base):
    """File metric model representing metrics for a file."""
    __tablename__ = "file_metrics"
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"))
    line_count = Column(Integer, nullable=True)
    comment_count = Column(Integer, nullable=True)
    function_count = Column(Integer, nullable=True)
    class_count = Column(Integer, nullable=True)
    import_count = Column(Integer, nullable=True)
    complexity = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    additional_metrics = Column(JSON, nullable=True)
    
    # Relationships
    file = relationship("File", back_populates="metrics")
    analysis_result = relationship("AnalysisResult", back_populates="file_metrics")
    
    def __repr__(self):
        return f"<FileMetric(file_id={self.file_id}, complexity={self.complexity})>"

class FunctionMetric(Base):
    """Function metric model representing metrics for a function."""
    __tablename__ = "function_metrics"
    
    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey("functions.id"))
    cyclomatic_complexity = Column(Integer, nullable=True)
    cognitive_complexity = Column(Integer, nullable=True)
    line_count = Column(Integer, nullable=True)
    parameter_count = Column(Integer, nullable=True)
    return_count = Column(Integer, nullable=True)
    halstead_volume = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    additional_metrics = Column(JSON, nullable=True)
    
    # Relationships
    function = relationship("Function", back_populates="metrics")
    
    def __repr__(self):
        return f"<FunctionMetric(function_id={self.function_id}, complexity={self.cyclomatic_complexity})>"

class ClassMetric(Base):
    """Class metric model representing metrics for a class."""
    __tablename__ = "class_metrics"
    
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id"))
    method_count = Column(Integer, nullable=True)
    attribute_count = Column(Integer, nullable=True)
    inheritance_depth = Column(Integer, nullable=True)
    coupling = Column(Integer, nullable=True)
    cohesion = Column(Float, nullable=True)
    additional_metrics = Column(JSON, nullable=True)
    
    # Relationships
    class_ = relationship("Class", back_populates="metrics")
    
    def __repr__(self):
        return f"<ClassMetric(class_id={self.class_id}, method_count={self.method_count})>"

class WebhookConfig(Base):
    """Webhook configuration model for event notifications."""
    __tablename__ = "webhook_configs"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)  # List of event types to trigger on
    secret = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_triggered = Column(DateTime, nullable=True)
    
    # Relationships
    repository = relationship("Repository")
    
    def __repr__(self):
        return f"<WebhookConfig(url='{self.url}')>"

class AnalysisJob(Base):
    """Analysis job model for tracking analysis tasks."""
    __tablename__ = "analysis_jobs"
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"))
    job_type = Column(String, nullable=False)  # e.g., "commit", "pr", "repo"
    status = Column(String, nullable=False)  # e.g., "pending", "running", "completed", "failed"
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    parameters = Column(JSON, nullable=True)
    result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    repository = relationship("Repository")
    result = relationship("AnalysisResult")
    
    def __repr__(self):
        return f"<AnalysisJob(job_type='{self.job_type}', status='{self.status}')>"
"""

