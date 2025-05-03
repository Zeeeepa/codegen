"""
API Routes Module

This module defines the API routes for the application, providing endpoints for
repository analysis, snapshot management, and real-time updates.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid

from codegen_on_oss.database.connection import get_db
from codegen_on_oss.database.repositories import (
    RepositoryRepository, SnapshotRepository, AnalysisResultRepository,
    AnalysisIssueRepository, FileRepository, AnalysisJobRepository
)
from codegen_on_oss.events.event_bus import EventType, Event, event_bus
from codegen_on_oss.api.websocket_manager import websocket_manager
from codegen_on_oss.api.schemas import (
    RepositoryCreate, RepositoryResponse, SnapshotCreate, SnapshotResponse,
    AnalysisRequest, AnalysisResponse, AnalysisJobResponse, AnalysisIssueResponse,
    FileResponse, WebhookCreate, WebhookResponse
)

logger = logging.getLogger(__name__)

# Create API routers
router = APIRouter()
ws_router = APIRouter()

# Repository routes
@router.post("/repositories", response_model=RepositoryResponse, status_code=201)
async def create_repository(
    repository: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new repository.
    
    Args:
        repository: The repository to create
        background_tasks: Background tasks
        db: The database session
        
    Returns:
        The created repository
    """
    repo_repo = RepositoryRepository(db)
    
    # Check if repository already exists
    existing_repo = repo_repo.get_by_url(repository.url)
    if existing_repo:
        return existing_repo
    
    # Create repository
    repo = repo_repo.create(
        name=repository.name,
        url=repository.url,
        description=repository.description,
        default_branch=repository.default_branch
    )
    
    # Publish repository added event
    event_bus.publish(Event(
        EventType.REPOSITORY_ADDED,
        {
            "repo_id": repo.id,
            "repo_url": repo.url,
            "repo_name": repo.name,
            "create_snapshot": repository.create_snapshot,
            "analyze": repository.analyze
        }
    ))
    
    return repo

@router.get("/repositories", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List repositories.
    
    Args:
        skip: Number of repositories to skip
        limit: Maximum number of repositories to return
        db: The database session
        
    Returns:
        A list of repositories
    """
    repo_repo = RepositoryRepository(db)
    return repo_repo.get_all(skip=skip, limit=limit)

@router.get("/repositories/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int = Path(..., title="The ID of the repository to get"),
    db: Session = Depends(get_db)
):
    """
    Get a repository by ID.
    
    Args:
        repo_id: The repository ID
        db: The database session
        
    Returns:
        The repository
    """
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.delete("/repositories/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: int = Path(..., title="The ID of the repository to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a repository.
    
    Args:
        repo_id: The repository ID
        db: The database session
        
    Returns:
        No content
    """
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Delete repository
    repo_repo.delete(repo_id)
    
    # Publish repository deleted event
    event_bus.publish(Event(
        EventType.REPOSITORY_DELETED,
        {
            "repo_id": repo_id,
            "repo_url": repo.url,
            "repo_name": repo.name
        }
    ))
    
    return None

# Snapshot routes
@router.post("/snapshots", response_model=SnapshotResponse, status_code=201)
async def create_snapshot(
    snapshot: SnapshotCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new snapshot.
    
    Args:
        snapshot: The snapshot to create
        background_tasks: Background tasks
        db: The database session
        
    Returns:
        The created snapshot
    """
    # This will be handled by a background task
    # We'll just create a job and return a job ID
    job_repo = AnalysisJobRepository(db)
    
    # Create job record
    job = job_repo.create(
        repo_id=snapshot.repo_id,
        job_type="create_snapshot",
        status="pending",
        parameters={
            "commit_sha": snapshot.commit_sha,
            "branch": snapshot.branch,
            "analyze": snapshot.analyze
        }
    )
    
    # Publish job created event
    event_bus.publish(Event(
        EventType.JOB_CREATED,
        {
            "job_id": job.id,
            "repo_id": job.repo_id,
            "job_type": job.job_type,
            "parameters": job.parameters
        }
    ))
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.id,
            "status": "pending",
            "message": "Snapshot creation job submitted"
        }
    )

@router.get("/snapshots", response_model=List[SnapshotResponse])
async def list_snapshots(
    repo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List snapshots.
    
    Args:
        repo_id: Optional repository ID filter
        skip: Number of snapshots to skip
        limit: Maximum number of snapshots to return
        db: The database session
        
    Returns:
        A list of snapshots
    """
    snapshot_repo = SnapshotRepository(db)
    
    if repo_id:
        # Get snapshots for repository
        snapshots = db.query(snapshot_repo.model).filter(
            snapshot_repo.model.repo_id == repo_id
        ).offset(skip).limit(limit).all()
        return snapshots
    else:
        # Get all snapshots
        return snapshot_repo.get_all(skip=skip, limit=limit)

@router.get("/snapshots/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str = Path(..., title="The ID of the snapshot to get"),
    db: Session = Depends(get_db)
):
    """
    Get a snapshot by ID.
    
    Args:
        snapshot_id: The snapshot ID
        db: The database session
        
    Returns:
        The snapshot
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot

@router.delete("/snapshots/{snapshot_id}", status_code=204)
async def delete_snapshot(
    snapshot_id: str = Path(..., title="The ID of the snapshot to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete a snapshot.
    
    Args:
        snapshot_id: The snapshot ID
        db: The database session
        
    Returns:
        No content
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    # Delete snapshot
    snapshot_repo.delete(snapshot.id)
    
    # Publish snapshot deleted event
    event_bus.publish(Event(
        EventType.SNAPSHOT_DELETED,
        {
            "snapshot_id": snapshot_id,
            "repo_id": snapshot.repo_id
        }
    ))
    
    return None

@router.get("/snapshots/{snapshot_id}/files", response_model=List[FileResponse])
async def list_snapshot_files(
    snapshot_id: str = Path(..., title="The ID of the snapshot to get files for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List files in a snapshot.
    
    Args:
        snapshot_id: The snapshot ID
        skip: Number of files to skip
        limit: Maximum number of files to return
        db: The database session
        
    Returns:
        A list of files
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    file_repo = FileRepository(db)
    return db.query(file_repo.model).filter(
        file_repo.model.snapshot_id == snapshot.id
    ).offset(skip).limit(limit).all()

@router.get("/snapshots/{snapshot_id}/files/{file_path:path}", response_model=FileResponse)
async def get_snapshot_file(
    snapshot_id: str = Path(..., title="The ID of the snapshot to get the file from"),
    file_path: str = Path(..., title="The path of the file to get"),
    db: Session = Depends(get_db)
):
    """
    Get a file from a snapshot.
    
    Args:
        snapshot_id: The snapshot ID
        file_path: The file path
        db: The database session
        
    Returns:
        The file
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    file_repo = FileRepository(db)
    file = file_repo.get_by_filepath(snapshot.id, file_path)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file

# Analysis routes
@router.post("/analysis", response_model=AnalysisJobResponse, status_code=202)
async def create_analysis(
    analysis: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new analysis job.
    
    Args:
        analysis: The analysis request
        background_tasks: Background tasks
        db: The database session
        
    Returns:
        The created analysis job
    """
    job_repo = AnalysisJobRepository(db)
    
    # Create job record
    job = job_repo.create(
        repo_id=analysis.repo_id,
        job_type=analysis.analysis_type,
        status="pending",
        parameters=analysis.parameters
    )
    
    # Publish job created event
    event_bus.publish(Event(
        EventType.JOB_CREATED,
        {
            "job_id": job.id,
            "repo_id": job.repo_id,
            "job_type": job.job_type,
            "parameters": job.parameters
        }
    ))
    
    return job

@router.get("/analysis/jobs", response_model=List[AnalysisJobResponse])
async def list_analysis_jobs(
    repo_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List analysis jobs.
    
    Args:
        repo_id: Optional repository ID filter
        status: Optional status filter
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        db: The database session
        
    Returns:
        A list of analysis jobs
    """
    job_repo = AnalysisJobRepository(db)
    
    if repo_id:
        # Get jobs for repository
        return job_repo.get_jobs_for_repo(repo_id, status)
    else:
        # Get all jobs
        query = db.query(job_repo.model)
        if status:
            query = query.filter(job_repo.model.status == status)
        return query.offset(skip).limit(limit).all()

@router.get("/analysis/jobs/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(
    job_id: int = Path(..., title="The ID of the analysis job to get"),
    db: Session = Depends(get_db)
):
    """
    Get an analysis job by ID.
    
    Args:
        job_id: The job ID
        db: The database session
        
    Returns:
        The analysis job
    """
    job_repo = AnalysisJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job

@router.get("/analysis/results", response_model=List[AnalysisResponse])
async def list_analysis_results(
    repo_id: Optional[int] = None,
    analysis_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List analysis results.
    
    Args:
        repo_id: Optional repository ID filter
        analysis_type: Optional analysis type filter
        skip: Number of results to skip
        limit: Maximum number of results to return
        db: The database session
        
    Returns:
        A list of analysis results
    """
    result_repo = AnalysisResultRepository(db)
    
    query = db.query(result_repo.model)
    if repo_id:
        query = query.filter(result_repo.model.repo_id == repo_id)
    if analysis_type:
        query = query.filter(result_repo.model.analysis_type == analysis_type)
    
    return query.offset(skip).limit(limit).all()

@router.get("/analysis/results/{result_id}", response_model=AnalysisResponse)
async def get_analysis_result(
    result_id: int = Path(..., title="The ID of the analysis result to get"),
    db: Session = Depends(get_db)
):
    """
    Get an analysis result by ID.
    
    Args:
        result_id: The result ID
        db: The database session
        
    Returns:
        The analysis result
    """
    result_repo = AnalysisResultRepository(db)
    result = result_repo.get_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result

@router.get("/analysis/results/{result_id}/issues", response_model=List[AnalysisIssueResponse])
async def list_analysis_issues(
    result_id: int = Path(..., title="The ID of the analysis result to get issues for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List issues for an analysis result.
    
    Args:
        result_id: The result ID
        skip: Number of issues to skip
        limit: Maximum number of issues to return
        db: The database session
        
    Returns:
        A list of analysis issues
    """
    issue_repo = AnalysisIssueRepository(db)
    return issue_repo.get_issues_for_analysis(result_id)

# WebSocket routes
@ws_router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Args:
        websocket: The WebSocket connection
        client_id: The client ID
    """
    # Generate a client ID if not provided
    if not client_id or client_id == "undefined":
        client_id = str(uuid.uuid4())
    
    await websocket_manager.handle_connection(websocket, client_id)
"""

