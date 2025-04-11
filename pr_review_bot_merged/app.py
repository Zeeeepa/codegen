#!/usr/bin/env python3
"""
PR Review Bot - A simple, locally hostable PR review bot using codegen libraries.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv
from github import Github
from fastapi import FastAPI, Request, Response
import uvicorn
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

def get_github_client():
    """Get GitHub client using token from environment variables."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("No GitHub token found. Set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    return Github(github_token)

def get_codebase(repo_str):
    """Get Codebase instance for the specified repository."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("No GitHub token found. Set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    return Codebase.from_repo(
        repo_str, 
        language="python", 
        secrets=SecretsConfig(github_token=github_token)
    )

def review_pr(repo_str, pr_number):
    """Review a pull request using CodeAgent."""
    try:
        # Get codebase
        codebase = get_codebase(repo_str)
        
        # Create notification comment
        review_notification_message = "PR Review Bot is starting to review the PR. Please wait..."
        comment = codebase._op.create_pr_comment(pr_number, review_notification_message)
        
        # Define tools
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
        
        Please review this pull request: {repo_str}/pull/{pr_number}
        
        Be explicit about the changes, produce a short summary, and point out possible improvements.
        Use the tools at your disposal to create proper PR reviews.
        Include code snippets if needed, and suggest improvements if necessary.
        """
        
        # Run the agent
        agent.run(prompt)
        
        # Delete notification comment
        comment.delete()
        
        return True
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        return False

def remove_bot_comments(repo_str, pr_number):
    """Remove all comments made by the bot on a PR."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_str)
        pr = repo.get_pull(int(pr_number))
        
        # Remove PR comments
        comments = pr.get_comments()
        if comments:
            for comment in comments:
                if comment.user.login == "codegen-team":
                    comment.delete()
        
        # Remove reviews
        reviews = pr.get_reviews()
        if reviews:
            for review in reviews:
                if review.user.login == "codegen-team":
                    review.delete()
        
        # Remove issue comments
        issue_comments = pr.get_issue_comments()
        if issue_comments:
            for comment in issue_comments:
                if comment.user.login == "codegen-team":
                    comment.delete()
        
        return True
    except Exception as e:
        logger.error(f"Error removing bot comments: {e}")
        return False

@app.post("/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    logger.info(f"Received GitHub webhook: {event_type}")
    
    if event_type == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        
        if not repo_name or not pr_number:
            return Response(status_code=400, content="Invalid payload")
        
        logger.info(f"PR #{pr_number} {action} in {repo_name}")
        
        # Check for label events
        if action == "labeled":
            label_name = payload.get("label", {}).get("name")
            if label_name == "review":
                logger.info(f"Starting review for PR #{pr_number}")
                review_pr(repo_name, pr_number)
        
        elif action == "unlabeled":
            label_name = payload.get("label", {}).get("name")
            if label_name == "review":
                logger.info(f"Removing bot comments for PR #{pr_number}")
                remove_bot_comments(repo_name, pr_number)
    
    return Response(status_code=200)

def review_pr_cli(repo, pr_number):
    """CLI command to review a PR."""
    logger.info(f"Starting review for PR #{pr_number} in {repo}")
    success = review_pr(repo, pr_number)
    if success:
        logger.info(f"Successfully reviewed PR #{pr_number}")
    else:
        logger.error(f"Failed to review PR #{pr_number}")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="PR Review Bot")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Review command
    review_parser = subparsers.add_parser("review", help="Review a PR")
    review_parser.add_argument("repo", help="Repository name (e.g., 'owner/repo')")
    review_parser.add_argument("pr", type=int, help="PR number to review")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start webhook server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    if args.command == "review":
        review_pr_cli(args.repo, args.pr)
    elif args.command == "server":
        logger.info(f"Starting server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()