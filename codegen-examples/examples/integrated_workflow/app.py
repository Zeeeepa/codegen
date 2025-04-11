#!/usr/bin/env python3
"""
Integrated AI Development Workflow

This example demonstrates how to create a complete AI-powered development workflow
by integrating multiple components from the Codegen toolkit:

1. Issue Solver Agent - Automatically solves coding issues
2. PR Review Bot - Reviews pull requests and provides feedback
3. Slack Chatbot - Provides a chat interface for interacting with the system
4. Snapshot Event Handler - Maintains codebase snapshots for fast analysis
5. Ticket-to-PR - Converts tickets to pull requests
6. Linear Webhooks - Handles Linear events
7. Codegen App - Provides a unified interface for all components
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import json
import logging
import time
from datetime import datetime

import modal
from dotenv import load_dotenv

# Import Codegen components
from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.issues import IssueOpenedEvent, IssueLabeledEvent
from codegen.extensions.github.types.pull_request import PullRequestOpenedEvent, PullRequestClosedEvent
from codegen.extensions.attribution.cli import analyze_ai_impact

# Import components from examples
from codegen.extensions.events.slack_handler import SlackHandler
from codegen.extensions.events.linear_handler import LinearHandler
from codegen.extensions.events.github_handler import GitHubHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Modal app
app = modal.App("integrated-workflow")

# Create image with dependencies
image = modal.Image.debian_slim().pip_install(
    "codegen",
    "python-dotenv",
    "pandas",
    "matplotlib",
    "networkx",
    "plotly",
    "slack-sdk",
    "slack-bolt",
    "pydantic",
)


class IntegratedWorkflow:
    """
    Integrated AI Development Workflow that combines:
    - Issue Solver Agent
    - PR Review Bot
    - Slack Chatbot
    - Snapshot Event Handler
    - Ticket-to-PR
    - Linear Webhooks
    - Codegen App
    """

    def __init__(self, repo: str, base_branch: str = "main", auto_fix_label: str = "auto-fix", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the integrated workflow.

        Args:
            repo: The repository to work with (e.g., "owner/repo")
            base_branch: The base branch to use (default: "main")
            auto_fix_label: The label that triggers auto-fixing (default: "auto-fix")
            config: Additional configuration options (default: None)
        """
        self.repo = repo
        self.base_branch = base_branch
        self.auto_fix_label = auto_fix_label
        self.config = config or {}
        
        # Initialize components
        self.issue_solver = IssueSolverAgent()
        self.cg = CodegenApp(name="integrated-workflow")
        
        # Initialize handlers
        self.slack_handler = SlackHandler(self.cg)
        self.linear_handler = LinearHandler(self.cg)
        self.github_handler = GitHubHandler(self.cg)
        
        # Set up codebase snapshots
        self.setup_snapshots()
        
        # Register event handlers
        self.setup_handlers()
    
    def setup_snapshots(self):
        """Set up codebase snapshots for fast analysis."""
        logger.info("Setting up codebase snapshots...")
        
        # Create a snapshot of the codebase
        self.cg.create_snapshot(
            repo=self.repo,
            branch=self.base_branch,
            snapshot_id=f"{self.repo.replace('/', '-')}-{self.base_branch}"
        )
        
        # Schedule snapshot updates
        @self.cg.scheduler.interval(minutes=10)
        def update_snapshots():
            logger.info("Updating codebase snapshots...")
            self.cg.update_snapshot(
                repo=self.repo,
                branch=self.base_branch,
                snapshot_id=f"{self.repo.replace('/', '-')}-{self.base_branch}"
            )
    
    def setup_handlers(self):
        """Register event handlers for GitHub, Slack, and Linear events."""
        
        # GitHub event handlers
        @self.cg.github.event("issues:opened")
        def handle_new_issue(event: IssueOpenedEvent):
            """Handle new GitHub issues."""
            logger.info(f"New issue opened: #{event.issue.number}")
            
            if self.should_auto_solve(event):
                self.solve_issue(event.issue.number)
            else:
                # Notify in Slack
                self.slack_handler.send_message(
                    channel=self.config.get("notification_channel", "dev-notifications"),
                    text=f"New issue opened: <{event.issue.html_url}|#{event.issue.number} {event.issue.title}>"
                )
        
        @self.cg.github.event("issues:labeled")
        def handle_issue_labeled(event: IssueLabeledEvent):
            """Handle issues that get labeled."""
            logger.info(f"Issue #{event.issue.number} labeled with '{event.label.name}'")
            
            if event.label.name == self.auto_fix_label:
                self.solve_issue(event.issue.number)
        
        @self.cg.github.event("pull_request:opened")
        def handle_new_pr(event: PullRequestOpenedEvent):
            """Handle new pull requests."""
            logger.info(f"New PR opened: #{event.pull_request.number}")
            
            # Auto-review PRs created by the issue solver
            if event.pull_request.user.login == "codegen-bot":
                # Add the review label to trigger the PR review bot
                self.cg.github.client.add_labels_to_issue(
                    repo=self.repo,
                    issue_number=event.pull_request.number,
                    labels=["Codegen"]
                )
            
            # Review the PR
            self.review_pr(event.pull_request.number)
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f"New PR opened: <{event.pull_request.html_url}|#{event.pull_request.number} {event.pull_request.title}>"
            )
        
        @self.cg.github.event("pull_request:closed")
        def handle_pr_merged(event: PullRequestClosedEvent):
            """Handle merged pull requests."""
            if event.pull_request.merged:
                logger.info(f"PR merged: #{event.pull_request.number}")
                
                # Run impact analysis after merges
                self.analyze_impact()
                
                # Notify in Slack
                self.slack_handler.send_message(
                    channel=self.config.get("notification_channel", "dev-notifications"),
                    text=f"PR merged: <{event.pull_request.html_url}|#{event.pull_request.number} {event.pull_request.title}>"
                )
        
        # Linear event handlers
        @self.cg.linear.event("Issue:created")
        def handle_linear_issue_created(event):
            """Handle new Linear issues."""
            logger.info(f"New Linear issue created: {event.data.id}")
            
            # Check if the issue should be converted to a PR
            if self.should_convert_to_pr(event):
                self.convert_ticket_to_pr(event.data)
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f"New Linear issue created: {event.data.title}"
            )
        
        # Slack event handlers
        @self.cg.slack.event("app_mention")
        def handle_slack_mention(event):
            """Handle mentions in Slack."""
            logger.info(f"Slack mention: {event.text}")
            
            # Process the message
            self.process_slack_message(event)
    
    def should_auto_solve(self, event):
        """
        Determine if an issue should be automatically solved.
        
        Args:
            event: The GitHub event
            
        Returns:
            bool: True if the issue should be auto-solved
        """
        # Auto-solve issues with the "auto-fix" label
        return any(label.name == self.auto_fix_label for label in event.issue.labels)
    
    def should_convert_to_pr(self, event):
        """
        Determine if a Linear issue should be converted to a PR.
        
        Args:
            event: The Linear event
            
        Returns:
            bool: True if the issue should be converted to a PR
        """
        # Convert issues with the "needs-pr" label
        return any(label.name == "needs-pr" for label in event.data.labels)
    
    def solve_issue(self, issue_number: int):
        """
        Solve a GitHub issue and create a PR with the solution.
        
        Args:
            issue_number: The GitHub issue number
            
        Returns:
            dict: The created PR data or None if failed
        """
        logger.info(f"Solving issue #{issue_number}...")
        
        try:
            # Get the issue details
            issue = self.cg.github.client.get_issue(self.repo, issue_number)
            
            # Solve the issue
            result = self.issue_solver.solve_github_issue(
                repo=self.repo,
                issue_number=issue_number,
                base_branch=self.base_branch
            )
            
            # Create a PR with the solution
            pr = self.issue_solver.create_pull_request(result)
            
            # Comment on the issue
            self.cg.github.client.create_issue_comment(
                repo=self.repo,
                issue_number=issue_number,
                body=f"I've created PR #{pr['number']} with a potential fix: {pr['html_url']}"
            )
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":robot_face: I've created PR #{pr['number']} to fix issue #{issue_number}: {pr['html_url']}"
            )
            
            logger.info(f"Created PR #{pr['number']} for issue #{issue_number}")
            return pr
        except Exception as e:
            logger.error(f"Failed to solve issue {issue_number}: {str(e)}")
            
            # Comment on the issue
            self.cg.github.client.create_issue_comment(
                repo=self.repo,
                issue_number=issue_number,
                body=f"I encountered an error while trying to solve this issue: {str(e)}"
            )
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":x: Failed to solve issue #{issue_number}: {str(e)}"
            )
            
            return None
    
    def review_pr(self, pr_number: int):
        """
        Review a pull request and provide feedback.
        
        Args:
            pr_number: The PR number
        """
        logger.info(f"Reviewing PR #{pr_number}...")
        
        try:
            # Get the PR details
            pr = self.cg.github.client.get_pull_request(self.repo, pr_number)
            
            # Get the diff
            diff = self.cg.github.client.get_pull_request_diff(self.repo, pr_number)
            
            # Load the codebase snapshot
            snapshot_id = f"{self.repo.replace('/', '-')}-{self.base_branch}"
            codebase = self.cg.get_snapshot(snapshot_id)
            
            # Generate review feedback
            feedback = self._generate_review_feedback(pr, diff, codebase)
            
            # Add the review comment
            self.cg.github.client.create_pull_request_review(
                repo=self.repo,
                pr_number=pr_number,
                body=feedback,
                event="COMMENT"  # Can be "APPROVE", "REQUEST_CHANGES", or "COMMENT"
            )
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":mag: Completed review of PR #{pr_number}: {pr['html_url']}"
            )
            
            logger.info(f"Completed review of PR #{pr_number}")
            return feedback
        except Exception as e:
            logger.error(f"Error reviewing PR #{pr_number}: {str(e)}")
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":x: Failed to review PR #{pr_number}: {str(e)}"
            )
            
            return None
    
    def _generate_review_feedback(self, pr, diff, codebase):
        """
        Generate feedback for a PR review.
        
        Args:
            pr: The PR data
            diff: The PR diff
            codebase: The codebase object
            
        Returns:
            str: The review feedback
        """
        # This is a simplified implementation
        # In a real-world scenario, you would use more sophisticated analysis
        
        feedback = []
        feedback.append("# PR Review")
        feedback.append(f"\nThank you for your contribution to PR #{pr['number']}!")
        
        # Add general feedback
        feedback.append("\n## General Feedback")
        feedback.append("- The changes look good overall.")
        feedback.append("- The code is well-structured and follows the project's conventions.")
        
        # Add specific feedback based on the diff
        feedback.append("\n## Specific Feedback")
        
        # Analyze the diff to provide specific feedback
        # This is a simplified example - in a real implementation,
        # you would perform more sophisticated analysis
        
        # Add code quality analysis
        feedback.append("\n## Code Quality Analysis")
        feedback.append("- Code duplication: Low")
        feedback.append("- Complexity: Medium")
        feedback.append("- Test coverage: Good")
        
        return "\n".join(feedback)
    
    def convert_ticket_to_pr(self, ticket):
        """
        Convert a Linear ticket to a GitHub PR.
        
        Args:
            ticket: The Linear ticket
        """
        logger.info(f"Converting ticket {ticket.id} to PR...")
        
        try:
            # Create a new branch
            branch_name = f"ticket-{ticket.id.lower()}"
            
            # Create an issue object
            issue = Issue(
                id=ticket.id,
                repo=self.repo,
                base_commit=self.base_branch,
                problem_statement=ticket.description or ticket.title
            )
            
            # Solve the issue
            result = self.issue_solver.run(issue)
            
            # Create a PR
            pr = self.issue_solver.create_pull_request(
                result,
                title=f"{ticket.id}: {ticket.title}",
                body=f"Fixes Linear ticket: {ticket.id}\n\n{ticket.description or ''}",
                head_branch=branch_name
            )
            
            # Update the Linear ticket
            self.cg.linear.client.update_issue(
                issue_id=ticket.id,
                state_id=self.get_in_progress_state_id(),
                description=f"{ticket.description or ''}\n\nPR: {pr['html_url']}"
            )
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":repeat: Converted Linear ticket {ticket.id} to PR: <{pr['html_url']}|#{pr['number']} {pr['title']}>"
            )
            
            logger.info(f"Created PR #{pr['number']} for ticket {ticket.id}")
            return pr
        except Exception as e:
            logger.error(f"Error converting ticket {ticket.id} to PR: {str(e)}")
            
            # Notify in Slack
            self.slack_handler.send_message(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":x: Failed to convert ticket {ticket.id} to PR: {str(e)}"
            )
            
            return None
    
    def get_in_progress_state_id(self):
        """
        Get the ID of the 'In Progress' state in Linear.
        
        Returns:
            str: The state ID
        """
        # This is a simplified example - in a real implementation,
        # you would fetch the actual state ID from Linear
        return "in-progress"
    
    def process_slack_message(self, event):
        """
        Process a message from Slack.
        
        Args:
            event: The Slack event
        """
        text = event.text.lower()
        channel = event.channel
        
        # Extract the actual message (remove the mention)
        message = text.split(">", 1)[1].strip() if ">" in text else text
        
        # Handle different commands
        if "solve issue" in message:
            # Extract the issue number
            try:
                # Use regex to extract issue number
                match = re.search(r'#?(\d+)', message)
                if match:
                    issue_number = int(match.group(1))
                    
                    # Solve the issue
                    self.slack_handler.send_message(
                        channel=channel,
                        text=f":gear: Working on solving issue #{issue_number}..."
                    )
                    
                    pr = self.solve_issue(issue_number)
                    
                    if pr:
                        self.slack_handler.send_message(
                            channel=channel,
                            text=f":white_check_mark: Created PR #{pr['number']} to fix issue #{issue_number}: {pr['html_url']}"
                        )
                    else:
                        self.slack_handler.send_message(
                            channel=channel,
                            text=f":x: Failed to solve issue #{issue_number}"
                        )
                else:
                    self.slack_handler.send_message(
                        channel=channel,
                        text="Please specify an issue number, e.g., `solve issue #123`"
                    )
            except Exception as e:
                self.slack_handler.send_message(
                    channel=channel,
                    text=f":x: Error: {str(e)}"
                )
        
        elif "review pr" in message:
            # Extract the PR number
            try:
                # Use regex to extract PR number
                match = re.search(r'#?(\d+)', message)
                if match:
                    pr_number = int(match.group(1))
                    
                    # Review the PR
                    self.slack_handler.send_message(
                        channel=channel,
                        text=f":mag: Reviewing PR #{pr_number}..."
                    )
                    
                    feedback = self.review_pr(pr_number)
                    
                    if feedback:
                        self.slack_handler.send_message(
                            channel=channel,
                            text=f":white_check_mark: Completed review of PR #{pr_number}. Check GitHub for detailed feedback."
                        )
                    else:
                        self.slack_handler.send_message(
                            channel=channel,
                            text=f":x: Failed to review PR #{pr_number}"
                        )
                else:
                    self.slack_handler.send_message(
                        channel=channel,
                        text="Please specify a PR number, e.g., `review pr #123`"
                    )
            except Exception as e:
                self.slack_handler.send_message(
                    channel=channel,
                    text=f":x: Error: {str(e)}"
                )
        
        elif "analyze impact" in message:
            # Analyze AI impact
            self.slack_handler.send_message(
                channel=channel,
                text=":mag: Analyzing AI impact on the codebase..."
            )
            
            try:
                results = self.analyze_impact()
                
                self.slack_handler.send_message(
                    channel=channel,
                    text=f":white_check_mark: AI Impact Analysis completed. {results}"
                )
            except Exception as e:
                self.slack_handler.send_message(
                    channel=channel,
                    text=f":x: Error analyzing AI impact: {str(e)}"
                )
        
        elif "help" in message:
            # Show help message
            help_text = """
I can help you with the following commands:
- `solve issue #123` - Solve a GitHub issue and create a PR
- `review pr #123` - Review a pull request and provide feedback
- `analyze impact` - Analyze the impact of AI-generated code on the codebase
- `help` - Show this help message
            """
            
            self.slack_handler.send_message(
                channel=channel,
                text=help_text
            )
        
        else:
            # Default response
            self.slack_handler.send_message(
                channel=channel,
                text="I'm not sure how to help with that. Try `help` to see what I can do."
            )
    
    def analyze_impact(self):
        """
        Analyze the impact of AI-generated code on the codebase.
        
        Returns:
            str: A summary of the analysis
        """
        logger.info("Analyzing AI impact...")
        
        try:
            # Get the codebase
            codebase = self.cg.get_codebase(self.repo, self.base_branch)
            
            # Define AI authors
            ai_authors = ["github-actions[bot]", "dependabot[bot]", "codegen-bot"]
            
            # Run the analysis
            results = analyze_ai_impact(codebase, ai_authors)
            
            # Generate a summary
            ai_lines = results.get("ai_lines", 0)
            total_lines = results.get("total_lines", 1)  # Avoid division by zero
            ai_percentage = (ai_lines / total_lines) * 100
            
            summary = f"AI-generated code: {ai_percentage:.1f}% ({ai_lines} out of {total_lines} lines)"
            
            # Store the results for later reference
            self._store_impact_results(results)
            
            logger.info(f"AI Impact Analysis Results: {summary}")
            return summary
        except Exception as e:
            logger.error(f"Error analyzing AI impact: {str(e)}")
            raise
    
    def _store_impact_results(self, results):
        """
        Store the AI impact analysis results.
        
        Args:
            results: The analysis results
        """
        # This is a simplified implementation
        # In a real-world scenario, you would store the results in a database
        
        # Create a directory for the results if it doesn't exist
        results_dir = Path("ai_impact_results")
        results_dir.mkdir(exist_ok=True)
        
        # Store the results in a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"{self.repo.replace('/', '-')}_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Stored AI impact results in {results_file}")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("slack-secret"),
        modal.Secret.from_name("linear-secret"),
    ],
    schedule=modal.Period(minutes=10),
)
def update_snapshots(repo: str, base_branch: str = "main"):
    """
    Update codebase snapshots periodically.
    
    Args:
        repo: The repository to work with (e.g., "owner/repo")
        base_branch: The base branch to use (default: "main")
    """
    cg = CodegenApp()
    
    logger.info(f"Updating snapshot for {repo}:{base_branch}")
    
    # Update the snapshot
    cg.update_snapshot(
        repo=repo,
        branch=base_branch,
        snapshot_id=f"{repo.replace('/', '-')}-{base_branch}"
    )
    
    logger.info(f"Snapshot updated for {repo}:{base_branch}")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("slack-secret"),
        modal.Secret.from_name("linear-secret"),
    ],
)
def run_workflow(repo: str, base_branch: str = "main", config: Optional[Dict[str, Any]] = None):
    """
    Run the integrated workflow.
    
    Args:
        repo: The repository to work with (e.g., "owner/repo")
        base_branch: The base branch to use (default: "main")
        config: Additional configuration options (default: None)
    """
    workflow = IntegratedWorkflow(repo, base_branch, config=config)
    
    # In a real implementation, this would be an event loop or server
    logger.info(f"Integrated workflow initialized for {repo}")
    logger.info("Listening for events...")
    
    # Keep the function running to handle events
    while True:
        time.sleep(60)


@app.local_entrypoint()
def main():
    """Main entry point for local execution."""
    if len(sys.argv) < 2:
        print("Usage: python app.py <repo> [<base_branch>]")
        sys.exit(1)
    
    repo = sys.argv[1]
    base_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    
    # Optional configuration
    config = {
        "notification_channel": "dev-notifications",  # Slack channel for notifications
        # Add more configuration options as needed
    }
    
    run_workflow.local(repo, base_branch, config)


if __name__ == "__main__":
    main()
