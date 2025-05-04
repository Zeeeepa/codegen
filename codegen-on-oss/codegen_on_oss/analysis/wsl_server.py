"""
WSL2 Server Backend for Code Validation

This module provides a FastAPI server designed to run on WSL2 for code validation,
repository comparison, and PR analysis. It integrates with ctrlplane for deployment
orchestration and provides endpoints for various code analysis tasks.
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator

from codegen import Codebase
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


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""
    base_repo_url: str
    head_repo_url: str
    file_changes: Dict[str, str]
    function_changes: Dict[str, str]
    complexity_changes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    summary: str


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""
    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str


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
            
            # Create snapshot from repository
            snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.repo_url,
                branch=request.branch,
                github_token=request.github_token,
            )
            
            # Initialize code integrity analyzer
            analyzer = CodeIntegrityAnalyzer(snapshot)
            
            # Perform analysis
            categories = request.categories or ["code_quality", "security", "maintainability"]
            results = []
            
            for category in categories:
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
            
            # Generate summary
            summary = f"Analysis of {request.repo_url} ({request.branch}) completed with an overall score of {overall_score:.2f}/10."
            
            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
            )
    
    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating code: {str(e)}",
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
            
            # Create snapshots from repositories
            base_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.base_repo_url,
                branch=request.base_branch,
                github_token=request.github_token,
            )
            
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.head_repo_url,
                branch=request.head_branch,
                github_token=request.github_token,
            )
            
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
            
            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                file_changes=file_changes,
                function_changes=function_changes,
                complexity_changes=complexity_changes,
                risk_assessment=risk_assessment,
                summary=summary,
            )
    
    except Exception as e:
        logger.error(f"Error comparing repositories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing repositories: {str(e)}",
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
        agent = SWEHarnessAgent(github_token=request.github_token)
        
        # Analyze pull request
        analysis_results = agent.analyze_pr(
            repo=request.repo_url,
            pr_number=request.pr_number,
            detailed=request.detailed,
        )
        
        # Post comment if requested
        if request.post_comment:
            agent.post_pr_comment(
                repo=request.repo_url,
                pr_number=request.pr_number,
                comment=analysis_results["summary"],
            )
        
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
        )
    
    except Exception as e:
        logger.error(f"Error analyzing pull request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing pull request: {str(e)}",
        )


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

