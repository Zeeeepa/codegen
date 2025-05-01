"""
CodeContextRetrievalServer - FastAPI server for accessing codebase analysis functionality.

This module implements a FastAPI server that provides endpoints for analysis,
context management, and agent execution.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from codegen import Codebase
from codegen.agents.code_agent import CodeAgent
from codegen.configs.models.codebase import CodebaseConfig
from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.snapshot.context_snapshot import CodebaseContextSnapshot


# Define API models
class RepositoryInfo(BaseModel):
    """Repository information for analysis requests."""
    repo_full_name: str
    commit: Optional[str] = None
    language: str = "python"
    disable_file_parse: bool = False


class AnalysisRequest(BaseModel):
    """Request model for codebase analysis."""
    repository: RepositoryInfo
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None


class SnapshotRequest(BaseModel):
    """Request model for creating a snapshot."""
    snapshot_id: Optional[str] = None
    repository: RepositoryInfo
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None


class AgentExecutionRequest(BaseModel):
    """Request model for executing an agent with context."""
    snapshot_id: Optional[str] = None
    repository: Optional[RepositoryInfo] = None
    prompt: str
    model: str = "gpt-4"
    metadata: Optional[Dict] = None
    tags: Optional[List[str]] = None


# Create FastAPI app
app = FastAPI(
    title="Code Context Retrieval Server",
    description="API for codebase analysis, context management, and agent execution",
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

# Initialize BucketStore if environment variables are set
bucket_store = None
if os.environ.get("S3_BUCKET") and os.environ.get("S3_ENDPOINT"):
    bucket_store = BucketStore(
        bucket_name=os.environ.get("S3_BUCKET"),
        endpoint_url=os.environ.get("S3_ENDPOINT"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    logger.info(f"Initialized BucketStore with bucket: {os.environ.get('S3_BUCKET')}")


@app.get("/")
async def root():
    """Root endpoint that returns server information."""
    return {
        "name": "Code Context Retrieval Server",
        "version": "0.1.0",
        "endpoints": [
            "/analyze",
            "/snapshot/create",
            "/snapshot/list",
            "/snapshot/load/{snapshot_id}",
            "/agent/execute",
        ],
    }


@app.post("/analyze")
async def analyze_codebase(request: AnalysisRequest):
    """
    Analyze a codebase and return the results.
    
    Args:
        request: The analysis request containing repository information
        
    Returns:
        The analysis results
    """
    try:
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=request.repository.repo_full_name,
            commit=request.repository.commit,
            language=request.repository.language,
            disable_file_parse=request.repository.disable_file_parse,
        )
        
        if request.metadata:
            harness.metadata = request.metadata
        if request.tags:
            harness.tags = request.tags
            
        results = harness.analyze_codebase()
        return JSONResponse(content=results)
    except Exception as e:
        logger.error(f"Error analyzing codebase: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/snapshot/create")
async def create_snapshot(request: SnapshotRequest):
    """
    Create a snapshot of a codebase.
    
    Args:
        request: The snapshot request containing repository information
        
    Returns:
        The snapshot ID and metadata
    """
    try:
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=request.repository.repo_full_name,
            commit=request.repository.commit,
            language=request.repository.language,
            disable_file_parse=request.repository.disable_file_parse,
        )
        
        if request.metadata:
            harness.metadata = request.metadata
        if request.tags:
            harness.tags = request.tags
            
        # Analyze the codebase
        harness.analyze_codebase()
        
        # Create the snapshot
        snapshot = CodebaseContextSnapshot(
            harness=harness,
            bucket_store=bucket_store,
            snapshot_id=request.snapshot_id,
        )
        
        # Save locally and to S3 if available
        snapshot_id = snapshot.create_snapshot(
            local_path=Path("snapshots")
        )
        
        return {
            "snapshot_id": snapshot_id,
            "repository": request.repository.dict(),
            "timestamp": snapshot.snapshot_data.get("timestamp"),
        }
    except Exception as e:
        logger.error(f"Error creating snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot/list")
async def list_snapshots(repo_name: Optional[str] = Query(None)):
    """
    List available snapshots.
    
    Args:
        repo_name: Optional repository name to filter snapshots
        
    Returns:
        A list of snapshot metadata
    """
    try:
        if not bucket_store:
            # List local snapshots
            snapshots_dir = Path("snapshots")
            if not snapshots_dir.exists():
                return []
                
            snapshots = []
            for file in snapshots_dir.glob("snapshot_*.json"):
                with open(file, "r") as f:
                    data = json.load(f)
                    if not repo_name or data.get("repo_name") == repo_name:
                        snapshots.append({
                            "snapshot_id": data.get("snapshot_id"),
                            "timestamp": data.get("timestamp"),
                            "repo_name": data.get("repo_name"),
                            "tags": data.get("tags", []),
                        })
            return snapshots
        else:
            # List S3 snapshots
            return CodebaseContextSnapshot.list_snapshots(
                bucket_store=bucket_store,
                repo_name=repo_name,
            )
    except Exception as e:
        logger.error(f"Error listing snapshots: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot/load/{snapshot_id}")
async def load_snapshot(snapshot_id: str):
    """
    Load a snapshot by ID.
    
    Args:
        snapshot_id: The ID of the snapshot to load
        
    Returns:
        The snapshot data
    """
    try:
        snapshot = CodebaseContextSnapshot.load_snapshot(
            snapshot_id=snapshot_id,
            local_path=Path("snapshots"),
            bucket_store=bucket_store,
        )
        
        if not snapshot:
            raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")
            
        return snapshot.snapshot_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading snapshot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/execute")
async def execute_agent(request: AgentExecutionRequest):
    """
    Execute an agent with the given context.
    
    Args:
        request: The agent execution request
        
    Returns:
        The agent execution results
    """
    try:
        # Get the codebase either from a snapshot or repository info
        if request.snapshot_id:
            # Load from snapshot
            snapshot = CodebaseContextSnapshot.load_snapshot(
                snapshot_id=request.snapshot_id,
                local_path=Path("snapshots"),
                bucket_store=bucket_store,
            )
            
            if not snapshot:
                raise HTTPException(status_code=404, detail=f"Snapshot {request.snapshot_id} not found")
                
            harness = snapshot.harness
            
        elif request.repository:
            # Create from repository info
            harness = CodebaseAnalysisHarness.from_repo(
                repo_full_name=request.repository.repo_full_name,
                commit=request.repository.commit,
                language=request.repository.language,
                disable_file_parse=request.repository.disable_file_parse,
            )
            
            # Analyze the codebase
            harness.analyze_codebase()
        else:
            raise HTTPException(
                status_code=400,
                detail="Either snapshot_id or repository must be provided"
            )
            
        # Set metadata and tags
        if request.metadata:
            harness.metadata = request.metadata
        if request.tags:
            harness.tags = request.tags
            
        # Create and run the agent
        agent = CodeAgent(
            codebase=harness.codebase,
            tags=harness.tags,
            metadata=harness.metadata,
        )
        
        result = agent.run(prompt=request.prompt)
        
        # Get the diff if there were changes
        diff = harness.codebase.get_diff()
        
        return {
            "result": result,
            "diff": diff,
            "edited_files": harness.files_in_patch(diff) if diff else [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """
    Start the FastAPI server.
    
    Args:
        host: The host to bind to
        port: The port to bind to
    """
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()

