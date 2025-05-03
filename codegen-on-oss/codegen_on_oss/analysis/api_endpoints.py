"""
API Endpoints for Codegen-on-OSS

This module provides API endpoints for the enhanced analysis system,
including repository analysis, commit analysis, snapshot management,
and metrics retrieval.
"""

import logging
import os
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Set

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, Field

from codegen import Codebase
from codegen_on_oss.analysis.coordinator import AnalysisCoordinator
from codegen_on_oss.database import get_db_session
from codegen_on_oss.database import (
    RepositoryRepository, CommitRepository, FileRepository, SymbolRepository,
    SnapshotRepository, AnalysisResultRepository, MetricRepository, IssueRepository
)

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1", tags=["analysis"])

# Define request models
class RepositoryAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: default branch)")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze (default: latest commit)")

class CommitAnalysisRequest(BaseModel):
    """Request model for commit analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    commit_sha: str = Field(..., description="Commit SHA to analyze")

class SnapshotRequest(BaseModel):
    """Request model for creating a snapshot."""
    repo_url: str = Field(..., description="URL of the repository to snapshot")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to snapshot (default: latest commit)")
    branch: Optional[str] = Field(None, description="Branch to snapshot (default: default branch)")
    description: Optional[str] = Field(None, description="Description of the snapshot")

class SnapshotComparisonRequest(BaseModel):
    """Request model for comparing snapshots."""
    snapshot_id1: int = Field(..., description="ID of the first snapshot")
    snapshot_id2: int = Field(..., description="ID of the second snapshot")

class SymbolAnalysisRequest(BaseModel):
    """Request model for symbol analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    symbol_name: str = Field(..., description="Name of the symbol to analyze")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze (default: latest commit)")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: default branch)")

# Define response models
class AnalysisResponse(BaseModel):
    """Base response model for analysis results."""
    status: str = "success"
    error: Optional[str] = None
    analysis_id: Optional[int] = None
    repository_id: Optional[int] = None
    commit_id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RepositoryAnalysisResponse(AnalysisResponse):
    """Response model for repository analysis."""
    repo_url: str
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    file_count: int
    symbol_count: int
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]

class CommitAnalysisResponse(AnalysisResponse):
    """Response model for commit analysis."""
    repo_url: str
    commit_sha: str
    author: str
    message: str
    timestamp: datetime
    file_changes: Dict[str, Any]
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]

class SnapshotResponse(AnalysisResponse):
    """Response model for snapshot creation."""
    snapshot_id: int
    repo_url: str
    commit_sha: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    file_count: int
    symbol_count: int

class SnapshotComparisonResponse(AnalysisResponse):
    """Response model for snapshot comparison."""
    snapshot_id1: int
    snapshot_id2: int
    files_added: List[str]
    files_modified: List[str]
    files_removed: List[str]
    symbols_added: List[Dict[str, Any]]
    symbols_modified: List[Dict[str, Any]]
    symbols_removed: List[Dict[str, Any]]
    metrics_diff: Dict[str, Any]

class SymbolAnalysisResponse(AnalysisResponse):
    """Response model for symbol analysis."""
    repo_url: str
    symbol_name: str
    symbol_type: str
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    dependencies: List[Dict[str, Any]]

# Background task for cleaning up temporary directories
def cleanup_temp_dirs(temp_dirs: List[str]):
    """Clean up temporary directories after analysis."""
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            try:
                subprocess.run(["rm", "-rf", temp_dir], check=True)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory {temp_dir}: {e}")

# API endpoints
@router.post("/analyze/repository", response_model=RepositoryAnalysisResponse)
async def analyze_repository(request: RepositoryAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a repository and return comprehensive metrics.
    """
    try:
        logger.info(f"Analyzing repository: {request.repo_url}")
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        background_tasks.add_task(cleanup_temp_dirs, [temp_dir])
        
        # Clone the repository
        clone_cmd = ["git", "clone"]
        if request.branch:
            clone_cmd.extend(["--branch", request.branch])
        clone_cmd.extend([request.repo_url, temp_dir])
        
        subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
        
        if request.commit_sha:
            # Checkout specific commit
            subprocess.run(
                ["git", "checkout", request.commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(temp_dir)
        
        # Create an AnalysisCoordinator instance
        coordinator = AnalysisCoordinator()
        
        # Analyze the repository
        result = await coordinator.analyze_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            commit_sha=request.commit_sha,
            codebase=codebase
        )
        
        # Extract metrics and issues
        metrics = result.get("metrics", {})
        issues = result.get("issues", {})
        symbols = result.get("symbols", {})
        
        # Create response
        response = RepositoryAnalysisResponse(
            status="success",
            repo_url=request.repo_url,
            branch=request.branch,
            commit_sha=request.commit_sha,
            file_count=len(result.get("files", [])),
            symbol_count=symbols.get("counts", {}).get("total_count", 0),
            metrics=metrics,
            issues=issues,
            analysis_id=result.get("analysis_result_id"),
            repository_id=result.get("repository_id"),
            commit_id=result.get("commit_id")
        )
        
        return response
    except Exception as e:
        logger.error(f"Error analyzing repository {request.repo_url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing repository: {str(e)}"
        )

@router.post("/analyze/commit", response_model=CommitAnalysisResponse)
async def analyze_commit(request: CommitAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a commit in a repository.
    """
    try:
        logger.info(f"Analyzing commit {request.commit_sha} in repository {request.repo_url}")
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        background_tasks.add_task(cleanup_temp_dirs, [temp_dir])
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", request.repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Checkout the commit
        subprocess.run(
            ["git", "checkout", request.commit_sha],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(temp_dir)
        
        # Create an AnalysisCoordinator instance
        coordinator = AnalysisCoordinator()
        
        # Analyze the commit
        result = await coordinator.analyze_repository(
            repo_url=request.repo_url,
            commit_sha=request.commit_sha,
            codebase=codebase
        )
        
        # Extract commit data, metrics, and issues
        commit_data = result.get("commit", {})
        metrics = result.get("metrics", {})
        issues = result.get("issues", {})
        
        # Create response
        response = CommitAnalysisResponse(
            status="success",
            repo_url=request.repo_url,
            commit_sha=request.commit_sha,
            author=commit_data.get("author", "Unknown"),
            message=commit_data.get("message", ""),
            timestamp=commit_data.get("timestamp", datetime.utcnow()),
            file_changes=commit_data.get("file_changes", {}),
            metrics=metrics,
            issues=issues,
            analysis_id=result.get("analysis_result_id"),
            repository_id=result.get("repository_id"),
            commit_id=result.get("commit_id")
        )
        
        return response
    except Exception as e:
        logger.error(f"Error analyzing commit {request.commit_sha} in repository {request.repo_url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing commit: {str(e)}"
        )

@router.post("/snapshots/create", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotRequest, background_tasks: BackgroundTasks):
    """
    Create a snapshot of a repository.
    """
    try:
        logger.info(f"Creating snapshot for repository: {request.repo_url}")
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        background_tasks.add_task(cleanup_temp_dirs, [temp_dir])
        
        # Clone the repository
        clone_cmd = ["git", "clone"]
        if request.branch:
            clone_cmd.extend(["--branch", request.branch])
        clone_cmd.extend([request.repo_url, temp_dir])
        
        subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
        
        if request.commit_sha:
            # Checkout specific commit
            subprocess.run(
                ["git", "checkout", request.commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(temp_dir)
        
        # Create an AnalysisCoordinator instance
        coordinator = AnalysisCoordinator()
        
        # Analyze the repository
        result = await coordinator.analyze_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            commit_sha=request.commit_sha,
            codebase=codebase
        )
        
        # Get snapshot data
        snapshot_data = result.get("snapshot", {})
        symbols = result.get("symbols", {})
        
        # Create response
        response = SnapshotResponse(
            status="success",
            snapshot_id=snapshot_data.get("id"),
            repo_url=request.repo_url,
            commit_sha=snapshot_data.get("commit_sha"),
            description=request.description,
            created_at=datetime.fromisoformat(snapshot_data.get("created_at")),
            file_count=len(result.get("files", [])),
            symbol_count=symbols.get("counts", {}).get("total_count", 0),
            analysis_id=result.get("analysis_result_id"),
            repository_id=result.get("repository_id"),
            commit_id=result.get("commit_id")
        )
        
        return response
    except Exception as e:
        logger.error(f"Error creating snapshot for repository {request.repo_url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating snapshot: {str(e)}"
        )

@router.post("/snapshots/compare", response_model=SnapshotComparisonResponse)
async def compare_snapshots(request: SnapshotComparisonRequest):
    """
    Compare two snapshots.
    """
    try:
        logger.info(f"Comparing snapshots {request.snapshot_id1} and {request.snapshot_id2}")
        
        # Get snapshots from database
        with get_db_session() as session:
            snapshot_repo = SnapshotRepository()
            snapshot1 = snapshot_repo.get_by_id(session, request.snapshot_id1)
            snapshot2 = snapshot_repo.get_by_id(session, request.snapshot_id2)
            
            if not snapshot1 or not snapshot2:
                raise HTTPException(
                    status_code=404,
                    detail="One or both snapshots not found"
                )
            
            # Compare snapshots
            # This is a simplified comparison, a real implementation would be more complex
            files1 = set(snapshot1.data.get("files", {}).keys())
            files2 = set(snapshot2.data.get("files", {}).keys())
            
            files_added = list(files2 - files1)
            files_removed = list(files1 - files2)
            files_common = files1.intersection(files2)
            
            files_modified = []
            for file_path in files_common:
                file1 = snapshot1.data["files"][file_path]
                file2 = snapshot2.data["files"][file_path]
                
                if file1.get("hash") != file2.get("hash"):
                    files_modified.append(file_path)
            
            # Compare symbols
            symbols1 = set(snapshot1.data.get("symbols", {}).keys())
            symbols2 = set(snapshot2.data.get("symbols", {}).keys())
            
            symbols_added = []
            for symbol_id in symbols2 - symbols1:
                symbols_added.append(snapshot2.data["symbols"][symbol_id])
            
            symbols_removed = []
            for symbol_id in symbols1 - symbols2:
                symbols_removed.append(snapshot1.data["symbols"][symbol_id])
            
            symbols_modified = []
            for symbol_id in symbols1.intersection(symbols2):
                symbol1 = snapshot1.data["symbols"][symbol_id]
                symbol2 = snapshot2.data["symbols"][symbol_id]
                
                if symbol1.get("content_hash") != symbol2.get("content_hash"):
                    symbols_modified.append(symbol2)
            
            # Create response
            response = SnapshotComparisonResponse(
                status="success",
                snapshot_id1=request.snapshot_id1,
                snapshot_id2=request.snapshot_id2,
                files_added=files_added,
                files_modified=files_modified,
                files_removed=files_removed,
                symbols_added=symbols_added,
                symbols_modified=symbols_modified,
                symbols_removed=symbols_removed,
                metrics_diff={}  # Would be calculated in a real implementation
            )
            
            return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing snapshots {request.snapshot_id1} and {request.snapshot_id2}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing snapshots: {str(e)}"
        )

@router.post("/analyze/symbol", response_model=SymbolAnalysisResponse)
async def analyze_symbol(request: SymbolAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a specific symbol in a repository.
    """
    try:
        logger.info(f"Analyzing symbol {request.symbol_name} in repository {request.repo_url}")
        
        # Create a temporary directory for the repository
        temp_dir = tempfile.mkdtemp()
        background_tasks.add_task(cleanup_temp_dirs, [temp_dir])
        
        # Clone the repository
        clone_cmd = ["git", "clone"]
        if request.branch:
            clone_cmd.extend(["--branch", request.branch])
        clone_cmd.extend([request.repo_url, temp_dir])
        
        subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
        
        if request.commit_sha:
            # Checkout specific commit
            subprocess.run(
                ["git", "checkout", request.commit_sha],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(temp_dir)
        
        # Create an AnalysisCoordinator instance
        coordinator = AnalysisCoordinator()
        
        # Analyze the repository
        result = await coordinator.analyze_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            commit_sha=request.commit_sha,
            codebase=codebase
        )
        
        # Find the symbol
        symbol_data = None
        symbol_metrics = {}
        symbol_issues = []
        symbol_dependencies = []
        
        symbols = result.get("symbols", {}).get("symbols", {})
        for symbol_type, symbol_list in symbols.items():
            for symbol in symbol_list:
                if symbol["name"] == request.symbol_name or symbol["qualified_name"].endswith(f".{request.symbol_name}"):
                    symbol_data = symbol
                    break
            if symbol_data:
                break
        
        if not symbol_data:
            raise HTTPException(
                status_code=404,
                detail=f"Symbol {request.symbol_name} not found in repository"
            )
        
        # Get metrics for the symbol
        metrics = result.get("metrics", {}).get("symbols", {})
        for symbol_id, metric_data in metrics.items():
            if symbol_id.endswith(f":{symbol_data['name']}:{symbol_data.get('line_start', 0)}"):
                symbol_metrics = metric_data
                break
        
        # Get issues for the symbol
        issues = result.get("issues", {}).get("symbols", {})
        for symbol_id, issue_list in issues.items():
            if symbol_id.endswith(f":{symbol_data['name']}:{symbol_data.get('line_start', 0)}"):
                symbol_issues = issue_list
                break
        
        # Get dependencies for the symbol
        dependencies = result.get("dependencies", {}).get("dependencies", [])
        for dependency in dependencies:
            if dependency["source"].endswith(f":{symbol_data['name']}:{symbol_data.get('line_start', 0)}"):
                symbol_dependencies.append(dependency)
        
        # Create response
        response = SymbolAnalysisResponse(
            status="success",
            repo_url=request.repo_url,
            symbol_name=symbol_data["name"],
            symbol_type=symbol_data["type"],
            file_path=symbol_data["file_path"],
            line_start=symbol_data.get("line_start"),
            line_end=symbol_data.get("line_end"),
            metrics=symbol_metrics,
            issues=symbol_issues,
            dependencies=symbol_dependencies,
            analysis_id=result.get("analysis_result_id"),
            repository_id=result.get("repository_id"),
            commit_id=result.get("commit_id")
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing symbol {request.symbol_name} in repository {request.repo_url}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing symbol: {str(e)}"
        )

@router.get("/repositories", response_model=List[Dict[str, Any]])
async def list_repositories(
    limit: int = Query(10, description="Maximum number of repositories to return"),
    offset: int = Query(0, description="Number of repositories to skip")
):
    """
    List all repositories.
    """
    try:
        logger.info(f"Listing repositories (limit={limit}, offset={offset})")
        
        with get_db_session() as session:
            repo_repo = RepositoryRepository()
            repositories = repo_repo.get_all(session, limit=limit, offset=offset)
            
            result = []
            for repo in repositories:
                result.append({
                    "id": repo.id,
                    "name": repo.name,
                    "url": repo.url,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at.isoformat(),
                    "last_analyzed": repo.last_analyzed.isoformat() if repo.last_analyzed else None
                })
            
            return result
    except Exception as e:
        logger.error(f"Error listing repositories: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing repositories: {str(e)}"
        )

@router.get("/snapshots", response_model=List[Dict[str, Any]])
async def list_snapshots(
    repository_id: Optional[int] = Query(None, description="Repository ID to filter by"),
    limit: int = Query(10, description="Maximum number of snapshots to return"),
    offset: int = Query(0, description="Number of snapshots to skip")
):
    """
    List all snapshots.
    """
    try:
        logger.info(f"Listing snapshots (repository_id={repository_id}, limit={limit}, offset={offset})")
        
        with get_db_session() as session:
            snapshot_repo = SnapshotRepository()
            
            if repository_id:
                snapshots = snapshot_repo.get_latest_snapshots(session, repository_id, limit=limit)
            else:
                snapshots = snapshot_repo.get_all(session, limit=limit, offset=offset)
            
            result = []
            for snapshot in snapshots:
                result.append({
                    "id": snapshot.id,
                    "repository_id": snapshot.repository_id,
                    "commit_sha": snapshot.commit_sha,
                    "snapshot_hash": snapshot.snapshot_hash,
                    "description": snapshot.description,
                    "created_at": snapshot.created_at.isoformat()
                })
            
            return result
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing snapshots: {str(e)}"
        )

@router.get("/analysis-results", response_model=List[Dict[str, Any]])
async def list_analysis_results(
    repository_id: Optional[int] = Query(None, description="Repository ID to filter by"),
    analysis_type: Optional[str] = Query(None, description="Analysis type to filter by"),
    limit: int = Query(10, description="Maximum number of analysis results to return"),
    offset: int = Query(0, description="Number of analysis results to skip")
):
    """
    List all analysis results.
    """
    try:
        logger.info(f"Listing analysis results (repository_id={repository_id}, analysis_type={analysis_type}, limit={limit}, offset={offset})")
        
        with get_db_session() as session:
            analysis_result_repo = AnalysisResultRepository()
            
            if repository_id and analysis_type:
                analysis_results = analysis_result_repo.get_by_type(session, repository_id, analysis_type)
                analysis_results = analysis_results[:limit]
            else:
                analysis_results = analysis_result_repo.get_all(session, limit=limit, offset=offset)
            
            result = []
            for analysis_result in analysis_results:
                result.append({
                    "id": analysis_result.id,
                    "repository_id": analysis_result.repository_id,
                    "commit_id": analysis_result.commit_id,
                    "snapshot_id": analysis_result.snapshot_id,
                    "analysis_type": analysis_result.analysis_type,
                    "status": analysis_result.status,
                    "created_at": analysis_result.created_at.isoformat(),
                    "completed_at": analysis_result.completed_at.isoformat() if analysis_result.completed_at else None
                })
            
            return result
    except Exception as e:
        logger.error(f"Error listing analysis results: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error listing analysis results: {str(e)}"
        )

