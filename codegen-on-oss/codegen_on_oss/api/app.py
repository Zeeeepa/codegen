"""
FastAPI application for the codegen-on-oss system.

This module provides a FastAPI application with routes for analyzing repositories,
managing snapshots, and retrieving analysis results.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from codegen_on_oss.config import settings, get_settings
from codegen_on_oss.database.connection import get_db
from codegen_on_oss.database.models import CodebaseSnapshot
from codegen_on_oss.snapshot.snapshot_service import SnapshotService
from codegen_on_oss.storage.service import StorageService
from codegen_on_oss.analysis.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Codegen Analysis API",
    description="API for analyzing code repositories and commits",
    version=settings.app_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API key security
api_key_header = APIKeyHeader(name=settings.api_key_header)


# Define request and response models
class RepoAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze")
    branch: Optional[str] = Field(None, description="Branch to analyze")
    analysis_types: Optional[List[str]] = Field(
        None, 
        description="Types of analysis to perform (code_quality, dependencies, security, file_analysis)"
    )


class SnapshotRequest(BaseModel):
    """Request model for creating a snapshot."""
    repo_url: str = Field(..., description="URL of the repository to snapshot")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to snapshot")
    branch: Optional[str] = Field(None, description="Branch to snapshot")


class SnapshotCompareRequest(BaseModel):
    """Request model for comparing snapshots."""
    snapshot_id_1: uuid.UUID = Field(..., description="ID of the first snapshot")
    snapshot_id_2: uuid.UUID = Field(..., description="ID of the second snapshot")


# Dependency for API key validation
async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify that the API key is valid."""
    if not settings.api_keys:
        # No API keys configured, allow all requests
        return True
    
    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": settings.api_key_header},
        )
    
    return True


# Dependency for services
def get_snapshot_service(db: Session = Depends(get_db)):
    """Get the snapshot service."""
    storage_service = StorageService()
    return SnapshotService(db, storage_service)


def get_analysis_service(
    db: Session = Depends(get_db),
    snapshot_service: SnapshotService = Depends(get_snapshot_service)
):
    """Get the analysis service."""
    return AnalysisService(db, snapshot_service)


# API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Codegen Analysis API",
        "version": settings.app_version,
        "description": "API for analyzing code repositories and commits",
    }


@app.post("/api/analysis/request", dependencies=[Depends(verify_api_key)])
async def request_analysis(
    request: RepoAnalysisRequest,
    background_tasks: BackgroundTasks,
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """Request a new analysis job."""
    # Start analysis in background
    background_tasks.add_task(
        analysis_service.analyze_codebase,
        repo_url=request.repo_url,
        commit_sha=request.commit_sha,
        branch=request.branch,
        analysis_types=request.analysis_types,
    )
    
    return {
        "status": "accepted",
        "message": "Analysis job started",
        "repo_url": request.repo_url,
        "commit_sha": request.commit_sha,
        "branch": request.branch,
    }


@app.get("/api/analysis/jobs/{job_id}", dependencies=[Depends(verify_api_key)])
async def get_analysis_job(
    job_id: uuid.UUID,
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """Get status of an analysis job."""
    job = await analysis_service.get_analysis_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@app.post("/api/snapshots", dependencies=[Depends(verify_api_key)])
async def create_snapshot(
    request: SnapshotRequest,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Create a new snapshot."""
    snapshot = await snapshot_service.create_snapshot(
        repo_url=request.repo_url,
        commit_sha=request.commit_sha,
        branch=request.branch,
    )
    
    return {
        "snapshot_id": str(snapshot.id),
        "repository": snapshot.repository,
        "commit_sha": snapshot.commit_sha,
        "branch": snapshot.branch,
        "created_at": snapshot.created_at.isoformat(),
        "metadata": snapshot.metadata,
    }


@app.get("/api/snapshots", dependencies=[Depends(verify_api_key)])
async def list_snapshots(
    repository: Optional[str] = None,
    branch: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """List available snapshots with filtering."""
    snapshots = await snapshot_service.list_snapshots(
        repository=repository,
        branch=branch,
        limit=limit,
        offset=offset,
    )
    
    return {
        "snapshots": [
            {
                "snapshot_id": str(snapshot.id),
                "repository": snapshot.repository,
                "commit_sha": snapshot.commit_sha,
                "branch": snapshot.branch,
                "created_at": snapshot.created_at.isoformat(),
                "metadata": snapshot.metadata,
            }
            for snapshot in snapshots
        ],
        "limit": limit,
        "offset": offset,
        "repository": repository,
        "branch": branch,
    }


@app.get("/api/snapshots/{snapshot_id}", dependencies=[Depends(verify_api_key)])
async def get_snapshot(
    snapshot_id: uuid.UUID,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Get snapshot details."""
    snapshot = await snapshot_service.get_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return {
        "snapshot_id": str(snapshot.id),
        "repository": snapshot.repository,
        "commit_sha": snapshot.commit_sha,
        "branch": snapshot.branch,
        "created_at": snapshot.created_at.isoformat(),
        "metadata": snapshot.metadata,
    }


@app.get("/api/snapshots/{snapshot_id}/files", dependencies=[Depends(verify_api_key)])
async def get_snapshot_files(
    snapshot_id: uuid.UUID,
    path_prefix: Optional[str] = None,
    limit: int = 1000,
    offset: int = 0,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Get files in a snapshot."""
    files = await snapshot_service.get_snapshot_files(
        snapshot_id=snapshot_id,
        path_prefix=path_prefix,
        limit=limit,
        offset=offset,
    )
    
    return {
        "snapshot_id": str(snapshot_id),
        "files": [
            {
                "file_path": file.file_path,
                "file_hash": file.file_hash,
                "file_size": file.file_size,
                "language": file.language,
            }
            for file in files
        ],
        "limit": limit,
        "offset": offset,
        "path_prefix": path_prefix,
    }


@app.get("/api/snapshots/{snapshot_id}/files/{file_path:path}", dependencies=[Depends(verify_api_key)])
async def get_file_content(
    snapshot_id: uuid.UUID,
    file_path: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Get the content of a file in a snapshot."""
    content = await snapshot_service.get_file_content(snapshot_id, file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # If content is bytes, convert to string if possible
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError:
            # Return binary content
            return Response(
                content=content,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={file_path.split('/')[-1]}"},
            )
    
    return {
        "snapshot_id": str(snapshot_id),
        "file_path": file_path,
        "content": content,
    }


@app.post("/api/snapshots/compare", dependencies=[Depends(verify_api_key)])
async def compare_snapshots(
    request: SnapshotCompareRequest,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Compare two snapshots and return detailed differences."""
    comparison = await snapshot_service.compare_snapshots(
        snapshot_id_1=request.snapshot_id_1,
        snapshot_id_2=request.snapshot_id_2,
    )
    
    return comparison


@app.get("/api/snapshots/{snapshot_id}/analysis/{analysis_type}", dependencies=[Depends(verify_api_key)])
async def get_analysis(
    snapshot_id: uuid.UUID,
    analysis_type: str,
    db: Session = Depends(get_db),
):
    """Get specific analysis results for a snapshot."""
    # Get the snapshot
    snapshot = await db.get(CodebaseSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    # Get the analysis results based on type
    if analysis_type == "code_quality":
        from codegen_on_oss.database.models import CodeMetrics
        query = db.query(CodeMetrics).filter(CodeMetrics.snapshot_id == snapshot_id)
        result = query.first()
    
    elif analysis_type == "dependencies":
        from codegen_on_oss.database.models import DependencyAnalysis
        query = db.query(DependencyAnalysis).filter(DependencyAnalysis.snapshot_id == snapshot_id)
        result = query.first()
    
    elif analysis_type == "security":
        from codegen_on_oss.database.models import SecurityAnalysis
        query = db.query(SecurityAnalysis).filter(SecurityAnalysis.snapshot_id == snapshot_id)
        result = query.first()
    
    elif analysis_type == "file_analysis":
        from codegen_on_oss.database.models import FileAnalysis
        query = db.query(FileAnalysis).filter(FileAnalysis.snapshot_id == snapshot_id)
        results = query.all()
        
        return {
            "snapshot_id": str(snapshot_id),
            "analysis_type": analysis_type,
            "files_analyzed": len(results),
            "files": [
                {
                    "file_path": file.file_path,
                    "language": file.language,
                    "lines": file.lines,
                    "complexity": file.complexity,
                    "issues_count": file.issues_count,
                }
                for file in results[:10]  # Return only the first 10 for brevity
            ],
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")
    
    if not result:
        raise HTTPException(status_code=404, detail=f"No {analysis_type} analysis found for this snapshot")
    
    # Convert SQLAlchemy model to dict
    data = {c.name: getattr(result, c.name) for c in result.__table__.columns}
    
    # Convert UUID to string
    if "snapshot_id" in data:
        data["snapshot_id"] = str(data["snapshot_id"])
    
    return {
        "snapshot_id": str(snapshot_id),
        "analysis_type": analysis_type,
        "data": data,
    }


@app.delete("/api/snapshots/{snapshot_id}", dependencies=[Depends(verify_api_key)])
async def delete_snapshot(
    snapshot_id: uuid.UUID,
    snapshot_service: SnapshotService = Depends(get_snapshot_service),
):
    """Delete a snapshot and its associated files."""
    success = await snapshot_service.delete_snapshot(snapshot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return {
        "status": "success",
        "message": f"Snapshot {snapshot_id} deleted successfully",
    }


# Add GraphQL support if enabled
if settings.enable_graphql:
    import strawberry
    from strawberry.fastapi import GraphQLRouter
    
    @strawberry.type
    class SnapshotType:
        id: str
        repository: str
        commit_sha: Optional[str]
        branch: Optional[str]
        created_at: str
        metadata: Dict[str, Any]
    
    @strawberry.type
    class Query:
        @strawberry.field
        async def snapshots(
            self,
            repository: Optional[str] = None,
            branch: Optional[str] = None,
            limit: int = 10,
            offset: int = 0,
            db: Session = Depends(get_db),
        ) -> List[SnapshotType]:
            """Get a list of snapshots."""
            snapshot_service = SnapshotService(db, StorageService())
            snapshots = await snapshot_service.list_snapshots(
                repository=repository,
                branch=branch,
                limit=limit,
                offset=offset,
            )
            
            return [
                SnapshotType(
                    id=str(snapshot.id),
                    repository=snapshot.repository,
                    commit_sha=snapshot.commit_sha,
                    branch=snapshot.branch,
                    created_at=snapshot.created_at.isoformat(),
                    metadata=snapshot.metadata,
                )
                for snapshot in snapshots
            ]
        
        @strawberry.field
        async def snapshot(
            self,
            id: str,
            db: Session = Depends(get_db),
        ) -> Optional[SnapshotType]:
            """Get a snapshot by ID."""
            snapshot_service = SnapshotService(db, StorageService())
            snapshot = await snapshot_service.get_snapshot(uuid.UUID(id))
            
            if not snapshot:
                return None
            
            return SnapshotType(
                id=str(snapshot.id),
                repository=snapshot.repository,
                commit_sha=snapshot.commit_sha,
                branch=snapshot.branch,
                created_at=snapshot.created_at.isoformat(),
                metadata=snapshot.metadata,
            )
    
    schema = strawberry.Schema(query=Query)
    graphql_app = GraphQLRouter(schema)
    
    app.include_router(graphql_app, prefix="/graphql")


# Add WebSocket support if enabled
if settings.enable_websockets:
    from fastapi import WebSocket, WebSocketDisconnect
    
    class ConnectionManager:
        def __init__(self):
            self.active_connections: Dict[str, List[WebSocket]] = {}
        
        async def connect(self, websocket: WebSocket, client_id: str):
            await websocket.accept()
            if client_id not in self.active_connections:
                self.active_connections[client_id] = []
            self.active_connections[client_id].append(websocket)
        
        def disconnect(self, websocket: WebSocket, client_id: str):
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
        
        async def send_message(self, message: Dict[str, Any], client_id: str):
            if client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    await connection.send_json(message)
    
    manager = ConnectionManager()
    
    @app.websocket("/ws/analysis/{job_id}")
    async def analysis_updates(websocket: WebSocket, job_id: str):
        await manager.connect(websocket, job_id)
        try:
            while True:
                # Wait for messages (keep connection alive)
                data = await websocket.receive_text()
                
                # Echo back the message
                await websocket.send_json({"message": f"Received: {data}"})
        except WebSocketDisconnect:
            manager.disconnect(websocket, job_id)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    from codegen_on_oss.database.connection import init_db
    
    # Initialize database
    init_db(create_tables=True)
    
    logger.info(f"Codegen Analysis API started (version: {settings.app_version})")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Codegen Analysis API shutting down")


# Main entry point
def start():
    """Start the FastAPI application using uvicorn."""
    import uvicorn
    
    uvicorn.run(
        "codegen_on_oss.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        workers=settings.api_workers,
    )


if __name__ == "__main__":
    start()

