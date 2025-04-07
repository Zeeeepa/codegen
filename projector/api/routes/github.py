"""
API routes for GitHub integration.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta

from projector.backend.github_manager import GitHubManager
from projector.api.main import get_github_manager

router = APIRouter()

class RepoContents(BaseModel):
    """Model for repository contents."""
    path: str
    type: str
    content: Optional[str] = None
    sha: Optional[str] = None

class PullRequest(BaseModel):
    """Model for a pull request."""
    number: int
    title: str
    body: Optional[str] = None
    html_url: str
    state: str
    created_at: str
    updated_at: str
    merged: bool
    merged_at: Optional[str] = None
    user: Dict[str, Any]

class Comment(BaseModel):
    """Model for a comment."""
    id: int
    body: str
    created_at: str
    updated_at: str
    user: Dict[str, Any]

class Branch(BaseModel):
    """Model for a branch."""
    name: str
    commit: Dict[str, Any]

class Commit(BaseModel):
    """Model for a commit."""
    sha: str
    message: str
    author: Dict[str, Any]
    committer: Dict[str, Any]
    html_url: str

@router.get("/repos/{owner}/{repo}/contents/{path:path}")
async def get_repository_contents(
    owner: str,
    repo: str,
    path: str = "",
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get repository contents."""
    contents = github_manager.get_repository_contents(owner, repo, path)
    if not contents:
        raise HTTPException(status_code=404, detail="Repository contents not found")
    
    return contents

@router.get("/repos/{owner}/{repo}/pulls", response_model=List[PullRequest])
async def get_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get pull requests."""
    repository = github_manager.get_repository(owner, repo)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    try:
        pulls = repository.get_pulls(state=state)
        
        result = []
        for pr in pulls:
            result.append({
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "html_url": pr.html_url,
                "state": pr.state,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "merged": pr.merged,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "user": {
                    "login": pr.user.login,
                    "avatar_url": pr.user.avatar_url
                }
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pull requests: {str(e)}")

@router.get("/repos/{owner}/{repo}/pulls/{pr_number}", response_model=PullRequest)
async def get_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get a pull request."""
    pr_data = github_manager.get_pull_request(owner, repo, pr_number)
    if not pr_data:
        raise HTTPException(status_code=404, detail="Pull request not found")
    
    return pr_data

@router.get("/repos/{owner}/{repo}/pulls/{pr_number}/comments", response_model=List[Comment])
async def get_pull_request_comments(
    owner: str,
    repo: str,
    pr_number: int,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get comments on a pull request."""
    comments = github_manager.get_comments(owner, repo, pr_number)
    if comments is None:
        raise HTTPException(status_code=500, detail="Error getting comments")
    
    return comments

@router.post("/repos/{owner}/{repo}/pulls/{pr_number}/comments", response_model=Comment)
async def create_pull_request_comment(
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Create a comment on a pull request."""
    comment = github_manager.create_comment(owner, repo, pr_number, body)
    if not comment:
        raise HTTPException(status_code=500, detail="Error creating comment")
    
    return comment

@router.get("/repos/{owner}/{repo}/branches", response_model=List[Branch])
async def get_branches(
    owner: str,
    repo: str,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get branches in a repository."""
    branches = github_manager.get_branches(owner, repo)
    if branches is None:
        raise HTTPException(status_code=500, detail="Error getting branches")
    
    return branches

@router.get("/repos/{owner}/{repo}/commits", response_model=List[Commit])
async def get_commits(
    owner: str,
    repo: str,
    branch: Optional[str] = None,
    path: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    max_count: int = 100,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get commits in a repository."""
    commits = github_manager.get_commits(
        owner=owner,
        repo=repo,
        branch=branch,
        path=path,
        since=since,
        until=until,
        max_count=max_count
    )
    if commits is None:
        raise HTTPException(status_code=500, detail="Error getting commits")
    
    return commits

@router.get("/repos/{owner}/{repo}/merges", response_model=List[PullRequest])
async def get_recent_merges(
    owner: str,
    repo: str,
    days: int = 7,
    github_manager: GitHubManager = Depends(get_github_manager)
):
    """Get recent merged pull requests."""
    merges = github_manager.get_recent_merges(owner, repo, days)
    if merges is None:
        raise HTTPException(status_code=500, detail="Error getting recent merges")
    
    return merges