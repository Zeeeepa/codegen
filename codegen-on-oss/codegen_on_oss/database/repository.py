"""
Repository pattern for database operations.
"""
from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast

from sqlalchemy.orm import Session

from codegen_on_oss.database.models import (
    AnalysisResult,
    Base,
    Commit,
    File,
    Issue,
    Metric,
    Repository,
    Snapshot,
    Symbol,
)

# Type variable for models
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository for database operations."""

    def __init__(self, session: Session, model_class: Any):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
            model_class: Model class
        """
        self.session = session
        self.model_class = model_class

    def get_all(self) -> List[T]:
        """Get all records.

        Returns:
            List of records
        """
        return self.session.query(self.model_class).all()

    def get_by_id(self, id: int) -> Optional[T]:
        """Get a record by ID.

        Args:
            id: Record ID

        Returns:
            Record or None
        """
        return self.session.query(self.model_class).filter(self.model_class.id == id).first()

    def create(self, **kwargs: Any) -> T:
        """Create a new record.

        Args:
            **kwargs: Record attributes

        Returns:
            Created record
        """
        record = self.model_class(**kwargs)
        self.session.add(record)
        self.session.commit()
        return record

    def update(self, id: int, **kwargs: Any) -> Optional[T]:
        """Update a record.

        Args:
            id: Record ID
            **kwargs: Record attributes to update

        Returns:
            Updated record or None
        """
        record = self.get_by_id(id)
        if record:
            for key, value in kwargs.items():
                setattr(record, key, value)
            self.session.commit()
        return record

    def delete(self, id: int) -> bool:
        """Delete a record.

        Args:
            id: Record ID

        Returns:
            True if deleted, False otherwise
        """
        record = self.get_by_id(id)
        if record:
            self.session.delete(record)
            self.session.commit()
            return True
        return False

    def filter_by(self, **kwargs: Any) -> List[T]:
        """Filter records by attributes.

        Args:
            **kwargs: Filter criteria

        Returns:
            List of records
        """
        return self.session.query(self.model_class).filter_by(**kwargs).all()

    def first_by(self, **kwargs: Any) -> Optional[T]:
        """Get first record by attributes.

        Args:
            **kwargs: Filter criteria

        Returns:
            Record or None
        """
        return self.session.query(self.model_class).filter_by(**kwargs).first()


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for Repository model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Repository)

    def get_by_url(self, url: str) -> Optional[Repository]:
        """Get a repository by URL.

        Args:
            url: Repository URL

        Returns:
            Repository or None
        """
        return self.first_by(url=url)


class CommitRepository(BaseRepository[Commit]):
    """Repository for Commit model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Commit)

    def get_by_sha(self, repository_id: int, sha: str) -> Optional[Commit]:
        """Get a commit by SHA.

        Args:
            repository_id: Repository ID
            sha: Commit SHA

        Returns:
            Commit or None
        """
        return self.first_by(repository_id=repository_id, sha=sha)


class FileRepository(BaseRepository[File]):
    """Repository for File model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, File)

    def get_by_path(self, repository_id: int, path: str) -> Optional[File]:
        """Get a file by path.

        Args:
            repository_id: Repository ID
            path: File path

        Returns:
            File or None
        """
        return self.first_by(repository_id=repository_id, path=path)


class SymbolRepository(BaseRepository[Symbol]):
    """Repository for Symbol model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Symbol)

    def get_by_name(self, name: str) -> List[Symbol]:
        """Get symbols by name.

        Args:
            name: Symbol name

        Returns:
            List of symbols
        """
        return self.filter_by(name=name)


class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for Snapshot model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Snapshot)


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for AnalysisResult model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, AnalysisResult)


class MetricRepository(BaseRepository[Metric]):
    """Repository for Metric model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Metric)


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue model."""

    def __init__(self, session: Session):
        """Initialize the repository.

        Args:
            session: SQLAlchemy session
        """
        super().__init__(session, Issue)

