#!/usr/bin/env python3
"""
PR Review Bot - A simple GitHub PR review bot using codegen libraries.

This bot can:
1. Review PRs using the codegen library
2. Run as a webhook server to automatically review PRs
3. Run as a CLI tool to review specific PRs
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional, List
import uvicorn
from fastapi import FastAPI, Request, Response
import json
from dotenv import load_dotenv

# Import codegen libraries directly - no mock implementations
from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen import CodeAgent
from codegen.extensions.langchain.tools import (
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)

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

def load_env():
    """
    Load environment variables from .env file.
    
    Returns:
        True if successful, False otherwise
    """
    load_dotenv()
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        print("Please create a .env file with your GitHub token")
        print("Example: GITHUB_TOKEN=ghp_your_token_here")
        return False
    return True

def review_pr(repo_name: str, pr_number: int) -> Dict[str, Any]:
    """
    Review a pull request using codegen.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number
        
    Returns:
        Result of the review
    """
    logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
    
    try:
        # Initialize Codebase with proper GitHub token
        github_token = os.environ.get("GITHUB_TOKEN")
        codebase = Codebase.from_repo(
            repo_name, 
            language="python",  # Default to Python, could be made dynamic
            secrets=SecretsConfig(github_token=github_token)
        )
        
        # Create a temporary comment to indicate the review is in progress
        review_attention_message = "PR Review Bot is starting to review the PR, please wait..."
        comment = codebase._op.create_pr_comment(pr_number, review_attention_message)
        
        # Define tools for the agent
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
        ]
        
        # Create agent with the defined tools
        agent = CodeAgent(codebase=codebase, tools=pr_tools)
        
        # Create prompt for the agent
        prompt = f"""
        Hey PR Review Bot!
        
        Please review this pull request: https://github.com/{repo_name}/pull/{pr_number}
        
        Provide a thorough code review that includes:
        1. A summary of the changes
        2. Code quality assessment
        3. Potential bugs or issues
        4. Suggestions for improvements
        5. Overall assessment
        
        Be specific in your feedback and include code snippets where relevant.
        """
        
        # Run the agent
        result = agent.run(prompt)
        
        # Delete the temporary comment
        if comment:
            comment.delete()
        
        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "status": "success",
            "message": "PR review completed successfully",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "status": "error",
            "message": f"Error reviewing PR: {str(e)}"
        }

@app.post("/webhook")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Response with status
    """
    # Get the event type from the headers
    event_type = request.headers.get("X-GitHub-Event")
    
    if not event_type:
        return Response(content="Missing X-GitHub-Event header", status_code=400)
    
    # Parse the payload
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return Response(content="Invalid JSON payload", status_code=400)
    
    # Handle pull_request events
    if event_type == "pull_request":
        action = payload.get("action")
        
        # Only process opened or synchronize events
        if action in ["opened", "synchronize", "labeled"]:
            pr_number = payload.get("number")
            repo = payload.get("repository", {})
            repo_name = repo.get("full_name")
            
            # Check if the PR has the "review" label
            labels = payload.get("pull_request", {}).get("labels", [])
            should_review = False
            
            # Check for specific labels that trigger a review
            for label in labels:
                if label.get("name", "").lower() in ["review", "codegen", "bot-review"]:
                    should_review = True
                    break
            
            # If it's a labeled event, check if the added label is a review label
            if action == "labeled" and payload.get("label", {}).get("name", "").lower() in ["review", "codegen", "bot-review"]:
                should_review = True
            
            if should_review and pr_number and repo_name:
                # Review the PR in a background task
                # In a production environment, you would use a task queue
                # For simplicity, we'll just log that we would review it
                logger.info(f"Received webhook to review PR #{pr_number} in {repo_name}")
                
                # Review the PR
                result = review_pr(repo_name, pr_number)
                
                return {"status": "success", "message": f"PR #{pr_number} review started", "result": result}
    
    # Return a success response for any other event
    return {"status": "success", "message": f"Received {event_type} event"}

def cli_review_pr(repo_name: str, pr_number: int):
    """
    CLI command to review a specific PR.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number
    """
    print(f"🔍 Reviewing PR #{pr_number} in {repo_name}...")
    
    result = review_pr(repo_name, pr_number)
    
    if result["status"] == "success":
        print(f"\n✅ PR #{pr_number} review completed successfully")
    else:
        print(f"\n❌ Error reviewing PR: {result['message']}")

def cli_server(port: int = 8000):
    """
    CLI command to start the webhook server.
    
    Args:
        port: Port to run the server on
    """
    print(f"🚀 Starting PR Review Bot server on port {port}...")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

def main():
    """
    Main entry point for the PR Review Bot.
    """
    # Load environment variables
    if not load_env():
        sys.exit(1)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PR Review Bot")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review a specific PR")
    review_parser.add_argument("repo", help="Repository name in format owner/repo")
    review_parser.add_argument("pr", type=int, help="Pull request number")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the webhook server")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == "review":
        cli_review_pr(args.repo, args.pr)
    elif args.command == "server":
        cli_server(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()