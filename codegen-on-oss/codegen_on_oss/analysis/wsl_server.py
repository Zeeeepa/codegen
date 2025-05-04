"""
WSL2 Server Backend for Code Validation

This module provides a FastAPI server designed to run on WSL2 for code validation,
repository comparison, and PR analysis. It integrates with ctrlplane for deployment
orchestration and provides endpoints for various code analysis tasks.
"""

import logging
import os
import tempfile
import traceback
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Codegen WSL2 Server",
    description="WSL2 Server Backend for Code Validation, Repository Comparison, and PR Analysis",
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

# API key security
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Get API key from environment variable
API_KEY = os.getenv("CODEGEN_API_KEY", "")


# Custom error handling
class CodegenError(Exception):
    """Base exception for Codegen errors."""

    def __init__(self, message: str, error_code: str, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(CodegenError):
    """Exception for validation errors."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, error_code, status_code=400)


class RepositoryError(CodegenError):
    """Exception for repository errors."""

    def __init__(self, message: str, error_code: str = "REPOSITORY_ERROR"):
        super().__init__(message, error_code, status_code=500)


class AnalysisError(CodegenError):
    """Exception for analysis errors."""

    def __init__(self, message: str, error_code: str = "ANALYSIS_ERROR"):
        super().__init__(message, error_code, status_code=500)


# Error handler
@app.exception_handler(CodegenError)
async def codegen_exception_handler(request: Request, exc: CodegenError):
    """Handle Codegen errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.message,
            "details": str(exc),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc),
        },
    )


# Request Models
class CodeValidationRequest(BaseModel):
    """Request model for code validation."""

    repo_url: str
    branch: Optional[str] = "main"
    categories: Optional[List[str]] = Field(default_factory=list)
    github_token: Optional[str] = None
    timeout: Optional[int] = 300  # Timeout in seconds
    include_metrics: bool = False  # Whether to include detailed metrics


class RepoComparisonRequest(BaseModel):
    """Request model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    base_branch: Optional[str] = "main"
    head_branch: Optional[str] = "main"
    github_token: Optional[str] = None
    timeout: Optional[int] = 300  # Timeout in seconds
    diff_format: Optional[str] = "unified"  # Format for diffs (unified, side-by-side)
    include_metrics: bool = False  # Whether to include detailed metrics


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    repo_url: str
    pr_number: int
    github_token: Optional[str] = None
    detailed: bool = True
    post_comment: bool = False
    timeout: Optional[int] = 300  # Timeout in seconds
    include_metrics: bool = False  # Whether to include detailed metrics


# Response Models
class ValidationResult(BaseModel):
    """Model for validation results."""

    category: str
    score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    metrics: Optional[Dict[str, Any]] = None  # Detailed metrics


class CodeValidationResponse(BaseModel):
    """Response model for code validation."""

    repo_url: str
    branch: str
    validation_results: List[ValidationResult]
    overall_score: float
    summary: str
    execution_time: float  # Time taken for analysis in seconds
    metrics: Optional[Dict[str, Any]] = None  # Detailed metrics


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    file_changes: Dict[str, str]
    function_changes: Dict[str, str]
    complexity_changes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    summary: str
    execution_time: float  # Time taken for comparison in seconds
    metrics: Optional[Dict[str, Any]] = None  # Detailed metrics
    diff_details: Optional[Dict[str, Any]] = None  # Detailed diff information


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""

    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    execution_time: float  # Time taken for analysis in seconds
    metrics: Optional[Dict[str, Any]] = None  # Detailed metrics


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    uptime: float  # Server uptime in seconds
    memory_usage: Dict[str, float]  # Memory usage statistics
    cpu_usage: float  # CPU usage percentage


# Dependency for API key validation
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    """Validate API key."""
    if not API_KEY:
        # If no API key is set, allow all requests
        return True

    if api_key_header == API_KEY:
        return True

    raise HTTPException(
        status_code=401,
        detail="Invalid API Key",
    )


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Codegen WSL2 Server for Code Validation",
        "version": "1.0.0",
        "endpoints": [
            "/validate",
            "/compare",
            "/analyze-pr",
            "/health",
        ],
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns detailed information about the server's health and resource usage.
    """
    import time

    import psutil

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime=time.time() - process.create_time(),
        memory_usage={
            "rss": memory_info.rss / (1024 * 1024),  # RSS in MB
            "vms": memory_info.vms / (1024 * 1024),  # VMS in MB
        },
        cpu_usage=process.cpu_percent(),
    )


@app.post("/validate", response_model=CodeValidationResponse)
async def validate_code(
    request: CodeValidationRequest,
    background_tasks: BackgroundTasks,
    api_key: bool = Depends(get_api_key),
):
    """
    Validate code in a repository.

    This endpoint analyzes a repository and provides validation results
    for code quality, security, and other categories.
    """
    import time

    start_time = time.time()

    try:
        # Validate request
        if not request.repo_url:
            raise ValidationError("Repository URL is required")

        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize snapshot manager
            SnapshotManager(temp_dir)

            try:
                # Create snapshot from repository
                snapshot = CodebaseSnapshot.create_from_repo(
                    repo_url=request.repo_url,
                    branch=request.branch,
                    github_token=request.github_token,
                    timeout=request.timeout,
                )
            except Exception as e:
                logger.error(f"Error creating snapshot: {str(e)}")
                error_msg = f"Failed to create snapshot from repository: {str(e)}"
                raise RepositoryError(error_msg) from e

            # Initialize code integrity analyzer
            analyzer = CodeIntegrityAnalyzer(snapshot)

            # Perform analysis
            categories = request.categories or ["code_quality", "security", "maintainability"]
            results = []

            for category in categories:
                try:
                    if category == "code_quality":
                        result = analyzer.analyze_code_quality()
                    elif category == "security":
                        result = analyzer.analyze_security()
                    elif category == "maintainability":
                        result = analyzer.analyze_maintainability()
                    else:
                        result = {
                            "score": 0.0,
                            "issues": [],
                            "recommendations": [f"Unknown category: {category}"],
                        }

                    # Add metrics if requested
                    metrics = None
                    if request.include_metrics:
                        metrics = analyzer.get_detailed_metrics(category)

                    results.append(
                        ValidationResult(
                            category=category,
                            score=result.get("score", 0.0),
                            issues=result.get("issues", []),
                            recommendations=result.get("recommendations", []),
                            metrics=metrics,
                        )
                    )
                except Exception as e:
                    logger.error(f"Error analyzing category {category}: {str(e)}")
                    results.append(
                        ValidationResult(
                            category=category,
                            score=0.0,
                            issues=[{"title": "Analysis Error", "description": str(e)}],
                            recommendations=["Try again later or contact support"],
                            metrics=None,
                        )
                    )

            # Calculate overall score
            overall_score = sum(r.score for r in results) / len(results) if results else 0.0

            # Generate summary
            summary = (
                f"Analysis of {request.repo_url} ({request.branch}) completed "
                f"with an overall score of {overall_score:.2f}/10."
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Get overall metrics if requested
            metrics = None
            if request.include_metrics:
                metrics = analyzer.get_overall_metrics()

            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
                execution_time=execution_time,
                metrics=metrics,
            )

    except CodegenError:
        # Re-raise Codegen errors to be handled by the exception handler
        raise
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        logger.error(traceback.format_exc())
        raise AnalysisError(f"Error validating code: {str(e)}") from e


@app.post("/compare", response_model=RepoComparisonResponse)
async def compare_repositories(
    request: RepoComparisonRequest,
    background_tasks: BackgroundTasks,
    api_key: bool = Depends(get_api_key),
):
    """
    Compare two repositories or branches.

    This endpoint analyzes the differences between two repositories or branches
    and provides a detailed comparison report.
    """
    import time

    start_time = time.time()

    try:
        # Validate request
        if not request.base_repo_url or not request.head_repo_url:
            raise ValidationError("Base and head repository URLs are required")

        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize snapshot manager
            SnapshotManager(temp_dir)

            try:
                # Create snapshots from repositories
                base_snapshot = CodebaseSnapshot.create_from_repo(
                    repo_url=request.base_repo_url,
                    branch=request.base_branch,
                    github_token=request.github_token,
                    timeout=request.timeout,
                )

                head_snapshot = CodebaseSnapshot.create_from_repo(
                    repo_url=request.head_repo_url,
                    branch=request.head_branch,
                    github_token=request.github_token,
                    timeout=request.timeout,
                )
            except Exception as e:
                logger.error(f"Error creating snapshots: {str(e)}")
                error_msg = f"Failed to create snapshots from repositories: {str(e)}"
                raise RepositoryError(error_msg) from e

            # Initialize diff analyzer
            diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

            # Analyze differences
            file_changes = diff_analyzer.analyze_file_changes()
            function_changes = diff_analyzer.analyze_function_changes()
            complexity_changes = diff_analyzer.analyze_complexity_changes()

            # Assess risk
            risk_assessment = diff_analyzer.assess_risk()

            # Generate summary
            summary = diff_analyzer.format_summary_text()

            # Calculate execution time
            execution_time = time.time() - start_time

            # Get detailed metrics if requested
            metrics = None
            diff_details = None
            if request.include_metrics:
                metrics = diff_analyzer.get_detailed_metrics()

            # Get detailed diff information if requested
            if request.diff_format:
                diff_details = diff_analyzer.get_detailed_diff(format=request.diff_format)

            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                file_changes=file_changes,
                function_changes=function_changes,
                complexity_changes=complexity_changes,
                risk_assessment=risk_assessment,
                summary=summary,
                execution_time=execution_time,
                metrics=metrics,
                diff_details=diff_details,
            )

    except CodegenError:
        # Re-raise Codegen errors to be handled by the exception handler
        raise
    except Exception as e:
        logger.error(f"Error comparing repositories: {str(e)}")
        logger.error(traceback.format_exc())
        raise AnalysisError(f"Error comparing repositories: {str(e)}") from e


@app.post("/analyze-pr", response_model=PRAnalysisResponse)
async def analyze_pull_request(
    request: PRAnalysisRequest,
    background_tasks: BackgroundTasks,
    api_key: bool = Depends(get_api_key),
):
    """
    Analyze a pull request.

    This endpoint analyzes a pull request and provides a detailed report
    on code quality, issues, and recommendations.
    """
    import time

    start_time = time.time()

    try:
        # Validate request
        if not request.repo_url:
            raise ValidationError("Repository URL is required")
        if request.pr_number <= 0:
            raise ValidationError("Invalid PR number")

        # Initialize SWE harness agent
        agent = SWEHarnessAgent(github_token=request.github_token)

        # Analyze pull request
        try:
            analysis_results = agent.analyze_pr(
                repo=request.repo_url,
                pr_number=request.pr_number,
                detailed=request.detailed,
                timeout=request.timeout,
            )
        except Exception as e:
            logger.error(f"Error analyzing PR: {str(e)}")
            raise AnalysisError(f"Failed to analyze pull request: {str(e)}") from e

        # Post comment if requested
        if request.post_comment:
            try:
                agent.post_pr_comment(
                    repo=request.repo_url,
                    pr_number=request.pr_number,
                    comment=analysis_results["summary"],
                )
            except Exception as e:
                logger.error(f"Error posting PR comment: {str(e)}")
                # Continue even if comment posting fails

        # Extract relevant information
        code_quality_score = analysis_results.get("code_quality_score", 0.0)
        issues_found = analysis_results.get("issues", [])
        recommendations = analysis_results.get("recommendations", [])
        summary = analysis_results.get("summary", "")

        # Calculate execution time
        execution_time = time.time() - start_time

        # Get detailed metrics if requested
        metrics = None
        if request.include_metrics:
            metrics = agent.get_detailed_metrics(
                repo=request.repo_url,
                pr_number=request.pr_number,
            )

        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results=analysis_results,
            code_quality_score=code_quality_score,
            issues_found=issues_found,
            recommendations=recommendations,
            summary=summary,
            execution_time=execution_time,
            metrics=metrics,
        )

    except CodegenError:
        # Re-raise Codegen errors to be handled by the exception handler
        raise
    except Exception as e:
        logger.error(f"Error analyzing pull request: {str(e)}")
        logger.error(traceback.format_exc())
        raise AnalysisError(f"Error analyzing pull request: {str(e)}") from e


def run_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    run_server()
