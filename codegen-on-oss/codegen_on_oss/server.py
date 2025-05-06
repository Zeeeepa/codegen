"""
Server for analyzing code repositories and commits.

This module provides a FastAPI server that can analyze repositories and commits,
compare branches, and provide detailed reports on code quality and issues.
It serves as a backend analysis server for PR validation and codebase analysis.
"""

import logging
import os
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from codegen import Codebase
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.analysis import (
    analyze_codebase,
    analyze_commit,
    analyze_pr,
    compare_branches,
)
from codegen_on_oss.analysis.code_integrity import validate_code_integrity
from codegen_on_oss.analysis.webhook_handler import process_github_webhook

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Code Analysis Server",
    description="Server for analyzing code repositories and commits",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class RepositoryInfo(BaseModel):
    """Repository information."""

    url: str = Field(..., description="Repository URL")
    branch: Optional[str] = Field(None, description="Branch name")
    commit: Optional[str] = Field(None, description="Commit SHA")
    access_token: Optional[str] = Field(None, description="GitHub access token")


class BranchComparisonRequest(BaseModel):
    """Branch comparison request."""

    repository_url: str = Field(..., description="Repository URL")
    base_branch: str = Field(..., description="Base branch name")
    head_branch: str = Field(..., description="Head branch name")
    access_token: Optional[str] = Field(None, description="GitHub access token")


class PRAnalysisRequest(BaseModel):
    """PR analysis request."""

    repository_url: str = Field(..., description="Repository URL")
    pr_number: int = Field(..., description="PR number")
    access_token: Optional[str] = Field(None, description="GitHub access token")


class WebhookPayload(BaseModel):
    """GitHub webhook payload."""

    action: Optional[str] = Field(None, description="Webhook action")
    repository: Optional[Dict[str, Any]] = Field(None, description="Repository information")
    pull_request: Optional[Dict[str, Any]] = Field(None, description="Pull request information")
    # Add other fields as needed


# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Code Analysis Server"}


@app.post("/analyze/repository", status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    repository_info: RepositoryInfo, background_tasks: BackgroundTasks
):
    """
    Analyze a repository.

    Args:
        repository_info: Repository information
        background_tasks: Background tasks

    Returns:
        Task ID
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(
        _analyze_repository_task,
        task_id,
        repository_info.url,
        repository_info.branch,
        repository_info.commit,
        repository_info.access_token,
    )
    return {"task_id": task_id, "status": "processing"}


async def _analyze_repository_task(
    task_id: str,
    repository_url: str,
    branch: Optional[str],
    commit: Optional[str],
    access_token: Optional[str],
):
    """
    Analyze a repository task.

    Args:
        task_id: Task ID
        repository_url: Repository URL
        branch: Branch name
        commit: Commit SHA
        access_token: GitHub access token
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            clone_cmd = ["git", "clone", repository_url, temp_dir]
            if access_token:
                auth_url = repository_url.replace(
                    "https://", f"https://x-access-token:{access_token}@"
                )
                clone_cmd = ["git", "clone", auth_url, temp_dir]
            
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Checkout branch or commit
            if branch:
                subprocess.run(
                    ["git", "checkout", branch],
                    cwd=temp_dir,
                    check=True,
                    capture_output=True,
                )
            elif commit:
                subprocess.run(
                    ["git", "checkout", commit],
                    cwd=temp_dir,
                    check=True,
                    capture_output=True,
                )
            
            # Analyze codebase
            codebase = Codebase(temp_dir)
            analysis_results = analyze_codebase(codebase)
            
            # Store results (implement storage mechanism)
            logger.info(f"Analysis completed for task {task_id}")
            
            # Validate code integrity
            integrity_results = validate_code_integrity(codebase)
            
            # Combine results
            results = {
                "analysis": analysis_results,
                "integrity": integrity_results,
            }
            
            # Store results (implement storage mechanism)
            logger.info(f"Task {task_id} completed successfully")
            
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")


@app.post("/analyze/commit", status_code=status.HTTP_202_ACCEPTED)
async def analyze_commit_endpoint(
    repository_info: RepositoryInfo, background_tasks: BackgroundTasks
):
    """
    Analyze a commit.

    Args:
        repository_info: Repository information
        background_tasks: Background tasks

    Returns:
        Task ID
    """
    if not repository_info.commit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commit SHA is required",
        )
    
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(
        _analyze_commit_task,
        task_id,
        repository_info.url,
        repository_info.commit,
        repository_info.access_token,
    )
    return {"task_id": task_id, "status": "processing"}


async def _analyze_commit_task(
    task_id: str,
    repository_url: str,
    commit: str,
    access_token: Optional[str],
):
    """
    Analyze a commit task.

    Args:
        task_id: Task ID
        repository_url: Repository URL
        commit: Commit SHA
        access_token: GitHub access token
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            clone_cmd = ["git", "clone", repository_url, temp_dir]
            if access_token:
                auth_url = repository_url.replace(
                    "https://", f"https://x-access-token:{access_token}@"
                )
                clone_cmd = ["git", "clone", auth_url, temp_dir]
            
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Checkout commit
            subprocess.run(
                ["git", "checkout", commit],
                cwd=temp_dir,
                check=True,
                capture_output=True,
            )
            
            # Analyze commit
            codebase = Codebase(temp_dir)
            analysis_results = analyze_commit(codebase, commit)
            
            # Store results (implement storage mechanism)
            logger.info(f"Task {task_id} completed successfully")
            
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")


@app.post("/compare/branches", status_code=status.HTTP_202_ACCEPTED)
async def compare_branches_endpoint(
    comparison_request: BranchComparisonRequest, background_tasks: BackgroundTasks
):
    """
    Compare branches.

    Args:
        comparison_request: Branch comparison request
        background_tasks: Background tasks

    Returns:
        Task ID
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(
        _compare_branches_task,
        task_id,
        comparison_request.repository_url,
        comparison_request.base_branch,
        comparison_request.head_branch,
        comparison_request.access_token,
    )
    return {"task_id": task_id, "status": "processing"}


async def _compare_branches_task(
    task_id: str,
    repository_url: str,
    base_branch: str,
    head_branch: str,
    access_token: Optional[str],
):
    """
    Compare branches task.

    Args:
        task_id: Task ID
        repository_url: Repository URL
        base_branch: Base branch name
        head_branch: Head branch name
        access_token: GitHub access token
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            clone_cmd = ["git", "clone", repository_url, temp_dir]
            if access_token:
                auth_url = repository_url.replace(
                    "https://", f"https://x-access-token:{access_token}@"
                )
                clone_cmd = ["git", "clone", auth_url, temp_dir]
            
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Compare branches
            codebase = Codebase(temp_dir)
            comparison_results = compare_branches(codebase, base_branch, head_branch)
            
            # Store results (implement storage mechanism)
            logger.info(f"Task {task_id} completed successfully")
            
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")


@app.post("/analyze/pr", status_code=status.HTTP_202_ACCEPTED)
async def analyze_pr_endpoint(
    pr_request: PRAnalysisRequest, background_tasks: BackgroundTasks
):
    """
    Analyze a PR.

    Args:
        pr_request: PR analysis request
        background_tasks: Background tasks

    Returns:
        Task ID
    """
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks.add_task(
        _analyze_pr_task,
        task_id,
        pr_request.repository_url,
        pr_request.pr_number,
        pr_request.access_token,
    )
    return {"task_id": task_id, "status": "processing"}


async def _analyze_pr_task(
    task_id: str,
    repository_url: str,
    pr_number: int,
    access_token: Optional[str],
):
    """
    Analyze a PR task.

    Args:
        task_id: Task ID
        repository_url: Repository URL
        pr_number: PR number
        access_token: GitHub access token
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone repository
            clone_cmd = ["git", "clone", repository_url, temp_dir]
            if access_token:
                auth_url = repository_url.replace(
                    "https://", f"https://x-access-token:{access_token}@"
                )
                clone_cmd = ["git", "clone", auth_url, temp_dir]
            
            subprocess.run(clone_cmd, check=True, capture_output=True)
            
            # Analyze PR
            codebase = Codebase(temp_dir)
            analysis_results = analyze_pr(codebase, pr_number, access_token)
            
            # Store results (implement storage mechanism)
            logger.info(f"Task {task_id} completed successfully")
            
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")


@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    GitHub webhook endpoint.

    Args:
        request: Request
        background_tasks: Background tasks

    Returns:
        Acknowledgement
    """
    # Verify webhook signature (implement signature verification)
    
    # Parse payload
    payload = await request.json()
    
    # Process webhook
    background_tasks.add_task(process_github_webhook, payload)
    
    return {"status": "processing"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.

    Args:
        request: Request
        exc: Exception

    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """
    Run the server.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

