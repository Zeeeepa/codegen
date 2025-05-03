"""
Database Service for Codegen OSS

This module provides a service layer for interacting with the database,
abstracting away the details of the ORM and providing a clean API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

from sqlalchemy import create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class

from .models import (
    Base, Repository, Snapshot, CodeEntity, FileEntity, 
    FunctionEntity, ClassEntity, Analysis, AnalysisMetrics, EventLog
)
from ..snapshot.codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class DatabaseConfig:
    """Configuration for database connection."""
    
    def __init__(
        self,
        dialect: str = "postgresql",
        host: str = "localhost",
        port: int = 5432,
        username: str = "postgres",
        password: str = "postgres",
        database: str = "codegen_oss",
        pool_size: int = 5,
        max_overflow: int = 10,
        echo: bool = False,
    ):
        self.dialect = dialect
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
    
    @property
    def connection_string(self) -> str:
        """Get the database connection string."""
        return f"{self.dialect}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseService:
    """Service for interacting with the database."""
    
    def __init__(self, config: DatabaseConfig):
        """Initialize the database service with the given configuration."""
        self.config = config
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def _create_engine(self) -> Engine:
        """Create a SQLAlchemy engine with the configured parameters."""
        return create_engine(
            self.config.connection_string,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=self.config.echo,
        )
    
    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self) -> None:
        """Drop all tables from the database."""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
    
    def add(self, obj: T) -> T:
        """Add an object to the database and commit the transaction."""
        with self.get_session() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
    
    def add_all(self, objects: List[T]) -> List[T]:
        """Add multiple objects to the database and commit the transaction."""
        with self.get_session() as session:
            session.add_all(objects)
            session.commit()
            for obj in objects:
                session.refresh(obj)
            return objects
    
    def get_by_id(self, model: Type[T], id: Any) -> Optional[T]:
        """Get an object by its ID."""
        with self.get_session() as session:
            return session.query(model).filter(model.id == id).first()
    
    def get_all(self, model: Type[T], limit: int = 100, offset: int = 0) -> List[T]:
        """Get all objects of a given model with pagination."""
        with self.get_session() as session:
            return session.query(model).limit(limit).offset(offset).all()
    
    def update(self, obj: T) -> T:
        """Update an object in the database."""
        with self.get_session() as session:
            session.merge(obj)
            session.commit()
            session.refresh(obj)
            return obj
    
    def delete(self, obj: T) -> None:
        """Delete an object from the database."""
        with self.get_session() as session:
            session.delete(obj)
            session.commit()
    
    def delete_by_id(self, model: Type[T], id: Any) -> bool:
        """Delete an object by its ID."""
        with self.get_session() as session:
            obj = session.query(model).filter(model.id == id).first()
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
    
    # Repository-specific methods
    
    def get_repository_by_url(self, url: str) -> Optional[Repository]:
        """Get a repository by its URL."""
        with self.get_session() as session:
            return session.query(Repository).filter(Repository.url == url).first()
    
    def get_or_create_repository(self, url: str, name: str, description: Optional[str] = None) -> Repository:
        """Get a repository by URL or create it if it doesn't exist."""
        with self.get_session() as session:
            repo = session.query(Repository).filter(Repository.url == url).first()
            if not repo:
                repo = Repository(
                    url=url,
                    name=name,
                    description=description,
                )
                session.add(repo)
                session.commit()
                session.refresh(repo)
            return repo
    
    # Snapshot-specific methods
    
    def get_snapshot_by_commit(self, repository_id: Any, commit_sha: str) -> Optional[Snapshot]:
        """Get a snapshot by repository ID and commit SHA."""
        with self.get_session() as session:
            return session.query(Snapshot).filter(
                Snapshot.repository_id == repository_id,
                Snapshot.commit_sha == commit_sha
            ).first()
    
    def store_snapshot(self, codebase_snapshot: CodebaseSnapshot, repository_id: Any) -> Snapshot:
        """Store a CodebaseSnapshot in the database."""
        with self.get_session() as session:
            # Check if snapshot already exists
            existing = session.query(Snapshot).filter(
                Snapshot.repository_id == repository_id,
                Snapshot.commit_sha == codebase_snapshot.commit_sha
            ).first()
            
            if existing:
                return existing
            
            # Create new snapshot
            snapshot = Snapshot(
                repository_id=repository_id,
                commit_sha=codebase_snapshot.commit_sha,
                timestamp=codebase_snapshot.timestamp,
                metadata=codebase_snapshot.metadata,
            )
            session.add(snapshot)
            session.flush()  # Get the ID without committing
            
            # Process files
            for filepath, file_metric in codebase_snapshot.file_metrics.items():
                file_entity = FileEntity(
                    name=file_metric["name"],
                    qualified_name=filepath,
                    filepath=filepath,
                    content_hash=file_metric["content_hash"],
                    line_count=file_metric["line_count"],
                    language=filepath.split(".")[-1] if "." in filepath else None,
                    metadata={
                        "symbol_count": file_metric["symbol_count"],
                        "function_count": file_metric["function_count"],
                        "class_count": file_metric["class_count"],
                        "import_count": file_metric["import_count"],
                    }
                )
                session.add(file_entity)
                snapshot.entities.append(file_entity)
            
            # Process functions
            for qualified_name, func_metric in codebase_snapshot.function_metrics.items():
                function_entity = FunctionEntity(
                    name=func_metric["name"],
                    qualified_name=qualified_name,
                    filepath=func_metric["filepath"],
                    line_count=func_metric["line_count"],
                    parameter_count=func_metric["parameter_count"],
                    return_statement_count=func_metric["return_statement_count"],
                    cyclomatic_complexity=func_metric["cyclomatic_complexity"],
                    metadata={
                        "function_call_count": func_metric["function_call_count"],
                        "call_site_count": func_metric["call_site_count"],
                        "decorator_count": func_metric["decorator_count"],
                        "dependency_count": func_metric["dependency_count"],
                    }
                )
                session.add(function_entity)
                snapshot.entities.append(function_entity)
            
            # Process classes
            for qualified_name, class_metric in codebase_snapshot.class_metrics.items():
                class_entity = ClassEntity(
                    name=class_metric["name"],
                    qualified_name=qualified_name,
                    filepath=class_metric["filepath"],
                    parent_class_names=class_metric["parent_class_count"],
                    metadata={
                        "method_count": class_metric["method_count"],
                        "attribute_count": class_metric["attribute_count"],
                        "decorator_count": class_metric["decorator_count"],
                        "dependency_count": class_metric["dependency_count"],
                    }
                )
                session.add(class_entity)
                snapshot.entities.append(class_entity)
            
            # Commit all changes
            session.commit()
            session.refresh(snapshot)
            return snapshot
    
    def compare_snapshots(self, snapshot_id_1: Any, snapshot_id_2: Any) -> Dict[str, Any]:
        """Compare two snapshots and return the differences."""
        with self.get_session() as session:
            snapshot1 = session.query(Snapshot).filter(Snapshot.id == snapshot_id_1).first()
            snapshot2 = session.query(Snapshot).filter(Snapshot.id == snapshot_id_2).first()
            
            if not snapshot1 or not snapshot2:
                raise ValueError("One or both snapshots not found")
            
            # Get entities for both snapshots
            entities1 = {e.qualified_name: e for e in snapshot1.entities}
            entities2 = {e.qualified_name: e for e in snapshot2.entities}
            
            # Find added, removed, and modified entities
            added = [name for name in entities2 if name not in entities1]
            removed = [name for name in entities1 if name not in entities2]
            modified = []
            
            for name in entities1:
                if name in entities2:
                    e1, e2 = entities1[name], entities2[name]
                    if e1.content_hash != e2.content_hash:
                        modified.append(name)
            
            # Calculate metrics
            metrics = {
                "total_entities_1": len(entities1),
                "total_entities_2": len(entities2),
                "added_count": len(added),
                "removed_count": len(removed),
                "modified_count": len(modified),
                "unchanged_count": len([name for name in entities1 if name in entities2 and name not in modified]),
            }
            
            return {
                "snapshot1": {
                    "id": str(snapshot1.id),
                    "commit_sha": snapshot1.commit_sha,
                    "timestamp": snapshot1.timestamp.isoformat(),
                },
                "snapshot2": {
                    "id": str(snapshot2.id),
                    "commit_sha": snapshot2.commit_sha,
                    "timestamp": snapshot2.timestamp.isoformat(),
                },
                "metrics": metrics,
                "added": added,
                "removed": removed,
                "modified": modified,
            }
    
    # Analysis-specific methods
    
    def create_analysis(
        self, 
        repository_id: Any, 
        analysis_type: str, 
        snapshot_id: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
    ) -> Analysis:
        """Create a new analysis record."""
        with self.get_session() as session:
            analysis = Analysis(
                repository_id=repository_id,
                snapshot_id=snapshot_id,
                analysis_type=analysis_type,
                data=data or {},
                summary=summary,
                status="pending",
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis
    
    def update_analysis_status(
        self, 
        analysis_id: Any, 
        status: str, 
        data: Optional[Dict[str, Any]] = None,
        summary: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Analysis:
        """Update the status of an analysis."""
        with self.get_session() as session:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                raise ValueError(f"Analysis with ID {analysis_id} not found")
            
            analysis.status = status
            if data:
                analysis.data = data
            if summary:
                analysis.summary = summary
            if error_message:
                analysis.error_message = error_message
            
            session.commit()
            session.refresh(analysis)
            return analysis
    
    def record_analysis_metrics(
        self,
        analysis_id: Any,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        cpu_usage_percent: Optional[float] = None,
        memory_usage_mb: Optional[float] = None,
        error: Optional[str] = None,
    ) -> AnalysisMetrics:
        """Record performance metrics for an analysis run."""
        with self.get_session() as session:
            metrics = AnalysisMetrics(
                analysis_id=analysis_id,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=(end_time - start_time).total_seconds() if end_time else None,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_mb=memory_usage_mb,
                error=error,
            )
            session.add(metrics)
            session.commit()
            session.refresh(metrics)
            return metrics
    
    # Event logging methods
    
    def log_event(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        repository_id: Optional[Any] = None,
        snapshot_id: Optional[Any] = None,
        analysis_id: Optional[Any] = None,
    ) -> EventLog:
        """Log a system event."""
        with self.get_session() as session:
            event = EventLog(
                event_type=event_type,
                data=data or {},
                repository_id=repository_id,
                snapshot_id=snapshot_id,
                analysis_id=analysis_id,
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        repository_id: Optional[Any] = None,
        snapshot_id: Optional[Any] = None,
        analysis_id: Optional[Any] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EventLog]:
        """Get events with optional filtering."""
        with self.get_session() as session:
            query = session.query(EventLog)
            
            if event_type:
                query = query.filter(EventLog.event_type == event_type)
            if repository_id:
                query = query.filter(EventLog.repository_id == repository_id)
            if snapshot_id:
                query = query.filter(EventLog.snapshot_id == snapshot_id)
            if analysis_id:
                query = query.filter(EventLog.analysis_id == analysis_id)
            
            return query.order_by(EventLog.timestamp.desc()).limit(limit).offset(offset).all()

