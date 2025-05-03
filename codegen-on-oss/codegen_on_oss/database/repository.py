"""
Database Repository for Codegen-on-OSS

This module provides repository classes for database operations on different
entities, such as repositories, commits, files, symbols, snapshots, and analysis results.
"""

import logging
from typing import List, Optional, Dict, Any, Union, Type, TypeVar, Generic
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, func, desc, asc

from codegen_on_oss.database.models import (
    Repository, Commit, File, Symbol, Snapshot, 
    AnalysisResult, Metric, Issue
)
from codegen_on_oss.database.manager import get_db_session

logger = logging.getLogger(__name__)

# Generic type for ORM models
T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository for database operations."""
    
    def __init__(self, model: Type[T]):
        """
        Initialize the repository.
        
        Args:
            model: The SQLAlchemy model class.
        """
        self.model = model
    
    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        """
        Get an entity by ID.
        
        Args:
            session: The database session.
            id: The entity ID.
            
        Returns:
            The entity or None if not found.
        """
        return session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, session: Session, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            session: The database session.
            limit: Maximum number of entities to return.
            offset: Number of entities to skip.
            
        Returns:
            A list of entities.
        """
        return session.query(self.model).limit(limit).offset(offset).all()
    
    def create(self, session: Session, **kwargs) -> T:
        """
        Create a new entity.
        
        Args:
            session: The database session.
            **kwargs: Entity attributes.
            
        Returns:
            The created entity.
        """
        entity = self.model(**kwargs)
        session.add(entity)
        session.flush()
        return entity
    
    def update(self, session: Session, id: int, **kwargs) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            session: The database session.
            id: The entity ID.
            **kwargs: Entity attributes to update.
            
        Returns:
            The updated entity or None if not found.
        """
        entity = self.get_by_id(session, id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            session.flush()
        return entity
    
    def delete(self, session: Session, id: int) -> bool:
        """
        Delete an entity.
        
        Args:
            session: The database session.
            id: The entity ID.
            
        Returns:
            True if the entity was deleted, False otherwise.
        """
        entity = self.get_by_id(session, id)
        if entity:
            session.delete(entity)
            session.flush()
            return True
        return False


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for Repository entities."""
    
    def __init__(self):
        super().__init__(Repository)
    
    def get_by_name_and_url(self, session: Session, name: str, url: str) -> Optional[Repository]:
        """
        Get a repository by name and URL.
        
        Args:
            session: The database session.
            name: The repository name.
            url: The repository URL.
            
        Returns:
            The repository or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.name == name, self.model.url == url)
        ).first()
    
    def get_by_name(self, session: Session, name: str) -> Optional[Repository]:
        """
        Get a repository by name.
        
        Args:
            session: The database session.
            name: The repository name.
            
        Returns:
            The repository or None if not found.
        """
        return session.query(self.model).filter(self.model.name == name).first()
    
    def update_last_analyzed(self, session: Session, id: int) -> Optional[Repository]:
        """
        Update the last_analyzed timestamp of a repository.
        
        Args:
            session: The database session.
            id: The repository ID.
            
        Returns:
            The updated repository or None if not found.
        """
        return self.update(session, id, last_analyzed=datetime.utcnow())


class CommitRepository(BaseRepository[Commit]):
    """Repository for Commit entities."""
    
    def __init__(self):
        super().__init__(Commit)
    
    def get_by_sha(self, session: Session, repository_id: int, sha: str) -> Optional[Commit]:
        """
        Get a commit by SHA.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            sha: The commit SHA.
            
        Returns:
            The commit or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.repository_id == repository_id, self.model.sha == sha)
        ).first()
    
    def get_latest_commits(self, session: Session, repository_id: int, limit: int = 10) -> List[Commit]:
        """
        Get the latest commits for a repository.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            limit: Maximum number of commits to return.
            
        Returns:
            A list of commits.
        """
        return session.query(self.model).filter(
            self.model.repository_id == repository_id
        ).order_by(desc(self.model.timestamp)).limit(limit).all()


class FileRepository(BaseRepository[File]):
    """Repository for File entities."""
    
    def __init__(self):
        super().__init__(File)
    
    def get_by_path(self, session: Session, commit_id: int, path: str) -> Optional[File]:
        """
        Get a file by path.
        
        Args:
            session: The database session.
            commit_id: The commit ID.
            path: The file path.
            
        Returns:
            The file or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.commit_id == commit_id, self.model.path == path)
        ).first()
    
    def get_by_language(self, session: Session, commit_id: int, language: str) -> List[File]:
        """
        Get files by language.
        
        Args:
            session: The database session.
            commit_id: The commit ID.
            language: The file language.
            
        Returns:
            A list of files.
        """
        return session.query(self.model).filter(
            and_(self.model.commit_id == commit_id, self.model.language == language)
        ).all()


class SymbolRepository(BaseRepository[Symbol]):
    """Repository for Symbol entities."""
    
    def __init__(self):
        super().__init__(Symbol)
    
    def get_by_qualified_name(self, session: Session, file_id: int, qualified_name: str) -> Optional[Symbol]:
        """
        Get a symbol by qualified name.
        
        Args:
            session: The database session.
            file_id: The file ID.
            qualified_name: The symbol qualified name.
            
        Returns:
            The symbol or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.file_id == file_id, self.model.qualified_name == qualified_name)
        ).first()
    
    def get_by_type(self, session: Session, file_id: int, type: str) -> List[Symbol]:
        """
        Get symbols by type.
        
        Args:
            session: The database session.
            file_id: The file ID.
            type: The symbol type.
            
        Returns:
            A list of symbols.
        """
        return session.query(self.model).filter(
            and_(self.model.file_id == file_id, self.model.type == type)
        ).all()
    
    def add_dependency(self, session: Session, source_id: int, target_id: int) -> bool:
        """
        Add a dependency between two symbols.
        
        Args:
            session: The database session.
            source_id: The source symbol ID.
            target_id: The target symbol ID.
            
        Returns:
            True if the dependency was added, False otherwise.
        """
        source = self.get_by_id(session, source_id)
        target = self.get_by_id(session, target_id)
        
        if source and target and target not in source.dependencies:
            source.dependencies.append(target)
            session.flush()
            return True
        return False


class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for Snapshot entities."""
    
    def __init__(self):
        super().__init__(Snapshot)
    
    def get_by_hash(self, session: Session, repository_id: int, snapshot_hash: str) -> Optional[Snapshot]:
        """
        Get a snapshot by hash.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            snapshot_hash: The snapshot hash.
            
        Returns:
            The snapshot or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.repository_id == repository_id, self.model.snapshot_hash == snapshot_hash)
        ).first()
    
    def get_latest_snapshots(self, session: Session, repository_id: int, limit: int = 10) -> List[Snapshot]:
        """
        Get the latest snapshots for a repository.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            limit: Maximum number of snapshots to return.
            
        Returns:
            A list of snapshots.
        """
        return session.query(self.model).filter(
            self.model.repository_id == repository_id
        ).order_by(desc(self.model.created_at)).limit(limit).all()
    
    def add_file(self, session: Session, snapshot_id: int, file_id: int) -> bool:
        """
        Add a file to a snapshot.
        
        Args:
            session: The database session.
            snapshot_id: The snapshot ID.
            file_id: The file ID.
            
        Returns:
            True if the file was added, False otherwise.
        """
        snapshot = self.get_by_id(session, snapshot_id)
        file = session.query(File).filter(File.id == file_id).first()
        
        if snapshot and file and file not in snapshot.files:
            snapshot.files.append(file)
            session.flush()
            return True
        return False


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for AnalysisResult entities."""
    
    def __init__(self):
        super().__init__(AnalysisResult)
    
    def get_by_type(self, session: Session, repository_id: int, analysis_type: str) -> List[AnalysisResult]:
        """
        Get analysis results by type.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            analysis_type: The analysis type.
            
        Returns:
            A list of analysis results.
        """
        return session.query(self.model).filter(
            and_(self.model.repository_id == repository_id, self.model.analysis_type == analysis_type)
        ).all()
    
    def get_latest_by_type(self, session: Session, repository_id: int, analysis_type: str) -> Optional[AnalysisResult]:
        """
        Get the latest analysis result by type.
        
        Args:
            session: The database session.
            repository_id: The repository ID.
            analysis_type: The analysis type.
            
        Returns:
            The analysis result or None if not found.
        """
        return session.query(self.model).filter(
            and_(self.model.repository_id == repository_id, self.model.analysis_type == analysis_type)
        ).order_by(desc(self.model.created_at)).first()
    
    def mark_completed(self, session: Session, id: int, status: str = "success") -> Optional[AnalysisResult]:
        """
        Mark an analysis result as completed.
        
        Args:
            session: The database session.
            id: The analysis result ID.
            status: The completion status.
            
        Returns:
            The updated analysis result or None if not found.
        """
        return self.update(session, id, status=status, completed_at=datetime.utcnow())


class MetricRepository(BaseRepository[Metric]):
    """Repository for Metric entities."""
    
    def __init__(self):
        super().__init__(Metric)
    
    def get_by_name(self, session: Session, analysis_result_id: int, name: str) -> List[Metric]:
        """
        Get metrics by name.
        
        Args:
            session: The database session.
            analysis_result_id: The analysis result ID.
            name: The metric name.
            
        Returns:
            A list of metrics.
        """
        return session.query(self.model).filter(
            and_(self.model.analysis_result_id == analysis_result_id, self.model.name == name)
        ).all()
    
    def get_for_file(self, session: Session, file_id: int) -> List[Metric]:
        """
        Get metrics for a file.
        
        Args:
            session: The database session.
            file_id: The file ID.
            
        Returns:
            A list of metrics.
        """
        return session.query(self.model).filter(self.model.file_id == file_id).all()
    
    def get_for_symbol(self, session: Session, symbol_id: int) -> List[Metric]:
        """
        Get metrics for a symbol.
        
        Args:
            session: The database session.
            symbol_id: The symbol ID.
            
        Returns:
            A list of metrics.
        """
        return session.query(self.model).filter(self.model.symbol_id == symbol_id).all()


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue entities."""
    
    def __init__(self):
        super().__init__(Issue)
    
    def get_by_type(self, session: Session, analysis_result_id: int, type: str) -> List[Issue]:
        """
        Get issues by type.
        
        Args:
            session: The database session.
            analysis_result_id: The analysis result ID.
            type: The issue type.
            
        Returns:
            A list of issues.
        """
        return session.query(self.model).filter(
            and_(self.model.analysis_result_id == analysis_result_id, self.model.type == type)
        ).all()
    
    def get_by_severity(self, session: Session, analysis_result_id: int, severity: int) -> List[Issue]:
        """
        Get issues by severity.
        
        Args:
            session: The database session.
            analysis_result_id: The analysis result ID.
            severity: The issue severity.
            
        Returns:
            A list of issues.
        """
        return session.query(self.model).filter(
            and_(self.model.analysis_result_id == analysis_result_id, self.model.severity == severity)
        ).all()
    
    def get_for_file(self, session: Session, file_id: int) -> List[Issue]:
        """
        Get issues for a file.
        
        Args:
            session: The database session.
            file_id: The file ID.
            
        Returns:
            A list of issues.
        """
        return session.query(self.model).filter(self.model.file_id == file_id).all()
    
    def get_for_symbol(self, session: Session, symbol_id: int) -> List[Issue]:
        """
        Get issues for a symbol.
        
        Args:
            session: The database session.
            symbol_id: The symbol ID.
            
        Returns:
            A list of issues.
        """
        return session.query(self.model).filter(self.model.symbol_id == symbol_id).all()

