"""
Repository pattern implementation for database operations.

This module provides repository classes for performing CRUD operations on database models.
"""

import logging
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type, Union
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, not_, desc, asc

from codegen_on_oss.database.models import (
    Base, Repository, Snapshot, File, Function, Class, Import, 
    AnalysisResult, Issue, UserPreference, WebhookConfig
)
from codegen_on_oss.database.connection import get_db_manager

logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """
    Base repository class for database operations.
    
    This class provides generic CRUD operations for database models.
    """
    
    def __init__(self, model_class: Type[T]):
        """
        Initialize the repository.
        
        Args:
            model_class: SQLAlchemy model class.
        """
        self.model_class = model_class
        self.db_manager = get_db_manager()
    
    def create(self, **kwargs) -> T:
        """
        Create a new record.
        
        Args:
            **kwargs: Model attributes.
            
        Returns:
            Created model instance.
        """
        with self.db_manager.session_scope() as session:
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance
    
    def get_by_id(self, id: str) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            id: Record ID.
            
        Returns:
            Model instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        Get all records.
        
        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.
            
        Returns:
            List of model instances.
        """
        with self.db_manager.session_scope() as session:
            query = session.query(self.model_class)
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
            return query.all()
    
    def update(self, id: str, **kwargs) -> Optional[T]:
        """
        Update a record.
        
        Args:
            id: Record ID.
            **kwargs: Model attributes to update.
            
        Returns:
            Updated model instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            instance = session.query(self.model_class).filter(self.model_class.id == id).first()
            if instance:
                for key, value in kwargs.items():
                    setattr(instance, key, value)
                session.flush()
                session.refresh(instance)
                return instance
            return None
    
    def delete(self, id: str) -> bool:
        """
        Delete a record.
        
        Args:
            id: Record ID.
            
        Returns:
            True if the record was deleted, False otherwise.
        """
        with self.db_manager.session_scope() as session:
            instance = session.query(self.model_class).filter(self.model_class.id == id).first()
            if instance:
                session.delete(instance)
                return True
            return False
    
    def count(self) -> int:
        """
        Count all records.
        
        Returns:
            Number of records.
        """
        with self.db_manager.session_scope() as session:
            return session.query(self.model_class).count()
    
    def exists(self, id: str) -> bool:
        """
        Check if a record exists.
        
        Args:
            id: Record ID.
            
        Returns:
            True if the record exists, False otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(session.query(self.model_class).filter(
                self.model_class.id == id
            ).exists()).scalar()


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for Repository model."""
    
    def __init__(self):
        super().__init__(Repository)
    
    def get_by_url(self, url: str) -> Optional[Repository]:
        """
        Get a repository by URL.
        
        Args:
            url: Repository URL.
            
        Returns:
            Repository instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Repository).filter(Repository.url == url).first()
    
    def get_or_create(self, url: str, name: str, **kwargs) -> Repository:
        """
        Get a repository by URL or create it if it doesn't exist.
        
        Args:
            url: Repository URL.
            name: Repository name.
            **kwargs: Additional repository attributes.
            
        Returns:
            Repository instance.
        """
        with self.db_manager.session_scope() as session:
            repository = session.query(Repository).filter(Repository.url == url).first()
            if not repository:
                repository = Repository(url=url, name=name, **kwargs)
                session.add(repository)
                session.flush()
                session.refresh(repository)
            return repository


class SnapshotRepository(BaseRepository[Snapshot]):
    """Repository for Snapshot model."""
    
    def __init__(self):
        super().__init__(Snapshot)
    
    def get_by_commit_sha(self, repository_id: str, commit_sha: str) -> Optional[Snapshot]:
        """
        Get a snapshot by repository ID and commit SHA.
        
        Args:
            repository_id: Repository ID.
            commit_sha: Commit SHA.
            
        Returns:
            Snapshot instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Snapshot).filter(
                Snapshot.repository_id == repository_id,
                Snapshot.commit_sha == commit_sha
            ).first()
    
    def get_latest_for_repository(self, repository_id: str) -> Optional[Snapshot]:
        """
        Get the latest snapshot for a repository.
        
        Args:
            repository_id: Repository ID.
            
        Returns:
            Latest snapshot instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Snapshot).filter(
                Snapshot.repository_id == repository_id
            ).order_by(desc(Snapshot.timestamp)).first()
    
    def get_snapshots_for_repository(
        self, 
        repository_id: str, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[Snapshot]:
        """
        Get snapshots for a repository.
        
        Args:
            repository_id: Repository ID.
            limit: Maximum number of snapshots to return.
            offset: Number of snapshots to skip.
            
        Returns:
            List of snapshot instances.
        """
        with self.db_manager.session_scope() as session:
            query = session.query(Snapshot).filter(
                Snapshot.repository_id == repository_id
            ).order_by(desc(Snapshot.timestamp))
            
            if limit is not None:
                query = query.limit(limit)
            if offset is not None:
                query = query.offset(offset)
                
            return query.all()


class FileRepository(BaseRepository[File]):
    """Repository for File model."""
    
    def __init__(self):
        super().__init__(File)
    
    def get_by_filepath(self, filepath: str) -> Optional[File]:
        """
        Get a file by filepath.
        
        Args:
            filepath: File path.
            
        Returns:
            File instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(File).filter(File.filepath == filepath).first()
    
    def get_by_content_hash(self, content_hash: str) -> Optional[File]:
        """
        Get a file by content hash.
        
        Args:
            content_hash: Content hash.
            
        Returns:
            File instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(File).filter(File.content_hash == content_hash).first()
    
    def get_or_create(self, filepath: str, name: str, content_hash: str, **kwargs) -> File:
        """
        Get a file by filepath or create it if it doesn't exist.
        
        Args:
            filepath: File path.
            name: File name.
            content_hash: Content hash.
            **kwargs: Additional file attributes.
            
        Returns:
            File instance.
        """
        with self.db_manager.session_scope() as session:
            file = session.query(File).filter(File.filepath == filepath).first()
            if not file:
                file = File(filepath=filepath, name=name, content_hash=content_hash, **kwargs)
                session.add(file)
                session.flush()
                session.refresh(file)
            return file


class FunctionRepository(BaseRepository[Function]):
    """Repository for Function model."""
    
    def __init__(self):
        super().__init__(Function)
    
    def get_by_qualified_name(self, qualified_name: str) -> Optional[Function]:
        """
        Get a function by qualified name.
        
        Args:
            qualified_name: Fully qualified function name.
            
        Returns:
            Function instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Function).filter(Function.qualified_name == qualified_name).first()
    
    def get_by_file_id(self, file_id: str) -> List[Function]:
        """
        Get functions by file ID.
        
        Args:
            file_id: File ID.
            
        Returns:
            List of function instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Function).filter(Function.file_id == file_id).all()
    
    def get_or_create(self, qualified_name: str, name: str, **kwargs) -> Function:
        """
        Get a function by qualified name or create it if it doesn't exist.
        
        Args:
            qualified_name: Fully qualified function name.
            name: Function name.
            **kwargs: Additional function attributes.
            
        Returns:
            Function instance.
        """
        with self.db_manager.session_scope() as session:
            function = session.query(Function).filter(Function.qualified_name == qualified_name).first()
            if not function:
                function = Function(qualified_name=qualified_name, name=name, **kwargs)
                session.add(function)
                session.flush()
                session.refresh(function)
            return function


class ClassRepository(BaseRepository[Class]):
    """Repository for Class model."""
    
    def __init__(self):
        super().__init__(Class)
    
    def get_by_qualified_name(self, qualified_name: str) -> Optional[Class]:
        """
        Get a class by qualified name.
        
        Args:
            qualified_name: Fully qualified class name.
            
        Returns:
            Class instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Class).filter(Class.qualified_name == qualified_name).first()
    
    def get_by_file_id(self, file_id: str) -> List[Class]:
        """
        Get classes by file ID.
        
        Args:
            file_id: File ID.
            
        Returns:
            List of class instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Class).filter(Class.file_id == file_id).all()
    
    def get_or_create(self, qualified_name: str, name: str, **kwargs) -> Class:
        """
        Get a class by qualified name or create it if it doesn't exist.
        
        Args:
            qualified_name: Fully qualified class name.
            name: Class name.
            **kwargs: Additional class attributes.
            
        Returns:
            Class instance.
        """
        with self.db_manager.session_scope() as session:
            class_obj = session.query(Class).filter(Class.qualified_name == qualified_name).first()
            if not class_obj:
                class_obj = Class(qualified_name=qualified_name, name=name, **kwargs)
                session.add(class_obj)
                session.flush()
                session.refresh(class_obj)
            return class_obj


class ImportRepository(BaseRepository[Import]):
    """Repository for Import model."""
    
    def __init__(self):
        super().__init__(Import)
    
    def get_by_module_and_symbol(
        self, 
        module_name: str, 
        imported_symbol: Optional[str] = None, 
        alias: Optional[str] = None
    ) -> Optional[Import]:
        """
        Get an import by module name, imported symbol, and alias.
        
        Args:
            module_name: Module name.
            imported_symbol: Imported symbol name.
            alias: Import alias.
            
        Returns:
            Import instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            query = session.query(Import).filter(Import.module_name == module_name)
            
            if imported_symbol is not None:
                query = query.filter(Import.imported_symbol == imported_symbol)
            
            if alias is not None:
                query = query.filter(Import.alias == alias)
                
            return query.first()
    
    def get_or_create(
        self, 
        module_name: str, 
        imported_symbol: Optional[str] = None, 
        alias: Optional[str] = None
    ) -> Import:
        """
        Get an import by module name, imported symbol, and alias or create it if it doesn't exist.
        
        Args:
            module_name: Module name.
            imported_symbol: Imported symbol name.
            alias: Import alias.
            
        Returns:
            Import instance.
        """
        with self.db_manager.session_scope() as session:
            import_obj = self.get_by_module_and_symbol(module_name, imported_symbol, alias)
            if not import_obj:
                import_obj = Import(
                    module_name=module_name,
                    imported_symbol=imported_symbol,
                    alias=alias
                )
                session.add(import_obj)
                session.flush()
                session.refresh(import_obj)
            return import_obj


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for AnalysisResult model."""
    
    def __init__(self):
        super().__init__(AnalysisResult)
    
    def get_by_snapshot_and_type(self, snapshot_id: str, analysis_type: str) -> Optional[AnalysisResult]:
        """
        Get an analysis result by snapshot ID and analysis type.
        
        Args:
            snapshot_id: Snapshot ID.
            analysis_type: Analysis type.
            
        Returns:
            AnalysisResult instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(AnalysisResult).filter(
                AnalysisResult.snapshot_id == snapshot_id,
                AnalysisResult.analysis_type == analysis_type
            ).first()
    
    def get_by_snapshot(self, snapshot_id: str) -> List[AnalysisResult]:
        """
        Get analysis results by snapshot ID.
        
        Args:
            snapshot_id: Snapshot ID.
            
        Returns:
            List of AnalysisResult instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(AnalysisResult).filter(
                AnalysisResult.snapshot_id == snapshot_id
            ).all()


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue model."""
    
    def __init__(self):
        super().__init__(Issue)
    
    def get_by_analysis_result(self, analysis_result_id: str) -> List[Issue]:
        """
        Get issues by analysis result ID.
        
        Args:
            analysis_result_id: Analysis result ID.
            
        Returns:
            List of Issue instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Issue).filter(
                Issue.analysis_result_id == analysis_result_id
            ).all()
    
    def get_by_file(self, file_id: str) -> List[Issue]:
        """
        Get issues by file ID.
        
        Args:
            file_id: File ID.
            
        Returns:
            List of Issue instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Issue).filter(
                Issue.file_id == file_id
            ).all()
    
    def get_by_type_and_severity(
        self, 
        issue_type: str, 
        severity: str
    ) -> List[Issue]:
        """
        Get issues by type and severity.
        
        Args:
            issue_type: Issue type.
            severity: Issue severity.
            
        Returns:
            List of Issue instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(Issue).filter(
                Issue.issue_type == issue_type,
                Issue.severity == severity
            ).all()


class UserPreferenceRepository(BaseRepository[UserPreference]):
    """Repository for UserPreference model."""
    
    def __init__(self):
        super().__init__(UserPreference)
    
    def get_by_user_and_key(self, user_id: str, preference_key: str) -> Optional[UserPreference]:
        """
        Get a user preference by user ID and preference key.
        
        Args:
            user_id: User ID.
            preference_key: Preference key.
            
        Returns:
            UserPreference instance if found, None otherwise.
        """
        with self.db_manager.session_scope() as session:
            return session.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == preference_key
            ).first()
    
    def get_all_for_user(self, user_id: str) -> List[UserPreference]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: User ID.
            
        Returns:
            List of UserPreference instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).all()
    
    def set_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        preference_value: Any
    ) -> UserPreference:
        """
        Set a user preference.
        
        Args:
            user_id: User ID.
            preference_key: Preference key.
            preference_value: Preference value.
            
        Returns:
            UserPreference instance.
        """
        with self.db_manager.session_scope() as session:
            preference = session.query(UserPreference).filter(
                UserPreference.user_id == user_id,
                UserPreference.preference_key == preference_key
            ).first()
            
            if preference:
                preference.preference_value = preference_value
                preference.updated_at = datetime.utcnow()
            else:
                preference = UserPreference(
                    user_id=user_id,
                    preference_key=preference_key,
                    preference_value=preference_value
                )
                session.add(preference)
                
            session.flush()
            session.refresh(preference)
            return preference


class WebhookConfigRepository(BaseRepository[WebhookConfig]):
    """Repository for WebhookConfig model."""
    
    def __init__(self):
        super().__init__(WebhookConfig)
    
    def get_by_repository(self, repository_id: str) -> List[WebhookConfig]:
        """
        Get webhook configurations by repository ID.
        
        Args:
            repository_id: Repository ID.
            
        Returns:
            List of WebhookConfig instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(WebhookConfig).filter(
                WebhookConfig.repository_id == repository_id,
                WebhookConfig.is_active == True
            ).all()
    
    def get_by_url(self, url: str) -> List[WebhookConfig]:
        """
        Get webhook configurations by URL.
        
        Args:
            url: Webhook URL.
            
        Returns:
            List of WebhookConfig instances.
        """
        with self.db_manager.session_scope() as session:
            return session.query(WebhookConfig).filter(
                WebhookConfig.url == url,
                WebhookConfig.is_active == True
            ).all()
    
    def update_last_triggered(self, webhook_id: str) -> Optional[WebhookConfig]:
        """
        Update the last triggered timestamp for a webhook configuration.
        
        Args:
            webhook_id: Webhook configuration ID.
            
        Returns:
            Updated WebhookConfig instance if found, None otherwise.
        """
        return self.update(webhook_id, last_triggered=datetime.utcnow())

