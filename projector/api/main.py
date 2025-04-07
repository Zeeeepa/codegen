"""
FastAPI backend for the Projector application.
"""
import os
import sys
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Add the src directory to the Python path for codegen modules
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src'))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Load environment variables
load_dotenv()

# Import backend components
from projector.backend.config import (
    SLACK_USER_TOKEN, GITHUB_TOKEN, GITHUB_USERNAME,
    SLACK_DEFAULT_CHANNEL, GITHUB_DEFAULT_REPO
)
from projector.backend.slack_manager import SlackManager
from projector.backend.github_manager import GitHubManager
from projector.backend.project_database import ProjectDatabase
from projector.backend.project_manager import ProjectManager
from projector.backend.thread_pool import ThreadPool
from projector.backend.ai_user_agent import AIUserAgent

# Import API routes
from projector.api.routes import projects, github, slack, chat, code_improvement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("projector/api.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Projector API",
    description="API for the Projector application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backend components
slack_manager = SlackManager(
    slack_token=SLACK_USER_TOKEN,
    default_channel=SLACK_DEFAULT_CHANNEL
)

github_manager = GitHubManager(
    github_token=GITHUB_TOKEN,
    github_username=GITHUB_USERNAME,
    default_repo=GITHUB_DEFAULT_REPO
)

thread_pool = ThreadPool(max_threads=10)

project_database = ProjectDatabase()

project_manager = ProjectManager(
    github_manager=github_manager,
    slack_manager=slack_manager,
    thread_pool=thread_pool
)

ai_user_agent = AIUserAgent(
    slack_manager=slack_manager,
    github_manager=github_manager,
    project_database=project_database,
    project_manager=project_manager,
    thread_pool=thread_pool,
    docs_path="docs"
)

# Dependency to get backend components
def get_slack_manager():
    return slack_manager

def get_github_manager():
    return github_manager

def get_project_database():
    return project_database

def get_project_manager():
    return project_manager

def get_ai_user_agent():
    return ai_user_agent

def get_thread_pool():
    return thread_pool

# Include API routes
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(github.router, prefix="/api/github", tags=["github"])
app.include_router(slack.router, prefix="/api/slack", tags=["slack"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(code_improvement.router, prefix="/api/code-improvement", tags=["code-improvement"])

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Projector API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)