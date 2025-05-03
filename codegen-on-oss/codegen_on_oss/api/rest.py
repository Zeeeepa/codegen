"""
REST API for Codegen-on-OSS

This module provides a REST API for accessing analysis results,
snapshots, and other data.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, Depends, HTTPException, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
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
from codegen_on_oss.events import EventBus, Event, EventType
from codegen_on_oss.api.websocket import WebSocketManager, add_websocket_routes
from codegen_on_oss.api.graphql import create_graphql_app

logger = logging.getLogger(__name__)


# Pydantic models for API
class CodebaseCreate(BaseModel):
    """Model for creating a codebase."""
    
    name: str
    repository_url: str
    default_branch: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CodebaseResponse(BaseModel):
    """Response model for a codebase."""
    
    id: int
    name: str
    repository_url: str
    default_branch: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


class SnapshotCreate(BaseModel):
    """Model for creating a snapshot."""
    
    codebase_id: int
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SnapshotResponse(BaseModel):
    """Response model for a snapshot."""
    
    id: int
    codebase_id: int
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    tag: Optional[str] = None
    created_at: datetime
    storage_path: str
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


class AnalysisResultCreate(BaseModel):
    """Model for creating an analysis result."""
    
    codebase_id: int
    snapshot_id: Optional[int] = None
    analysis_type: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResultResponse(BaseModel):
    """Response model for an analysis result."""
    
    id: int
    codebase_id: int
    snapshot_id: Optional[int] = None
    analysis_type: str
    created_at: datetime
    summary: str
    details: Dict[str, Any]
    metrics: Dict[str, Any]
    
    class Config:
        orm_mode = True


class IssueCreate(BaseModel):
    """Model for creating an issue."""
    
    analysis_result_id: int
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    severity: str
    issue_type: str
    recommendation: Optional[str] = None


class IssueResponse(BaseModel):
    """Response model for an issue."""
    
    id: int
    analysis_result_id: int
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    severity: str
    issue_type: str
    created_at: datetime
    resolved: bool
    resolved_at: Optional[datetime] = None
    recommendation: Optional[str] = None
    
    class Config:
        orm_mode = True


class SymbolCreate(BaseModel):
    """Model for creating a symbol."""
    
    codebase_id: int
    name: str
    symbol_type: str
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SymbolResponse(BaseModel):
    """Response model for a symbol."""
    
    id: int
    codebase_id: int
    name: str
    symbol_type: str
    file_path: str
    line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


class MetricsCreate(BaseModel):
    """Model for creating metrics."""
    
    symbol_id: int
    cyclomatic_complexity: Optional[float] = None
    halstead_volume: Optional[float] = None
    maintainability_index: Optional[float] = None
    lines_of_code: Optional[int] = None
    comment_ratio: Optional[float] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class MetricsResponse(BaseModel):
    """Response model for metrics."""
    
    id: int
    symbol_id: int
    cyclomatic_complexity: Optional[float] = None
    halstead_volume: Optional[float] = None
    maintainability_index: Optional[float] = None
    lines_of_code: Optional[int] = None
    comment_ratio: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    custom_metrics: Dict[str, Any]
    
    class Config:
        orm_mode = True


class RelationshipCreate(BaseModel):
    """Model for creating a relationship."""
    
    source_id: int
    target_id: int
    relationship_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    """Response model for a relationship."""
    
    id: int
    source_id: int
    target_id: int
    relationship_type: str
    created_at: datetime
    metadata: Dict[str, Any]
    
    class Config:
        orm_mode = True


def create_rest_app() -> FastAPI:
    """Create a REST API app."""
    app = FastAPI(
        title="Codegen-on-OSS API",
        description="API for accessing analysis results, snapshots, and other data",
        version="1.0.0",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Create event bus
    event_bus = EventBus()
    
    # Create WebSocket manager
    websocket_manager = WebSocketManager(event_bus)
    
    # Add WebSocket routes
    add_websocket_routes(app, websocket_manager)
    
    # Add GraphQL route
    graphql_app = create_graphql_app()
    app.include_router(graphql_app, prefix="/graphql")
    
    # Codebase routes
    @app.post("/codebases", response_model=CodebaseResponse)
    def create_codebase(
        codebase: CodebaseCreate, db: Session = Depends(get_db)
    ) -> CodebaseEntity:
        """Create a new codebase."""
        db_codebase = CodebaseEntity(**codebase.dict())
        db.add(db_codebase)
        db.commit()
        db.refresh(db_codebase)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.CODEBASE_ADDED,
                source="rest_api",
                data={"codebase_id": db_codebase.id, "name": db_codebase.name},
            )
        )
        
        return db_codebase
    
    @app.get("/codebases", response_model=List[CodebaseResponse])
    def get_codebases(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Session = Depends(get_db),
    ) -> List[CodebaseEntity]:
        """Get all codebases."""
        return db.query(CodebaseEntity).offset(skip).limit(limit).all()
    
    @app.get("/codebases/{codebase_id}", response_model=CodebaseResponse)
    def get_codebase(
        codebase_id: int = Path(..., gt=0), db: Session = Depends(get_db)
    ) -> CodebaseEntity:
        """Get a codebase by ID."""
        db_codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == codebase_id).first()
        if db_codebase is None:
            raise HTTPException(status_code=404, detail="Codebase not found")
        return db_codebase
    
    # Snapshot routes
    @app.post("/snapshots", response_model=SnapshotResponse)
    def create_snapshot(
        snapshot: SnapshotCreate, db: Session = Depends(get_db)
    ) -> SnapshotEntity:
        """Create a new snapshot."""
        # Check if codebase exists
        db_codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == snapshot.codebase_id).first()
        if db_codebase is None:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        db_snapshot = SnapshotEntity(**snapshot.dict())
        db.add(db_snapshot)
        db.commit()
        db.refresh(db_snapshot)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.SNAPSHOT_CREATED,
                source="rest_api",
                data={
                    "snapshot_id": db_snapshot.id,
                    "codebase_id": db_snapshot.codebase_id,
                },
            )
        )
        
        return db_snapshot
    
    @app.get("/snapshots", response_model=List[SnapshotResponse])
    def get_snapshots(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        codebase_id: Optional[int] = Query(None, gt=0),
        db: Session = Depends(get_db),
    ) -> List[SnapshotEntity]:
        """Get all snapshots, optionally filtered by codebase ID."""
        query = db.query(SnapshotEntity)
        
        if codebase_id is not None:
            query = query.filter(SnapshotEntity.codebase_id == codebase_id)
        
        return query.order_by(SnapshotEntity.created_at.desc()).offset(skip).limit(limit).all()
    
    @app.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
    def get_snapshot(
        snapshot_id: int = Path(..., gt=0), db: Session = Depends(get_db)
    ) -> SnapshotEntity:
        """Get a snapshot by ID."""
        db_snapshot = db.query(SnapshotEntity).filter(SnapshotEntity.id == snapshot_id).first()
        if db_snapshot is None:
            raise HTTPException(status_code=404, detail="Snapshot not found")
        return db_snapshot
    
    # Analysis result routes
    @app.post("/analysis-results", response_model=AnalysisResultResponse)
    def create_analysis_result(
        analysis_result: AnalysisResultCreate, db: Session = Depends(get_db)
    ) -> AnalysisResultEntity:
        """Create a new analysis result."""
        # Check if codebase exists
        db_codebase = db.query(CodebaseEntity).filter(CodebaseEntity.id == analysis_result.codebase_id).first()
        if db_codebase is None:
            raise HTTPException(status_code=404, detail="Codebase not found")
        
        # Check if snapshot exists if provided
        if analysis_result.snapshot_id is not None:
            db_snapshot = db.query(SnapshotEntity).filter(SnapshotEntity.id == analysis_result.snapshot_id).first()
            if db_snapshot is None:
                raise HTTPException(status_code=404, detail="Snapshot not found")
        
        db_analysis_result = AnalysisResultEntity(**analysis_result.dict())
        db.add(db_analysis_result)
        db.commit()
        db.refresh(db_analysis_result)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.ANALYSIS_COMPLETED,
                source="rest_api",
                data={
                    "analysis_result_id": db_analysis_result.id,
                    "codebase_id": db_analysis_result.codebase_id,
                    "snapshot_id": db_analysis_result.snapshot_id,
                    "analysis_type": db_analysis_result.analysis_type,
                },
            )
        )
        
        return db_analysis_result
    
    @app.get("/analysis-results", response_model=List[AnalysisResultResponse])
    def get_analysis_results(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        codebase_id: Optional[int] = Query(None, gt=0),
        snapshot_id: Optional[int] = Query(None, gt=0),
        analysis_type: Optional[str] = Query(None),
        db: Session = Depends(get_db),
    ) -> List[AnalysisResultEntity]:
        """Get all analysis results, optionally filtered by codebase ID, snapshot ID, or analysis type."""
        query = db.query(AnalysisResultEntity)
        
        if codebase_id is not None:
            query = query.filter(AnalysisResultEntity.codebase_id == codebase_id)
        
        if snapshot_id is not None:
            query = query.filter(AnalysisResultEntity.snapshot_id == snapshot_id)
        
        if analysis_type is not None:
            query = query.filter(AnalysisResultEntity.analysis_type == analysis_type)
        
        return query.order_by(AnalysisResultEntity.created_at.desc()).offset(skip).limit(limit).all()
    
    @app.get("/analysis-results/{analysis_result_id}", response_model=AnalysisResultResponse)
    def get_analysis_result(
        analysis_result_id: int = Path(..., gt=0), db: Session = Depends(get_db)
    ) -> AnalysisResultEntity:
        """Get an analysis result by ID."""
        db_analysis_result = db.query(AnalysisResultEntity).filter(AnalysisResultEntity.id == analysis_result_id).first()
        if db_analysis_result is None:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        return db_analysis_result
    
    # Issue routes
    @app.post("/issues", response_model=IssueResponse)
    def create_issue(
        issue: IssueCreate, db: Session = Depends(get_db)
    ) -> IssueEntity:
        """Create a new issue."""
        # Check if analysis result exists
        db_analysis_result = db.query(AnalysisResultEntity).filter(AnalysisResultEntity.id == issue.analysis_result_id).first()
        if db_analysis_result is None:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        db_issue = IssueEntity(**issue.dict())
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.ISSUE_DETECTED,
                source="rest_api",
                data={
                    "issue_id": db_issue.id,
                    "analysis_result_id": db_issue.analysis_result_id,
                    "title": db_issue.title,
                    "severity": db_issue.severity,
                },
            )
        )
        
        return db_issue
    
    @app.get("/issues", response_model=List[IssueResponse])
    def get_issues(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        analysis_result_id: Optional[int] = Query(None, gt=0),
        severity: Optional[str] = Query(None),
        issue_type: Optional[str] = Query(None),
        resolved: Optional[bool] = Query(None),
        db: Session = Depends(get_db),
    ) -> List[IssueEntity]:
        """Get all issues, optionally filtered by analysis result ID, severity, issue type, or resolved status."""
        query = db.query(IssueEntity)
        
        if analysis_result_id is not None:
            query = query.filter(IssueEntity.analysis_result_id == analysis_result_id)
        
        if severity is not None:
            query = query.filter(IssueEntity.severity == severity)
        
        if issue_type is not None:
            query = query.filter(IssueEntity.issue_type == issue_type)
        
        if resolved is not None:
            query = query.filter(IssueEntity.resolved == resolved)
        
        return query.offset(skip).limit(limit).all()
    
    @app.get("/issues/{issue_id}", response_model=IssueResponse)
    def get_issue(
        issue_id: int = Path(..., gt=0), db: Session = Depends(get_db)
    ) -> IssueEntity:
        """Get an issue by ID."""
        db_issue = db.query(IssueEntity).filter(IssueEntity.id == issue_id).first()
        if db_issue is None:
            raise HTTPException(status_code=404, detail="Issue not found")
        return db_issue
    
    @app.put("/issues/{issue_id}/resolve", response_model=IssueResponse)
    def resolve_issue(
        issue_id: int = Path(..., gt=0), db: Session = Depends(get_db)
    ) -> IssueEntity:
        """Resolve an issue."""
        db_issue = db.query(IssueEntity).filter(IssueEntity.id == issue_id).first()
        if db_issue is None:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        db_issue.resolved = True
        db_issue.resolved_at = datetime.utcnow()
        db.commit()
        db.refresh(db_issue)
        
        # Publish event
        event_bus.publish(
            Event(
                type=EventType.ISSUE_RESOLVED,
                source="rest_api",
                data={
                    "issue_id": db_issue.id,
                    "analysis_result_id": db_issue.analysis_result_id,
                },
            )
        )
        
        return db_issue
    
    return app

