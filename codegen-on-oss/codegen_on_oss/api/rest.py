"""
REST API for the codegen-on-oss system.

This module provides a REST API for accessing analysis data.
"""

import logging
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from codegen_on_oss.database.connection import get_db
from codegen_on_oss.database.repositories import (
    RepositoryRepository,
    SnapshotRepository,
    FileRepository,
    AnalysisResultRepository,
    AnalysisIssueRepository,
    AnalysisJobRepository,
)
from codegen_on_oss.events.event_bus import EventType, Event, event_bus
from codegen_on_oss.snapshot.enhanced_snapshot_manager import EnhancedSnapshotManager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.post("/repositories", status_code=201)
async def create_repository(
    repo_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new repository.
    
    Args:
        repo_data: Repository data
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        Created repository
    """
    repo_repo = RepositoryRepository(db)
    
    # Check if repository already exists
    existing_repo = repo_repo.get_by_url(repo_data["url"])
    if existing_repo:
        return existing_repo
    
    # Create repository
    repo = repo_repo.create(
        name=repo_data["name"],
        url=repo_data["url"],
        description=repo_data.get("description"),
        default_branch=repo_data.get("default_branch", "main"),
    )
    
    # Publish repository added event
    event_bus.publish(
        Event(
            EventType.REPOSITORY_ADDED,
            {
                "repo_id": repo.id,
                "repo_url": repo.url,
                "repo_name": repo.name,
                "create_snapshot": repo_data.get("create_snapshot", False),
                "analyze": repo_data.get("analyze", False),
            },
        )
    )
    
    return repo


@router.get("/repositories")
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List repositories.
    
    Args:
        skip: Number of repositories to skip
        limit: Maximum number of repositories to return
        db: Database session
    
    Returns:
        List of repositories
    """
    repo_repo = RepositoryRepository(db)
    return repo_repo.get_all(skip=skip, limit=limit)


@router.get("/repositories/{repo_id}")
async def get_repository(
    repo_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a repository by ID.
    
    Args:
        repo_id: Repository ID
        db: Database session
    
    Returns:
        Repository
    """
    repo_repo = RepositoryRepository(db)
    repo = repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/repositories/{repo_id}", status_code=204)
async def delete_repository(
    repo_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a repository.
    
    Args:
        repo_id: Repository ID
        db: Database session
    
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
    event_bus.publish(
        Event(
            EventType.REPOSITORY_DELETED,
            {
                "repo_id": repo_id,
                "repo_url": repo.url,
                "repo_name": repo.name,
            },
        )
    )
    
    return None


@router.post("/snapshots", status_code=202)
async def create_snapshot(
    snapshot_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new snapshot.
    
    Args:
        snapshot_data: Snapshot data
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        Job information
    """
    # Create a job record
    job_repo = AnalysisJobRepository(db)
    
    job = job_repo.create(
        repository=snapshot_data["repo_url"],
        commit_sha=snapshot_data.get("commit_sha"),
        branch=snapshot_data.get("branch"),
        analysis_types=["snapshot"],
        status="pending",
    )
    
    # Publish job created event
    event_bus.publish(
        Event(
            EventType.JOB_CREATED,
            {
                "job_id": job.id,
                "repo_url": snapshot_data["repo_url"],
                "commit_sha": snapshot_data.get("commit_sha"),
                "branch": snapshot_data.get("branch"),
                "job_type": "snapshot",
            },
        )
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.id,
            "status": "pending",
            "message": "Snapshot creation job submitted",
        },
    )


@router.get("/snapshots")
async def list_snapshots(
    repo_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List snapshots.
    
    Args:
        repo_id: Optional repository ID filter
        skip: Number of snapshots to skip
        limit: Maximum number of snapshots to return
        db: Database session
    
    Returns:
        List of snapshots
    """
    snapshot_repo = SnapshotRepository(db)
    
    if repo_id:
        # Get snapshots for repository
        return snapshot_repo.get_snapshots_for_repository(repo_id)
    else:
        # Get all snapshots
        return snapshot_repo.get_all(skip=skip, limit=limit)


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a snapshot by ID.
    
    Args:
        snapshot_id: Snapshot ID
        db: Database session
    
    Returns:
        Snapshot
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot


@router.delete("/snapshots/{snapshot_id}", status_code=204)
async def delete_snapshot(
    snapshot_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a snapshot.
    
    Args:
        snapshot_id: Snapshot ID
        db: Database session
    
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
    event_bus.publish(
        Event(
            EventType.SNAPSHOT_DELETED,
            {
                "snapshot_id": snapshot_id,
                "repo_id": snapshot.repository_id,
            },
        )
    )
    
    return None


@router.get("/snapshots/{snapshot_id}/files")
async def list_snapshot_files(
    snapshot_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List files in a snapshot.
    
    Args:
        snapshot_id: Snapshot ID
        skip: Number of files to skip
        limit: Maximum number of files to return
        db: Database session
    
    Returns:
        List of files
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    file_repo = FileRepository(db)
    return file_repo.get_files_for_snapshot(snapshot.id)


@router.get("/snapshots/{snapshot_id}/files/{file_path:path}")
async def get_snapshot_file(
    snapshot_id: str,
    file_path: str,
    db: Session = Depends(get_db),
):
    """
    Get a file from a snapshot.
    
    Args:
        snapshot_id: Snapshot ID
        file_path: File path
        db: Database session
    
    Returns:
        File content
    """
    snapshot_repo = SnapshotRepository(db)
    snapshot = snapshot_repo.get_by_snapshot_id(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    # Get file content
    snapshot_manager = EnhancedSnapshotManager(db)
    content = snapshot_manager.get_file_content(snapshot_id, file_path)
    
    if not content:
        raise HTTPException(status_code=404, detail="File not found")
    
    return content


@router.post("/analysis", status_code=202)
async def create_analysis(
    analysis_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a new analysis job.
    
    Args:
        analysis_data: Analysis data
        background_tasks: Background tasks
        db: Database session
    
    Returns:
        Job information
    """
    # Create a job record
    job_repo = AnalysisJobRepository(db)
    
    job = job_repo.create(
        repository=analysis_data["repo_url"],
        commit_sha=analysis_data.get("commit_sha"),
        branch=analysis_data.get("branch"),
        snapshot_id=analysis_data.get("snapshot_id"),
        analysis_types=analysis_data.get("analysis_types", ["code_quality"]),
        status="pending",
    )
    
    # Publish job created event
    event_bus.publish(
        Event(
            EventType.JOB_CREATED,
            {
                "job_id": job.id,
                "repo_url": analysis_data["repo_url"],
                "commit_sha": analysis_data.get("commit_sha"),
                "branch": analysis_data.get("branch"),
                "snapshot_id": analysis_data.get("snapshot_id"),
                "analysis_types": analysis_data.get("analysis_types", ["code_quality"]),
                "job_type": "analysis",
            },
        )
    )
    
    return JSONResponse(
        status_code=202,
        content={
            "job_id": job.id,
            "status": "pending",
            "message": "Analysis job submitted",
        },
    )


@router.get("/analysis/jobs")
async def list_analysis_jobs(
    repo_url: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List analysis jobs.
    
    Args:
        repo_url: Optional repository URL filter
        status: Optional status filter
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        db: Database session
    
    Returns:
        List of analysis jobs
    """
    job_repo = AnalysisJobRepository(db)
    
    # Get all jobs
    query = db.query(job_repo.model)
    
    if repo_url:
        query = query.filter(job_repo.model.repository == repo_url)
    
    if status:
        query = query.filter(job_repo.model.status == status)
    
    return query.offset(skip).limit(limit).all()


@router.get("/analysis/jobs/{job_id}")
async def get_analysis_job(
    job_id: str,
    db: Session = Depends(get_db),
):
    """
    Get an analysis job by ID.
    
    Args:
        job_id: Job ID
        db: Database session
    
    Returns:
        Analysis job
    """
    job_repo = AnalysisJobRepository(db)
    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job


@router.get("/analysis/results")
async def list_analysis_results(
    repo_id: Optional[int] = None,
    snapshot_id: Optional[int] = None,
    analysis_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List analysis results.
    
    Args:
        repo_id: Optional repository ID filter
        snapshot_id: Optional snapshot ID filter
        analysis_type: Optional analysis type filter
        skip: Number of results to skip
        limit: Maximum number of results to return
        db: Database session
    
    Returns:
        List of analysis results
    """
    result_repo = AnalysisResultRepository(db)
    
    # Get all results
    query = db.query(result_repo.model)
    
    if repo_id:
        query = query.filter(result_repo.model.repository_id == repo_id)
    
    if snapshot_id:
        query = query.filter(result_repo.model.snapshot_id == snapshot_id)
    
    if analysis_type:
        query = query.filter(result_repo.model.analysis_type == analysis_type)
    
    return query.offset(skip).limit(limit).all()


@router.get("/analysis/results/{result_id}")
async def get_analysis_result(
    result_id: int,
    db: Session = Depends(get_db),
):
    """
    Get an analysis result by ID.
    
    Args:
        result_id: Result ID
        db: Database session
    
    Returns:
        Analysis result
    """
    result_repo = AnalysisResultRepository(db)
    result = result_repo.get_by_id(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return result


@router.get("/analysis/results/{result_id}/issues")
async def list_analysis_issues(
    result_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List issues for an analysis result.
    
    Args:
        result_id: Result ID
        skip: Number of issues to skip
        limit: Maximum number of issues to return
        db: Database session
    
    Returns:
        List of analysis issues
    """
    issue_repo = AnalysisIssueRepository(db)
    return issue_repo.get_issues_for_analysis(result_id)


@router.post("/snapshots/compare")
async def compare_snapshots(
    comparison_data: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Compare two snapshots.
    
    Args:
        comparison_data: Comparison data
        db: Database session
    
    Returns:
        Comparison results
    """
    snapshot_manager = EnhancedSnapshotManager(db)
    
    return snapshot_manager.compare_snapshots(
        comparison_data["snapshot_id_1"],
        comparison_data["snapshot_id_2"],
    )

