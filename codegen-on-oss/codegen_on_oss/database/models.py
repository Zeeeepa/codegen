"""Database models for the codegen-on-oss system."""
from __future__ import annotations

import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Create a base class for declarative models
Base = declarative_base()


# Association tables for many-to-many relationships
file_symbol_association = Table(
    "file_symbol_association",
    Base.metadata,
    Column("file_id", Integer, ForeignKey("files.id")),
    Column("symbol_id", Integer, ForeignKey("symbols.id")),
)


class Repository(Base):
    """Repository model."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    commits = relationship("Commit", back_populates="repository")
    files = relationship("File", back_populates="repository")
    snapshots = relationship("Snapshot", back_populates="repository")
    analysis_results = relationship("AnalysisResult", back_populates="repository")

    def __repr__(self) -> str:
        return f"<Repository(name='{self.name}', url='{self.url}')>"


class Commit(Base):
    """Commit model."""

    __tablename__ = "commits"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    sha = Column(String(40), nullable=False)
    message = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    committed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="commits")
    snapshots = relationship("Snapshot", back_populates="commit")
    analysis_results = relationship("AnalysisResult", back_populates="commit")

    def __repr__(self) -> str:
        return f"<Commit(sha='{self.sha}', message='{self.message[:20] if self.message else ''}...')>"


class File(Base):
    """File model."""

    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    path = Column(String(255), nullable=False)
    language = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="files")
    symbols = relationship("Symbol", secondary=file_symbol_association, back_populates="files")
    metrics = relationship("Metric", back_populates="file")
    issues = relationship("Issue", back_populates="file")

    def __repr__(self) -> str:
        return f"<File(path='{self.path}', language='{self.language}')>"


class SymbolType(enum.Enum):
    """Symbol type enum."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    MODULE = "module"
    OTHER = "other"


class Symbol(Base):
    """Symbol model."""

    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(Enum(SymbolType), nullable=False)
    signature = Column(Text, nullable=True)
    docstring = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    files = relationship("File", secondary=file_symbol_association, back_populates="symbols")
    metrics = relationship("Metric", back_populates="symbol")
    issues = relationship("Issue", back_populates="symbol")

    def __repr__(self) -> str:
        return f"<Symbol(name='{self.name}', type='{self.type}')>"


class SnapshotType(enum.Enum):
    """Snapshot type enum."""

    FULL = "full"
    DIFFERENTIAL = "differential"


class Snapshot(Base):
    """Snapshot model."""

    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_id = Column(Integer, ForeignKey("commits.id"), nullable=True)
    type = Column(Enum(SnapshotType), nullable=False, default=SnapshotType.FULL)
    description = Column(Text, nullable=True)
    data = Column(Text, nullable=True)  # JSON data
    created_at = Column(DateTime, default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="snapshots")
    commit = relationship("Commit", back_populates="snapshots")
    analysis_results = relationship("AnalysisResult", back_populates="snapshot")

    def __repr__(self) -> str:
        return f"<Snapshot(type='{self.type}', created_at='{self.created_at}')>"


class AnalysisType(enum.Enum):
    """Analysis type enum."""

    REPOSITORY = "repository"
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    SYMBOL = "symbol"
    FEATURE = "feature"


class AnalysisResult(Base):
    """Analysis result model."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    commit_id = Column(Integer, ForeignKey("commits.id"), nullable=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=True)
    type = Column(Enum(AnalysisType), nullable=False)
    data = Column(Text, nullable=True)  # JSON data
    created_at = Column(DateTime, default=func.now())

    # Relationships
    repository = relationship("Repository", back_populates="analysis_results")
    commit = relationship("Commit", back_populates="analysis_results")
    snapshot = relationship("Snapshot", back_populates="analysis_results")

    def __repr__(self) -> str:
        return f"<AnalysisResult(type='{self.type}', created_at='{self.created_at}')>"


class MetricType(enum.Enum):
    """Metric type enum."""

    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    LINES_OF_CODE = "lines_of_code"
    COMMENT_RATIO = "comment_ratio"
    TEST_COVERAGE = "test_coverage"
    OTHER = "other"


class Metric(Base):
    """Metric model."""

    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=True)
    type = Column(Enum(MetricType), nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    file = relationship("File", back_populates="metrics")
    symbol = relationship("Symbol", back_populates="metrics")

    def __repr__(self) -> str:
        return f"<Metric(type='{self.type}', value='{self.value}')>"


class IssueType(enum.Enum):
    """Issue type enum."""

    CODE_SMELL = "code_smell"
    BUG = "bug"
    VULNERABILITY = "vulnerability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    OTHER = "other"


class Issue(Base):
    """Issue model."""

    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=True)
    type = Column(Enum(IssueType), nullable=False)
    severity = Column(Integer, nullable=False)  # 1-5, 5 being most severe
    message = Column(Text, nullable=False)
    line_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    file = relationship("File", back_populates="issues")
    symbol = relationship("Symbol", back_populates="issues")

    def __repr__(self) -> str:
        return f"<Issue(type='{self.type}', severity='{self.severity}', message='{self.message[:20]}...')>"

