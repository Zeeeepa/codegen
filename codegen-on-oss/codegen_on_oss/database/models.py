"""
Database models for Codegen-on-OSS

This module provides SQLAlchemy models for storing analysis results,
snapshots, and other data.
"""

import enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CodebaseEntity(Base):
    """Model for storing codebase metadata."""

    __tablename__ = "codebases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    repository_url = Column(String(255), index=True)
    default_branch = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    snapshots = relationship("SnapshotEntity", back_populates="codebase")
    analysis_results = relationship("AnalysisResultEntity", back_populates="codebase")
    symbols = relationship("SymbolEntity", back_populates="codebase")


class SnapshotEntity(Base):
    """Model for storing snapshot metadata."""

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"))
    commit_hash = Column(String(40), index=True)
    branch = Column(String(255), index=True)
    tag = Column(String(255), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    storage_path = Column(String(255))  # Path to the snapshot in storage
    diff_from_previous = Column(Text, nullable=True)  # Stored diff if using differential snapshots

    # Relationships
    codebase = relationship("CodebaseEntity", back_populates="snapshots")
    analysis_results = relationship("AnalysisResultEntity", back_populates="snapshot")


class AnalysisType(enum.Enum):
    """Types of analysis that can be performed."""

    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    FEATURE = "feature"
    COMMIT = "commit"
    DIFF = "diff"
    CUSTOM = "custom"


class AnalysisResultEntity(Base):
    """Model for storing analysis results."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"))
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True)
    analysis_type = Column(Enum(AnalysisType))
    created_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    details = Column(JSON)
    metrics = Column(JSON)

    # Relationships
    codebase = relationship("CodebaseEntity", back_populates="analysis_results")
    snapshot = relationship("SnapshotEntity", back_populates="analysis_results")
    issues = relationship("IssueEntity", back_populates="analysis_result")


class SymbolType(enum.Enum):
    """Types of symbols that can be tracked."""

    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    VARIABLE = "variable"
    IMPORT = "import"
    OTHER = "other"


class SymbolEntity(Base):
    """Model for storing information about code symbols."""

    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    codebase_id = Column(Integer, ForeignKey("codebases.id"))
    name = Column(String(255), index=True)
    symbol_type = Column(Enum(SymbolType))
    file_path = Column(String(255), index=True)
    line_number = Column(Integer)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    codebase = relationship("CodebaseEntity", back_populates="symbols")
    source_relationships = relationship(
        "RelationshipEntity", 
        foreign_keys="[RelationshipEntity.source_id]",
        back_populates="source"
    )
    target_relationships = relationship(
        "RelationshipEntity", 
        foreign_keys="[RelationshipEntity.target_id]",
        back_populates="target"
    )
    metrics = relationship("MetricsEntity", back_populates="symbol")


class MetricsEntity(Base):
    """Model for storing code metrics for symbols."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"))
    cyclomatic_complexity = Column(Float, nullable=True)
    halstead_volume = Column(Float, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    lines_of_code = Column(Integer, nullable=True)
    comment_ratio = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    custom_metrics = Column(JSON)

    # Relationships
    symbol = relationship("SymbolEntity", back_populates="metrics")


class IssueEntity(Base):
    """Model for storing code issues and recommendations."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    analysis_result_id = Column(Integer, ForeignKey("analysis_results.id"))
    title = Column(String(255))
    description = Column(Text)
    file_path = Column(String(255), index=True)
    line_number = Column(Integer, nullable=True)
    severity = Column(String(50), index=True)  # e.g., "high", "medium", "low"
    issue_type = Column(String(100), index=True)  # e.g., "security", "performance", "style"
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    recommendation = Column(Text, nullable=True)

    # Relationships
    analysis_result = relationship("AnalysisResultEntity", back_populates="issues")


class RelationshipType(enum.Enum):
    """Types of relationships between symbols."""

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    CONTAINS = "contains"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    OTHER = "other"


class RelationshipEntity(Base):
    """Model for storing relationships between symbols."""

    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("symbols.id"))
    target_id = Column(Integer, ForeignKey("symbols.id"))
    relationship_type = Column(Enum(RelationshipType))
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)

    # Relationships
    source = relationship(
        "SymbolEntity", 
        foreign_keys=[source_id],
        back_populates="source_relationships"
    )
    target = relationship(
        "SymbolEntity", 
        foreign_keys=[target_id],
        back_populates="target_relationships"
    )

