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


# Request Models
class CodeValidationRequest(BaseModel):
    """Request model for code validation."""

    repo_url: str
    branch: Optional[str] = "main"
    categories: Optional[List[str]] = Field(default_factory=list)
    github_token: Optional[str] = None


class RepoComparisonRequest(BaseModel):
    """Request model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    base_branch: Optional[str] = "main"
    head_branch: Optional[str] = "main"
    github_token: Optional[str] = None


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    repo_url: str
    pr_number: int
    github_token: Optional[str] = None
    detailed: bool = True
    post_comment: bool = False


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
    error: Optional[str] = None


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    file_changes: Dict[str, str]
    function_changes: Dict[str, str]
    complexity_changes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    summary: str
    error: Optional[str] = None


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""

    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Model for error responses."""

    detail: str
    error_type: Optional[str] = None
    traceback: Optional[str] = None


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


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_type": exc.__class__.__name__,
            "traceback": traceback.format_exc(),
        },
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


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
            logger.info(f"Created snapshot with {len(snapshot.files)} files")

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
                    result = {
                        "score": 0.0,
                        "issues": [],
                        "recommendations": [f"Unknown category: {category}"],
                    }
                logger.info(f"Completed analysis for {category}")

                results.append(
                    ValidationResult(
                        category=category,
                        score=result.get("score", 0.0),
                        issues=result.get("issues", []),
                        recommendations=result.get("recommendations", []),
                    )
                )

            # Calculate overall score
            overall_score = sum(r.score for r in results) / len(results) if results else 0.0
            logger.info(f"Overall score: {overall_score:.2f}/10")

            # Generate summary
            summary = (
                f"Analysis of {request.repo_url} ({request.branch}) completed "
                f"with an overall score of {overall_score:.2f}/10."
            )

            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
                error=None,
            )

    except Exception as e:
        error_msg = f"Error validating code: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Return a response with error information instead of raising an exception
        return CodeValidationResponse(
            repo_url=request.repo_url,
            branch=request.branch,
            validation_results=[],
            overall_score=0.0,
            summary=f"Analysis failed: {str(e)}",
            error=error_msg,
        )


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
            logger.info(f"Created base snapshot with {len(base_snapshot.files)} files")

            logger.info(f"Creating head snapshot from {request.head_repo_url} ({request.head_branch})")
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.head_repo_url,
                branch=request.head_branch,
                github_token=request.github_token,
            )
            logger.info(f"Created head snapshot with {len(head_snapshot.files)} files")

            # Initialize diff analyzer
            diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)
            logger.info("Initialized diff analyzer")

            # Analyze differences
            logger.info("Analyzing file changes")
            file_changes = diff_analyzer.analyze_file_changes()
            logger.info(f"Found {len(file_changes)} file changes")
            
            logger.info("Analyzing function changes")
            function_changes = diff_analyzer.analyze_function_changes()
            logger.info(f"Found {len(function_changes)} function changes")
            
            logger.info("Analyzing complexity changes")
            complexity_changes = diff_analyzer.analyze_complexity_changes()
            logger.info(f"Found {len(complexity_changes)} complexity changes")

            # Assess risk
            logger.info("Assessing risk")
            risk_assessment = diff_analyzer.assess_risk()

            # Generate summary
            summary = diff_analyzer.format_summary_text()
            logger.info("Generated comparison summary")

            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                file_changes=file_changes,
                function_changes=function_changes,
                complexity_changes=complexity_changes,
                risk_assessment=risk_assessment,
                summary=summary,
                error=None,
            )

    except Exception as e:
        error_msg = f"Error comparing repositories: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Return a response with error information instead of raising an exception
        return RepoComparisonResponse(
            base_repo_url=request.base_repo_url,
            head_repo_url=request.head_repo_url,
            file_changes={},
            function_changes={},
            complexity_changes={},
            risk_assessment={},
            summary=f"Comparison failed: {str(e)}",
            error=error_msg,
        )


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

        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results=analysis_results,
            code_quality_score=code_quality_score,
            issues_found=issues_found,
            recommendations=recommendations,
            summary=summary,
            error=None,
        )

    except Exception as e:
        error_msg = f"Error analyzing pull request: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Return a response with error information instead of raising an exception
        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results={},
            code_quality_score=0.0,
            issues_found=[],
            recommendations=[],
            summary=f"Analysis failed: {str(e)}",
            error=error_msg,
        )


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    logger.info(f"Starting WSL2 server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
