"""
Server for analyzing code repositories and commits.

This module provides a FastAPI server that can analyze repositories and commits,
compare branches, and provide detailed reports on code quality and issues.
It serves as a backend analysis server for PR validation and codebase analysis.
"""

import os
import tempfile
import subprocess
import logging
import json
import time
import asyncio
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from pathlib import Path
import uvicorn
from functools import lru_cache

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator, root_validator

from codegen import Codebase
from codegen_on_oss.analysis.coordinator import AnalysisCoordinator
from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer
from codegen_on_oss.analysis.project_manager import ProjectManager
from codegen_on_oss.analysis.webhook_handler import WebhookHandler
from codegen_on_oss.analysis.feature_analyzer import FeatureAnalyzer
from codegen_on_oss.analysis.api_endpoints import router as api_router
from codegen_on_oss.database import get_db_manager, get_db_session
from codegen_on_oss.database import (
    RepositoryRepository, CommitRepository, FileRepository, SymbolRepository,
    SnapshotRepository, AnalysisResultRepository, MetricRepository, IssueRepository
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Code Analysis Server",
    description="Server for analyzing code repositories and commits",
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

# Include API router
app.include_router(api_router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        # Initialize database
        db_manager = get_db_manager()
        db_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        # Don't raise an exception here, as it would prevent the app from starting

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint for the API."""
    return {
        "name": "Code Analysis Server",
        "description": "Server for analyzing code repositories and commits",
        "version": "1.0.0",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
