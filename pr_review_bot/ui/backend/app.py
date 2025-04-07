from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import datetime
import json
import os
from pathlib import Path

app = FastAPI(title="PR Review Bot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Repository(BaseModel):
    name: str
    status: str
    health: str
    
class Branch(BaseModel):
    repository: str
    implements: int
    status: str
    
class Error(BaseModel):
    message: str
    repository: str
    details: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    
class Dashboard(BaseModel):
    status: str
    repositories_count: int
    last_check: str
    recent_activity: List[str]
    repository_health: Dict[str, str]
    active_branches: List[Branch]
    errors: List[Error]

# Mock data for development
def get_mock_data():
    return {
        "status": "Running",
        "repositories_count": 7,
        "last_check": "2 mins ago",
        "recent_activity": [
            "PR #123 created",
            "PR #120 reviewed",
            "PR #118 merged",
            "Branch monitor error",
            "PR #115 reviewed"
        ],
        "repository_health": {
            "codegen": "Healthy",
            "bolt-chat": "Healthy",
            "agentgen": "2 errors",
            "langgraph-slackbot": "Healthy",
            "mcp-index": "1 warning"
        },
        "active_branches": [
            {"repository": "codegen", "implements": 7, "status": "PR #123 Open"},
            {"repository": "agentgen", "implements": 1, "status": "PR #45 Open"},
            {"repository": "bolt-chat", "implements": 5, "status": "No commits"},
            {"repository": "mcp-index", "implements": 2, "status": "PR #67 Merged"}
        ],
        "errors": [
            {
                "message": "No commits between main and branch",
                "repository": "Zeeeepa/codegen",
                "details": "Error processing branch gen/33d8dcdc-9a6b-4db2-b07b-5d469a888365",
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=3)
            },
            {
                "message": "Can't compare offset-naive and offset-aware datetimes",
                "repository": "Zeeeepa/agentgen",
                "details": "When processing PR #42",
                "timestamp": datetime.datetime.now() - datetime.timedelta(hours=1)
            }
        ]
    }

# Routes
@app.get("/")
async def root():
    return {"message": "PR Review Bot API"}

@app.get("/api/dashboard", response_model=Dashboard)
async def get_dashboard():
    # In a real implementation, this would fetch data from the PR Review Bot
    data = get_mock_data()
    return data

@app.get("/api/repositories")
async def get_repositories():
    data = get_mock_data()
    repos = []
    for name, health in data["repository_health"].items():
        repos.append({
            "name": name,
            "status": "Monitored",
            "health": health
        })
    return repos

@app.get("/api/errors")
async def get_errors():
    data = get_mock_data()
    return data["errors"]

@app.get("/api/repository/{repo_name}")
async def get_repository(repo_name: str):
    data = get_mock_data()
    if repo_name not in data["repository_health"]:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # In a real implementation, this would fetch detailed data for the specific repository
    return {
        "name": repo_name,
        "status": "Monitored",
        "health": data["repository_health"].get(repo_name, "Unknown"),
        "branches": [b for b in data["active_branches"] if b["repository"] == repo_name],
        "errors": [e for e in data["errors"] if repo_name in e["repository"]]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)