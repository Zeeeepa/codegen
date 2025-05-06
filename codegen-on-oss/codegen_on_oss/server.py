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
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer

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


class ProjectRegistrationRequest(BaseModel):
    """Request model for registering a project for analysis."""

    repo_url: str = Field(..., description="URL of the repository to register")
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    default_branch: str = Field("main", description="Default branch of the repository")
    webhook_url: Optional[str] = Field(
        None, description="Webhook URL to notify when analysis is complete"
    )
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")


class WebhookRegistrationRequest(BaseModel):
    """Request model for registering a webhook."""

    project_id: str = Field(..., description="ID of the project to register the webhook for")
    webhook_url: str = Field(..., description="URL to send webhook notifications to")
    events: List[str] = Field(
        ["pr", "commit", "branch"], description="Events to trigger the webhook"
    )
    secret: Optional[str] = Field(None, description="Secret to sign webhook payloads with")


class FunctionAnalysisRequest(BaseModel):
    """Request model for analyzing a specific function."""

    repo_url: str = Field(..., description="URL of the repository to analyze")
    function_name: str = Field(..., description="Fully qualified name of the function to analyze")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: default branch)")
    commit: Optional[str] = Field(None, description="Commit to analyze (default: latest commit)")


class FeatureAnalysisRequest(BaseModel):
    """Request model for analyzing a specific feature."""

    repo_url: str = Field(..., description="URL of the repository to analyze")
    feature_path: str = Field(..., description="Path to the feature (file or directory)")
    branch: Optional[str] = Field(None, description="Branch to analyze (default: default branch)")
    commit: Optional[str] = Field(None, description="Commit to analyze (default: latest commit)")


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


class FunctionAnalysisResponse(AnalysisResponse):
    """Response model for function analysis."""

    function_name: str
    complexity: int
    parameters: List[str]
    return_type: str
    line_count: int
    dependencies: List[str]
    callers: List[str]
    is_tested: bool
    test_coverage: Optional[float] = None
    issues: List[Dict[str, Any]]


class FeatureAnalysisResponse(AnalysisResponse):
    """Response model for feature analysis."""

    feature_path: str
    functions: List[Dict[str, Any]]
    classes: List[Dict[str, Any]]
    complexity: Dict[str, Any]
    dependencies: List[str]
    issues: List[Dict[str, Any]]


class ProjectResponse(BaseModel):
    """Response model for project information."""

    project_id: str
    name: str
    repo_url: str
    description: Optional[str] = None
    default_branch: str
    last_analyzed: Optional[datetime] = None
    webhook_url: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response model for webhook information."""

    webhook_id: str
    project_id: str
    webhook_url: str
    events: List[str]
    created_at: datetime
    last_triggered: Optional[datetime] = None


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
            {
                "path": "/analyze_repo",
                "method": "POST",
                "description": "Analyze a repository",
            },
            {
                "path": "/analyze_commit",
                "method": "POST",
                "description": "Analyze a commit in a repository",
            },
            {
                "path": "/compare_branches",
                "method": "POST",
                "description": "Compare two branches in a repository",
            },
            {
                "path": "/analyze_pr",
                "method": "POST",
                "description": "Analyze a pull request in a repository",
            },
            {
                "path": "/register_project",
                "method": "POST",
                "description": "Register a project for analysis",
            },
            {
                "path": "/register_webhook",
                "method": "POST",
                "description": "Register a webhook",
            },
            {
                "path": "/analyze_function",
                "method": "POST",
                "description": "Analyze a specific function",
            },
            {
                "path": "/analyze_feature",
                "method": "POST",
                "description": "Analyze a specific feature",
            },
        ],
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
            "imports": analyzer.analyze_imports(),
        }

        # Cache result
        analysis_cache[cache_key] = result

        return result
    except Exception as e:
        logger.error(f"Error analyzing repository {request.repo_url}: {e}")
        return {"repo_url": request.repo_url, "status": "error", "error": str(e)}


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

        # Create temporary directories for the repository
        base_dir = tempfile.mkdtemp()
        commit_dir = tempfile.mkdtemp()
        temp_dirs = [base_dir, commit_dir]

        # Clone the repository for the base
        subprocess.run(
            ["git", "clone", request.repo_url, base_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Get the parent commit
        parent_commit = subprocess.run(
            [
                "git",
                "-C",
                base_dir,
                "rev-parse",
                f"{request.commit_hash}^",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        # Checkout the parent commit
        subprocess.run(
            ["git", "-C", base_dir, "checkout", parent_commit],
            check=True,
            capture_output=True,
            text=True,
        )

        # Clone the repository for the commit
        subprocess.run(
            ["git", "clone", request.repo_url, commit_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout the commit
        subprocess.run(
            ["git", "-C", commit_dir, "checkout", request.commit_hash],
            check=True,
            capture_output=True,
            text=True,
        )

        # Create codebases from the directories
        base_codebase = Codebase.from_directory(base_dir)
        commit_codebase = Codebase.from_directory(commit_dir)

        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(original_codebase=base_codebase, commit_codebase=commit_codebase)

        # Analyze the commit
        result = analyzer.analyze_commit()

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
            "files_removed": result.files_removed,
        }

        # Cache result
        analysis_cache[cache_key] = response

        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)

        return response
    except Exception as e:
        logger.error(
            f"Error analyzing commit {request.commit_hash} in repository {request.repo_url}: {e}"
        )
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "commit_hash": request.commit_hash,
            "status": "error",
            "error": str(e),
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

        logger.info(
            f"Comparing branches {request.base_branch} and {request.compare_branch} in repository {request.repo_url}"
        )

        # Create temporary directories for the repository
        base_dir = tempfile.mkdtemp()
        compare_dir = tempfile.mkdtemp()
        temp_dirs = [base_dir, compare_dir]

        # Clone the repository for the base branch
        subprocess.run(
            ["git", "clone", request.repo_url, base_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout the base branch
        subprocess.run(
            ["git", "-C", base_dir, "checkout", request.base_branch],
            check=True,
            capture_output=True,
            text=True,
        )

        # Clone the repository for the compare branch
        subprocess.run(
            ["git", "clone", request.repo_url, compare_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout the compare branch
        subprocess.run(
            ["git", "-C", compare_dir, "checkout", request.compare_branch],
            check=True,
            capture_output=True,
            text=True,
        )

        # Create codebases from the directories
        base_codebase = Codebase.from_directory(base_dir)
        compare_codebase = Codebase.from_directory(compare_dir)

        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(original_codebase=base_codebase, commit_codebase=compare_codebase)

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
            "files_removed": result.files_removed,
        }

        # Cache result
        analysis_cache[cache_key] = response

        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)

        return response
    except Exception as e:
        logger.error(
            f"Error comparing branches {request.base_branch} and {request.compare_branch} in repository {request.repo_url}: {e}"
        )
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "base_branch": request.base_branch,
            "compare_branch": request.compare_branch,
            "status": "error",
            "error": str(e),
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

        # Create temporary directories for the repository
        base_dir = tempfile.mkdtemp()
        pr_dir = tempfile.mkdtemp()
        temp_dirs = [base_dir, pr_dir]

        # Clone the repository for the base
        subprocess.run(
            ["git", "clone", request.repo_url, base_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Get the base branch for the PR
        base_branch = "main"  # Default to main if we can't determine the base branch

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
            [
                "git",
                "-C",
                pr_dir,
                "fetch",
                "origin",
                f"pull/{request.pr_number}/head:pr-{request.pr_number}",
            ],
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
        analyzer = CommitAnalyzer(original_codebase=base_codebase, commit_codebase=pr_codebase)

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
            "files_removed": result.files_removed,
        }

        # Cache result
        analysis_cache[cache_key] = response

        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)

        return response
    except Exception as e:
        logger.error(
            f"Error analyzing PR #{request.pr_number} in repository {request.repo_url}: {e}"
        )
        # Schedule cleanup of temporary directories
        background_tasks.add_task(cleanup_temp_dirs, temp_dirs)
        return {
            "repo_url": request.repo_url,
            "pr_number": request.pr_number,
            "status": "error",
            "error": str(e),
        }


@app.post("/register_project", response_model=ProjectResponse)
async def register_project(request: ProjectRegistrationRequest):
    """
    Register a project for analysis.
    """
    try:
        logger.info(f"Registering project {request.name} for analysis")

        # Create a temporary directory for the repository
        repo_dir = tempfile.mkdtemp()

        # Clone the repository
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Create a Codebase instance
        codebase = Codebase.from_directory(repo_dir)

        # Create a SnapshotManager instance
        snapshot_manager = SnapshotManager(codebase)

        # Create a SWEHarnessAgent instance
        swe_harness_agent = SWEHarnessAgent(codebase)

        # Analyze the codebase
        snapshot_manager.analyze()
        swe_harness_agent.analyze()

        # Create a ProjectResponse
        project_response = ProjectResponse(
            project_id="1",
            name=request.name,
            repo_url=request.repo_url,
            description=request.description,
            default_branch=request.default_branch,
            last_analyzed=datetime.now(),
            webhook_url=request.webhook_url,
        )

        return project_response
    except Exception as e:
        logger.error(f"Error registering project {request.name} for analysis: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/register_webhook", response_model=WebhookResponse)
async def register_webhook(request: WebhookRegistrationRequest):
    """
    Register a webhook.
    """
    try:
        logger.info(f"Registering webhook for project {request.project_id}")

        # Create a WebhookResponse
        webhook_response = WebhookResponse(
            webhook_id="1",
            project_id=request.project_id,
            webhook_url=request.webhook_url,
            events=request.events,
            created_at=datetime.now(),
        )

        return webhook_response
    except Exception as e:
        logger.error(f"Error registering webhook for project {request.project_id}: {e}")
        return {"status": "error", "error": str(e)}


@app.post("/analyze_function", response_model=FunctionAnalysisResponse)
async def analyze_function(request: FunctionAnalysisRequest):
    """
    Analyze a specific function.
    """
    try:
        # Check cache
        cache_key = (
            f"function:{request.repo_url}:{request.function_name}:{request.branch}:{request.commit}"
        )
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]

        logger.info(f"Analyzing function {request.function_name} in repository {request.repo_url}")

        # Create a temporary directory for the repository
        repo_dir = tempfile.mkdtemp()

        # Clone the repository
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout the branch if specified
        if request.branch:
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.branch],
                check=True,
                capture_output=True,
                text=True,
            )

        # Checkout the commit if specified
        if request.commit:
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.commit],
                check=True,
                capture_output=True,
                text=True,
            )

        # Create a Codebase instance
        codebase = Codebase.from_directory(repo_dir)

        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(original_codebase=codebase, commit_codebase=codebase)

        # Analyze the function
        result = analyzer.analyze_function(request.function_name)

        response = {
            "function_name": request.function_name,
            "complexity": result.complexity,
            "parameters": result.parameters,
            "return_type": result.return_type,
            "line_count": result.line_count,
            "dependencies": result.dependencies,
            "callers": result.callers,
            "is_tested": result.is_tested,
            "test_coverage": result.test_coverage,
            "issues": [issue.to_dict() for issue in result.issues],
        }

        # Cache result
        analysis_cache[cache_key] = response

        return response
    except Exception as e:
        logger.error(
            f"Error analyzing function {request.function_name} in repository {request.repo_url}: {e}"
        )
        return {"status": "error", "error": str(e)}


@app.post("/analyze_feature", response_model=FeatureAnalysisResponse)
async def analyze_feature(request: FeatureAnalysisRequest):
    """
    Analyze a specific feature.
    """
    try:
        # Check cache
        cache_key = (
            f"feature:{request.repo_url}:{request.feature_path}:{request.branch}:{request.commit}"
        )
        if cache_key in analysis_cache:
            logger.info(f"Using cached result for {cache_key}")
            return analysis_cache[cache_key]

        logger.info(f"Analyzing feature {request.feature_path} in repository {request.repo_url}")

        # Create a temporary directory for the repository
        repo_dir = tempfile.mkdtemp()

        # Clone the repository
        subprocess.run(
            ["git", "clone", request.repo_url, repo_dir],
            check=True,
            capture_output=True,
            text=True,
        )

        # Checkout the branch if specified
        if request.branch:
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.branch],
                check=True,
                capture_output=True,
                text=True,
            )

        # Checkout the commit if specified
        if request.commit:
            subprocess.run(
                ["git", "-C", repo_dir, "checkout", request.commit],
                check=True,
                capture_output=True,
                text=True,
            )

        # Create a Codebase instance
        codebase = Codebase.from_directory(repo_dir)

        # Create a CommitAnalyzer instance
        analyzer = CommitAnalyzer(original_codebase=codebase, commit_codebase=codebase)

        # Analyze the feature
        result = analyzer.analyze_feature(request.feature_path)

        response = {
            "feature_path": request.feature_path,
            "functions": result.functions,
            "classes": result.classes,
            "complexity": result.complexity,
            "dependencies": result.dependencies,
            "issues": [issue.to_dict() for issue in result.issues],
        }

        # Cache result
        analysis_cache[cache_key] = response

        return response
    except Exception as e:
        logger.error(
            f"Error analyzing feature {request.feature_path} in repository {request.repo_url}: {e}"
        )
        return {"status": "error", "error": str(e)}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
