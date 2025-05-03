"""
Main Application Module

This module provides the main FastAPI application that integrates all components
of the system, including the API routes, database, event system, and WebSocket support.
"""

import logging
import os
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException, WebSocket, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from codegen_on_oss.database.connection import db_manager
from codegen_on_oss.events.event_bus import EventType, Event, event_bus
from codegen_on_oss.api.routes import router, ws_router
from codegen_on_oss.events.handlers import (
    AnalysisEventHandler, SnapshotEventHandler, RepositoryEventHandler,
    JobEventHandler, WebhookEventHandler
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Codegen Analysis API",
    description="API for code analysis and repository management",
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

# Include API routers
app.include_router(router, prefix="/api")
app.include_router(ws_router)

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("Starting up the application")
    
    # Create database tables
    db_manager.create_tables()
    
    # Initialize event handlers
    # These are already initialized when the modules are imported
    # but we'll log it here for clarity
    logger.info("Event handlers initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down the application")

@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {
        "name": "Codegen Analysis API",
        "description": "API for code analysis and repository management",
        "version": "1.0.0",
        "documentation": "/docs",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

def run_app(host: str = "0.0.0.0", port: int = 8000):
    """
    Run the FastAPI application.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_app()
"""

