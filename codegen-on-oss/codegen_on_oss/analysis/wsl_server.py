"""
WSL2 Server Backend for Code Validation

This module provides a FastAPI server designed to run on WSL2 for code validation,
repository comparison, and PR analysis. It integrates with ctrlplane for deployment
orchestration and provides endpoints for various code analysis tasks.
"""

import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.codebase_comparison import CodebaseComparison
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.error_handler import setup_error_handler
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("wsl_server.log"),
    ],
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Codegen WSL2 Server",
    description="WSL2 Server Backend for Code Validation, Repository Comparison, and PR Analysis",
    version="1.1.0",
)

# Set up error handler
setup_error_handler(app)

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


# Request Models
class CodeValidationRequest(BaseModel):
    """Request model for code validation."""

    repo_url: str
    branch: Optional[str] = "main"
    categories: Optional[List[str]] = Field(default_factory=list)
    github_token: Optional[str] = None
    include_details: bool = True


class RepoComparisonRequest(BaseModel):
    """Request model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    base_branch: Optional[str] = "main"
    head_branch: Optional[str] = "main"
    github_token: Optional[str] = None
    include_file_diffs: bool = True
    include_function_details: bool = True
    include_class_details: bool = True


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    repo_url: str
    pr_number: int
    github_token: Optional[str] = None
    detailed: bool = True
    post_comment: bool = False
    include_diff: bool = True


# Response Models
class ValidationResult(BaseModel):
    """Model for validation results."""

    category: str
    score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]


class CodeValidationResponse(BaseModel):
    """Response model for code validation."""

    repo_url: str
    branch: str
    validation_results: List[ValidationResult]
    overall_score: float
    summary: str
    timestamp: float = Field(default_factory=time.time)
    execution_time: Optional[float] = None


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    base_branch: str
    head_branch: str
    file_changes: Dict[str, Any]
    function_changes: Dict[str, Any]
    class_changes: Dict[str, Any]
    impact_analysis: Dict[str, Any]
    summary: str
    timestamp: float = Field(default_factory=time.time)
    execution_time: Optional[float] = None


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""

    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    timestamp: float = Field(default_factory=time.time)
    execution_time: Optional[float] = None


# Dependency for API key validation
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    """Validate API key."""
    if not API_KEY:
        # If no API key is set, allow all requests
        return True

    if api_key_header == API_KEY:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else "unknown",
            "headers": dict(request.headers),
        },
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Response: {response.status_code} - Took {process_time:.4f}s",
        extra={
            "status_code": response.status_code,
            "process_time": process_time,
        },
    )
    
    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Codegen WSL2 Server for Code Validation",
        "version": "1.1.0",
        "endpoints": [
            "/validate",
            "/compare",
            "/analyze-pr",
            "/health",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.1.0",
        "endpoints": {
            "/validate": "operational",
            "/compare": "operational",
            "/analyze-pr": "operational",
        },
    }


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
    start_time = time.time()
    
    try:
        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize snapshot manager
            snapshot_manager = SnapshotManager(temp_dir)
            logger.info(f"Initialized snapshot manager in {temp_dir}")

            # Create snapshot from repository
            logger.info(f"Creating snapshot from {request.repo_url} ({request.branch})")
            snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.repo_url,
                branch=request.branch,
                github_token=request.github_token,
            )
            logger.info(f"Created snapshot with {len(snapshot.get_file_paths())} files")

            # Initialize code integrity analyzer
            analyzer = CodeIntegrityAnalyzer(snapshot)
            logger.info("Initialized code integrity analyzer")

            # Perform analysis
            categories = request.categories or ["code_quality", "security", "maintainability"]
            results = []
            logger.info(f"Analyzing categories: {categories}")

            for category in categories:
                logger.info(f"Analyzing category: {category}")
                if category == "code_quality":
                    result = analyzer.analyze_code_quality()
                elif category == "security":
                    result = analyzer.analyze_security()
                elif category == "maintainability":
                    result = analyzer.analyze_maintainability()
                else:
                    logger.warning(f"Unknown category: {category}")
                    result = {
                        "score": 0.0,
                        "issues": [],
                        "recommendations": [f"Unknown category: {category}"],
                    }

                results.append(
                    ValidationResult(
                        category=category,
                        score=result.get("score", 0.0),
                        issues=result.get("issues", []),
                        recommendations=result.get("recommendations", []),
                    )
                )
                logger.info(f"Completed analysis for {category} with score {result.get('score', 0.0)}")

            # Calculate overall score
            overall_score = sum(r.score for r in results) / len(results) if results else 0.0
            logger.info(f"Overall score: {overall_score:.2f}/10")

            # Generate summary
            summary = (
                f"Analysis of {request.repo_url} ({request.branch}) completed "
                f"with an overall score of {overall_score:.2f}/10."
            )

            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"Validation completed in {execution_time:.2f} seconds")

            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
                execution_time=execution_time,
            )

    except Exception as e:
        logger.error(f"Error validating code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating code: {str(e)}",
        ) from e


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
    start_time = time.time()
    
    try:
        # Create temporary directory for analysis
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize snapshot manager
            snapshot_manager = SnapshotManager(temp_dir)
            logger.info(f"Initialized snapshot manager in {temp_dir}")

            # Create snapshots from repositories
            logger.info(f"Creating base snapshot from {request.base_repo_url} ({request.base_branch})")
            base_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.base_repo_url,
                branch=request.base_branch,
                github_token=request.github_token,
            )
            logger.info(f"Created base snapshot with {len(base_snapshot.get_file_paths())} files")

            logger.info(f"Creating head snapshot from {request.head_repo_url} ({request.head_branch})")
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.head_repo_url,
                branch=request.head_branch,
                github_token=request.github_token,
            )
            logger.info(f"Created head snapshot with {len(head_snapshot.get_file_paths())} files")

            # Initialize codebase comparison
            comparison = CodebaseComparison(base_snapshot, head_snapshot)
            logger.info("Initialized codebase comparison")

            # Generate comparison report
            logger.info("Generating comparison report")
            report = comparison.generate_report()
            logger.info("Generated comparison report")

            # Extract relevant information
            file_changes = report["file_changes"]
            function_changes = report["function_changes"]
            class_changes = report["class_changes"]
            impact_analysis = report["impact_analysis"]
            summary = report["summary"]

            # Filter results based on request parameters
            if not request.include_file_diffs:
                # Remove diff content to reduce response size
                for file_path, file_info in file_changes.items():
                    if "diff" in file_info:
                        file_info.pop("diff")
                    if "content" in file_info:
                        file_info.pop("content")

            if not request.include_function_details:
                # Simplify function changes to just status
                function_changes = {
                    func_name: {"status": func_info["status"]}
                    for func_name, func_info in function_changes.items()
                }

            if not request.include_class_details:
                # Simplify class changes to just status
                class_changes = {
                    class_name: {"status": class_info["status"]}
                    for class_name, class_info in class_changes.items()
                }

            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"Comparison completed in {execution_time:.2f} seconds")

            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                base_branch=request.base_branch,
                head_branch=request.head_branch,
                file_changes=file_changes,
                function_changes=function_changes,
                class_changes=class_changes,
                impact_analysis=impact_analysis,
                summary=summary,
                execution_time=execution_time,
            )

    except Exception as e:
        logger.error(f"Error comparing repositories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing repositories: {str(e)}",
        ) from e


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
    start_time = time.time()
    
    try:
        # Initialize SWE harness agent
        logger.info(f"Initializing SWE harness agent for PR analysis")
        agent = SWEHarnessAgent(github_token=request.github_token)

        # Analyze pull request
        logger.info(f"Analyzing PR {request.repo_url}#{request.pr_number}")
        analysis_results = agent.analyze_pr(
            repo=request.repo_url,
            pr_number=request.pr_number,
            detailed=request.detailed,
            include_diff=request.include_diff,
        )
        logger.info(f"Completed PR analysis")

        # Post comment if requested
        if request.post_comment:
            logger.info(f"Posting comment to PR {request.repo_url}#{request.pr_number}")
            agent.post_pr_comment(
                repo=request.repo_url,
                pr_number=request.pr_number,
                comment=analysis_results["summary"],
            )
            logger.info(f"Posted comment to PR")

        # Extract relevant information
        code_quality_score = analysis_results.get("code_quality_score", 0.0)
        issues_found = analysis_results.get("issues", [])
        recommendations = analysis_results.get("recommendations", [])
        summary = analysis_results.get("summary", "")

        # Calculate execution time
        execution_time = time.time() - start_time
        logger.info(f"PR analysis completed in {execution_time:.2f} seconds")

        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results=analysis_results,
            code_quality_score=code_quality_score,
            issues_found=issues_found,
            recommendations=recommendations,
            summary=summary,
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error analyzing pull request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing pull request: {str(e)}",
        ) from e


def run_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
    """Run the FastAPI server."""
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        log_config=log_config,
    )


if __name__ == "__main__":
    run_server()
