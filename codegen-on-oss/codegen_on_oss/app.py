"""
Main application for Codegen-on-OSS

This module provides the main application that integrates all components.
"""

import os
import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from codegen_on_oss.database import init_db
from codegen_on_oss.events import EventBus
from codegen_on_oss.api import create_rest_app, create_graphql_app, WebSocketManager

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create the main application.
    
    Returns:
        The FastAPI application.
    """
    # Initialize database
    init_db()
    
    # Create event bus
    event_bus = EventBus()
    
    # Create REST API app
    app = create_rest_app()
    
    # Add GraphQL route
    graphql_app = create_graphql_app()
    app.include_router(graphql_app, prefix="/graphql")
    
    # Create WebSocket manager
    websocket_manager = WebSocketManager(event_bus)
    
    # Add WebSocket routes
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket, client_id: str):
        await websocket_manager.handle_client(websocket, client_id)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", "8000"))
    
    # Run the application
    uvicorn.run(
        "codegen_on_oss.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

