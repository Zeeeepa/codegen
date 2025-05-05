"""
Main application for the codegen-on-oss system.

This module provides the main FastAPI application.
"""

import logging

import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from codegen_on_oss.api.rest import router as rest_router
from codegen_on_oss.server.api.websocket_manager import websocket_manager
from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.events.event_bus import event_bus

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Codegen-on-OSS API",
    description="API for the Codegen-on-OSS system",
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

# Include API routers
app.include_router(rest_router, prefix="/api")


# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection
        client_id: Client ID
    """
    await websocket_manager.handle_connection(websocket, client_id)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Initialize database
    db_manager.create_tables()

    # Start event bus
    event_bus.start()

    logger.info("Application started")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    # Stop event bus
    event_bus.stop()

    logger.info("Application stopped")


def run_app(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the application.

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    uvicorn.run(app, host=host, port=port)
