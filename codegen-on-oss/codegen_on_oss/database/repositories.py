"""
Repository pattern implementation for database operations.

This module provides repository classes for database operations.
"""

from typing import List, Optional, Dict, Any, TypeVar, Generic, Type
from sqlalchemy.orm import Session

from codegen_on_oss.database.models import (
    Repository, Snapshot, File, Function, Class, Import,
    AnalysisResult, Issue, SymbolAnalysis, DependencyGraph, CodeMetrics, AnalysisJob
)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository class for database operations."""

    def __init__(self, db: Session, model_class: Type[T]):
        """
        Initialize the repository.

        Args:
            db: Database session
            model_class: Model class
        """
        self.db = db
        self.model = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all entities.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> T:
        """
        Create a new entity.

        Args:
            **kwargs: Entity attributes

        Returns:
            Created entity
        """
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update an entity.

        Args:
            id: Entity ID
            **kwargs: Entity attributes to update

        Returns:
            Updated entity or None if not found
        """
        entity = self.get_by_id(id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            self.db.commit()
            self.db.refresh(entity)
        return entity

    def delete(self, id: int) -> bool:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_id(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for Repository entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, Repository)

    def get_by_url(self, url: str) -> Optional[Repository]:
        """
        Get a repository by URL.

        Args:
            url: Repository URL

        Returns:
            Repository or None if not found
        """
        return self.db.query(self.model).filter(self.model.url == url).first()


class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for Snapshot entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, Snapshot)

    def get_by_snapshot_id(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a snapshot by snapshot ID.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            Snapshot or None if not found
        """
        return self.db.query(self.model).filter(self.model.snapshot_id == snapshot_id).first()

    def get_snapshots_for_repository(self, repo_id: int) -> List[Snapshot]:
        """
        Get snapshots for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            List of snapshots
        """
        return self.db.query(self.model).filter(self.model.repository_id == repo_id).all()

    def get_latest_for_repository(self, repo_id: int) -> Optional[Snapshot]:
        """
        Get the latest snapshot for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            Latest snapshot or None if not found
        """
        return (
            self.db.query(self.model)
            .filter(self.model.repository_id == repo_id)
            .order_by(self.model.timestamp.desc())
            .first()
        )


class FileRepository(BaseRepository[File]):
    """Repository for File entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, File)

    def get_by_filepath(self, snapshot_id: int, filepath: str) -> Optional[File]:
        """
        Get a file by filepath.

        Args:
            snapshot_id: Snapshot ID
            filepath: File path

        Returns:
            File or None if not found
        """
        return (
            self.db.query(self.model)
            .filter(self.model.snapshot_id == snapshot_id, self.model.filepath == filepath)
            .first()
        )

    def get_files_for_snapshot(self, snapshot_id: int) -> List[File]:
        """
        Get files for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of files
        """
        return self.db.query(self.model).filter(self.model.snapshot_id == snapshot_id).all()


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for AnalysisResult entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, AnalysisResult)

    def get_results_for_snapshot(self, snapshot_id: int) -> List[AnalysisResult]:
        """
        Get analysis results for a snapshot.

        Args:
            snapshot_id: Snapshot ID

        Returns:
            List of analysis results
        """
        return self.db.query(self.model).filter(self.model.snapshot_id == snapshot_id).all()

    def get_results_for_repository(self, repo_id: int) -> List[AnalysisResult]:
        """
        Get analysis results for a repository.

        Args:
            repo_id: Repository ID

        Returns:
            List of analysis results
        """
        return self.db.query(self.model).filter(self.model.repository_id == repo_id).all()

    def get_latest_result_for_snapshot(self, snapshot_id: int, analysis_type: str) -> Optional[AnalysisResult]:
        """
        Get the latest analysis result for a snapshot and analysis type.

        Args:
            snapshot_id: Snapshot ID
            analysis_type: Analysis type

        Returns:
            Latest analysis result or None if not found
        """
        return (
            self.db.query(self.model)
            .filter(self.model.snapshot_id == snapshot_id, self.model.analysis_type == analysis_type)
            .order_by(self.model.created_at.desc())
            .first()
        )


class AnalysisIssueRepository(BaseRepository[Issue]):
    """Repository for Issue entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, Issue)

    def get_issues_for_analysis(self, analysis_id: int) -> List[Issue]:
        """
        Get issues for an analysis result.

        Args:
            analysis_id: Analysis result ID

        Returns:
            List of issues
        """
        return self.db.query(self.model).filter(self.model.analysis_result_id == analysis_id).all()


class AnalysisJobRepository(BaseRepository[AnalysisJob]):
    """Repository for AnalysisJob entities."""

    def __init__(self, db: Session):
        """
        Initialize the repository.

        Args:
            db: Database session
        """
        super().__init__(db, AnalysisJob)

    def get_jobs_for_repo(self, repo_id: int, status: Optional[str] = None) -> List[AnalysisJob]:
        """
        Get jobs for a repository.

        Args:
            repo_id: Repository ID
            status: Optional status filter

        Returns:
            List of jobs
        """
        query = self.db.query(self.model).filter(self.model.repository == repo_id)
        if status:
            query = query.filter(self.model.status == status)
        return query.all()

