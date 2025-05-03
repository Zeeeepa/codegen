"""
REST API for codegen-on-oss.

This module provides a FastAPI-based REST API for interacting with the codegen-on-oss system.
"""

import logging
import os
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator, root_validator

from codegen import Codebase
from codegen_on_oss.database.connection import get_db_manager
from codegen_on_oss.database.service import CodebaseService, UserPreferenceService, WebhookService
from codegen_on_oss.cache.manager import get_cache_manager
from codegen_on_oss.events.bus import get_event_bus, EventType
from codegen_on_oss.api.graphql import execute_query
from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import SnapshotManager

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Codegen Analysis API",
    description="API for analyzing code repositories and commits",
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

# Initialize services
codebase_service = CodebaseService()
user_preference_service = UserPreferenceService()
webhook_service = WebhookService()
cache_manager = get_cache_manager()
event_bus = get_event_bus()

# Define request models
class RepoAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    branch: Optional[str] = Field(None, description="Branch to analyze")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to analyze")
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")

class SnapshotRequest(BaseModel):
    """Request model for creating a snapshot."""
    repo_url: str = Field(..., description="URL of the repository to snapshot")
    branch: Optional[str] = Field(None, description="Branch to snapshot")
    commit_sha: Optional[str] = Field(None, description="Commit SHA to snapshot")
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")

class CompareSnapshotsRequest(BaseModel):
    """Request model for comparing snapshots."""
    base_snapshot_id: str = Field(..., description="ID of the base snapshot")
    compare_snapshot_id: str = Field(..., description="ID of the snapshot to compare against the base")

class GraphQLRequest(BaseModel):
    """Request model for GraphQL queries."""
    query: str = Field(..., description="GraphQL query")
    variables: Optional[Dict[str, Any]] = Field(None, description="Query variables")

class WebhookRegistrationRequest(BaseModel):
    """Request model for registering a webhook."""
    repo_url: str = Field(..., description="URL of the repository")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(["analysis_completed"], description="Events to trigger the webhook")
    secret: Optional[str] = Field(None, description="Secret to sign webhook payloads with")

class UserPreferenceRequest(BaseModel):
    """Request model for setting user preferences."""
    user_id: str = Field(..., description="User ID")
    preference_key: str = Field(..., description="Preference key")
    preference_value: Any = Field(..., description="Preference value")

# Define response models
class AnalysisResponse(BaseModel):
    """Base response model for analysis results."""
    repo_url: str
    status: str = "success"
    error: Optional[str] = None

class SnapshotResponse(BaseModel):
    """Response model for snapshot operations."""
    snapshot_id: str
    repo_url: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    timestamp: datetime
    status: str = "success"
    error: Optional[str] = None

class CompareSnapshotsResponse(BaseModel):
    """Response model for snapshot comparison."""
    base_snapshot_id: str
    compare_snapshot_id: str
    differences: Dict[str, Any]
    status: str = "success"
    error: Optional[str] = None

class WebhookResponse(BaseModel):
    """Response model for webhook registration."""
    webhook_id: str
    repo_url: str
    url: str
    events: List[str]
    status: str = "success"
    error: Optional[str] = None

class UserPreferenceResponse(BaseModel):
    """Response model for user preferences."""
    user_id: str
    preference_key: str
    preference_value: Any
    status: str = "success"
    error: Optional[str] = None

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

@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {
        "name": "Codegen Analysis API",
        "description": "API for analyzing code repositories and commits",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/analyze_repo", "method": "POST", "description": "Analyze a repository"},
            {"path": "/create_snapshot", "method": "POST", "description": "Create a snapshot of a repository"},
            {"path": "/get_snapshot/{snapshot_id}", "method": "GET", "description": "Get a snapshot by ID"},
            {"path": "/compare_snapshots", "method": "POST", "description": "Compare two snapshots"},
            {"path": "/graphql", "method": "POST", "description": "Execute a GraphQL query"},
            {"path": "/register_webhook", "method": "POST", "description": "Register a webhook"},
            {"path": "/set_preference", "method": "POST", "description": "Set a user preference"},
            {"path": "/get_preference/{user_id}/{preference_key}", "method": "GET", "description": "Get a user preference"},
        ]
    }

@app.post("/analyze_repo", response_model=AnalysisResponse)
async def analyze_repo(request: RepoAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a repository and return comprehensive metrics.
    """
    try:
        # Check cache
        cache_key = f"repo_analysis:{request.repo_url}:{request.branch or 'default'}:{request.commit_sha or 'latest'}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Using cached result for {cache_key}")
            return cached_result
        
        # Create temporary directories
        temp_dirs = []
        repo_dir = tempfile.mkdtemp()
        temp_dirs.append(repo_dir)
        
        # Clone the repository
        logger.info(f"Cloning repository: {request.repo_url}")
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Checkout the branch or commit if specified
        if request.branch:
            logger.info(f"Checking out branch: {request.branch}")
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.branch],
                check=True,
                capture_output=True,
                text=True,
            )
        
        if request.commit_sha:
            logger.info(f"Checking out commit: {request.commit_sha}")
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.commit_sha],
                check=True,
                capture_output=True,
                text=True,
            )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(repo_dir)
        
        # Create or get the repository in the database
        repo_name = os.path.basename(request.repo_url.rstrip("/").replace(".git", ""))
        repository = codebase_service.create_repository(
            url=request.repo_url,
            name=repo_name,
            default_branch=request.branch or "main"
        )
        
        # Create a snapshot
        snapshot = codebase_service.create_snapshot(
            codebase=codebase,
            repository_id=repository.id,
            commit_sha=request.commit_sha,
            branch=request.branch
        )
        
        # Analyze the codebase
        analyzer = CodeAnalyzer(codebase)
        
        # Store analysis results
        complexity_result = analyzer.analyze_complexity()
        codebase_service.store_analysis_result(
            snapshot_id=snapshot.id,
            analysis_type="complexity",
            result=complexity_result
        )
        
        imports_result = analyzer.analyze_imports()
        codebase_service.store_analysis_result(
            snapshot_id=snapshot.id,
            analysis_type="imports",
            result=imports_result
        )
        
        summary_result = analyzer.get_codebase_summary()
        codebase_service.store_analysis_result(
            snapshot_id=snapshot.id,
            analysis_type="summary",
            result=summary_result
        )
        
        # Combine results
        result = {
            "repo_url": request.repo_url,
            "status": "success",
            "snapshot_id": snapshot.id,
            "summary": summary_result,
            "complexity": complexity_result,
            "imports": imports_result
        }
        
        # Cache result
        cache_manager.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        # Publish event
        event_bus.publish_event(
            EventType.ANALYSIS_COMPLETED,
            {
                "repo_url": request.repo_url,
                "snapshot_id": snapshot.id,
                "branch": request.branch,
                "commit_sha": request.commit_sha
            }
        )
        
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing repository {request.repo_url}: {e}")
        
        # Publish event
        event_bus.publish_event(
            EventType.ANALYSIS_FAILED,
            {
                "repo_url": request.repo_url,
                "branch": request.branch,
                "commit_sha": request.commit_sha,
                "error": str(e)
            }
        )
        
        # Schedule cleanup of temporary directories
        if 'temp_dirs' in locals():
            background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return {
            "repo_url": request.repo_url,
            "status": "error",
            "error": str(e)
        }

@app.post("/create_snapshot", response_model=SnapshotResponse)
async def create_snapshot(request: SnapshotRequest, background_tasks: BackgroundTasks):
    """
    Create a snapshot of a repository.
    """
    try:
        # Create temporary directories
        temp_dirs = []
        repo_dir = tempfile.mkdtemp()
        temp_dirs.append(repo_dir)
        
        # Clone the repository
        logger.info(f"Cloning repository: {request.repo_url}")
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Checkout the branch or commit if specified
        if request.branch:
            logger.info(f"Checking out branch: {request.branch}")
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.branch],
                check=True,
                capture_output=True,
                text=True,
            )
        
        if request.commit_sha:
            logger.info(f"Checking out commit: {request.commit_sha}")
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.commit_sha],
                check=True,
                capture_output=True,
                text=True,
            )
        
        # Create a Codebase instance
        codebase = Codebase.from_directory(repo_dir)
        
        # Create or get the repository in the database
        repo_name = os.path.basename(request.repo_url.rstrip("/").replace(".git", ""))
        repository = codebase_service.create_repository(
            url=request.repo_url,
            name=repo_name,
            default_branch=request.branch or "main"
        )
        
        # Create a snapshot
        snapshot = codebase_service.create_snapshot(
            codebase=codebase,
            repository_id=repository.id,
            commit_sha=request.commit_sha,
            branch=request.branch
        )
        
        # Publish event
        event_bus.publish_event(
            EventType.SNAPSHOT_CREATED,
            {
                "repo_url": request.repo_url,
                "snapshot_id": snapshot.id,
                "branch": request.branch,
                "commit_sha": request.commit_sha
            }
        )
        
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return {
            "snapshot_id": snapshot.id,
            "repo_url": request.repo_url,
            "commit_sha": request.commit_sha,
            "branch": request.branch,
            "timestamp": snapshot.timestamp,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error creating snapshot for repository {request.repo_url}: {e}")
        
        # Schedule cleanup of temporary directories
        if 'temp_dirs' in locals():
            background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return {
            "snapshot_id": "",
            "repo_url": request.repo_url,
            "commit_sha": request.commit_sha,
            "branch": request.branch,
            "timestamp": datetime.utcnow(),
            "status": "error",
            "error": str(e)
        }

@app.get("/get_snapshot/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(snapshot_id: str):
    """
    Get a snapshot by ID.
    """
    try:
        snapshot = codebase_service.snapshot_repo.get_by_id(snapshot_id)
        
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Snapshot with ID {snapshot_id} not found")
        
        repository = codebase_service.repository_repo.get_by_id(snapshot.repository_id)
        
        return {
            "snapshot_id": snapshot.id,
            "repo_url": repository.url if repository else "",
            "commit_sha": snapshot.commit_sha,
            "branch": snapshot.branch,
            "timestamp": snapshot.timestamp,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot {snapshot_id}: {e}")
        return {
            "snapshot_id": snapshot_id,
            "repo_url": "",
            "commit_sha": None,
            "branch": None,
            "timestamp": datetime.utcnow(),
            "status": "error",
            "error": str(e)
        }

@app.post("/compare_snapshots", response_model=CompareSnapshotsResponse)
async def compare_snapshots(request: CompareSnapshotsRequest):
    """
    Compare two snapshots.
    """
    try:
        # Check cache
        cache_key = f"snapshot_comparison:{request.base_snapshot_id}:{request.compare_snapshot_id}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"Using cached result for {cache_key}")
            return cached_result
        
        # Compare snapshots
        differences = codebase_service.compare_snapshots(
            base_snapshot_id=request.base_snapshot_id,
            compare_snapshot_id=request.compare_snapshot_id
        )
        
        result = {
            "base_snapshot_id": request.base_snapshot_id,
            "compare_snapshot_id": request.compare_snapshot_id,
            "differences": differences,
            "status": "success"
        }
        
        # Cache result
        cache_manager.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        return result
    except Exception as e:
        logger.error(f"Error comparing snapshots {request.base_snapshot_id} and {request.compare_snapshot_id}: {e}")
        return {
            "base_snapshot_id": request.base_snapshot_id,
            "compare_snapshot_id": request.compare_snapshot_id,
            "differences": {},
            "status": "error",
            "error": str(e)
        }

@app.post("/graphql")
async def graphql(request: GraphQLRequest):
    """
    Execute a GraphQL query.
    """
    try:
        result = execute_query(request.query, request.variables)
        return result
    except Exception as e:
        logger.error(f"Error executing GraphQL query: {e}")
        return {"errors": [str(e)]}

@app.post("/register_webhook", response_model=WebhookResponse)
async def register_webhook(request: WebhookRegistrationRequest):
    """
    Register a webhook.
    """
    try:
        # Get or create the repository
        repo_name = os.path.basename(request.repo_url.rstrip("/").replace(".git", ""))
        repository = codebase_service.create_repository(
            url=request.repo_url,
            name=repo_name
        )
        
        # Register the webhook
        webhook = webhook_service.register_webhook(
            repository_id=repository.id,
            url=request.url,
            events=request.events,
            secret=request.secret
        )
        
        return {
            "webhook_id": webhook.id,
            "repo_url": request.repo_url,
            "url": webhook.url,
            "events": webhook.events,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error registering webhook for repository {request.repo_url}: {e}")
        return {
            "webhook_id": "",
            "repo_url": request.repo_url,
            "url": request.url,
            "events": request.events,
            "status": "error",
            "error": str(e)
        }

@app.post("/set_preference", response_model=UserPreferenceResponse)
async def set_preference(request: UserPreferenceRequest):
    """
    Set a user preference.
    """
    try:
        user_preference_service.set_preference(
            user_id=request.user_id,
            preference_key=request.preference_key,
            preference_value=request.preference_value
        )
        
        return {
            "user_id": request.user_id,
            "preference_key": request.preference_key,
            "preference_value": request.preference_value,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error setting preference for user {request.user_id}: {e}")
        return {
            "user_id": request.user_id,
            "preference_key": request.preference_key,
            "preference_value": request.preference_value,
            "status": "error",
            "error": str(e)
        }

@app.get("/get_preference/{user_id}/{preference_key}", response_model=UserPreferenceResponse)
async def get_preference(user_id: str, preference_key: str, default_value: Optional[str] = None):
    """
    Get a user preference.
    """
    try:
        value = user_preference_service.get_preference(
            user_id=user_id,
            preference_key=preference_key,
            default_value=default_value
        )
        
        return {
            "user_id": user_id,
            "preference_key": preference_key,
            "preference_value": value,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting preference for user {user_id}: {e}")
        return {
            "user_id": user_id,
            "preference_key": preference_key,
            "preference_value": default_value,
            "status": "error",
            "error": str(e)
        }

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()

