"""
API Server for Codegen OSS

This module provides a FastAPI server with GraphQL and WebSocket support
for frontend integration.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.graphql import GraphQLApp
from sqlalchemy.orm import Session

from .graphql_schema import schema
from ..database.service import DatabaseService, DatabaseConfig
from ..events.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Codegen OSS API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
db_config = DatabaseConfig()
db_service = DatabaseService(db_config)

# Create database tables if they don't exist
db_service.create_tables()


# Dependency to get database session
def get_db():
    db = db_service.get_session()
    try:
        yield db
    finally:
        db.close()


# Add GraphQL endpoint
app.add_route("/graphql", GraphQLApp(schema=schema))

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_subscriptions: Dict[WebSocket, List[EventType]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_subscriptions[websocket] = []
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.connection_subscriptions:
            del self.connection_subscriptions[websocket]
    
    def subscribe(self, websocket: WebSocket, event_type: EventType):
        if websocket in self.connection_subscriptions:
            if event_type not in self.connection_subscriptions[websocket]:
                self.connection_subscriptions[websocket].append(event_type)
    
    def unsubscribe(self, websocket: WebSocket, event_type: EventType):
        if websocket in self.connection_subscriptions:
            if event_type in self.connection_subscriptions[websocket]:
                self.connection_subscriptions[websocket].remove(event_type)
    
    async def broadcast(self, event: Event):
        for websocket in self.active_connections:
            subscriptions = self.connection_subscriptions.get(websocket, [])
            if event.event_type in subscriptions:
                await self.send_event(websocket, event)
    
    async def send_event(self, websocket: WebSocket, event: Event):
        try:
            await websocket.send_text(event.to_json())
        except Exception as e:
            logger.error(f"Error sending event to WebSocket: {e}")


# Create connection manager
manager = ConnectionManager()

# Register event handler for broadcasting events
async def broadcast_event(event: Event):
    await manager.broadcast(event)

# Register the async event handler with the event bus
for event_type in EventType:
    event_bus.subscribe_async(event_type, broadcast_event)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    event_type_name = message.get("event_type")
                    if event_type_name:
                        try:
                            event_type = EventType[event_type_name]
                            manager.subscribe(websocket, event_type)
                            await websocket.send_text(json.dumps({
                                "status": "success",
                                "message": f"Subscribed to {event_type_name}",
                            }))
                        except KeyError:
                            await websocket.send_text(json.dumps({
                                "status": "error",
                                "message": f"Unknown event type: {event_type_name}",
                            }))
                
                elif action == "unsubscribe":
                    event_type_name = message.get("event_type")
                    if event_type_name:
                        try:
                            event_type = EventType[event_type_name]
                            manager.unsubscribe(websocket, event_type)
                            await websocket.send_text(json.dumps({
                                "status": "success",
                                "message": f"Unsubscribed from {event_type_name}",
                            }))
                        except KeyError:
                            await websocket.send_text(json.dumps({
                                "status": "error",
                                "message": f"Unknown event type: {event_type_name}",
                            }))
                
                else:
                    await websocket.send_text(json.dumps({
                        "status": "error",
                        "message": f"Unknown action: {action}",
                    }))
            
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON",
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# REST API endpoints for basic operations

@app.get("/api/repositories")
async def get_repositories(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """Get all repositories with pagination."""
    repositories = db_service.get_all(db, limit=limit, offset=offset)
    return {"repositories": repositories}


@app.get("/api/repositories/{repository_id}")
async def get_repository(repository_id: str, db: Session = Depends(get_db)):
    """Get a repository by ID."""
    repository = db_service.get_by_id(db, repository_id)
    if not repository:
        return Response(status_code=404, content=json.dumps({"error": "Repository not found"}))
    return {"repository": repository}


@app.get("/api/snapshots")
async def get_snapshots(repository_id: Optional[str] = None, limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """Get all snapshots with optional filtering by repository ID."""
    if repository_id:
        snapshots = db_service.get_snapshots_by_repository(db, repository_id, limit=limit, offset=offset)
    else:
        snapshots = db_service.get_all(db, limit=limit, offset=offset)
    return {"snapshots": snapshots}


@app.get("/api/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: str, db: Session = Depends(get_db)):
    """Get a snapshot by ID."""
    snapshot = db_service.get_by_id(db, snapshot_id)
    if not snapshot:
        return Response(status_code=404, content=json.dumps({"error": "Snapshot not found"}))
    return {"snapshot": snapshot}


@app.get("/api/analyses")
async def get_analyses(
    repository_id: Optional[str] = None,
    snapshot_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all analyses with optional filtering."""
    analyses = db_service.get_analyses(
        db,
        repository_id=repository_id,
        snapshot_id=snapshot_id,
        analysis_type=analysis_type,
        status=status,
        limit=limit,
        offset=offset
    )
    return {"analyses": analyses}


@app.get("/api/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Get an analysis by ID."""
    analysis = db_service.get_by_id(db, analysis_id)
    if not analysis:
        return Response(status_code=404, content=json.dumps({"error": "Analysis not found"}))
    return {"analysis": analysis}


@app.get("/api/compare")
async def compare_snapshots(
    snapshot_id_1: str,
    snapshot_id_2: str,
    detail_level: str = "summary",
    db: Session = Depends(get_db)
):
    """Compare two snapshots."""
    try:
        comparison = db_service.compare_snapshots(snapshot_id_1, snapshot_id_2, detail_level=detail_level)
        return {"comparison": comparison}
    except ValueError as e:
        return Response(status_code=400, content=json.dumps({"error": str(e)}))


@app.get("/api/visualization")
async def get_visualization_data(
    snapshot_id: str,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Get visualization data for a snapshot."""
    try:
        data = db_service.get_visualization_data(snapshot_id, format=format)
        return {"data": data}
    except ValueError as e:
        return Response(status_code=400, content=json.dumps({"error": str(e)}))


# Add context to GraphQL requests
@app.middleware("http")
async def add_db_to_context(request: Request, call_next):
    if request.url.path == "/graphql":
        request.state.session = next(get_db())
    response = await call_next(request)
    return response


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)

