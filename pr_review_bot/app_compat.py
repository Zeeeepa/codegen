#!/usr/bin/env python3
"""
Compatibility entry point for the PR Review Bot.
This script provides backward compatibility with the old app.py structure.
"""

import os
import sys
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from pydantic import BaseModel
from github import Github

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Try to import from the new structure
try:
    from pr_review_bot.core.github_client import GitHubClient
    from pr_review_bot.core.pr_reviewer import PRReviewer
    from pr_review_bot.core.compatibility import HAS_CODEGEN, HAS_AGENTGEN
    NEW_STRUCTURE = True
except ImportError:
    # Fall back to old structure
    NEW_STRUCTURE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pr_review_bot")

# Create FastAPI app
app = FastAPI(title="PR Review Bot")

# Webhook secret for GitHub
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Initialize GitHub client and PR reviewer
github_token = os.environ.get("GITHUB_TOKEN", "")
if not github_token:
    logger.error("GITHUB_TOKEN environment variable is required")
    print("\n❌ GITHUB_TOKEN environment variable is required")
    print("Please create a .env file with your GitHub token")
    print("Example: GITHUB_TOKEN=ghp_your_token_here")
    sys.exit(1)

if NEW_STRUCTURE:
    logger.info("Using new PR Review Bot structure")
    github_client = GitHubClient(github_token)
    pr_reviewer = PRReviewer(github_token)
else:
    logger.info("Using old PR Review Bot structure")
    # Import helpers from the old structure
    try:
        from helpers import review_pr, get_github_client, remove_bot_comments, pr_review_agent
        github_client = get_github_client(github_token)
    except ImportError:
        logger.error("Could not import helpers module")
        print("\n❌ Could not import helpers module")
        sys.exit(1)

async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    """
    Verify the GitHub webhook signature.
    """
    if not WEBHOOK_SECRET or not x_hub_signature_256:
        return True
    
    body = await request.body()
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={signature}"
    
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

@app.get("/")
async def root():
    """
    Root endpoint for the PR Review Bot.
    """
    return {"message": "PR Review Bot is running"}

@app.post("/webhook")
async def webhook(request: Request, verified: bool = Depends(verify_signature)):
    """
    GitHub webhook endpoint.
    """
    body = await request.body()
    event = json.loads(body)
    
    # Get the event type from the headers
    event_type = request.headers.get("X-GitHub-Event", "")
    
    logger.info(f"Received {event_type} event")
    
    # Handle pull request events
    if event_type == "pull_request":
        action = event.get("action", "")
        logger.info(f"Pull request {action} event")
        
        # Process the event based on action
        if action in ["opened", "synchronize", "reopened"]:
            pr_number = event["pull_request"]["number"]
            repo_name = event["repository"]["full_name"]
            
            # Review the PR
            logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
            
            try:
                if NEW_STRUCTURE:
                    # Use the new PR reviewer
                    result = pr_reviewer.review_pr(repo_name, pr_number)
                else:
                    # Use the old PR reviewer
                    result = pr_review_agent(event)
                
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                return {"status": "error", "message": str(e)}
        
        # Handle labeled events
        elif action == "labeled":
            label_name = event["label"]["name"]
            pr_number = event["pull_request"]["number"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} labeled with Codegen, starting review")
                
                try:
                    if NEW_STRUCTURE:
                        # Use the new PR reviewer
                        repo_name = event["repository"]["full_name"]
                        result = pr_reviewer.review_pr(repo_name, pr_number)
                    else:
                        # Use the old PR reviewer
                        result = pr_review_agent(event)
                    
                    return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Error reviewing PR: {e}")
                    return {"status": "error", "message": str(e)}
        
        # Handle unlabeled events
        elif action == "unlabeled":
            label_name = event["label"]["name"]
            pr_number = event["pull_request"]["number"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} unlabeled, removing bot comments")
                
                try:
                    if NEW_STRUCTURE:
                        # Use the new GitHub client
                        repo_name = event["repository"]["full_name"]
                        repo = github_client.get_repository(repo_name)
                        pr = github_client.get_pull_request(repo, pr_number)
                        removed_count = github_client.remove_bot_comments(pr)
                        
                        return {
                            "status": "success",
                            "pr_number": pr_number,
                            "repo_name": repo_name,
                            "removed_comments": removed_count
                        }
                    else:
                        # Use the old bot comment remover
                        result = remove_bot_comments(event)
                        return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Error removing bot comments: {e}")
                    return {"status": "error", "message": str(e)}
    
    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
