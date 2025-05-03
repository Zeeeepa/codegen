"""
API Server for Codegen-on-OSS

This module provides a FastAPI server that serves the GraphQL API.
"""

import json
import logging
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from graphql import graphql_sync
from starlette.graphql import GraphQLApp
from starlette.websockets import WebSocketState

from codegen_on_oss.api.graphql_schema import schema
from codegen_on_oss.database.manager import DatabaseManager
from codegen_on_oss.analysis.orchestrator import AnalysisOrchestrator
from codegen_on_oss.snapshot.enhanced_snapshot import EnhancedSnapshotManager

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Codegen-on-OSS API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL endpoint
app.add_route("/graphql", GraphQLApp(schema=schema))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_json(self, client_id: str, data: Dict[str, Any]):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(data)
    
    async def broadcast_json(self, data: Dict[str, Any]):
        for client_id, websocket in list(self.active_connections.items()):
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                self.disconnect(client_id)


# Create connection manager
manager = ConnectionManager()

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle GraphQL subscriptions
                if "type" in message and message["type"] == "subscription":
                    query = message.get("query", "")
                    variables = message.get("variables", {})
                    operation_name = message.get("operationName")
                    
                    # Execute GraphQL query
                    result = await graphql_sync(
                        schema,
                        query,
                        variable_values=variables,
                        operation_name=operation_name,
                        context_value={"request": websocket}
                    )
                    
                    # Send result back to client
                    await websocket.send_json({
                        "id": message.get("id"),
                        "type": "subscription_result",
                        "payload": result.to_dict()
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "error": "Invalid JSON"
                })
            except Exception as e:
                logger.exception(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "error": str(e)
                })
    except WebSocketDisconnect:
        manager.disconnect(client_id)


# REST API endpoints for non-GraphQL operations
@app.post("/api/snapshots")
async def create_snapshot(request: Request):
    """Create a new snapshot from a repository."""
    try:
        data = await request.json()
        repo_url = data.get("repo_url")
        commit_sha = data.get("commit_sha")
        metadata = data.get("metadata", {})
        
        if not repo_url:
            return JSONResponse(
                status_code=400,
                content={"error": "repo_url is required"}
            )
        
        # Create snapshot
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        # Create codebase from repo
        from codegen import Codebase
        codebase = Codebase.from_repo(repo_url)
        
        if commit_sha:
            codebase.checkout(commit=commit_sha)
        
        # Create snapshot
        snapshot = snapshot_manager.create_snapshot(
            codebase=codebase,
            commit_sha=commit_sha,
            metadata=metadata
        )
        
        # Notify connected clients
        await manager.broadcast_json({
            "type": "snapshot_created",
            "payload": {
                "id": snapshot.snapshot_id,
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "timestamp": snapshot.timestamp.isoformat()
            }
        })
        
        return {
            "id": snapshot.snapshot_id,
            "repo_url": repo_url,
            "commit_sha": commit_sha,
            "timestamp": snapshot.timestamp.isoformat()
        }
    except Exception as e:
        logger.exception(f"Error creating snapshot: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/analyses")
async def run_analysis(request: Request):
    """Run an analysis on a snapshot."""
    try:
        data = await request.json()
        snapshot_id = data.get("snapshot_id")
        analyzer_type = data.get("analyzer_type")
        params = data.get("params", {})
        
        if not snapshot_id:
            return JSONResponse(
                status_code=400,
                content={"error": "snapshot_id is required"}
            )
        
        if not analyzer_type:
            return JSONResponse(
                status_code=400,
                content={"error": "analyzer_type is required"}
            )
        
        # Run analysis
        db_manager = DatabaseManager()
        orchestrator = AnalysisOrchestrator(db_manager=db_manager)
        
        analysis_id = orchestrator.run_analysis(
            analyzer_type=analyzer_type,
            snapshot_id=snapshot_id,
            params=params
        )
        
        return {
            "id": analysis_id,
            "snapshot_id": snapshot_id,
            "analyzer_type": analyzer_type,
            "status": "pending"
        }
    except Exception as e:
        logger.exception(f"Error running analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get the result of an analysis."""
    try:
        db_manager = DatabaseManager()
        orchestrator = AnalysisOrchestrator(db_manager=db_manager)
        
        result = orchestrator.get_analysis_result(analysis_id)
        
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.exception(f"Error getting analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/analyses/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get the status of an analysis."""
    try:
        db_manager = DatabaseManager()
        orchestrator = AnalysisOrchestrator(db_manager=db_manager)
        
        status = orchestrator.scheduler.get_analysis_status(analysis_id)
        
        return status
    except Exception as e:
        logger.exception(f"Error getting analysis status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/snapshots/compare")
async def compare_snapshots(request: Request):
    """Compare two snapshots."""
    try:
        data = await request.json()
        base_snapshot_id = data.get("base_snapshot_id")
        compare_snapshot_id = data.get("compare_snapshot_id")
        
        if not base_snapshot_id:
            return JSONResponse(
                status_code=400,
                content={"error": "base_snapshot_id is required"}
            )
        
        if not compare_snapshot_id:
            return JSONResponse(
                status_code=400,
                content={"error": "compare_snapshot_id is required"}
            )
        
        # Compare snapshots
        db_manager = DatabaseManager()
        snapshot_manager = EnhancedSnapshotManager(db_manager=db_manager)
        
        diff = snapshot_manager.compare_snapshots(base_snapshot_id, compare_snapshot_id)
        
        return diff
    except ValueError as e:
        return JSONResponse(
            status_code=404,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.exception(f"Error comparing snapshots: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Run the server
def run_server(host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    """Run the API server."""
    # Initialize database
    db_manager = DatabaseManager()
    db_manager.create_tables()
    
    # Run server
    uvicorn.run(app, host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server(debug=True)

