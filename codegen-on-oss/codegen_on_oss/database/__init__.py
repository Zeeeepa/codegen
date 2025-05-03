"""
Database package for the codegen-on-oss system.

This package provides database models and utilities for storing and retrieving analysis data.
"""

from codegen_on_oss.database.connection import db_manager, get_db, init_db
from codegen_on_oss.database.models import (
    AnalysisJob,
    AnalysisResult,
    AnalysisType,
    Base,
    Class,
    CodeMetrics,
    DependencyGraph,
    File,
    Function,
    Import,
    Issue,
    IssueSeverity,
    RelationshipType,
    Repository,
    Snapshot,
    SymbolAnalysis,
    SymbolType,
)

__all__ = [
    "Base",
    "Repository",
    "Snapshot",
    "File",
    "Function",
    "Class",
    "Import",
    "AnalysisResult",
    "Issue",
    "SymbolAnalysis",
    "DependencyGraph",
    "CodeMetrics",
    "AnalysisJob",
    "AnalysisType",
    "SymbolType",
    "RelationshipType",
    "IssueSeverity",
    "db_manager",
    "get_db",
    "init_db",
]

