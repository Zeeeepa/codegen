#!/usr/bin/env python3
"""
PR Review Bot - Simple implementation using codegen libraries
"""

import os
import sys
import logging
from logging import getLogger
import argparse
from github import Github
from dotenv import load_dotenv

from codegen import Codebase
from codegen import CodeAgent
from codegen.configs.models.secrets import SecretsConfig
from codegen.extensions.langchain.tools import (
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

# Load environment variables
load_dotenv()

def review_pr(repo_name, pr_number):
    """
    Review a pull request using codegen libraries.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        pr_number: Pull request number
    """
    logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
    
    # Initialize Codebase with GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        return False
    
    try:
        # Create codebase from repo
        codebase = Codebase.from_repo(
            repo_name, 
            language="python",  # Default to Python, could be made dynamic
            secrets=SecretsConfig(github_token=github_token)
        )
        
        # Create a temporary comment to indicate the review is in progress
        review_attention_message = "CodegenBot is starting to review the PR, please wait..."
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
        Hey CodegenBot!

        Here's a task for you. Please review this pull request!
        https://github.com/{repo_name}/pull/{pr_number}
        
        Do not terminate until you have reviewed the pull request and are satisfied with your review.

        Review this Pull request like a senior engineer:
        - Be explicit about the changes
        - Produce a short summary
        - Point out possible improvements where present
        - Don't be self-congratulatory, stick to the facts
        - Use the tools at your disposal to create proper PR reviews
        - Include code snippets if needed
        - Suggest improvements if you feel it's necessary
        """
        
        # Run the agent
        agent.run(prompt)
        
        # Delete the temporary comment
        if comment:
            comment.delete()
        
        return True
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def list_open_prs(repo_name):
    """
    List all open PRs in a repository.
    
    Args:
        repo_name: Repository name in format "owner/repo"
    """
    logger.info(f"Listing open PRs in {repo_name}")
    
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        return []
    
    try:
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        open_prs = list(repo.get_pulls(state="open"))
        
        if not open_prs:
            print(f"\nNo open PRs found in {repo_name}")
            return []
        
        print(f"\nFound {len(open_prs)} open PRs in {repo_name}:")
        for i, pr in enumerate(open_prs, 1):
            print(f"{i}. #{pr.number}: {pr.title} by {pr.user.login}")
        
        return open_prs
    except Exception as e:
        logger.error(f"Error listing PRs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def main():
    """
    Main entry point for the PR Review Bot.
    """
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--repo", type=str, help="Repository name in format 'owner/repo'")
    parser.add_argument("--pr", type=int, help="Pull request number to review")
    parser.add_argument("--list", action="store_true", help="List open PRs in the repository")
    parser.add_argument("--review-all", action="store_true", help="Review all open PRs in the repository")
    
    args = parser.parse_args()
    
    # Check if GitHub token is set
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        print("Please create a .env file with your GitHub token")
        print("Example: GITHUB_TOKEN=ghp_your_token_here")
        return 1
    
    # Check if any AI API keys are set
    has_ai_key = (
        os.environ.get("ANTHROPIC_API_KEY") or 
        os.environ.get("OPENAI_API_KEY")
    )
    
    if not has_ai_key:
        logger.warning("No AI API keys found, code review will be limited")
        print("\n⚠️ No AI API keys found, code review will be limited")
        print("For best results, set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file")
    
    # If no arguments are provided, show help
    if not (args.repo or args.pr or args.list or args.review_all):
        parser.print_help()
        return 1
    
    # If repo is not provided, prompt for it
    repo_name = args.repo
    if not repo_name:
        repo_name = input("Enter repository name (owner/repo): ")
    
    # List open PRs if requested
    if args.list:
        list_open_prs(repo_name)
        return 0
    
    # Review all open PRs if requested
    if args.review_all:
        open_prs = list_open_prs(repo_name)
        if not open_prs:
            return 0
        
        for pr in open_prs:
            print(f"\n🔍 Reviewing PR #{pr.number}: {pr.title}")
            review_pr(repo_name, pr.number)
        
        return 0
    
    # Review a specific PR if requested
    if args.pr:
        pr_number = args.pr
        review_pr(repo_name, pr_number)
        return 0
    
    # If PR is not provided but repo is, prompt for PR number
    if repo_name:
        open_prs = list_open_prs(repo_name)
        if not open_prs:
            return 0
        
        pr_index = input(f"\nEnter PR number to review (1-{len(open_prs)}): ")
        try:
            pr_index = int(pr_index) - 1
            if 0 <= pr_index < len(open_prs):
                pr = open_prs[pr_index]
                print(f"\n🔍 Reviewing PR #{pr.number}: {pr.title}")
                review_pr(repo_name, pr.number)
            else:
                print(f"Invalid PR index: {pr_index + 1}")
        except ValueError:
            print(f"Invalid input: {pr_index}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())