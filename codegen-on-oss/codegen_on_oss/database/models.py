"""
Database Models for Codegen-on-OSS

This module defines the SQLAlchemy ORM models for the unified data model
that connects all aspects of code analysis, including repositories, commits,
files, symbols, snapshots, and analysis results.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Text, Boolean, JSON, Table, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column

Base = declarative_base()

# Association tables for many-to-many relationships
symbol_dependencies = Table(
    'symbol_dependencies',
    Base.metadata,
    Column('source_id', Integer, ForeignKey('symbols.id'), primary_key=True),
    Column('target_id', Integer, ForeignKey('symbols.id'), primary_key=True)
)

file_snapshots = Table(
    'file_snapshots',
    Base.metadata,
    Column('file_id', Integer, ForeignKey('files.id'), primary_key=True),
    Column('snapshot_id', Integer, ForeignKey('snapshots.id'), primary_key=True)
)

class Repository(Base):
    """Repository model representing a code repository."""
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    default_branch = Column(String(255), default="main")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime)
    
    # Relationships
    commits = relationship("Commit", back_populates="repository")
    snapshots = relationship("Snapshot", back_populates="repository")
    
    __table_args__ = (
        UniqueConstraint('name', 'url', name='uq_repo_name_url'),
        Index('idx_repo_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}')>"


class Commit(Base):
    """Commit model representing a specific commit in a repository."""
    __tablename__ = 'commits'
    
    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    sha = Column(String(64), nullable=False)
    author = Column(String(255))
    message = Column(Text)
    timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="commits")
    files = relationship("File", back_populates="commit")
    analysis_results = relationship("AnalysisResult", back_populates="commit")
    
    __table_args__ = (
        UniqueConstraint('repository_id', 'sha', name='uq_repo_commit_sha'),
        Index('idx_commit_sha', 'sha'),
    )
    
    def __repr__(self):
        return f"<Commit(sha='{self.sha}', message='{self.message[:30]}...')>"


class File(Base):
    """File model representing a source code file in a commit."""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False)
    path = Column(String(512), nullable=False)
    language = Column(String(50))
    content_hash = Column(String(64))  # Hash of file content for quick comparison
    loc = Column(Integer)  # Lines of code
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    commit = relationship("Commit", back_populates="files")
    symbols = relationship("Symbol", back_populates="file")
    snapshots = relationship("Snapshot", secondary=file_snapshots, back_populates="files")
    metrics = relationship("Metric", back_populates="file")
    issues = relationship("Issue", back_populates="file")
    
    __table_args__ = (
        UniqueConstraint('commit_id', 'path', name='uq_commit_file_path'),
        Index('idx_file_path', 'path'),
    )
    
    def __repr__(self):
        return f"<File(path='{self.path}', language='{self.language}')>"


class Symbol(Base):
    """Symbol model representing a code symbol (function, class, etc.)."""
    __tablename__ = 'symbols'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    name = Column(String(255), nullable=False)
    qualified_name = Column(String(512), nullable=False)
    type = Column(String(50), nullable=False)  # function, class, variable, etc.
    line_start = Column(Integer)
    line_end = Column(Integer)
    content_hash = Column(String(64))  # Hash of symbol content
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship("File", back_populates="symbols")
    metrics = relationship("Metric", back_populates="symbol")
    issues = relationship("Issue", back_populates="symbol")
    
    # Dependencies (self-referential many-to-many)
    dependencies = relationship(
        "Symbol",
        secondary=symbol_dependencies,
        primaryjoin=id==symbol_dependencies.c.source_id,
        secondaryjoin=id==symbol_dependencies.c.target_id,
        backref="dependents"
    )
    
    __table_args__ = (
        UniqueConstraint('file_id', 'qualified_name', name='uq_file_symbol_qname'),
        Index('idx_symbol_name', 'name'),
        Index('idx_symbol_qualified_name', 'qualified_name'),
    )
    
    def __repr__(self):
        return f"<Symbol(name='{self.name}', type='{self.type}')>"


class Snapshot(Base):
    """Snapshot model representing a point-in-time capture of a codebase."""
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    commit_sha = Column(String(64))
    snapshot_hash = Column(String(64), nullable=False)  # Hash of snapshot content
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="snapshots")
    files = relationship("File", secondary=file_snapshots, back_populates="snapshots")
    analysis_results = relationship("AnalysisResult", back_populates="snapshot")
    
    # Snapshot data stored as JSON
    data = Column(JSON)
    
    __table_args__ = (
        UniqueConstraint('repository_id', 'snapshot_hash', name='uq_repo_snapshot_hash'),
        Index('idx_snapshot_hash', 'snapshot_hash'),
    )
    
    def __repr__(self):
        return f"<Snapshot(id='{self.id}', commit_sha='{self.commit_sha}')>"


class AnalysisResult(Base):
    """Analysis result model representing the outcome of a code analysis."""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=True)
    snapshot_id = Column(Integer, ForeignKey('snapshots.id'), nullable=True)
    analysis_type = Column(String(50), nullable=False)  # repository, commit, feature, etc.
    status = Column(String(20), nullable=False)  # success, failure, in_progress
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    repository = relationship("Repository")
    commit = relationship("Commit", back_populates="analysis_results")
    snapshot = relationship("Snapshot", back_populates="analysis_results")
    metrics = relationship("Metric", back_populates="analysis_result")
    issues = relationship("Issue", back_populates="analysis_result")
    
    # Analysis data stored as JSON
    data = Column(JSON)
    
    __table_args__ = (
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_status', 'status'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(type='{self.analysis_type}', status='{self.status}')>"


class Metric(Base):
    """Metric model representing a code quality metric."""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey('analysis_results.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'), nullable=True)
    name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    threshold = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="metrics")
    file = relationship("File", back_populates="metrics")
    symbol = relationship("Symbol", back_populates="metrics")
    
    __table_args__ = (
        Index('idx_metric_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Metric(name='{self.name}', value={self.value})>"


class Issue(Base):
    """Issue model representing a code quality issue."""
    __tablename__ = 'issues'
    
    id = Column(Integer, primary_key=True)
    analysis_result_id = Column(Integer, ForeignKey('analysis_results.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'), nullable=True)
    type = Column(String(50), nullable=False)  # error, warning, info
    severity = Column(Integer, nullable=False)  # 1-5, with 5 being most severe
    message = Column(Text, nullable=False)
    line_start = Column(Integer)
    line_end = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="issues")
    file = relationship("File", back_populates="issues")
    symbol = relationship("Symbol", back_populates="issues")
    
    # Remediation info stored as JSON
    remediation = Column(JSON)
    
    __table_args__ = (
        Index('idx_issue_type', 'type'),
        Index('idx_issue_severity', 'severity'),
    )
    
    def __repr__(self):
        return f"<Issue(type='{self.type}', severity={self.severity}, message='{self.message[:30]}...')>"

