"""
PR Review Agent

This module provides an AI-powered GitHub PR review bot that automatically reviews pull requests
when triggered by labels. The bot uses Codegen's GitHub integration and AI capabilities to provide
comprehensive code reviews with actionable feedback.
"""

import os
import logging
from typing import Optional

import modal
from fastapi import Request
from github import Github

from codegen import Codebase, CodeAgent
from codegen.extensions.events.app import CodegenApp
from codegen.extensions.github.types.events.pull_request import (
    PullRequestLabeledEvent,
    PullRequestUnlabeledEvent
)
from codegen.extensions.langchain.tools import (
    GithubViewPRTool,
    GithubCreatePRCommentTool,
    GithubCreatePRReviewCommentTool,
)
from codegen.configs.models.secrets import SecretsConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
REVIEW_LABEL = "Codegen"
SLACK_NOTIFICATION_CHANNEL = "general"  # Change to your preferred channel

# Set up the base image with required dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        "codegen>=0.18",
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
        "pygithub",
    )
)

# Initialize the Codegen app with GitHub integration
app = CodegenApp(name="github-pr-review", image=base_image)


def remove_bot_comments(event: PullRequestUnlabeledEvent) -> None:
    """Remove all comments made by the bot on a PR when the label is removed."""
    try:
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(f"{event.organization.login}/{event.repository.name}")
        pr = repo.get_pull(int(event.number))
        
        # Get all types of comments
        pr_comments = pr.get_comments()
        reviews = pr.get_reviews()
        issue_comments = pr.get_issue_comments()
        
        # Bot username to filter by
        bot_username = "codegen-team"  # Change to your bot's username
        
        # Remove PR comments
        for comment in pr_comments:
            if comment.user.login == bot_username:
                logger.info(f"Removing PR comment from {comment.user.login}")
                comment.delete()
        
        # Remove reviews
        for review in reviews:
            if review.user.login == bot_username:
                logger.info(f"Removing review from {review.user.login}")
                review.delete()
        
        # Remove issue comments
        for comment in issue_comments:
            if comment.user.login == bot_username:
                logger.info(f"Removing issue comment from {comment.user.login}")
                comment.delete()
                
        logger.info(f"Successfully cleaned up all bot comments on PR #{event.number}")
    except Exception as e:
        logger.error(f"Error removing bot comments: {str(e)}")


def pr_review_agent(event: PullRequestLabeledEvent) -> None:
    """Run the PR review agent to analyze and comment on the PR."""
    try:
        # Initialize codebase for the repository
        repo_str = f"{event.organization.login}/{event.repository.name}"
        logger.info(f"Initializing codebase for {repo_str}")
        
        codebase = Codebase.from_repo(
            repo_str,
            language='python',  # This can be made dynamic based on repo
            secrets=SecretsConfig(github_token=os.environ["GITHUB_TOKEN"])
        )

        # Create a temporary comment to show the bot is working
        logger.info(f"Creating temporary comment on PR #{event.number}")
        review_message = "CodegenBot is starting to review the PR. Please wait..."
        comment = codebase._op.create_pr_comment(event.number, review_message)

        # Set up PR review tools
        logger.info("Setting up PR review tools")
        pr_tools = [
            GithubViewPRTool(codebase),
            GithubCreatePRCommentTool(codebase),
            GithubCreatePRReviewCommentTool(codebase),
        ]

        # Create and run the review agent
        logger.info("Creating and running the review agent")
        agent = CodeAgent(codebase=codebase, tools=pr_tools)
        
        prompt = f"""
Review this pull request like a senior engineer:
{event.pull_request.url}

Be explicit about the changes, produce a short summary, and point out possible improvements.
Focus on facts and technical details, using code snippets where helpful.
Consider:
1. Code quality and best practices
2. Potential bugs or edge cases
3. Performance implications
4. Security considerations
5. Test coverage

Use the tools at your disposal to create proper PR reviews. Include code snippets if needed,
and suggest specific improvements where appropriate.
"""
        
        # Run the agent
        logger.info("Running the agent with the review prompt")
        agent.run(prompt)
        
        # Clean up the temporary comment
        logger.info("Cleaning up temporary comment")
        comment.delete()
        
        # Optional: Send a notification to Slack
        if hasattr(app, 'slack') and hasattr(app.slack, 'client'):
            try:
                app.slack.client.chat_postMessage(
                    channel=SLACK_NOTIFICATION_CHANNEL,
                    text=f"Completed review of PR #{event.number}: {event.pull_request.title}"
                )
            except Exception as slack_error:
                logger.warning(f"Failed to send Slack notification: {str(slack_error)}")
        
        logger.info(f"Successfully completed review of PR #{event.number}")
    except Exception as e:
        logger.error(f"Error in PR review agent: {str(e)}")
        # Try to notify about the error
        try:
            if 'comment' in locals() and comment:
                comment.edit(f"Error reviewing PR: {str(e)}")
        except Exception:
            logger.error("Failed to update error message on PR comment")


@app.github.event("pull_request:labeled")
def handle_labeled(event: PullRequestLabeledEvent):
    """Handle PR labeled events."""
    logger.info(f"PR #{event.number} labeled with: {event.label.name}")
    
    if event.label.name == REVIEW_LABEL:
        logger.info(f"Starting review for PR #{event.number}: {event.pull_request.title}")
        
        # Optional: Notify Slack
        if hasattr(app, 'slack') and hasattr(app.slack, 'client'):
            try:
                app.slack.client.chat_postMessage(
                    channel=SLACK_NOTIFICATION_CHANNEL,
                    text=f"PR #{event.number} labeled with {REVIEW_LABEL}, starting review"
                )
            except Exception as slack_error:
                logger.warning(f"Failed to send Slack notification: {str(slack_error)}")
        
        # Start the review process
        pr_review_agent(event)


@app.github.event("pull_request:unlabeled")
def handle_unlabeled(event: PullRequestUnlabeledEvent):
    """Handle PR unlabeled events."""
    logger.info(f"PR #{event.number} unlabeled: {event.label.name}")
    
    if event.label.name == REVIEW_LABEL:
        logger.info(f"Removing bot comments for PR #{event.number}")
        # Clean up bot comments when label is removed
        remove_bot_comments(event)


@app.function(secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST")
def entrypoint(event: dict, request: Request):
    """Handle GitHub webhook events."""
    logger.info("Received GitHub webhook event")
    return app.github.handle(event, request)


# For local testing
if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Create a simple FastAPI app for testing
    from fastapi import FastAPI
    test_app = FastAPI()
    
    @test_app.post("/webhook")
    async def test_webhook(request: Request):
        event = await request.json()
        return app.github.handle(event, request)
    
    uvicorn.run(test_app, host="0.0.0.0", port=8000)
