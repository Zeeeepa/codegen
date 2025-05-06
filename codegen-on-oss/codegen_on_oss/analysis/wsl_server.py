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
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.code_integrity import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.commit_analysis import DiffAnalyzer
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


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the application."""
    error_id = str(uuid.uuid4())  # Generate unique error ID
    logger.error(f"Error ID {error_id}: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "error_id": error_id,
            "message": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An unexpected error occurred",
        },
    )


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
    detailed_analysis: bool = False  # New field for detailed analysis


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    repo_url: str
    pr_number: int
    github_token: Optional[str] = None
    detailed: bool = True
    post_comment: bool = False
    include_file_content: bool = False  # New field to include file content in the response


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
    error: Optional[str] = None  # New field for error messages


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    file_changes: Dict[str, str]
    function_changes: Dict[str, str]
    complexity_changes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    summary: str
    detailed_analysis: Optional[Dict[str, Any]] = None  # New field for detailed analysis
    error: Optional[str] = None  # New field for error messages


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""

    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    file_content: Optional[Dict[str, str]] = None  # New field for file content
    error: Optional[str] = None  # New field for error messages


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
            logger.info(f"Creating snapshot from repository: {request.repo_url} (branch: {request.branch})")
            snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.repo_url,
                branch=request.branch,
                github_token=request.github_token,
            )
            logger.info(f"Snapshot created with {len(snapshot.files)} files")

            # Initialize code integrity analyzer
            logger.info("Initializing code integrity analyzer")
            analyzer = CodeIntegrityAnalyzer(snapshot)

            # Perform analysis
            categories = request.categories or ["code_quality", "security", "maintainability"]
            logger.info(f"Analyzing categories: {categories}")
            results = []

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
                logger.info(f"Category {category} analyzed with score: {result.get('score', 0.0)}")

            # Calculate overall score
            overall_score = sum(r.score for r in results) / len(results) if results else 0.0
            logger.info(f"Overall score: {overall_score:.2f}/10")

            # Generate summary
            summary = (
                f"Analysis of {request.repo_url} ({request.branch}) completed "
                f"with an overall score of {overall_score:.2f}/10."
            )
            logger.info(f"Analysis summary: {summary}")

            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
            )

    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a response with error information
        return CodeValidationResponse(
            repo_url=request.repo_url,
            branch=request.branch,
            validation_results=[],
            overall_score=0.0,
            summary=f"Error validating code: {str(e)}",
            error=str(e),
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
            logger.info(f"Creating base snapshot from repository: {request.base_repo_url} (branch: {request.base_branch})")
            base_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.base_repo_url,
                branch=request.base_branch,
                github_token=request.github_token,
            )
            logger.info(f"Base snapshot created with {len(base_snapshot.files)} files")

            logger.info(f"Creating head snapshot from repository: {request.head_repo_url} (branch: {request.head_branch})")
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.head_repo_url,
                branch=request.head_branch,
                github_token=request.github_token,
            )
            logger.info(f"Head snapshot created with {len(head_snapshot.files)} files")

            # Initialize diff analyzer
            logger.info("Initializing diff analyzer")
            diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

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
            logger.info(f"Risk assessment completed: {risk_assessment}")

            # Generate summary
            logger.info("Generating summary")
            summary = diff_analyzer.format_summary_text()
            logger.info(f"Summary generated: {summary}")

            # Perform detailed analysis if requested
            detailed_analysis = None
            if request.detailed_analysis:
                logger.info("Performing detailed analysis")
                detailed_analysis = diff_analyzer.perform_detailed_analysis()
                logger.info("Detailed analysis completed")

            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                file_changes=file_changes,
                function_changes=function_changes,
                complexity_changes=complexity_changes,
                risk_assessment=risk_assessment,
                summary=summary,
                detailed_analysis=detailed_analysis,
            )

    except Exception as e:
        logger.error(f"Error comparing repositories: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a response with error information
        return RepoComparisonResponse(
            base_repo_url=request.base_repo_url,
            head_repo_url=request.head_repo_url,
            file_changes={},
            function_changes={},
            complexity_changes={},
            risk_assessment={},
            summary=f"Error comparing repositories: {str(e)}",
            error=str(e),
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
        logger.info(f"Initializing SWE harness agent for PR analysis: {request.repo_url}#{request.pr_number}")
        agent = SWEHarnessAgent(github_token=request.github_token)

        # Analyze pull request
        logger.info(f"Analyzing pull request: {request.repo_url}#{request.pr_number} (detailed: {request.detailed})")
        analysis_results = agent.analyze_pr(
            repo=request.repo_url,
            pr_number=request.pr_number,
            detailed=request.detailed,
        )
        logger.info(f"PR analysis completed for {request.repo_url}#{request.pr_number}")

        # Post comment if requested
        if request.post_comment:
            logger.info(f"Posting comment to PR: {request.repo_url}#{request.pr_number}")
            agent.post_pr_comment(
                repo=request.repo_url,
                pr_number=request.pr_number,
                comment=analysis_results["summary"],
            )
            logger.info(f"Comment posted to PR: {request.repo_url}#{request.pr_number}")

        # Extract relevant information
        code_quality_score = analysis_results.get("code_quality_score", 0.0)
        issues_found = analysis_results.get("issues", [])
        recommendations = analysis_results.get("recommendations", [])
        summary = analysis_results.get("summary", "")
        
        # Get file content if requested
        file_content = None
        if request.include_file_content:
            logger.info(f"Retrieving file content for PR: {request.repo_url}#{request.pr_number}")
            file_content = agent.get_pr_file_content(
                repo=request.repo_url,
                pr_number=request.pr_number,
            )
            logger.info(f"Retrieved content for {len(file_content) if file_content else 0} files")

        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results=analysis_results,
            code_quality_score=code_quality_score,
            issues_found=issues_found,
            recommendations=recommendations,
            summary=summary,
            file_content=file_content,
        )

    except Exception as e:
        logger.error(f"Error analyzing pull request: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Return a response with error information
        return PRAnalysisResponse(
            repo_url=request.repo_url,
            pr_number=request.pr_number,
            analysis_results={},
            code_quality_score=0.0,
            issues_found=[],
            recommendations=[],
            summary=f"Error analyzing pull request: {str(e)}",
            error=str(e),
        )


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    logger.info(f"Starting WSL2 server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
