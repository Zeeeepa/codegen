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
import traceback
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator

from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.swe_harness_agent import SWEHarnessAgent
from codegen_on_oss.errors import CodegenError
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

# Rate limiting settings
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "100"))  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_STORAGE = os.getenv("RATE_LIMIT_STORAGE", "memory")  # 'memory' or 'redis'
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# In-memory rate limit storage
request_counts = {}

# Initialize Redis client if using Redis for rate limiting
if RATE_LIMIT_STORAGE == "redis":
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL)
        logger.info(f"Using Redis for rate limiting: {REDIS_URL}")
    except ImportError:
        logger.warning("Redis package not installed. Falling back to in-memory rate limiting.")
        RATE_LIMIT_STORAGE = "memory"
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {str(e)}. Falling back to in-memory rate limiting.")
        RATE_LIMIT_STORAGE = "memory"


# Custom exception for rate limiting
class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Rate limiting functions
def check_rate_limit(client_ip: str) -> bool:
    """
    Check if a client has exceeded the rate limit.
    
    Args:
        client_ip: The client's IP address
        
    Returns:
        True if the client has not exceeded the rate limit, False otherwise
    """
    current_time = time.time()
    
    if RATE_LIMIT_STORAGE == "redis":
        # Use Redis for distributed rate limiting
        try:
            # Clean up old entries (not needed with Redis TTL)
            
            # Get current count
            count_key = f"rate_limit:{client_ip}:count"
            count = redis_client.get(count_key)
            
            if count is None:
                # First request from this client
                redis_client.set(count_key, 1, ex=RATE_LIMIT_WINDOW)
                return True
            
            count = int(count)
            if count >= RATE_LIMIT:
                return False
            
            # Increment count
            redis_client.incr(count_key)
            return True
        except Exception as e:
            logger.error(f"Redis rate limiting error: {str(e)}")
            # Fall back to in-memory rate limiting
            return check_rate_limit_memory(client_ip, current_time)
    else:
        # Use in-memory rate limiting
        return check_rate_limit_memory(client_ip, current_time)


def check_rate_limit_memory(client_ip: str, current_time: float) -> bool:
    """
    Check rate limit using in-memory storage.
    
    Args:
        client_ip: The client's IP address
        current_time: The current time
        
    Returns:
        True if the client has not exceeded the rate limit, False otherwise
    """
    # Clean up old entries
    for ip in list(request_counts.keys()):
        if current_time - request_counts[ip]["timestamp"] > RATE_LIMIT_WINDOW:
            del request_counts[ip]
    
    # Check rate limit
    if client_ip in request_counts:
        if request_counts[client_ip]["count"] >= RATE_LIMIT:
            return False
        request_counts[client_ip]["count"] += 1
    else:
        request_counts[client_ip] = {"count": 1, "timestamp": current_time}
    
    return True


# Middleware for rate limiting and error handling
@app.middleware("http")
async def middleware(request: Request, call_next):
    """Middleware for rate limiting and error handling."""
    # Rate limiting
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "error_type": "RateLimitExceeded",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "path": request.url.path,
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
            },
        )
    
    # Error handling
    try:
        response = await call_next(request)
        return response
    except RateLimitExceeded:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Rate limit exceeded",
                "error_type": "RateLimitExceeded",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "path": request.url.path,
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
            },
        )
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        logger.error(traceback.format_exc())
        
        error_type = type(e).__name__
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if isinstance(e, HTTPException):
            status_code = e.status_code
        elif isinstance(e, CodegenError):
            status_code = status.HTTP_400_BAD_REQUEST
        
        # Only include traceback in debug mode
        debug_mode = os.getenv("DEBUG", "").lower() in ("true", "1", "t", "yes")
        error_response = {
            "detail": str(e),
            "error_type": error_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "path": request.url.path,
            "status_code": status_code,
        }
        
        # Only add traceback in debug mode
        if debug_mode:
            error_response["traceback"] = traceback.format_exc().splitlines()
        
        return JSONResponse(
            status_code=status_code,
            content=error_response,
        )


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


# Request Models
class CodeValidationRequest(BaseModel):
    """Request model for code validation."""

    repo_url: str
    branch: Optional[str] = "main"
    categories: Optional[List[str]] = Field(default_factory=list)
    github_token: Optional[str] = None

    @validator("repo_url")
    def validate_repo_url(cls, v):
        """Validate repository URL."""
        if not v.startswith(("http://", "https://", "git@")):
            raise ValueError("Repository URL must start with http://, https://, or git@")
        return v


class RepoComparisonRequest(BaseModel):
    """Request model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    base_branch: Optional[str] = "main"
    head_branch: Optional[str] = "main"
    github_token: Optional[str] = None

    @validator("base_repo_url", "head_repo_url")
    def validate_repo_url(cls, v):
        """Validate repository URL."""
        if not v.startswith(("http://", "https://", "git@")):
            raise ValueError("Repository URL must start with http://, https://, or git@")
        return v


class PRAnalysisRequest(BaseModel):
    """Request model for PR analysis."""

    repo_url: str
    pr_number: int
    github_token: Optional[str] = None
    detailed: bool = True
    post_comment: bool = False

    @validator("repo_url")
    def validate_repo_url(cls, v):
        """Validate repository URL."""
        if not v.startswith(("http://", "https://", "git@")):
            raise ValueError("Repository URL must start with http://, https://, or git@")
        return v

    @validator("pr_number")
    def validate_pr_number(cls, v):
        """Validate PR number."""
        if v <= 0:
            raise ValueError("PR number must be positive")
        return v


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
    execution_time: float


class RepoComparisonResponse(BaseModel):
    """Response model for repository comparison."""

    base_repo_url: str
    head_repo_url: str
    file_changes: Dict[str, str]
    function_changes: Dict[str, str]
    complexity_changes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    summary: str
    execution_time: float


class PRAnalysisResponse(BaseModel):
    """Response model for PR analysis."""

    repo_url: str
    pr_number: int
    analysis_results: Dict[str, Any]
    code_quality_score: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    execution_time: float


class ErrorResponse(BaseModel):
    """Model for error responses."""

    detail: str
    error_type: str
    timestamp: str
    path: str
    status_code: int
    traceback: Optional[List[str]] = None


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
    # Check if temporary directory can be created
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            pass
        
        return {
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0.0",
            "rate_limit": {
                "limit": RATE_LIMIT,
                "window": RATE_LIMIT_WINDOW,
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
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

            # Create snapshot from repository
            logger.info(
                f"Creating snapshot from repository: {request.repo_url} "
                f"(branch: {request.branch})"
            )
            snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.repo_url,
                branch=request.branch,
                github_token=request.github_token,
            )

            # Initialize code integrity analyzer
            logger.info("Initializing code integrity analyzer")
            analyzer = CodeIntegrityAnalyzer(snapshot)

            # Perform analysis
            categories = request.categories or ["code_quality", "security", "maintainability"]
            results = []

            logger.info(f"Analyzing categories: {categories}")
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
            summary = (
                f"Analysis of {request.repo_url} ({request.branch}) completed "
                f"with an overall score of {overall_score:.2f}/10."
            )

            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"Analysis completed in {execution_time:.2f} seconds")

            return CodeValidationResponse(
                repo_url=request.repo_url,
                branch=request.branch,
                validation_results=results,
                overall_score=overall_score,
                summary=summary,
                execution_time=execution_time,
            )

    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        logger.error(traceback.format_exc())
        
        if isinstance(e, CodegenError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error validating code: {str(e)}",
            ) from e
        else:
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

            # Create snapshots from repositories
            logger.info(
                f"Creating base snapshot from repository: {request.base_repo_url} "
                f"(branch: {request.base_branch})"
            )
            base_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.base_repo_url,
                branch=request.base_branch,
                github_token=request.github_token,
            )

            logger.info(
                f"Creating head snapshot from repository: {request.head_repo_url} "
                f"(branch: {request.head_branch})"
            )
            head_snapshot = CodebaseSnapshot.create_from_repo(
                repo_url=request.head_repo_url,
                branch=request.head_branch,
                github_token=request.github_token,
            )

            # Initialize diff analyzer
            logger.info("Initializing diff analyzer")
            diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

            # Analyze differences
            logger.info("Analyzing file changes")
            file_changes = diff_analyzer.analyze_file_changes()
            
            logger.info("Analyzing function changes")
            function_changes = diff_analyzer.analyze_function_changes()
            
            logger.info("Analyzing complexity changes")
            complexity_changes = diff_analyzer.analyze_complexity_changes()

            # Assess risk
            logger.info("Assessing risk")
            risk_assessment = diff_analyzer.assess_risk()

            # Generate summary
            logger.info("Generating summary")
            summary = diff_analyzer.format_summary_text()

            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"Comparison completed in {execution_time:.2f} seconds")

            return RepoComparisonResponse(
                base_repo_url=request.base_repo_url,
                head_repo_url=request.head_repo_url,
                file_changes=file_changes,
                function_changes=function_changes,
                complexity_changes=complexity_changes,
                risk_assessment=risk_assessment,
                summary=summary,
                execution_time=execution_time,
            )

    except Exception as e:
        logger.error(f"Error comparing repositories: {str(e)}")
        logger.error(traceback.format_exc())
        
        if isinstance(e, CodegenError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error comparing repositories: {str(e)}",
            ) from e
        else:
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
        logger.info(
            f"Initializing SWE harness agent for PR analysis: "
            f"{request.repo_url}#{request.pr_number}"
        )
        agent = SWEHarnessAgent(github_token=request.github_token)

        # Analyze pull request
        logger.info(
            f"Analyzing PR: {request.repo_url}#{request.pr_number} "
            f"(detailed: {request.detailed})"
        )
        analysis_results = agent.analyze_pr(
            repo=request.repo_url,
            pr_number=request.pr_number,
            detailed=request.detailed,
        )

        # Post comment if requested
        if request.post_comment:
            logger.info(f"Posting comment to PR: {request.repo_url}#{request.pr_number}")
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
        logger.error(f"Error analyzing pull request: {str(e)}")
        logger.error(traceback.format_exc())
        
        if isinstance(e, CodegenError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error analyzing pull request: {str(e)}",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error analyzing pull request: {str(e)}",
            ) from e


@app.get("/metrics")
async def get_metrics(api_key: bool = Depends(get_api_key)):
    """Get server metrics."""
    return {
        "uptime": time.time() - app.state.start_time if hasattr(app.state, "start_time") else 0,
        "requests": {
            "total": sum(client["count"] for client in request_counts.values()),
            "clients": len(request_counts),
        },
        "rate_limit": {
            "limit": RATE_LIMIT,
            "window": RATE_LIMIT_WINDOW,
        },
    }


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI server."""
    # Set start time for uptime tracking
    app.state.start_time = time.time()
    
    # Run the server
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
