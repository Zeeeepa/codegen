"""
CodeContextRetrievalServer: A FastAPI server for accessing codebase analysis and context functionality.
Provides endpoints for analysis, context management, and agent execution.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from pydantic import BaseModel

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.snapshot.context_snapshot import CodebaseContextSnapshot


class RepositoryRequest(BaseModel):
    """Request model for repository operations."""
    repo_full_name: str
    commit: Optional[str] = None
    language: str = "python"
    disable_file_parse: bool = False


class SnapshotRequest(BaseModel):
    """Request model for snapshot operations."""
    snapshot_id: str
    bucket_name: Optional[str] = None


class AgentRunRequest(BaseModel):
    """Request model for agent run operations."""
    repo_full_name: str
    commit: Optional[str] = None
    prompt: str
    model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


app = FastAPI(
    title="CodeContextRetrievalServer",
    description="API for codebase analysis and context retrieval",
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the CodeContextRetrievalServer"}


@app.post("/analyze")
async def analyze_repository(request: RepositoryRequest):
    """
    Analyze a repository and return the results.
    
    Args:
        request: The repository request
        
    Returns:
        The analysis results
    """
    try:
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=request.repo_full_name,
            commit=request.commit,
            language=request.language,
            disable_file_parse=request.disable_file_parse,
        )
        results = harness.analyze_codebase()
        return results
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/snapshot/create")
async def create_snapshot(request: RepositoryRequest):
    """
    Create a snapshot of a repository.
    
    Args:
        request: The repository request
        
    Returns:
        The snapshot ID
    """
    try:
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=request.repo_full_name,
            commit=request.commit,
            language=request.language,
            disable_file_parse=request.disable_file_parse,
        )
        snapshot = CodebaseContextSnapshot(harness)
        snapshot_id = snapshot.create_snapshot()
        return {"snapshot_id": snapshot_id}
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/snapshot/load")
async def load_snapshot(request: SnapshotRequest):
    """
    Load a snapshot.
    
    Args:
        request: The snapshot request
        
    Returns:
        The snapshot data
    """
    try:
        snapshot_data = CodebaseContextSnapshot.load_snapshot(
            snapshot_id=request.snapshot_id,
            bucket_name=request.bucket_name,
        )
        return snapshot_data
    except Exception as e:
        logger.error(f"Error loading snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot/list")
async def list_snapshots(repo_name: Optional[str] = None):
    """
    List snapshots.
    
    Args:
        repo_name: Optional repository name to filter by
        
    Returns:
        A list of snapshots
    """
    try:
        # Create a temporary harness just to get a snapshot object
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=repo_name or "temp/temp",
            disable_file_parse=True,
        )
        snapshot = CodebaseContextSnapshot(harness)
        snapshots = snapshot.list_snapshots(repo_name)
        return {"snapshots": snapshots}
    except Exception as e:
        logger.error(f"Error listing snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/run")
async def run_agent(request: AgentRunRequest):
    """
    Run an agent on a repository.
    
    Args:
        request: The agent run request
        
    Returns:
        The agent run results
    """
    try:
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=request.repo_full_name,
            commit=request.commit,
            metadata=request.metadata,
        )
        result = harness.run_agent(
            prompt=request.prompt,
            model=request.model,
        )
        return result
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the server.
    
    Args:
        host: The host to bind to
        port: The port to bind to
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

