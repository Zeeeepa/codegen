"""
CodeContextRetrievalServer - FastAPI server for accessing codebase analysis and context functionality.
"""

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field

from codegen_on_oss.analysis.harness_integration import CodebaseAnalysisHarness
from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.snapshot.context_snapshot import CodebaseContextSnapshot


# Define API models
class RepositoryInfo(BaseModel):
    repo_full_name: str = Field(..., description="Full repository name (owner/repo)")
    commit: str | None = Field(None, description="Commit hash to analyze")
    language: str = Field("python", description="Primary language of the repository")


class AgentRunRequest(BaseModel):
    prompt: str = Field(..., description="Prompt to send to the agent")
    model: str | None = Field(None, description="Model to use for the agent")
    metadata: dict[str, Any] | None = Field(
        None, description="Metadata for the agent run"
    )


class SnapshotInfo(BaseModel):
    snapshot_id: str = Field(..., description="ID of the snapshot")
    created_at: str = Field(..., description="Creation timestamp")
    repo_info: dict[str, Any] = Field(..., description="Repository information")


# Create FastAPI app
app = FastAPI(
    title="Code Context Retrieval Server",
    description="API for codebase analysis, context management, and agent execution",
    version="0.1.0",
)

# Global storage for active harnesses and snapshots
active_harnesses: dict[str, CodebaseAnalysisHarness] = {}
bucket_store: BucketStore | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize resources on server startup."""
    global bucket_store
    try:
        bucket_store = BucketStore()
        logger.info("Initialized bucket store for remote storage")
    except Exception as e:
        logger.warning(f"Failed to initialize bucket store: {e}")
        logger.info("Continuing without remote storage capabilities")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Code Context Retrieval Server",
        "version": "0.1.0",
        "endpoints": [
            "/analyze/repository",
            "/analyze/file_stats",
            "/snapshot/create",
            "/snapshot/list",
            "/snapshot/load/{snapshot_id}",
            "/agent/run",
        ],
    }


@app.post("/analyze/repository", response_model=dict[str, Any])
async def analyze_repository(repo_info: RepositoryInfo):
    """
    Analyze a repository and return the results.

    Creates a new CodebaseAnalysisHarness for the repository and performs analysis.
    """
    harness_key = f"{repo_info.repo_full_name}:{repo_info.commit or 'latest'}"

    try:
        # Create a new harness for the repository
        harness = CodebaseAnalysisHarness.from_repo(
            repo_full_name=repo_info.repo_full_name,
            commit=repo_info.commit,
            language=repo_info.language,
        )

        # Store the harness for later use
        active_harnesses[harness_key] = harness

        # Perform analysis
        results = harness.analyze_codebase()

        return {
            "harness_key": harness_key,
            "results": results,
        }
    except Exception as e:
        logger.error(f"Repository analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/file_stats", response_model=dict[str, Any])
async def get_file_stats(
    harness_key: str = Query(..., description="Key of the active harness"),
):
    """
    Get file statistics for an analyzed repository.
    """
    if harness_key not in active_harnesses:
        raise HTTPException(status_code=404, detail=f"Harness {harness_key} not found")

    harness = active_harnesses[harness_key]

    if not harness.analysis_results:
        # Run analysis if not already done
        harness.analyze_codebase()

    return harness.analysis_results.get("file_stats", {})


@app.post("/snapshot/create", response_model=dict[str, str])
async def create_snapshot(
    harness_key: str = Query(..., description="Key of the active harness"),
    local_path: str | None = Query(
        None, description="Optional local path to save the snapshot"
    ),
):
    """
    Create a snapshot of the current codebase state and analysis results.
    """
    if harness_key not in active_harnesses:
        raise HTTPException(status_code=404, detail=f"Harness {harness_key} not found")

    harness = active_harnesses[harness_key]

    try:
        snapshot = CodebaseContextSnapshot(harness=harness, bucket_store=bucket_store)
        snapshot_id = snapshot.create_snapshot(local_path=local_path)

        return {
            "snapshot_id": snapshot_id,
            "message": "Snapshot created successfully",
        }
    except Exception as e:
        logger.error(f"Snapshot creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/snapshot/list", response_model=list[SnapshotInfo])
async def list_snapshots():
    """
    List all available snapshots.
    """
    snapshots = []

    # List snapshots from bucket store if available
    if bucket_store:
        try:
            keys = bucket_store.list_keys(prefix="snapshots/")
            for key in keys:
                try:
                    data = bucket_store.get_json(key)
                    snapshots.append(
                        SnapshotInfo(
                            snapshot_id=data["snapshot_id"],
                            created_at=data["created_at"],
                            repo_info=data["repo_info"],
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to load snapshot {key}: {e}")
        except Exception as e:
            logger.warning(f"Failed to list snapshots from bucket store: {e}")

    # List local snapshots
    for directory in [Path("./snapshots"), Path("./data/snapshots")]:
        if directory.exists():
            for snapshot_file in directory.glob("snapshot_*.json"):
                try:
                    with open(snapshot_file) as f:
                        data = json.load(f)
                        snapshots.append(
                            SnapshotInfo(
                                snapshot_id=data["snapshot_id"],
                                created_at=data["created_at"],
                                repo_info=data["repo_info"],
                            )
                        )
                except Exception as e:
                    logger.warning(
                        f"Failed to load local snapshot {snapshot_file}: {e}"
                    )

    return snapshots


@app.get("/snapshot/load/{snapshot_id}", response_model=dict[str, Any])
async def load_snapshot(snapshot_id: str):
    """
    Load a snapshot by ID and return its data.
    """
    try:
        snapshot = CodebaseContextSnapshot(
            snapshot_id=snapshot_id, bucket_store=bucket_store
        )
        data = snapshot.load_snapshot()
        return data
    except Exception as e:
        logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")


@app.post("/agent/run", response_model=dict[str, Any])
async def run_agent(
    request: AgentRunRequest,
    harness_key: str = Query(..., description="Key of the active harness"),
):
    """
    Run an agent on the codebase with the given prompt.
    """
    if harness_key not in active_harnesses:
        raise HTTPException(status_code=404, detail=f"Harness {harness_key} not found")

    harness = active_harnesses[harness_key]

    try:
        # Update metadata if provided
        if request.metadata:
            harness.metadata.update(request.metadata)

        # Run the agent
        result = harness.run_agent(prompt=request.prompt, model=request.model)

        return {
            "harness_key": harness_key,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return app
