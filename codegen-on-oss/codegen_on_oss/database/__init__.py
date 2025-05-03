"""
Database package for Codegen-on-OSS.

This package provides database models, repositories, and utilities for
storing and retrieving code analysis data.
"""

from codegen_on_oss.database.models import (
    Base, Repository, Commit, File, Symbol, Snapshot, 
    AnalysisResult, Metric, Issue
)
from codegen_on_oss.database.manager import (
    DatabaseSettings, DatabaseManager, get_db_manager, get_db_session
)
from codegen_on_oss.database.repository import (
    BaseRepository, RepositoryRepository, CommitRepository,
    FileRepository, SymbolRepository, SnapshotRepository,
    AnalysisResultRepository, MetricRepository, IssueRepository
)

__all__ = [
    # Models
    'Base', 'Repository', 'Commit', 'File', 'Symbol', 
    'Snapshot', 'AnalysisResult', 'Metric', 'Issue',
    
    # Database management
    'DatabaseSettings', 'DatabaseManager', 'get_db_manager', 'get_db_session',
    
    # Repositories
    'BaseRepository', 'RepositoryRepository', 'CommitRepository',
    'FileRepository', 'SymbolRepository', 'SnapshotRepository',
    'AnalysisResultRepository', 'MetricRepository', 'IssueRepository',
]

