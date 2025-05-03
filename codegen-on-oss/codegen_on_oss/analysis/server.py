"""
Server for analyzing code repositories and commits.

This module provides a FastAPI server that can analyze repositories and commits,
compare branches, and provide detailed reports on code quality and issues.
"""

import os
import tempfile
import subprocess
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import uvicorn

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer, CommitAnalysisResult, CommitIssue

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

# Define request models
class RepoAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")

class CommitAnalysisRequest(BaseModel):
    """Request model for commit analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    commit_hash: str = Field(..., description="Hash of the commit to analyze")

class BranchComparisonRequest(BaseModel):
    """Request model for branch comparison."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    base_branch: str = Field("main", description="Base branch name (default: main)")
    compare_branch: str = Field(..., description="Branch to compare against the base branch")

class PullRequestAnalysisRequest(BaseModel):
    """Request model for pull request analysis."""
    repo_url: str = Field(..., description="URL of the repository to analyze")
    pr_number: int = Field(..., description="Pull request number to analyze")

# Define response models
class AnalysisResponse(BaseModel):
    """Base response model for analysis results."""
    repo_url: str
    status: str = "success"
    error: Optional[str] = None

class CommitAnalysisResponse(AnalysisResponse):
    """Response model for commit analysis."""
    commit_hash: str
    is_properly_implemented: bool
    summary: str
    issues: List[Dict[str, Any]]
    metrics_diff: Dict[str, Any]
    files_added: List[str]
    files_modified: List[str]
    files_removed: List[str]

class BranchComparisonResponse(AnalysisResponse):
    """Response model for branch comparison."""
    base_branch: str
    compare_branch: str
    is_properly_implemented: bool
    summary: str
    issues: List[Dict[str, Any]]
    metrics_diff: Dict[str, Any]
    files_added: List[str]
    files_modified: List[str]
    files_removed: List[str]

class PullRequestAnalysisResponse(AnalysisResponse):
    """Response model for pull request analysis."""
    pr_number: int
    is_properly_implemented: bool
    summary: str
    issues: List[Dict[str, Any]]
    metrics_diff: Dict[str, Any]
    files_added: List[str]
    files_modified: List[str]
    files_removed: List[str]

# In-memory cache for analysis results
analysis_cache = {}

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
        "name": "Code Analysis Server",
        "description": "Server for analyzing code repositories and commits",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/analyze_repo", "method": "POST", "description": "Analyze a repository"},
            {"path": "/analyze_commit", "method": "POST", "description": "Analyze a commit in a repository"},
            {"path": "/compare_branches", "method": "POST", "description": "Compare two branches in a repository"},
            {"path": "/analyze_pr", "method": "POST", "description": "Analyze a pull request in a repository"},
        ]
    }

@app.post("/analyze_repo", response_model=AnalysisResponse)
async def analyze_repo(request: RepoAnalysisRequest):
    """
    Analyze a repository and return comprehensive metrics.
    """
    try:
        # Check cache
        cache_key = f"repo:{request.repo_url}"
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]
        
        logger.info(f"Analyzing repository: {request.repo_url}")
        codebase = Codebase.from_repo(request.repo_url)
        analyzer = CodeAnalyzer(codebase)
        
        result = {
            "repo_url": request.repo_url,
            "status": "success",
            "summary": analyzer.get_codebase_summary(),
            "complexity": analyzer.analyze_complexity(),
            "imports": analyzer.analyze_imports()
        }
        
        # Cache result
        analysis_cache[cache_key] = result
        
        return result
    except Exception as e:
        logger.error(f"Error analyzing repository {request.repo_url}: {e}")
        return {
            "repo_url": request.repo_url,
            "status": "error",
            "error": str(e)
        }

@app.post("/analyze_commit", response_model=CommitAnalysisResponse)
async def analyze_commit(request: CommitAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a commit in a repository.
    """
    temp_dirs = []
    try:
        # Check cache
        cache_key = f"commit:{request.repo_url}:{request.commit_hash}"
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]
        
        logger.info(f"Analyzing commit {request.commit_hash} in repository {request.repo_url}")
        
        result = CodeAnalyzer.analyze_commit_from_repo_and_commit(
            repo_url=request.repo_url,
            commit_hash=request.commit_hash
        )
        
        response = {
            "repo_url": request.repo_url,
            "commit_hash": request.commit_hash,
            "status": "success",
            "is_properly_implemented": result.is_properly_implemented,
            "summary": result.get_summary(),
            "issues": [issue.to_dict() for issue in result.issues],
            "metrics_diff": result.metrics_diff,
            "files_added": result.files_added,
            "files_modified": result.files_modified,
            "files_removed": result.files_removed
        }
        
        # Cache result
        analysis_cache[cache_key] = response
        
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return response
    except Exception as e:
        logger.error(f"Error analyzing commit {request.commit_hash} in repository {request.repo_url}: {e}")
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "commit_hash": request.commit_hash,
            "status": "error",
            "error": str(e)
        }

@app.post("/compare_branches", response_model=BranchComparisonResponse)
async def compare_branches(request: BranchComparisonRequest, background_tasks: BackgroundTasks):
    """
    Compare two branches in a repository.
    """
    temp_dirs = []
    try:
        # Check cache
        cache_key = f"branches:{request.repo_url}:{request.base_branch}:{request.compare_branch}"
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]
        
        logger.info(f"Comparing branches {request.base_branch} and {request.compare_branch} in repository {request.repo_url}")
        
        # Create temporary directories for both branches
        base_dir = tempfile.mkdtemp()
        compare_dir = tempfile.mkdtemp()
        temp_dirs.extend([base_dir, compare_dir])
        
        # Clone the repository for the base branch
        subprocess.run(
            ["git", "clone", "--branch", request.base_branch, request.repo_url, base_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Clone the repository for the compare branch
        subprocess.run(
            ["git", "clone", "--branch", request.compare_branch, request.repo_url, compare_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Create codebases from the directories
        base_codebase = Codebase.from_directory(base_dir)
        compare_codebase = Codebase.from_directory(compare_dir)
        
        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(
            original_codebase=base_codebase,
            commit_codebase=compare_codebase
        )
        
        # Analyze the differences
        result = analyzer.analyze_commit()
        
        response = {
            "repo_url": request.repo_url,
            "base_branch": request.base_branch,
            "compare_branch": request.compare_branch,
            "status": "success",
            "is_properly_implemented": result.is_properly_implemented,
            "summary": result.get_summary(),
            "issues": [issue.to_dict() for issue in result.issues],
            "metrics_diff": result.metrics_diff,
            "files_added": result.files_added,
            "files_modified": result.files_modified,
            "files_removed": result.files_removed
        }
        
        # Cache result
        analysis_cache[cache_key] = response
        
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return response
    except Exception as e:
        logger.error(f"Error comparing branches {request.base_branch} and {request.compare_branch} in repository {request.repo_url}: {e}")
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "base_branch": request.base_branch,
            "compare_branch": request.compare_branch,
            "status": "error",
            "error": str(e)
        }

@app.post("/analyze_pr", response_model=PullRequestAnalysisResponse)
async def analyze_pr(request: PullRequestAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze a pull request in a repository.
    """
    temp_dirs = []
    try:
        # Check cache
        cache_key = f"pr:{request.repo_url}:{request.pr_number}"
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]
        
        logger.info(f"Analyzing PR #{request.pr_number} in repository {request.repo_url}")
        
        # Create a temporary directory for the repository
        repo_dir = tempfile.mkdtemp()
        temp_dirs.append(repo_dir)
        
        # Clone the repository
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Get PR information using git commands
        # First, fetch the PR
        subprocess.run(
            ["git", "-C", repo_dir, "fetch", "origin", f"pull/{request.pr_number}/head:pr-{request.pr_number}"],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Get the base branch of the PR
        pr_info = subprocess.run(
            ["git", "-C", repo_dir, "show", f"pr-{request.pr_number}", "--format=%B", "-s"],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Try to extract the base branch from the PR description
        # Default to 'main' if not found
        base_branch = "main"
        for line in pr_info.stdout.splitlines():
            if line.startswith("base:") or line.startswith("Base:"):
                base_branch = line.split(":", 1)[1].strip()
                break
        
        # Create temporary directories for both branches
        base_dir = tempfile.mkdtemp()
        pr_dir = tempfile.mkdtemp()
        temp_dirs.extend([base_dir, pr_dir])
        
        # Clone the repository for the base branch
        subprocess.run(
            ["git", "clone", request.repo_url, base_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Checkout the base branch
        subprocess.run(
            ["git", "-C", base_dir, "checkout", base_branch],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Clone the repository for the PR branch
        subprocess.run(
            ["git", "clone", request.repo_url, pr_dir],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Fetch and checkout the PR
        subprocess.run(
            ["git", "-C", pr_dir, "fetch", "origin", f"pull/{request.pr_number}/head:pr-{request.pr_number}"],
            check=True,
            capture_output=True,
            text=True,
        )
        
        subprocess.run(
            ["git", "-C", pr_dir, "checkout", f"pr-{request.pr_number}"],
            check=True,
            capture_output=True,
            text=True,
        )
        
        # Create codebases from the directories
        base_codebase = Codebase.from_directory(base_dir)
        pr_codebase = Codebase.from_directory(pr_dir)
        
        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(
            original_codebase=base_codebase,
            commit_codebase=pr_codebase
        )
        
        # Analyze the differences
        result = analyzer.analyze_commit()
        
        response = {
            "repo_url": request.repo_url,
            "pr_number": request.pr_number,
            "status": "success",
            "is_properly_implemented": result.is_properly_implemented,
            "summary": result.get_summary(),
            "issues": [issue.to_dict() for issue in result.issues],
            "metrics_diff": result.metrics_diff,
            "files_added": result.files_added,
            "files_modified": result.files_modified,
            "files_removed": result.files_removed
        }
        
        # Cache result
        analysis_cache[cache_key] = response
        
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        
        return response
    except Exception as e:
        logger.error(f"Error analyzing PR #{request.pr_number} in repository {request.repo_url}: {e}")
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "pr_number": request.pr_number,
            "status": "error",
            "error": str(e)
        }

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
"""

