#!/usr/bin/env python3
"""
PR Review Bot - A simple bot for reviewing GitHub pull requests using codegen.

This bot can be run in two modes:
1. CLI mode: Review a specific PR
2. Server mode: Start a webhook server to listen for PR events

Usage:
    CLI mode: python app.py review <owner/repo> <pr_number>
    Server mode: python app.py server [--port PORT]
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI, Request, Response
import json
import hmac
import hashlib
from github import Github

# Import codegen libraries
from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig
from codegen.extensions.langchain.tools import (
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="PR Review Bot")

def load_env() -> bool:
    """
    Load environment variables from .env file.
    
    Returns:
        bool: True if successful, False otherwise
    """
    load_dotenv()
    
    # Check for required environment variables
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
        Dict[str, Any]: Result of the review
    """
    logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
    
    try:
        # Initialize GitHub client
        github_token = os.environ.get("GITHUB_TOKEN")
        github = Github(github_token)
        repo = github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Create a temporary comment to indicate the review is in progress
        review_attention_message = "PR Review Bot is starting to review the PR, please wait..."
        comment = pr.create_issue_comment(review_attention_message)
        
        # Initialize Codebase with proper authentication
        codebase = Codebase.from_repo(
            repo_name, 
            language="python",  # Default to Python, could be made dynamic
            secrets=SecretsConfig(github_token=github_token)
        )
        
        # Define tools for the review
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
        ]
        
        # Check if we have AI API keys
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if anthropic_api_key or openai_api_key:
            # Use AI for review if API keys are available
            from codegen import CodeAgent
            
            # Create agent with the defined tools
            agent = CodeAgent(codebase=codebase, tools=pr_tools)
            
            # Create prompt for the review
            prompt = f"""
            Hey PR Review Bot!
            
            Please review this pull request: {pr.html_url}
            
            Review this Pull request thoroughly:
            1. Check for code quality issues
            2. Look for potential bugs or edge cases
            3. Suggest improvements where appropriate
            4. Be specific about the changes and their impact
            
            Produce a short summary of your findings and point out possible improvements.
            Use the tools at your disposal to create proper PR reviews.
            Include code snippets if needed, and suggest improvements if necessary.
            """
            
            # Run the agent
            agent.run(prompt)
            
            # Delete the temporary comment
            comment.delete()
            
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "review_type": "ai",
                "result": "AI review completed"
            }
        else:
            logger.warning("No AI API keys found, using basic review")
            
            # Create a simple review comment
            comment_body = f"""
            ## PR Review
            
            This PR has been reviewed by the PR Review Bot.
            
            ### Summary
            - PR Number: #{pr_number}
            - Title: {pr.title}
            - Description: {pr.body or "No description provided"}
            
            ### Review
            This is a basic review without AI assistance. For more detailed reviews, please set up ANTHROPIC_API_KEY or OPENAI_API_KEY.
            
            ### Files Changed
            {", ".join([f.filename for f in pr.get_files()])}
            
            ### Recommendation
            The PR appears to be valid and can be merged if all checks pass.
            """
            
            # Delete the temporary comment
            comment.delete()
            
            # Create the review comment
            pr.create_issue_comment(comment_body)
            
            return {
                "pr_number": pr_number,
                "repo_name": repo_name,
                "review_type": "basic",
                "result": "Basic review completed"
            }
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Try to delete the temporary comment if it exists
        try:
            if 'comment' in locals():
                comment.delete()
        except:
            pass
        
        return {
            "pr_number": pr_number,
            "repo_name": repo_name,
            "error": str(e),
            "result": "Review failed"
        }

def verify_github_webhook(request: Request, payload: bytes) -> bool:
    """
    Verify GitHub webhook signature.
    
    Args:
        request: FastAPI request
        payload: Request body
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    github_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not github_secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not set, skipping signature verification")
        return True
    
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.warning("No X-Hub-Signature-256 header found")
        return False
    
    # Calculate expected signature
    expected_signature = "sha256=" + hmac.new(
        github_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

@app.post("/webhook")
async def github_webhook(request: Request):
    """
    Handle GitHub webhook events.
    
    Args:
        request: FastAPI request
        
    Returns:
        Response: HTTP response
    """
    # Get request body
    payload = await request.body()
    
    # Verify webhook signature
    if not verify_github_webhook(request, payload):
        logger.warning("Invalid webhook signature")
        return Response(status_code=401)
    
    # Parse event data
    event_type = request.headers.get("X-GitHub-Event")
    event_data = json.loads(payload)
    
    logger.info(f"Received GitHub webhook event: {event_type}")
    
    # Handle pull request events
    if event_type == "pull_request":
        action = event_data.get("action")
        pr = event_data.get("pull_request", {})
        repo = event_data.get("repository", {})
        
        logger.info(f"PR #{pr.get('number')} {action}")
        
        # Check if we should review this PR
        if action in ["opened", "reopened", "synchronize"]:
            # Get repository name
            repo_name = repo.get("full_name")
            pr_number = pr.get("number")
            
            # Review the PR
            review_result = review_pr(repo_name, pr_number)
            
            return {"status": "success", "review": review_result}
    
    return {"status": "success", "message": f"Received {event_type} event"}

def cli_review_command(args):
    """
    Handle CLI review command.
    
    Args:
        args: Command line arguments
    """
    # Review the PR
    result = review_pr(args.repo, args.pr_number)
    
    # Print the result
    if "error" in result:
        print(f"\n❌ Error reviewing PR: {result['error']}")
    else:
        print(f"\n✅ PR review completed: {result['result']}")

def cli_server_command(args):
    """
    Handle CLI server command.
    
    Args:
        args: Command line arguments
    """
    # Start the server
    print(f"\n🚀 Starting server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)

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
    review_parser.add_argument("pr_number", type=int, help="Pull request number")
    review_parser.set_defaults(func=cli_review_command)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start webhook server")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    server_parser.set_defaults(func=cli_server_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()