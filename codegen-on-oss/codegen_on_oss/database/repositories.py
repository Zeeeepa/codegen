"""
Database Repositories Module

This module provides repository classes for accessing and manipulating data in the database.
Each repository class corresponds to a specific entity in the data model.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Generic, TypeVar, Type

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, not_, desc, asc

from codegen_on_oss.database.models import (
    Repository, Snapshot, AnalysisResult, AnalysisIssue, 
    File, Function, Class, FileMetric, FunctionMetric, ClassMetric,
    WebhookConfig, AnalysisJob
)

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Base repository class with common CRUD operations.
    
    This class provides generic methods for creating, reading, updating, and deleting
    entities in the database.
    """
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Initialize the repository.
        
        Args:
            db: The database session
            model: The model class this repository operates on
        """
        self.db = db
        self.model = model
    
    def create(self, **kwargs) -> T:
        """
        Create a new entity.
        
        Args:
            **kwargs: Entity attributes
            
        Returns:
            The created entity
        """
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Get an entity by its ID.
        
        Args:
            id: The entity ID
            
        Returns:
            The entity if found, None otherwise
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all entities with pagination.
        
        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return
            
        Returns:
            A list of entities
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update an entity.
        
        Args:
            id: The entity ID
            **kwargs: Entity attributes to update
            
        Returns:
            The updated entity if found, None otherwise
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
            id: The entity ID
            
        Returns:
            True if the entity was deleted, False otherwise
        """
        entity = self.get_by_id(id)
        if entity:
            self.db.delete(entity)
            self.db.commit()
            return True
        return False

class RepositoryRepository(BaseRepository[Repository]):
    """Repository for managing Repository entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, Repository)
    
    def get_by_url(self, url: str) -> Optional[Repository]:
        """
        Get a repository by its URL.
        
        Args:
            url: The repository URL
            
        Returns:
            The repository if found, None otherwise
        """
        return self.db.query(Repository).filter(Repository.url == url).first()
    
    def get_or_create(self, url: str, name: str, **kwargs) -> Repository:
        """
        Get a repository by its URL or create it if it doesn't exist.
        
        Args:
            url: The repository URL
            name: The repository name
            **kwargs: Additional repository attributes
            
        Returns:
            The repository
        """
        repository = self.get_by_url(url)
        if not repository:
            repository = self.create(url=url, name=name, **kwargs)
        return repository

class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for managing Snapshot entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, Snapshot)
    
    def get_by_snapshot_id(self, snapshot_id: str) -> Optional[Snapshot]:
        """
        Get a snapshot by its snapshot ID.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            The snapshot if found, None otherwise
        """
        return self.db.query(Snapshot).filter(Snapshot.snapshot_id == snapshot_id).first()
    
    def get_by_commit_sha(self, repo_id: int, commit_sha: str) -> Optional[Snapshot]:
        """
        Get a snapshot by its repository ID and commit SHA.
        
        Args:
            repo_id: The repository ID
            commit_sha: The commit SHA
            
        Returns:
            The snapshot if found, None otherwise
        """
        return self.db.query(Snapshot).filter(
            Snapshot.repo_id == repo_id,
            Snapshot.commit_sha == commit_sha
        ).first()
    
    def get_latest_for_repo(self, repo_id: int) -> Optional[Snapshot]:
        """
        Get the latest snapshot for a repository.
        
        Args:
            repo_id: The repository ID
            
        Returns:
            The latest snapshot if found, None otherwise
        """
        return self.db.query(Snapshot).filter(
            Snapshot.repo_id == repo_id
        ).order_by(desc(Snapshot.timestamp)).first()

class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for managing AnalysisResult entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, AnalysisResult)
    
    def get_by_snapshot_id(self, snapshot_id: int) -> List[AnalysisResult]:
        """
        Get analysis results by snapshot ID.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            A list of analysis results
        """
        return self.db.query(AnalysisResult).filter(
            AnalysisResult.snapshot_id == snapshot_id
        ).all()
    
    def get_latest_for_repo(self, repo_id: int, analysis_type: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Get the latest analysis result for a repository.
        
        Args:
            repo_id: The repository ID
            analysis_type: Optional analysis type filter
            
        Returns:
            The latest analysis result if found, None otherwise
        """
        query = self.db.query(AnalysisResult).filter(AnalysisResult.repo_id == repo_id)
        if analysis_type:
            query = query.filter(AnalysisResult.analysis_type == analysis_type)
        return query.order_by(desc(AnalysisResult.timestamp)).first()

class FileRepository(BaseRepository[File]):
    """Repository for managing File entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, File)
    
    def get_by_filepath(self, snapshot_id: int, filepath: str) -> Optional[File]:
        """
        Get a file by its snapshot ID and filepath.
        
        Args:
            snapshot_id: The snapshot ID
            filepath: The file path
            
        Returns:
            The file if found, None otherwise
        """
        return self.db.query(File).filter(
            File.snapshot_id == snapshot_id,
            File.filepath == filepath
        ).first()
    
    def get_files_for_snapshot(self, snapshot_id: int) -> List[File]:
        """
        Get all files for a snapshot.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            A list of files
        """
        return self.db.query(File).filter(File.snapshot_id == snapshot_id).all()

class FunctionRepository(BaseRepository[Function]):
    """Repository for managing Function entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, Function)
    
    def get_by_qualified_name(self, file_id: int, qualified_name: str) -> Optional[Function]:
        """
        Get a function by its file ID and qualified name.
        
        Args:
            file_id: The file ID
            qualified_name: The qualified function name
            
        Returns:
            The function if found, None otherwise
        """
        return self.db.query(Function).filter(
            Function.file_id == file_id,
            Function.qualified_name == qualified_name
        ).first()
    
    def get_functions_for_file(self, file_id: int) -> List[Function]:
        """
        Get all functions for a file.
        
        Args:
            file_id: The file ID
            
        Returns:
            A list of functions
        """
        return self.db.query(Function).filter(Function.file_id == file_id).all()

class ClassRepository(BaseRepository[Class]):
    """Repository for managing Class entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, Class)
    
    def get_by_qualified_name(self, file_id: int, qualified_name: str) -> Optional[Class]:
        """
        Get a class by its file ID and qualified name.
        
        Args:
            file_id: The file ID
            qualified_name: The qualified class name
            
        Returns:
            The class if found, None otherwise
        """
        return self.db.query(Class).filter(
            Class.file_id == file_id,
            Class.qualified_name == qualified_name
        ).first()
    
    def get_classes_for_file(self, file_id: int) -> List[Class]:
        """
        Get all classes for a file.
        
        Args:
            file_id: The file ID
            
        Returns:
            A list of classes
        """
        return self.db.query(Class).filter(Class.file_id == file_id).all()

class AnalysisIssueRepository(BaseRepository[AnalysisIssue]):
    """Repository for managing AnalysisIssue entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, AnalysisIssue)
    
    def get_issues_for_analysis(self, analysis_result_id: int) -> List[AnalysisIssue]:
        """
        Get all issues for an analysis result.
        
        Args:
            analysis_result_id: The analysis result ID
            
        Returns:
            A list of issues
        """
        return self.db.query(AnalysisIssue).filter(
            AnalysisIssue.analysis_result_id == analysis_result_id
        ).all()
    
    def get_issues_for_file(self, file_id: int) -> List[AnalysisIssue]:
        """
        Get all issues for a file.
        
        Args:
            file_id: The file ID
            
        Returns:
            A list of issues
        """
        file = self.db.query(File).get(file_id)
        if file:
            return file.issues
        return []

class FileMetricRepository(BaseRepository[FileMetric]):
    """Repository for managing FileMetric entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, FileMetric)
    
    def get_metrics_for_file(self, file_id: int) -> List[FileMetric]:
        """
        Get all metrics for a file.
        
        Args:
            file_id: The file ID
            
        Returns:
            A list of file metrics
        """
        return self.db.query(FileMetric).filter(FileMetric.file_id == file_id).all()
    
    def get_metrics_for_analysis(self, analysis_result_id: int) -> List[FileMetric]:
        """
        Get all file metrics for an analysis result.
        
        Args:
            analysis_result_id: The analysis result ID
            
        Returns:
            A list of file metrics
        """
        return self.db.query(FileMetric).filter(
            FileMetric.analysis_result_id == analysis_result_id
        ).all()

class FunctionMetricRepository(BaseRepository[FunctionMetric]):
    """Repository for managing FunctionMetric entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, FunctionMetric)
    
    def get_metrics_for_function(self, function_id: int) -> List[FunctionMetric]:
        """
        Get all metrics for a function.
        
        Args:
            function_id: The function ID
            
        Returns:
            A list of function metrics
        """
        return self.db.query(FunctionMetric).filter(
            FunctionMetric.function_id == function_id
        ).all()

class ClassMetricRepository(BaseRepository[ClassMetric]):
    """Repository for managing ClassMetric entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, ClassMetric)
    
    def get_metrics_for_class(self, class_id: int) -> List[ClassMetric]:
        """
        Get all metrics for a class.
        
        Args:
            class_id: The class ID
            
        Returns:
            A list of class metrics
        """
        return self.db.query(ClassMetric).filter(
            ClassMetric.class_id == class_id
        ).all()

class WebhookConfigRepository(BaseRepository[WebhookConfig]):
    """Repository for managing WebhookConfig entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, WebhookConfig)
    
    def get_webhooks_for_repo(self, repo_id: int) -> List[WebhookConfig]:
        """
        Get all webhook configurations for a repository.
        
        Args:
            repo_id: The repository ID
            
        Returns:
            A list of webhook configurations
        """
        return self.db.query(WebhookConfig).filter(
            WebhookConfig.repo_id == repo_id
        ).all()

class AnalysisJobRepository(BaseRepository[AnalysisJob]):
    """Repository for managing AnalysisJob entities."""
    
    def __init__(self, db: Session):
        super().__init__(db, AnalysisJob)
    
    def get_jobs_for_repo(self, repo_id: int, status: Optional[str] = None) -> List[AnalysisJob]:
        """
        Get all analysis jobs for a repository.
        
        Args:
            repo_id: The repository ID
            status: Optional status filter
            
        Returns:
            A list of analysis jobs
        """
        query = self.db.query(AnalysisJob).filter(AnalysisJob.repo_id == repo_id)
        if status:
            query = query.filter(AnalysisJob.status == status)
        return query.order_by(desc(AnalysisJob.created_at)).all()
    
    def get_pending_jobs(self) -> List[AnalysisJob]:
        """
        Get all pending analysis jobs.
        
        Returns:
            A list of pending analysis jobs
        """
        return self.db.query(AnalysisJob).filter(
            AnalysisJob.status == "pending"
        ).order_by(asc(AnalysisJob.created_at)).all()
"""

