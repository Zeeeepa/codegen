"""
Service layer for database operations.

This module provides service classes that use repositories to perform business logic.
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol

from codegen_on_oss.database.repository import (
    RepositoryRepository, SnapshotRepository, FileRepository,
    FunctionRepository, ClassRepository, ImportRepository,
    AnalysisResultRepository, IssueRepository, UserPreferenceRepository,
    WebhookConfigRepository
)
from codegen_on_oss.database.models import (
    Repository, Snapshot, File, Function as DBFunction,
    Class as DBClass, Import, AnalysisResult, Issue
)

logger = logging.getLogger(__name__)

class CodebaseService:
    """
    Service for managing codebase data in the database.
    
    This class provides methods for creating and retrieving snapshots,
    analyzing codebases, and managing related data.
    """
    
    def __init__(self):
        """Initialize the service with repositories."""
        self.repository_repo = RepositoryRepository()
        self.snapshot_repo = SnapshotRepository()
        self.file_repo = FileRepository()
        self.function_repo = FunctionRepository()
        self.class_repo = ClassRepository()
        self.import_repo = ImportRepository()
        self.analysis_result_repo = AnalysisResultRepository()
        self.issue_repo = IssueRepository()
    
    def create_repository(
        self, 
        url: str, 
        name: str, 
        description: Optional[str] = None,
        default_branch: str = 'main'
    ) -> Repository:
        """
        Create a new repository record.
        
        Args:
            url: Repository URL.
            name: Repository name.
            description: Repository description.
            default_branch: Default branch name.
            
        Returns:
            Created Repository instance.
        """
        return self.repository_repo.get_or_create(
            url=url,
            name=name,
            description=description,
            default_branch=default_branch
        )
    
    def get_repository(self, url: str) -> Optional[Repository]:
        """
        Get a repository by URL.
        
        Args:
            url: Repository URL.
            
        Returns:
            Repository instance if found, None otherwise.
        """
        return self.repository_repo.get_by_url(url)
    
    def create_snapshot(
        self, 
        codebase: Codebase, 
        repository_id: str,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Snapshot:
        """
        Create a new snapshot of a codebase.
        
        Args:
            codebase: Codebase instance.
            repository_id: Repository ID.
            commit_sha: Commit SHA.
            branch: Branch name.
            metadata: Additional metadata.
            
        Returns:
            Created Snapshot instance.
        """
        # Create the snapshot
        snapshot = self.snapshot_repo.create(
            repository_id=repository_id,
            commit_sha=commit_sha,
            branch=branch,
            metadata=metadata or {}
        )
        
        # Process files
        for source_file in codebase.files:
            self._process_file(source_file, snapshot)
        
        return snapshot
    
    def _process_file(self, source_file: SourceFile, snapshot: Snapshot) -> File:
        """
        Process a source file and add it to the snapshot.
        
        Args:
            source_file: SourceFile instance.
            snapshot: Snapshot instance.
            
        Returns:
            Created or updated File instance.
        """
        # Calculate content hash
        content_hash = hashlib.md5(source_file.content.encode()).hexdigest()
        
        # Create or get the file
        file = self.file_repo.get_or_create(
            filepath=source_file.filepath,
            name=source_file.name,
            content_hash=content_hash,
            line_count=len(source_file.content.splitlines()),
            content=source_file.content
        )
        
        # Add the file to the snapshot
        with self.snapshot_repo.db_manager.session_scope() as session:
            db_snapshot = session.query(Snapshot).filter(Snapshot.id == snapshot.id).first()
            db_file = session.query(File).filter(File.id == file.id).first()
            
            if db_snapshot and db_file and db_file not in db_snapshot.files:
                db_snapshot.files.append(db_file)
        
        # Process functions
        for function in source_file.functions:
            self._process_function(function, file, snapshot)
        
        # Process classes
        for class_def in source_file.classes:
            self._process_class(class_def, file, snapshot)
        
        # Process imports
        for import_stmt in source_file.imports:
            self._process_import(import_stmt, file)
        
        return file
    
    def _process_function(self, function: Function, file: File, snapshot: Snapshot) -> DBFunction:
        """
        Process a function and add it to the file and snapshot.
        
        Args:
            function: Function instance.
            file: File instance.
            snapshot: Snapshot instance.
            
        Returns:
            Created or updated DBFunction instance.
        """
        # Create or get the function
        db_function = self.function_repo.get_or_create(
            qualified_name=function.qualified_name,
            name=function.name,
            file_id=file.id,
            source=function.source,
            line_start=function.line_start,
            line_end=function.line_end,
            parameters=[param.name for param in function.parameters],
            return_type=str(function.return_type) if function.return_type else None,
            cyclomatic_complexity=self._calculate_cyclomatic_complexity(function)
        )
        
        # Add the function to the snapshot
        with self.snapshot_repo.db_manager.session_scope() as session:
            db_snapshot = session.query(Snapshot).filter(Snapshot.id == snapshot.id).first()
            db_func = session.query(DBFunction).filter(DBFunction.id == db_function.id).first()
            
            if db_snapshot and db_func and db_func not in db_snapshot.functions:
                db_snapshot.functions.append(db_func)
        
        # Process dependencies
        for dependency in function.dependencies:
            if isinstance(dependency, Function):
                dep_function = self.function_repo.get_by_qualified_name(dependency.qualified_name)
                if dep_function:
                    with self.function_repo.db_manager.session_scope() as session:
                        db_func = session.query(DBFunction).filter(DBFunction.id == db_function.id).first()
                        dep_func = session.query(DBFunction).filter(DBFunction.id == dep_function.id).first()
                        
                        if db_func and dep_func and dep_func not in db_func.dependencies:
                            db_func.dependencies.append(dep_func)
        
        return db_function
    
    def _process_class(self, class_def: Class, file: File, snapshot: Snapshot) -> DBClass:
        """
        Process a class and add it to the file and snapshot.
        
        Args:
            class_def: Class instance.
            file: File instance.
            snapshot: Snapshot instance.
            
        Returns:
            Created or updated DBClass instance.
        """
        # Create or get the class
        db_class = self.class_repo.get_or_create(
            qualified_name=class_def.qualified_name,
            name=class_def.name,
            file_id=file.id,
            source=class_def.source,
            line_start=class_def.line_start,
            line_end=class_def.line_end,
            parent_classes=class_def.parent_class_names
        )
        
        # Add the class to the snapshot
        with self.snapshot_repo.db_manager.session_scope() as session:
            db_snapshot = session.query(Snapshot).filter(Snapshot.id == snapshot.id).first()
            db_cls = session.query(DBClass).filter(DBClass.id == db_class.id).first()
            
            if db_snapshot and db_cls and db_cls not in db_snapshot.classes:
                db_snapshot.classes.append(db_cls)
        
        # Process dependencies
        for dependency in class_def.dependencies:
            if isinstance(dependency, Class):
                dep_class = self.class_repo.get_by_qualified_name(dependency.qualified_name)
                if dep_class:
                    with self.class_repo.db_manager.session_scope() as session:
                        db_cls = session.query(DBClass).filter(DBClass.id == db_class.id).first()
                        dep_cls = session.query(DBClass).filter(DBClass.id == dep_class.id).first()
                        
                        if db_cls and dep_cls and dep_cls not in db_cls.dependencies:
                            db_cls.dependencies.append(dep_cls)
        
        # Process methods (which are functions)
        for method in class_def.methods:
            self._process_function(method, file, snapshot)
        
        return db_class
    
    def _process_import(self, import_stmt, file: File) -> Import:
        """
        Process an import statement and add it to the file.
        
        Args:
            import_stmt: Import statement.
            file: File instance.
            
        Returns:
            Created or updated Import instance.
        """
        # Extract import information
        module_name = getattr(import_stmt, 'module_name', None)
        if not module_name and hasattr(import_stmt, 'imported_symbol'):
            if hasattr(import_stmt.imported_symbol, 'module'):
                module_name = import_stmt.imported_symbol.module
        
        if not module_name:
            module_name = str(import_stmt)
        
        imported_symbol = None
        if hasattr(import_stmt, 'imported_symbol'):
            if hasattr(import_stmt.imported_symbol, 'name'):
                imported_symbol = import_stmt.imported_symbol.name
            elif hasattr(import_stmt.imported_symbol, 'qualified_name'):
                imported_symbol = import_stmt.imported_symbol.qualified_name
        
        alias = getattr(import_stmt, 'alias', None)
        
        # Create or get the import
        import_obj = self.import_repo.get_or_create(
            module_name=module_name,
            imported_symbol=imported_symbol,
            alias=alias
        )
        
        # Add the import to the file
        with self.file_repo.db_manager.session_scope() as session:
            db_file = session.query(File).filter(File.id == file.id).first()
            db_import = session.query(Import).filter(Import.id == import_obj.id).first()
            
            if db_file and db_import and db_import not in db_file.imports:
                db_file.imports.append(db_import)
        
        return import_obj
    
    def _calculate_cyclomatic_complexity(self, function: Function) -> int:
        """
        Calculate the cyclomatic complexity of a function.
        
        Args:
            function: Function instance.
            
        Returns:
            Cyclomatic complexity score.
        """
        # Base complexity
        complexity = 1
        
        if not function.ast_nodes:
            return complexity
        
        # Count decision points in AST nodes
        for node in function.ast_nodes:
            # Control flow statements
            if node.type in [
                "if_statement", "for_statement", "while_statement", 
                "try_statement", "catch_clause", "case_statement",
                "ternary_expression", "list_comprehension", "dictionary_comprehension",
                "set_comprehension", "lambda_expression"
            ]:
                complexity += 1
        
        # Count logical operators in source code
        if function.source:
            # Count logical operators that create branches
            complexity += function.source.count(" and ") + function.source.count(" or ")
            
            # Count ternary operators if not already counted in AST
            complexity += function.source.count(" if ") - function.source.count("if ")
            
            # Count exception handling if not already counted in AST
            complexity += function.source.count("except ") - function.source.count("except:")
            
            # Count early returns which create additional paths
            complexity += function.source.count("return ") - 1
            if complexity < 1:
                complexity = 1  # Ensure at least one return is not counted as complexity
        
        return complexity
    
    def store_analysis_result(
        self, 
        snapshot_id: str, 
        analysis_type: str, 
        result: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Store an analysis result.
        
        Args:
            snapshot_id: Snapshot ID.
            analysis_type: Analysis type.
            result: Analysis result data.
            
        Returns:
            Created AnalysisResult instance.
        """
        # Check if an analysis result already exists for this snapshot and type
        existing = self.analysis_result_repo.get_by_snapshot_and_type(snapshot_id, analysis_type)
        if existing:
            return self.analysis_result_repo.update(existing.id, result=result)
        
        # Create a new analysis result
        return self.analysis_result_repo.create(
            snapshot_id=snapshot_id,
            analysis_type=analysis_type,
            result=result
        )
    
    def store_issue(
        self, 
        analysis_result_id: str, 
        issue_type: str, 
        severity: str, 
        message: str,
        file_id: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None
    ) -> Issue:
        """
        Store an issue.
        
        Args:
            analysis_result_id: Analysis result ID.
            issue_type: Issue type.
            severity: Issue severity.
            message: Issue message.
            file_id: File ID.
            line_number: Line number.
            column_number: Column number.
            
        Returns:
            Created Issue instance.
        """
        return self.issue_repo.create(
            analysis_result_id=analysis_result_id,
            file_id=file_id,
            issue_type=issue_type,
            severity=severity,
            message=message,
            line_number=line_number,
            column_number=column_number
        )
    
    def get_snapshot_by_commit(
        self, 
        repository_id: str, 
        commit_sha: str
    ) -> Optional[Snapshot]:
        """
        Get a snapshot by repository ID and commit SHA.
        
        Args:
            repository_id: Repository ID.
            commit_sha: Commit SHA.
            
        Returns:
            Snapshot instance if found, None otherwise.
        """
        return self.snapshot_repo.get_by_commit_sha(repository_id, commit_sha)
    
    def get_latest_snapshot(self, repository_id: str) -> Optional[Snapshot]:
        """
        Get the latest snapshot for a repository.
        
        Args:
            repository_id: Repository ID.
            
        Returns:
            Latest snapshot instance if found, None otherwise.
        """
        return self.snapshot_repo.get_latest_for_repository(repository_id)
    
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
        return self.snapshot_repo.get_snapshots_for_repository(repository_id, limit, offset)
    
    def get_analysis_results_for_snapshot(self, snapshot_id: str) -> List[AnalysisResult]:
        """
        Get analysis results for a snapshot.
        
        Args:
            snapshot_id: Snapshot ID.
            
        Returns:
            List of AnalysisResult instances.
        """
        return self.analysis_result_repo.get_by_snapshot(snapshot_id)
    
    def get_issues_for_analysis_result(self, analysis_result_id: str) -> List[Issue]:
        """
        Get issues for an analysis result.
        
        Args:
            analysis_result_id: Analysis result ID.
            
        Returns:
            List of Issue instances.
        """
        return self.issue_repo.get_by_analysis_result(analysis_result_id)
    
    def get_issues_for_file(self, file_id: str) -> List[Issue]:
        """
        Get issues for a file.
        
        Args:
            file_id: File ID.
            
        Returns:
            List of Issue instances.
        """
        return self.issue_repo.get_by_file(file_id)
    
    def compare_snapshots(
        self, 
        base_snapshot_id: str, 
        compare_snapshot_id: str
    ) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            base_snapshot_id: Base snapshot ID.
            compare_snapshot_id: Snapshot to compare against the base.
            
        Returns:
            Dictionary with comparison results.
        """
        base_snapshot = self.snapshot_repo.get_by_id(base_snapshot_id)
        compare_snapshot = self.snapshot_repo.get_by_id(compare_snapshot_id)
        
        if not base_snapshot or not compare_snapshot:
            raise ValueError("Both snapshots must exist")
        
        # Compare files
        base_files = {file.filepath: file for file in base_snapshot.files}
        compare_files = {file.filepath: file for file in compare_snapshot.files}
        
        files_added = [filepath for filepath in compare_files if filepath not in base_files]
        files_removed = [filepath for filepath in base_files if filepath not in compare_files]
        files_modified = [
            filepath for filepath in base_files 
            if filepath in compare_files and base_files[filepath].content_hash != compare_files[filepath].content_hash
        ]
        
        # Compare functions
        base_functions = {func.qualified_name: func for func in base_snapshot.functions}
        compare_functions = {func.qualified_name: func for func in compare_snapshot.functions}
        
        functions_added = [name for name in compare_functions if name not in base_functions]
        functions_removed = [name for name in base_functions if name not in compare_functions]
        functions_modified = []
        
        for name, func in base_functions.items():
            if name in compare_functions:
                compare_func = compare_functions[name]
                if (func.source != compare_func.source or 
                    func.parameters != compare_func.parameters or 
                    func.return_type != compare_func.return_type or 
                    func.cyclomatic_complexity != compare_func.cyclomatic_complexity):
                    functions_modified.append(name)
        
        # Compare classes
        base_classes = {cls.qualified_name: cls for cls in base_snapshot.classes}
        compare_classes = {cls.qualified_name: cls for cls in compare_snapshot.classes}
        
        classes_added = [name for name in compare_classes if name not in base_classes]
        classes_removed = [name for name in base_classes if name not in compare_classes]
        classes_modified = []
        
        for name, cls in base_classes.items():
            if name in compare_classes:
                compare_cls = compare_classes[name]
                if (cls.source != compare_cls.source or 
                    cls.parent_classes != compare_cls.parent_classes):
                    classes_modified.append(name)
        
        # Compile results
        return {
            "files": {
                "added": files_added,
                "removed": files_removed,
                "modified": files_modified
            },
            "functions": {
                "added": functions_added,
                "removed": functions_removed,
                "modified": functions_modified
            },
            "classes": {
                "added": classes_added,
                "removed": classes_removed,
                "modified": classes_modified
            },
            "metrics": {
                "base": {
                    "file_count": len(base_snapshot.files),
                    "function_count": len(base_snapshot.functions),
                    "class_count": len(base_snapshot.classes)
                },
                "compare": {
                    "file_count": len(compare_snapshot.files),
                    "function_count": len(compare_snapshot.functions),
                    "class_count": len(compare_snapshot.classes)
                }
            }
        }


class UserPreferenceService:
    """
    Service for managing user preferences.
    
    This class provides methods for getting and setting user preferences.
    """
    
    def __init__(self):
        """Initialize the service with repositories."""
        self.user_preference_repo = UserPreferenceRepository()
    
    def get_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        default_value: Any = None
    ) -> Any:
        """
        Get a user preference.
        
        Args:
            user_id: User ID.
            preference_key: Preference key.
            default_value: Default value to return if the preference doesn't exist.
            
        Returns:
            Preference value or default value.
        """
        preference = self.user_preference_repo.get_by_user_and_key(user_id, preference_key)
        if preference:
            return preference.preference_value
        return default_value
    
    def set_preference(
        self, 
        user_id: str, 
        preference_key: str, 
        preference_value: Any
    ) -> None:
        """
        Set a user preference.
        
        Args:
            user_id: User ID.
            preference_key: Preference key.
            preference_value: Preference value.
        """
        self.user_preference_repo.set_preference(user_id, preference_key, preference_value)
    
    def get_all_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get all preferences for a user.
        
        Args:
            user_id: User ID.
            
        Returns:
            Dictionary of preference keys and values.
        """
        preferences = self.user_preference_repo.get_all_for_user(user_id)
        return {pref.preference_key: pref.preference_value for pref in preferences}


class WebhookService:
    """
    Service for managing webhooks.
    
    This class provides methods for registering and triggering webhooks.
    """
    
    def __init__(self):
        """Initialize the service with repositories."""
        self.webhook_config_repo = WebhookConfigRepository()
        self.repository_repo = RepositoryRepository()
    
    def register_webhook(
        self, 
        repository_id: str, 
        url: str, 
        events: List[str], 
        secret: Optional[str] = None
    ) -> WebhookConfig:
        """
        Register a webhook.
        
        Args:
            repository_id: Repository ID.
            url: Webhook URL.
            events: List of events to trigger the webhook.
            secret: Secret to sign webhook payloads with.
            
        Returns:
            Created WebhookConfig instance.
        """
        return self.webhook_config_repo.create(
            repository_id=repository_id,
            url=url,
            events=events,
            secret=secret
        )
    
    def get_webhooks_for_repository(self, repository_id: str) -> List[WebhookConfig]:
        """
        Get webhooks for a repository.
        
        Args:
            repository_id: Repository ID.
            
        Returns:
            List of WebhookConfig instances.
        """
        return self.webhook_config_repo.get_by_repository(repository_id)
    
    def update_webhook_last_triggered(self, webhook_id: str) -> None:
        """
        Update the last triggered timestamp for a webhook.
        
        Args:
            webhook_id: Webhook ID.
        """
        self.webhook_config_repo.update_last_triggered(webhook_id)

