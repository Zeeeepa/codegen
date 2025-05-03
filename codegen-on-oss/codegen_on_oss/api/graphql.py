"""
GraphQL API for Codegen-on-OSS

This module provides a GraphQL API for accessing analysis results,
snapshots, and other data.
"""

import logging
from typing import Any, Dict, List, Optional, Union

import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from codegen_on_oss.database import (
    get_db,
    CodebaseEntity,
    SnapshotEntity,
    AnalysisResultEntity,
    SymbolEntity,
    MetricsEntity,
    IssueEntity,
    RelationshipEntity,
)

logger = logging.getLogger(__name__)


# GraphQL types
@strawberry.type
class Codebase:
    """GraphQL type for a codebase."""
    
    id: int
    name: str
    repository_url: str
    default_branch: Optional[str] = None
    created_at: str
    updated_at: str
    
    @strawberry.field
    def snapshots(self, info) -> List["Snapshot"]:
        """Get snapshots for this codebase."""
        db = info.context["db"]
        snapshots = (
            db.query(SnapshotEntity)
            .filter(SnapshotEntity.codebase_id == self.id)
            .order_by(SnapshotEntity.created_at.desc())
            .all()
        )
        return [
            Snapshot(
                id=s.id,
                codebase_id=s.codebase_id,
                commit_hash=s.commit_hash,
                branch=s.branch,
                tag=s.tag,
                created_at=s.created_at.isoformat(),
                storage_path=s.storage_path,
            )
            for s in snapshots
        ]
    
    @strawberry.field
    def analysis_results(self, info) -> List["AnalysisResult"]:
        """Get analysis results for this codebase."""
        db = info.context["db"]
        results = (
            db.query(AnalysisResultEntity)
            .filter(AnalysisResultEntity.codebase_id == self.id)
            .order_by(AnalysisResultEntity.created_at.desc())
            .all()
        )
        return [
            AnalysisResult(
                id=r.id,
                codebase_id=r.codebase_id,
                snapshot_id=r.snapshot_id,
                analysis_type=r.analysis_type.value,
                created_at=r.created_at.isoformat(),
                summary=r.summary,
                details=r.details,
                metrics=r.metrics,
            )
            for r in results
        ]
    
    @strawberry.field
    def symbols(self, info) -> List["Symbol"]:
        """Get symbols for this codebase."""
        db = info.context["db"]
        symbols = (
            db.query(SymbolEntity)
            .filter(SymbolEntity.codebase_id == self.id)
            .all()
        )
        return [
            Symbol(
                id=s.id,
                codebase_id=s.codebase_id,
                name=s.name,
                symbol_type=s.symbol_type.value,
                file_path=s.file_path,
                line_number=s.line_number,
                signature=s.signature,
                docstring=s.docstring,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
                metadata=s.metadata,
            )
            for s in symbols
        ]


@strawberry.type
class Snapshot:
    """GraphQL type for a snapshot."""
    
    id: int
    codebase_id: int
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    created_at: str
    storage_path: str
    
    @strawberry.field
    def codebase(self, info) -> Codebase:
        """Get the codebase for this snapshot."""
        db = info.context["db"]
        codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == self.codebase_id).first()
        return Codebase(
            id=codebase.id,
            name=codebase.name,
            repository_url=codebase.repository_url,
            default_branch=codebase.default_branch,
            created_at=codebase.created_at.isoformat(),
            updated_at=codebase.updated_at.isoformat(),
        )
    
    @strawberry.field
    def analysis_results(self, info) -> List["AnalysisResult"]:
        """Get analysis results for this snapshot."""
        db = info.context["db"]
        results = (
            db.query(AnalysisResultEntity)
            .filter(AnalysisResultEntity.snapshot_id == self.id)
            .order_by(AnalysisResultEntity.created_at.desc())
            .all()
        )
        return [
            AnalysisResult(
                id=r.id,
                codebase_id=r.codebase_id,
                snapshot_id=r.snapshot_id,
                analysis_type=r.analysis_type.value,
                created_at=r.created_at.isoformat(),
                summary=r.summary,
                details=r.details,
                metrics=r.metrics,
            )
            for r in results
        ]


@strawberry.type
class AnalysisResult:
    """GraphQL type for an analysis result."""
    
    id: int
    codebase_id: int
    snapshot_id: Optional[int] = None
    analysis_type: str
    created_at: str
    summary: str
    details: Dict[str, Any]
    metrics: Dict[str, Any]
    
    @strawberry.field
    def codebase(self, info) -> Codebase:
        """Get the codebase for this analysis result."""
        db = info.context["db"]
        codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == self.codebase_id).first()
        return Codebase(
            id=codebase.id,
            name=codebase.name,
            repository_url=codebase.repository_url,
            default_branch=codebase.default_branch,
            created_at=codebase.created_at.isoformat(),
            updated_at=codebase.updated_at.isoformat(),
        )
    
    @strawberry.field
    def snapshot(self, info) -> Optional[Snapshot]:
        """Get the snapshot for this analysis result."""
        if not self.snapshot_id:
            return None
        
        db = info.context["db"]
        snapshot = db.query(SnapshotEntity).filter(SnapshotEntity.id == self.snapshot_id).first()
        
        if not snapshot:
            return None
        
        return Snapshot(
            id=snapshot.id,
            codebase_id=snapshot.codebase_id,
            commit_hash=snapshot.commit_hash,
            branch=snapshot.branch,
            tag=snapshot.tag,
            created_at=snapshot.created_at.isoformat(),
            storage_path=snapshot.storage_path,
        )
    
    @strawberry.field
    def issues(self, info) -> List["Issue"]:
        """Get issues for this analysis result."""
        db = info.context["db"]
        issues = (
            db.query(IssueEntity)
            .filter(IssueEntity.analysis_result_id == self.id)
            .all()
        )
        return [
            Issue(
                id=i.id,
                analysis_result_id=i.analysis_result_id,
                title=i.title,
                description=i.description,
                file_path=i.file_path,
                line_number=i.line_number,
                severity=i.severity,
                issue_type=i.issue_type,
                created_at=i.created_at.isoformat(),
                resolved=i.resolved,
                resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
                recommendation=i.recommendation,
            )
            for i in issues
        ]


@strawberry.type
class Symbol:
    """GraphQL type for a symbol."""
    
    id: int
    codebase_id: int
    name: str
    symbol_type: str
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]
    
    @strawberry.field
    def codebase(self, info) -> Codebase:
        """Get the codebase for this symbol."""
        db = info.context["db"]
        codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == self.codebase_id).first()
        return Codebase(
            id=codebase.id,
            name=codebase.name,
            repository_url=codebase.repository_url,
            default_branch=codebase.default_branch,
            created_at=codebase.created_at.isoformat(),
            updated_at=codebase.updated_at.isoformat(),
        )
    
    @strawberry.field
    def metrics(self, info) -> Optional["Metrics"]:
        """Get metrics for this symbol."""
        db = info.context["db"]
        metrics = db.query(MetricsEntity).filter(MetricsEntity.symbol_id == self.id).first()
        
        if not metrics:
            return None
        
        return Metrics(
            id=metrics.id,
            symbol_id=metrics.symbol_id,
            cyclomatic_complexity=metrics.cyclomatic_complexity,
            halstead_volume=metrics.halstead_volume,
            maintainability_index=metrics.maintainability_index,
            lines_of_code=metrics.lines_of_code,
            comment_ratio=metrics.comment_ratio,
            created_at=metrics.created_at.isoformat(),
            updated_at=metrics.updated_at.isoformat(),
            custom_metrics=metrics.custom_metrics,
        )
    
    @strawberry.field
    def relationships(self, info) -> List["Relationship"]:
        """Get relationships for this symbol."""
        db = info.context["db"]
        relationships = (
            db.query(RelationshipEntity)
            .filter(
                (RelationshipEntity.source_id == self.id) | (RelationshipEntity.target_id == self.id)
            )
            .all()
        )
        return [
            Relationship(
                id=r.id,
                source_id=r.source_id,
                target_id=r.target_id,
                relationship_type=r.relationship_type.value,
                created_at=r.created_at.isoformat(),
                metadata=r.metadata,
            )
            for r in relationships
        ]


@strawberry.type
class Metrics:
    """GraphQL type for metrics."""
    
    id: int
    symbol_id: int
    cyclomatic_complexity: Optional[float] = None
    halstead_volume: Optional[float] = None
    maintainability_index: Optional[float] = None
    lines_of_code: Optional[int] = None
    comment_ratio: Optional[float] = None
    created_at: str
    updated_at: str
    custom_metrics: Dict[str, Any]
    
    @strawberry.field
    def symbol(self, info) -> Symbol:
        """Get the symbol for these metrics."""
        db = info.context["db"]
        symbol = db.query(SymbolEntity).filter(SymbolEntity.id == self.symbol_id).first()
        return Symbol(
            id=symbol.id,
            codebase_id=symbol.codebase_id,
            name=symbol.name,
            symbol_type=symbol.symbol_type.value,
            file_path=symbol.file_path,
            line_number=symbol.line_number,
            signature=symbol.signature,
            docstring=symbol.docstring,
            created_at=symbol.created_at.isoformat(),
            updated_at=symbol.updated_at.isoformat(),
            metadata=symbol.metadata,
        )


@strawberry.type
class Issue:
    """GraphQL type for an issue."""
    
    id: int
    analysis_result_id: int
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    severity: str
    issue_type: str
    created_at: str
    resolved: bool
    resolved_at: Optional[str] = None
    recommendation: Optional[str] = None
    
    @strawberry.field
    def analysis_result(self, info) -> AnalysisResult:
        """Get the analysis result for this issue."""
        db = info.context["db"]
        result = db.query(AnalysisResultEntity).filter(AnalysisResultEntity.id == self.analysis_result_id).first()
        return AnalysisResult(
            id=result.id,
            codebase_id=result.codebase_id,
            snapshot_id=result.snapshot_id,
            analysis_type=result.analysis_type.value,
            created_at=result.created_at.isoformat(),
            summary=result.summary,
            details=result.details,
            metrics=result.metrics,
        )


@strawberry.type
class Relationship:
    """GraphQL type for a relationship."""
    
    id: int
    source_id: int
    target_id: int
    relationship_type: str
    created_at: str
    metadata: Dict[str, Any]
    
    @strawberry.field
    def source(self, info) -> Symbol:
        """Get the source symbol for this relationship."""
        db = info.context["db"]
        symbol = db.query(SymbolEntity).filter(SymbolEntity.id == self.source_id).first()
        return Symbol(
            id=symbol.id,
            codebase_id=symbol.codebase_id,
            name=symbol.name,
            symbol_type=symbol.symbol_type.value,
            file_path=symbol.file_path,
            line_number=symbol.line_number,
            signature=symbol.signature,
            docstring=symbol.docstring,
            created_at=symbol.created_at.isoformat(),
            updated_at=symbol.updated_at.isoformat(),
            metadata=symbol.metadata,
        )
    
    @strawberry.field
    def target(self, info) -> Symbol:
        """Get the target symbol for this relationship."""
        db = info.context["db"]
        symbol = db.query(SymbolEntity).filter(SymbolEntity.id == self.target_id).first()
        return Symbol(
            id=symbol.id,
            codebase_id=symbol.codebase_id,
            name=symbol.name,
            symbol_type=symbol.symbol_type.value,
            file_path=symbol.file_path,
            line_number=symbol.line_number,
            signature=symbol.signature,
            docstring=symbol.docstring,
            created_at=symbol.created_at.isoformat(),
            updated_at=symbol.updated_at.isoformat(),
            metadata=symbol.metadata,
        )


# GraphQL queries
@strawberry.type
class Query:
    """GraphQL queries."""
    
    @strawberry.field
    def codebase(self, info, id: int) -> Optional[Codebase]:
        """Get a codebase by ID."""
        db = info.context["db"]
        codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == id).first()
        
        if not codebase:
            return None
        
        return Codebase(
            id=codebase.id,
            name=codebase.name,
            repository_url=codebase.repository_url,
            default_branch=codebase.default_branch,
            created_at=codebase.created_at.isoformat(),
            updated_at=codebase.updated_at.isoformat(),
        )
    
    @strawberry.field
    def codebases(self, info) -> List[Codebase]:
        """Get all codebases."""
        db = info.context["db"]
        codebases = db.query(CodebaseEntity).all()
        return [
            Codebase(
                id=c.id,
                name=c.name,
                repository_url=c.repository_url,
                default_branch=c.default_branch,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in codebases
        ]
    
    @strawberry.field
    def snapshot(self, info, id: int) -> Optional[Snapshot]:
        """Get a snapshot by ID."""
        db = info.context["db"]
        snapshot = db.query(SnapshotEntity).filter(SnapshotEntity.id == id).first()
        
        if not snapshot:
            return None
        
        return Snapshot(
            id=snapshot.id,
            codebase_id=snapshot.codebase_id,
            commit_hash=snapshot.commit_hash,
            branch=snapshot.branch,
            tag=snapshot.tag,
            created_at=snapshot.created_at.isoformat(),
            storage_path=snapshot.storage_path,
        )
    
    @strawberry.field
    def snapshots(self, info, codebase_id: Optional[int] = None) -> List[Snapshot]:
        """Get snapshots, optionally filtered by codebase ID."""
        db = info.context["db"]
        query = db.query(SnapshotEntity)
        
        if codebase_id is not None:
            query = query.filter(SnapshotEntity.codebase_id == codebase_id)
        
        snapshots = query.order_by(SnapshotEntity.created_at.desc()).all()
        
        return [
            Snapshot(
                id=s.id,
                codebase_id=s.codebase_id,
                commit_hash=s.commit_hash,
                branch=s.branch,
                tag=s.tag,
                created_at=s.created_at.isoformat(),
                storage_path=s.storage_path,
            )
            for s in snapshots
        ]
    
    @strawberry.field
    def analysis_result(self, info, id: int) -> Optional[AnalysisResult]:
        """Get an analysis result by ID."""
        db = info.context["db"]
        result = db.query(AnalysisResultEntity).filter(AnalysisResultEntity.id == id).first()
        
        if not result:
            return None
        
        return AnalysisResult(
            id=result.id,
            codebase_id=result.codebase_id,
            snapshot_id=result.snapshot_id,
            analysis_type=result.analysis_type.value,
            created_at=result.created_at.isoformat(),
            summary=result.summary,
            details=result.details,
            metrics=result.metrics,
        )
    
    @strawberry.field
    def analysis_results(
        self, info, codebase_id: Optional[int] = None, snapshot_id: Optional[int] = None
    ) -> List[AnalysisResult]:
        """Get analysis results, optionally filtered by codebase ID or snapshot ID."""
        db = info.context["db"]
        query = db.query(AnalysisResultEntity)
        
        if codebase_id is not None:
            query = query.filter(AnalysisResultEntity.codebase_id == codebase_id)
        
        if snapshot_id is not None:
            query = query.filter(AnalysisResultEntity.snapshot_id == snapshot_id)
        
        results = query.order_by(AnalysisResultEntity.created_at.desc()).all()
        
        return [
            AnalysisResult(
                id=r.id,
                codebase_id=r.codebase_id,
                snapshot_id=r.snapshot_id,
                analysis_type=r.analysis_type.value,
                created_at=r.created_at.isoformat(),
                summary=r.summary,
                details=r.details,
                metrics=r.metrics,
            )
            for r in results
        ]
    
    @strawberry.field
    def symbol(self, info, id: int) -> Optional[Symbol]:
        """Get a symbol by ID."""
        db = info.context["db"]
        symbol = db.query(SymbolEntity).filter(SymbolEntity.id == id).first()
        
        if not symbol:
            return None
        
        return Symbol(
            id=symbol.id,
            codebase_id=symbol.codebase_id,
            name=symbol.name,
            symbol_type=symbol.symbol_type.value,
            file_path=symbol.file_path,
            line_number=symbol.line_number,
            signature=symbol.signature,
            docstring=symbol.docstring,
            created_at=symbol.created_at.isoformat(),
            updated_at=symbol.updated_at.isoformat(),
            metadata=symbol.metadata,
        )
    
    @strawberry.field
    def symbols(
        self, info, codebase_id: Optional[int] = None, symbol_type: Optional[str] = None
    ) -> List[Symbol]:
        """Get symbols, optionally filtered by codebase ID or symbol type."""
        db = info.context["db"]
        query = db.query(SymbolEntity)
        
        if codebase_id is not None:
            query = query.filter(SymbolEntity.codebase_id == codebase_id)
        
        if symbol_type is not None:
            query = query.filter(SymbolEntity.symbol_type == symbol_type)
        
        symbols = query.all()
        
        return [
            Symbol(
                id=s.id,
                codebase_id=s.codebase_id,
                name=s.name,
                symbol_type=s.symbol_type.value,
                file_path=s.file_path,
                line_number=s.line_number,
                signature=s.signature,
                docstring=s.docstring,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat(),
                metadata=s.metadata,
            )
            for s in symbols
        ]
    
    @strawberry.field
    def issue(self, info, id: int) -> Optional[Issue]:
        """Get an issue by ID."""
        db = info.context["db"]
        issue = db.query(IssueEntity).filter(IssueEntity.id == id).first()
        
        if not issue:
            return None
        
        return Issue(
            id=issue.id,
            analysis_result_id=issue.analysis_result_id,
            title=issue.title,
            description=issue.description,
            file_path=issue.file_path,
            line_number=issue.line_number,
            severity=issue.severity,
            issue_type=issue.issue_type,
            created_at=issue.created_at.isoformat(),
            resolved=issue.resolved,
            resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
            recommendation=issue.recommendation,
        )
    
    @strawberry.field
    def issues(
        self,
        info,
        analysis_result_id: Optional[int] = None,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[Issue]:
        """Get issues, optionally filtered by analysis result ID, severity, or resolved status."""
        db = info.context["db"]
        query = db.query(IssueEntity)
        
        if analysis_result_id is not None:
            query = query.filter(IssueEntity.analysis_result_id == analysis_result_id)
        
        if severity is not None:
            query = query.filter(IssueEntity.severity == severity)
        
        if resolved is not None:
            query = query.filter(IssueEntity.resolved == resolved)
        
        issues = query.all()
        
        return [
            Issue(
                id=i.id,
                analysis_result_id=i.analysis_result_id,
                title=i.title,
                description=i.description,
                file_path=i.file_path,
                line_number=i.line_number,
                severity=i.severity,
                issue_type=i.issue_type,
                created_at=i.created_at.isoformat(),
                resolved=i.resolved,
                resolved_at=i.resolved_at.isoformat() if i.resolved_at else None,
                recommendation=i.recommendation,
            )
            for i in issues
        ]


# GraphQL mutations
@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    @strawberry.mutation
    def resolve_issue(self, info, id: int) -> Issue:
        """Resolve an issue."""
        db = info.context["db"]
        issue = db.query(IssueEntity).filter(IssueEntity.id == id).first()
        
        if not issue:
            raise ValueError(f"Issue with ID {id} not found")
        
        issue.resolved = True
        issue.resolved_at = datetime.now()
        db.commit()
        db.refresh(issue)
        
        return Issue(
            id=issue.id,
            analysis_result_id=issue.analysis_result_id,
            title=issue.title,
            description=issue.description,
            file_path=issue.file_path,
            line_number=issue.line_number,
            severity=issue.severity,
            issue_type=issue.issue_type,
            created_at=issue.created_at.isoformat(),
            resolved=issue.resolved,
            resolved_at=issue.resolved_at.isoformat() if issue.resolved_at else None,
            recommendation=issue.recommendation,
        )


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


def get_context(db: Session = Depends(get_db)):
    """Get GraphQL context."""
    return {"db": db}


def create_graphql_app() -> GraphQLRouter:
    """Create a GraphQL router."""
    return GraphQLRouter(schema, context_getter=get_context)

