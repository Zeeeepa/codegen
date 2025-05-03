"""
Database models for the codegen-on-oss system.

This module defines the SQLAlchemy models for storing analysis data.
"""

import enum
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AnalysisType(enum.Enum):
    """Analysis type enum."""

    CODE_QUALITY = "code_quality"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    IMPORTS = "imports"
    METRICS = "metrics"
    SUMMARY = "summary"


class SymbolType(enum.Enum):
    """Symbol type enum."""

    FUNCTION = "function"
    CLASS = "class"
    VARIABLE = "variable"
    MODULE = "module"
    IMPORT = "import"
    OTHER = "other"


class RelationshipType(enum.Enum):
    """Relationship type enum."""

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    CONTAINS = "contains"
    REFERENCES = "references"
    OTHER = "other"


class IssueSeverity(enum.Enum):
    """Issue severity enum."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Repository(Base):
    """Repository model."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    default_branch = Column(String(255), nullable=False, default="main")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    snapshots = relationship("Snapshot", back_populates="repository", cascade="all, delete-orphan")
    analysis_results = relationship(
        "AnalysisResult", back_populates="repository", cascade="all, delete-orphan"
    )


class Snapshot(Base):
    """Snapshot model."""

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_sha = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    tag = Column(String(255), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    storage_path = Column(String(255), nullable=False)
    metadata = Column(JSON, nullable=True)
    is_incremental = Column(Boolean, nullable=False, default=False)
    parent_snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True)

    repository = relationship("Repository", back_populates="snapshots")
    parent_snapshot = relationship("Snapshot", remote_side=[id], backref="child_snapshots")
    analysis_results = relationship(
        "AnalysisResult", back_populates="snapshot", cascade="all, delete-orphan"
    )
    files = relationship("File", back_populates="snapshot", cascade="all, delete-orphan")


class File(Base):
    """File model."""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    filepath = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    extension = Column(String(50), nullable=True)
    s3_key = Column(String(255), nullable=True)
    content_hash = Column(String(64), nullable=True)
    line_count = Column(Integer, nullable=True)
    language = Column(String(50), nullable=True)

    snapshot = relationship("Snapshot", back_populates="files")
    repository = relationship("Repository")
    functions = relationship("Function", back_populates="file", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="file", cascade="all, delete-orphan")
    imports = relationship("Import", back_populates="file", cascade="all, delete-orphan")


class Function(Base):
    """Function model."""

    __tablename__ = "functions"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(255), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    complexity = Column(Integer, nullable=True)
    parameters = Column(JSON, nullable=True)
    return_type = Column(String(255), nullable=True)
    docstring = Column(Text, nullable=True)
    source = Column(Text, nullable=True)

    file = relationship("File", back_populates="functions")
    snapshot = relationship("Snapshot")


class Class(Base):
    """Class model."""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(255), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    base_classes = Column(JSON, nullable=True)
    docstring = Column(Text, nullable=True)
    source = Column(Text, nullable=True)

    file = relationship("File", back_populates="classes")
    snapshot = relationship("Snapshot")


class Import(Base):
    """Import model."""

    __tablename__ = "imports"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False)
    module_name = Column(String(255), nullable=False)
    alias = Column(String(255), nullable=True)
    is_from_import = Column(Boolean, nullable=False, default=False)
    imported_names = Column(JSON, nullable=True)
    line_number = Column(Integer, nullable=True)

    file = relationship("File", back_populates="imports")
    snapshot = relationship("Snapshot")


class AnalysisResult(Base):
    """Analysis result model."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True)
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    summary = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)

    repository = relationship("Repository", back_populates="analysis_results")
    snapshot = relationship("Snapshot", back_populates="analysis_results")
    issues = relationship("Issue", back_populates="analysis_result", cascade="all, delete-orphan")


class Issue(Base):
    """Issue model."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    severity = Column(Enum(IssueSeverity), nullable=False)
    issue_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    recommendation = Column(Text, nullable=True)

    analysis_result = relationship("AnalysisResult", back_populates="issues")


class SymbolAnalysis(Base):
    """Symbol analysis model."""

    __tablename__ = "symbol_analyses"

    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    symbol_type = Column(Enum(SymbolType), nullable=False)
    symbol_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    line_number = Column(Integer, nullable=True)
    complexity = Column(Integer, nullable=True)
    dependencies = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)

    analysis_result = relationship("AnalysisResult")


class DependencyGraph(Base):
    """Dependency graph model."""

    __tablename__ = "dependency_graphs"

    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    graph_data = Column(JSON, nullable=False)
    node_count = Column(Integer, nullable=False)
    edge_count = Column(Integer, nullable=False)
    clusters = Column(JSON, nullable=True)
    central_nodes = Column(JSON, nullable=True)

    analysis_result = relationship("AnalysisResult")


class CodeMetrics(Base):
    """Code metrics model."""

    __tablename__ = "code_metrics"

    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"), nullable=False)
    total_lines = Column(Integer, nullable=False)
    code_lines = Column(Integer, nullable=False)
    comment_lines = Column(Integer, nullable=False)
    blank_lines = Column(Integer, nullable=False)
    complexity = Column(Integer, nullable=True)
    maintainability_index = Column(Integer, nullable=True)
    language_breakdown = Column(JSON, nullable=True)

    analysis_result = relationship("AnalysisResult")


class AnalysisJob(Base):
    """Analysis job model."""

    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository = Column(String(255), nullable=False)
    commit_sha = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    snapshot_id = Column(String(36), nullable=True)
    analysis_types = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)
