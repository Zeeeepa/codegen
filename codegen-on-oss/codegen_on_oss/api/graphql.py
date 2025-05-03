"""
GraphQL API for codegen-on-oss.

This module provides a GraphQL API for querying code analysis data.
"""

import logging
from typing import Dict, List, Any, Optional, Union

import graphene
from graphene import ObjectType, String, Int, Float, Boolean, List as GrapheneList
from graphene import Field, Interface, Enum, DateTime, JSONString
from graphql import GraphQLError

from codegen_on_oss.database.models import (
    Repository as DBRepository,
    Snapshot as DBSnapshot,
    File as DBFile,
    Function as DBFunction,
    Class as DBClass,
    Import as DBImport,
    AnalysisResult as DBAnalysisResult,
    Issue as DBIssue
)
from codegen_on_oss.database.connection import get_db_manager
from codegen_on_oss.database.repository import (
    RepositoryRepository, SnapshotRepository, FileRepository,
    FunctionRepository, ClassRepository, ImportRepository,
    AnalysisResultRepository, IssueRepository
)

logger = logging.getLogger(__name__)

# Initialize repositories
repository_repo = RepositoryRepository()
snapshot_repo = SnapshotRepository()
file_repo = FileRepository()
function_repo = FunctionRepository()
class_repo = ClassRepository()
import_repo = ImportRepository()
analysis_result_repo = AnalysisResultRepository()
issue_repo = IssueRepository()

# GraphQL types
class IssueSeverityEnum(Enum):
    """Issue severity enum."""
    
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


class AnalysisTypeEnum(Enum):
    """Analysis type enum."""
    
    COMPLEXITY = 'complexity'
    DEPENDENCIES = 'dependencies'
    IMPORTS = 'imports'
    ISSUES = 'issues'
    METRICS = 'metrics'
    SUMMARY = 'summary'


class NodeInterface(Interface):
    """Node interface for GraphQL objects."""
    
    id = String(required=True)


class Repository(ObjectType):
    """Repository GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    name = String(required=True)
    url = String(required=True)
    description = String()
    default_branch = String(required=True)
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)
    
    snapshots = GrapheneList(lambda: Snapshot)
    latest_snapshot = Field(lambda: Snapshot)
    
    def resolve_snapshots(self, info):
        """Resolve snapshots field."""
        return snapshot_repo.get_snapshots_for_repository(self.id)
    
    def resolve_latest_snapshot(self, info):
        """Resolve latest_snapshot field."""
        return snapshot_repo.get_latest_for_repository(self.id)


class Snapshot(ObjectType):
    """Snapshot GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    repository_id = String(required=True)
    commit_sha = String()
    branch = String()
    timestamp = DateTime(required=True)
    metadata = JSONString()
    
    repository = Field(Repository)
    files = GrapheneList(lambda: File)
    functions = GrapheneList(lambda: Function)
    classes = GrapheneList(lambda: Class)
    analysis_results = GrapheneList(lambda: AnalysisResult)
    
    def resolve_repository(self, info):
        """Resolve repository field."""
        return repository_repo.get_by_id(self.repository_id)
    
    def resolve_files(self, info):
        """Resolve files field."""
        with get_db_manager().session_scope() as session:
            snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == self.id).first()
            if snapshot:
                return snapshot.files
            return []
    
    def resolve_functions(self, info):
        """Resolve functions field."""
        with get_db_manager().session_scope() as session:
            snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == self.id).first()
            if snapshot:
                return snapshot.functions
            return []
    
    def resolve_classes(self, info):
        """Resolve classes field."""
        with get_db_manager().session_scope() as session:
            snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == self.id).first()
            if snapshot:
                return snapshot.classes
            return []
    
    def resolve_analysis_results(self, info):
        """Resolve analysis_results field."""
        return analysis_result_repo.get_by_snapshot(self.id)


class File(ObjectType):
    """File GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    filepath = String(required=True)
    name = String(required=True)
    content_hash = String(required=True)
    line_count = Int(required=True)
    content = String()
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)
    
    snapshots = GrapheneList(Snapshot)
    functions = GrapheneList(lambda: Function)
    classes = GrapheneList(lambda: Class)
    imports = GrapheneList(lambda: Import)
    issues = GrapheneList(lambda: Issue)
    
    def resolve_snapshots(self, info):
        """Resolve snapshots field."""
        with get_db_manager().session_scope() as session:
            file = session.query(DBFile).filter(DBFile.id == self.id).first()
            if file:
                return file.snapshots
            return []
    
    def resolve_functions(self, info):
        """Resolve functions field."""
        return function_repo.get_by_file_id(self.id)
    
    def resolve_classes(self, info):
        """Resolve classes field."""
        return class_repo.get_by_file_id(self.id)
    
    def resolve_imports(self, info):
        """Resolve imports field."""
        with get_db_manager().session_scope() as session:
            file = session.query(DBFile).filter(DBFile.id == self.id).first()
            if file:
                return file.imports
            return []
    
    def resolve_issues(self, info):
        """Resolve issues field."""
        return issue_repo.get_by_file(self.id)


class Function(ObjectType):
    """Function GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    name = String(required=True)
    qualified_name = String(required=True)
    file_id = String()
    source = String()
    line_start = Int()
    line_end = Int()
    parameters = JSONString()
    return_type = String()
    cyclomatic_complexity = Int(required=True)
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)
    
    file = Field(File)
    snapshots = GrapheneList(Snapshot)
    dependencies = GrapheneList(lambda: Function)
    dependents = GrapheneList(lambda: Function)
    
    def resolve_file(self, info):
        """Resolve file field."""
        if self.file_id:
            return file_repo.get_by_id(self.file_id)
        return None
    
    def resolve_snapshots(self, info):
        """Resolve snapshots field."""
        with get_db_manager().session_scope() as session:
            function = session.query(DBFunction).filter(DBFunction.id == self.id).first()
            if function:
                return function.snapshots
            return []
    
    def resolve_dependencies(self, info):
        """Resolve dependencies field."""
        with get_db_manager().session_scope() as session:
            function = session.query(DBFunction).filter(DBFunction.id == self.id).first()
            if function:
                return function.dependencies
            return []
    
    def resolve_dependents(self, info):
        """Resolve dependents field."""
        with get_db_manager().session_scope() as session:
            function = session.query(DBFunction).filter(DBFunction.id == self.id).first()
            if function:
                return function.dependents
            return []


class Class(ObjectType):
    """Class GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    name = String(required=True)
    qualified_name = String(required=True)
    file_id = String()
    source = String()
    line_start = Int()
    line_end = Int()
    parent_classes = JSONString()
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)
    
    file = Field(File)
    snapshots = GrapheneList(Snapshot)
    dependencies = GrapheneList(lambda: Class)
    dependents = GrapheneList(lambda: Class)
    
    def resolve_file(self, info):
        """Resolve file field."""
        if self.file_id:
            return file_repo.get_by_id(self.file_id)
        return None
    
    def resolve_snapshots(self, info):
        """Resolve snapshots field."""
        with get_db_manager().session_scope() as session:
            class_obj = session.query(DBClass).filter(DBClass.id == self.id).first()
            if class_obj:
                return class_obj.snapshots
            return []
    
    def resolve_dependencies(self, info):
        """Resolve dependencies field."""
        with get_db_manager().session_scope() as session:
            class_obj = session.query(DBClass).filter(DBClass.id == self.id).first()
            if class_obj:
                return class_obj.dependencies
            return []
    
    def resolve_dependents(self, info):
        """Resolve dependents field."""
        with get_db_manager().session_scope() as session:
            class_obj = session.query(DBClass).filter(DBClass.id == self.id).first()
            if class_obj:
                return class_obj.dependents
            return []


class Import(ObjectType):
    """Import GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    module_name = String(required=True)
    imported_symbol = String()
    alias = String()
    created_at = DateTime(required=True)
    updated_at = DateTime(required=True)
    
    files = GrapheneList(File)
    
    def resolve_files(self, info):
        """Resolve files field."""
        with get_db_manager().session_scope() as session:
            import_obj = session.query(DBImport).filter(DBImport.id == self.id).first()
            if import_obj:
                return import_obj.files
            return []


class AnalysisResult(ObjectType):
    """AnalysisResult GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    snapshot_id = String(required=True)
    analysis_type = String(required=True)
    result = JSONString(required=True)
    created_at = DateTime(required=True)
    
    snapshot = Field(Snapshot)
    issues = GrapheneList(lambda: Issue)
    
    def resolve_snapshot(self, info):
        """Resolve snapshot field."""
        return snapshot_repo.get_by_id(self.snapshot_id)
    
    def resolve_issues(self, info):
        """Resolve issues field."""
        return issue_repo.get_by_analysis_result(self.id)


class Issue(ObjectType):
    """Issue GraphQL type."""
    
    class Meta:
        interfaces = (NodeInterface,)
    
    id = String(required=True)
    analysis_result_id = String(required=True)
    file_id = String()
    issue_type = String(required=True)
    severity = String(required=True)
    message = String(required=True)
    line_number = Int()
    column_number = Int()
    created_at = DateTime(required=True)
    
    analysis_result = Field(AnalysisResult)
    file = Field(File)
    
    def resolve_analysis_result(self, info):
        """Resolve analysis_result field."""
        return analysis_result_repo.get_by_id(self.analysis_result_id)
    
    def resolve_file(self, info):
        """Resolve file field."""
        if self.file_id:
            return file_repo.get_by_id(self.file_id)
        return None


# GraphQL queries
class Query(ObjectType):
    """GraphQL query root."""
    
    # Node query
    node = Field(NodeInterface, id=String(required=True))
    
    # Repository queries
    repository = Field(Repository, id=String(), url=String())
    repositories = GrapheneList(Repository, limit=Int(), offset=Int())
    
    # Snapshot queries
    snapshot = Field(Snapshot, id=String(required=True))
    snapshots = GrapheneList(
        Snapshot,
        repository_id=String(),
        commit_sha=String(),
        branch=String(),
        limit=Int(),
        offset=Int()
    )
    
    # File queries
    file = Field(File, id=String(), filepath=String())
    files = GrapheneList(
        File,
        snapshot_id=String(),
        name=String(),
        limit=Int(),
        offset=Int()
    )
    
    # Function queries
    function = Field(Function, id=String(), qualified_name=String())
    functions = GrapheneList(
        Function,
        snapshot_id=String(),
        file_id=String(),
        name=String(),
        limit=Int(),
        offset=Int()
    )
    
    # Class queries
    class_obj = Field(Class, id=String(), qualified_name=String())
    classes = GrapheneList(
        Class,
        snapshot_id=String(),
        file_id=String(),
        name=String(),
        limit=Int(),
        offset=Int()
    )
    
    # Import queries
    import_obj = Field(Import, id=String(), module_name=String())
    imports = GrapheneList(
        Import,
        file_id=String(),
        module_name=String(),
        limit=Int(),
        offset=Int()
    )
    
    # Analysis result queries
    analysis_result = Field(AnalysisResult, id=String(required=True))
    analysis_results = GrapheneList(
        AnalysisResult,
        snapshot_id=String(),
        analysis_type=String(),
        limit=Int(),
        offset=Int()
    )
    
    # Issue queries
    issue = Field(Issue, id=String(required=True))
    issues = GrapheneList(
        Issue,
        analysis_result_id=String(),
        file_id=String(),
        issue_type=String(),
        severity=String(),
        limit=Int(),
        offset=Int()
    )
    
    def resolve_node(self, info, id):
        """Resolve node field."""
        # Check each repository to find the node
        for repo_class in [
            repository_repo, snapshot_repo, file_repo, function_repo,
            class_repo, import_repo, analysis_result_repo, issue_repo
        ]:
            node = repo_class.get_by_id(id)
            if node:
                return node
        
        return None
    
    def resolve_repository(self, info, id=None, url=None):
        """Resolve repository field."""
        if id:
            return repository_repo.get_by_id(id)
        elif url:
            return repository_repo.get_by_url(url)
        return None
    
    def resolve_repositories(self, info, limit=None, offset=None):
        """Resolve repositories field."""
        return repository_repo.get_all(limit=limit, offset=offset)
    
    def resolve_snapshot(self, info, id):
        """Resolve snapshot field."""
        return snapshot_repo.get_by_id(id)
    
    def resolve_snapshots(self, info, repository_id=None, commit_sha=None, branch=None, limit=None, offset=None):
        """Resolve snapshots field."""
        if repository_id and commit_sha:
            snapshot = snapshot_repo.get_by_commit_sha(repository_id, commit_sha)
            return [snapshot] if snapshot else []
        elif repository_id:
            return snapshot_repo.get_snapshots_for_repository(repository_id, limit=limit, offset=offset)
        else:
            return snapshot_repo.get_all(limit=limit, offset=offset)
    
    def resolve_file(self, info, id=None, filepath=None):
        """Resolve file field."""
        if id:
            return file_repo.get_by_id(id)
        elif filepath:
            return file_repo.get_by_filepath(filepath)
        return None
    
    def resolve_files(self, info, snapshot_id=None, name=None, limit=None, offset=None):
        """Resolve files field."""
        if snapshot_id:
            with get_db_manager().session_scope() as session:
                snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == snapshot_id).first()
                if snapshot:
                    files = snapshot.files
                    if name:
                        files = [f for f in files if f.name == name]
                    
                    # Apply limit and offset
                    if offset is not None:
                        files = files[offset:]
                    if limit is not None:
                        files = files[:limit]
                    
                    return files
                return []
        else:
            return file_repo.get_all(limit=limit, offset=offset)
    
    def resolve_function(self, info, id=None, qualified_name=None):
        """Resolve function field."""
        if id:
            return function_repo.get_by_id(id)
        elif qualified_name:
            return function_repo.get_by_qualified_name(qualified_name)
        return None
    
    def resolve_functions(self, info, snapshot_id=None, file_id=None, name=None, limit=None, offset=None):
        """Resolve functions field."""
        if snapshot_id:
            with get_db_manager().session_scope() as session:
                snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == snapshot_id).first()
                if snapshot:
                    functions = snapshot.functions
                    if file_id:
                        functions = [f for f in functions if f.file_id == file_id]
                    if name:
                        functions = [f for f in functions if f.name == name]
                    
                    # Apply limit and offset
                    if offset is not None:
                        functions = functions[offset:]
                    if limit is not None:
                        functions = functions[:limit]
                    
                    return functions
                return []
        elif file_id:
            functions = function_repo.get_by_file_id(file_id)
            if name:
                functions = [f for f in functions if f.name == name]
            
            # Apply limit and offset
            if offset is not None:
                functions = functions[offset:]
            if limit is not None:
                functions = functions[:limit]
            
            return functions
        else:
            return function_repo.get_all(limit=limit, offset=offset)
    
    def resolve_class_obj(self, info, id=None, qualified_name=None):
        """Resolve class_obj field."""
        if id:
            return class_repo.get_by_id(id)
        elif qualified_name:
            return class_repo.get_by_qualified_name(qualified_name)
        return None
    
    def resolve_classes(self, info, snapshot_id=None, file_id=None, name=None, limit=None, offset=None):
        """Resolve classes field."""
        if snapshot_id:
            with get_db_manager().session_scope() as session:
                snapshot = session.query(DBSnapshot).filter(DBSnapshot.id == snapshot_id).first()
                if snapshot:
                    classes = snapshot.classes
                    if file_id:
                        classes = [c for c in classes if c.file_id == file_id]
                    if name:
                        classes = [c for c in classes if c.name == name]
                    
                    # Apply limit and offset
                    if offset is not None:
                        classes = classes[offset:]
                    if limit is not None:
                        classes = classes[:limit]
                    
                    return classes
                return []
        elif file_id:
            classes = class_repo.get_by_file_id(file_id)
            if name:
                classes = [c for c in classes if c.name == name]
            
            # Apply limit and offset
            if offset is not None:
                classes = classes[offset:]
            if limit is not None:
                classes = classes[:limit]
            
            return classes
        else:
            return class_repo.get_all(limit=limit, offset=offset)
    
    def resolve_import_obj(self, info, id=None, module_name=None):
        """Resolve import_obj field."""
        if id:
            return import_repo.get_by_id(id)
        elif module_name:
            return import_repo.get_by_module_and_symbol(module_name)
        return None
    
    def resolve_imports(self, info, file_id=None, module_name=None, limit=None, offset=None):
        """Resolve imports field."""
        if file_id:
            with get_db_manager().session_scope() as session:
                file = session.query(DBFile).filter(DBFile.id == file_id).first()
                if file:
                    imports = file.imports
                    if module_name:
                        imports = [i for i in imports if i.module_name == module_name]
                    
                    # Apply limit and offset
                    if offset is not None:
                        imports = imports[offset:]
                    if limit is not None:
                        imports = imports[:limit]
                    
                    return imports
                return []
        else:
            return import_repo.get_all(limit=limit, offset=offset)
    
    def resolve_analysis_result(self, info, id):
        """Resolve analysis_result field."""
        return analysis_result_repo.get_by_id(id)
    
    def resolve_analysis_results(self, info, snapshot_id=None, analysis_type=None, limit=None, offset=None):
        """Resolve analysis_results field."""
        if snapshot_id and analysis_type:
            result = analysis_result_repo.get_by_snapshot_and_type(snapshot_id, analysis_type)
            return [result] if result else []
        elif snapshot_id:
            return analysis_result_repo.get_by_snapshot(snapshot_id)
        else:
            return analysis_result_repo.get_all(limit=limit, offset=offset)
    
    def resolve_issue(self, info, id):
        """Resolve issue field."""
        return issue_repo.get_by_id(id)
    
    def resolve_issues(self, info, analysis_result_id=None, file_id=None, issue_type=None, severity=None, limit=None, offset=None):
        """Resolve issues field."""
        if analysis_result_id:
            issues = issue_repo.get_by_analysis_result(analysis_result_id)
        elif file_id:
            issues = issue_repo.get_by_file(file_id)
        elif issue_type and severity:
            issues = issue_repo.get_by_type_and_severity(issue_type, severity)
        else:
            issues = issue_repo.get_all(limit=limit, offset=offset)
        
        # Apply filters
        if issue_type and (analysis_result_id or file_id):
            issues = [i for i in issues if i.issue_type == issue_type]
        if severity and (analysis_result_id or file_id):
            issues = [i for i in issues if i.severity == severity]
        
        # Apply limit and offset
        if offset is not None:
            issues = issues[offset:]
        if limit is not None:
            issues = issues[:limit]
        
        return issues


# Create the GraphQL schema
schema = graphene.Schema(query=Query)

def execute_query(query, variables=None):
    """
    Execute a GraphQL query.
    
    Args:
        query: GraphQL query string.
        variables: Query variables.
        
    Returns:
        Query result.
    """
    try:
        result = schema.execute(query, variable_values=variables)
        
        if result.errors:
            logger.error(f"GraphQL query errors: {result.errors}")
            return {"errors": [str(error) for error in result.errors]}
        
        return {"data": result.data}
    except Exception as e:
        logger.error(f"Error executing GraphQL query: {e}")
        return {"errors": [str(e)]}
