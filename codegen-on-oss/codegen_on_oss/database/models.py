"""
Database Models for Codegen-on-OSS

This module defines the SQLAlchemy ORM models for the database schema.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, 
    Text, Boolean, JSON, Table, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class CodebaseSnapshot(Base):
    """
    Represents a snapshot of a codebase at a specific point in time.
    """
    __tablename__ = "codebase_snapshots"
    
    id = Column(String, primary_key=True)
    snapshot_id = Column(String, unique=True, index=True)
    commit_sha = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)
    storage_path = Column(String)
    
    # Relationships
    analyses = relationship("AnalysisResult", back_populates="snapshot")
    
    def __init__(self, snapshot_id=None, commit_sha=None, metadata=None, storage_path=None):
        """
        Initialize a new CodebaseSnapshot.
        
        Args:
            snapshot_id: Unique identifier for the snapshot
            commit_sha: The commit SHA associated with this snapshot
            metadata: Additional metadata about the snapshot
            storage_path: Path to the stored snapshot data
        """
        self.id = str(uuid.uuid4())
        self.snapshot_id = snapshot_id or self.id
        self.commit_sha = commit_sha
        self.metadata = metadata or {}
        self.storage_path = storage_path
        self.timestamp = datetime.utcnow()


class AnalysisResult(Base):
    """
    Represents the result of an analysis run on a codebase snapshot.
    """
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True)
    snapshot_id = Column(String, ForeignKey("codebase_snapshots.id"), index=True)
    analyzer_type = Column(String, index=True)
    status = Column(String, index=True)  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result_data = Column(JSON, nullable=True)
    
    # Relationships
    snapshot = relationship("CodebaseSnapshot", back_populates="analyses")
    metrics = relationship("CodeMetrics", back_populates="analysis", uselist=False)
    symbol_analyses = relationship("SymbolAnalysis", back_populates="analysis")
    dependency_graph = relationship("DependencyGraph", back_populates="analysis", uselist=False)
    
    def __init__(self, snapshot_id, analyzer_type, status="pending", result_data=None):
        """
        Initialize a new AnalysisResult.
        
        Args:
            snapshot_id: ID of the associated snapshot
            analyzer_type: Type of analyzer used
            status: Current status of the analysis
            result_data: Raw result data from the analysis
        """
        self.id = str(uuid.uuid4())
        self.snapshot_id = snapshot_id
        self.analyzer_type = analyzer_type
        self.status = status
        self.result_data = result_data
        self.created_at = datetime.utcnow()


class CodeMetrics(Base):
    """
    Stores code quality metrics for an analysis result.
    """
    __tablename__ = "code_metrics"
    
    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analysis_results.id"), index=True)
    complexity = Column(Float)
    maintainability = Column(Float)
    halstead_metrics = Column(JSON)
    doi_metrics = Column(JSON)  # Depth of Inheritance metrics
    lines_of_code = Column(Integer)
    
    # Relationships
    analysis = relationship("AnalysisResult", back_populates="metrics")
    
    def __init__(self, analysis_id, complexity=0.0, maintainability=0.0, 
                 halstead_metrics=None, doi_metrics=None, lines_of_code=0):
        """
        Initialize a new CodeMetrics instance.
        
        Args:
            analysis_id: ID of the associated analysis
            complexity: Overall complexity score
            maintainability: Maintainability index
            halstead_metrics: Halstead complexity metrics
            doi_metrics: Depth of Inheritance metrics
            lines_of_code: Total lines of code
        """
        self.id = str(uuid.uuid4())
        self.analysis_id = analysis_id
        self.complexity = complexity
        self.maintainability = maintainability
        self.halstead_metrics = halstead_metrics or {}
        self.doi_metrics = doi_metrics or {}
        self.lines_of_code = lines_of_code


class SymbolAnalysis(Base):
    """
    Stores analysis data for individual code symbols (functions, classes, etc.).
    """
    __tablename__ = "symbol_analyses"
    
    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analysis_results.id"), index=True)
    symbol_type = Column(String, index=True)  # function, class, variable, etc.
    symbol_name = Column(String, index=True)
    file_path = Column(String, index=True)
    line_number = Column(Integer)
    complexity = Column(Float)
    dependencies = Column(JSON)
    
    # Relationships
    analysis = relationship("AnalysisResult", back_populates="symbol_analyses")
    
    def __init__(self, analysis_id, symbol_type, symbol_name, file_path=None, 
                 line_number=None, complexity=0.0, dependencies=None):
        """
        Initialize a new SymbolAnalysis instance.
        
        Args:
            analysis_id: ID of the associated analysis
            symbol_type: Type of the symbol
            symbol_name: Name of the symbol
            file_path: Path to the file containing the symbol
            line_number: Line number where the symbol is defined
            complexity: Complexity score for the symbol
            dependencies: Dependencies of the symbol
        """
        self.id = str(uuid.uuid4())
        self.analysis_id = analysis_id
        self.symbol_type = symbol_type
        self.symbol_name = symbol_name
        self.file_path = file_path
        self.line_number = line_number
        self.complexity = complexity
        self.dependencies = dependencies or []


class DependencyGraph(Base):
    """
    Stores dependency graph data for an analysis result.
    """
    __tablename__ = "dependency_graphs"
    
    id = Column(String, primary_key=True)
    analysis_id = Column(String, ForeignKey("analysis_results.id"), index=True)
    graph_data = Column(JSON)
    node_count = Column(Integer)
    edge_count = Column(Integer)
    clusters = Column(JSON)
    central_nodes = Column(JSON)
    
    # Relationships
    analysis = relationship("AnalysisResult", back_populates="dependency_graph")
    
    def __init__(self, analysis_id, graph_data=None, node_count=0, edge_count=0, 
                 clusters=None, central_nodes=None):
        """
        Initialize a new DependencyGraph instance.
        
        Args:
            analysis_id: ID of the associated analysis
            graph_data: Raw graph data
            node_count: Number of nodes in the graph
            edge_count: Number of edges in the graph
            clusters: Identified clusters in the graph
            central_nodes: Central nodes in the graph
        """
        self.id = str(uuid.uuid4())
        self.analysis_id = analysis_id
        self.graph_data = graph_data or {}
        self.node_count = node_count
        self.edge_count = edge_count
        self.clusters = clusters or []
        self.central_nodes = central_nodes or []

