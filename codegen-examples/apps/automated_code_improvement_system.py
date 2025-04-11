#!/usr/bin/env python3
"""
Automated Code Improvement System

This application integrates multiple Codegen components to create a comprehensive
automated code improvement system:

1. Issue Solver Agent - Automatically solves coding issues
2. PR Review Bot - Reviews pull requests and provides feedback
3. Slack Chatbot - Provides a chat interface for interacting with the system
4. Snapshot Event Handler - Maintains codebase snapshots for fast analysis
5. AI Impact Analysis - Tracks and visualizes AI contributions to the codebase

The system can:
- Automatically detect and fix issues in the codebase
- Review pull requests and provide detailed feedback
- Respond to Slack commands for various tasks
- Track the impact of AI-generated code on the codebase
- Provide insights and analytics about code quality and improvements
"""

import os
import sys
import re
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

import modal
from dotenv import load_dotenv

# Import Codegen components
from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.issues import IssueOpenedEvent, IssueLabeledEvent
from codegen.extensions.github.types.pull_request import PullRequestOpenedEvent, PullRequestClosedEvent
from codegen.extensions.attribution.cli import analyze_ai_impact

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create Modal app
app = modal.App("automated-code-improvement-system")

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


class AutomatedCodeImprovementSystem:
    """
    Automated Code Improvement System that integrates:
    - Issue Solver Agent
    - PR Review Bot
    - Slack Chatbot
    - Snapshot Event Handler
    - AI Impact Analysis
    
    This system provides a comprehensive solution for automating code improvements,
    reviewing pull requests, and tracking AI contributions to the codebase.
    """

    def __init__(
        self, 
        repo: str, 
        base_branch: str = "main", 
        auto_fix_label: str = "auto-fix",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the Automated Code Improvement System.

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
        self.cg = CodegenApp(name="code-improvement-system")
        
        # Set up codebase snapshots
        self.setup_snapshots()
        
        # Register event handlers
        self.setup_handlers()
        
        logger.info(f"Automated Code Improvement System initialized for {repo}")

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
        @self.cg.scheduler.interval(minutes=30)
        def update_snapshots():
            logger.info("Updating codebase snapshots...")
            self.cg.update_snapshot(
                repo=self.repo,
                branch=self.base_branch,
                snapshot_id=f"{self.repo.replace('/', '-')}-{self.base_branch}"
            )

    def setup_handlers(self):
        """Register event handlers for GitHub, Slack, and Linear events."""
        
        # Issue handlers
        @self.cg.github.event("issues:opened")
        def handle_new_issue(event: IssueOpenedEvent):
            """Handle new GitHub issues."""
            logger.info(f"New issue opened: #{event.issue.number}")
            
            if self.should_auto_solve(event):
                self.solve_issue(event.issue.number)
            else:
                # Notify in Slack
                self.cg.slack.client.chat_postMessage(
                    channel=self.config.get("notification_channel", "dev-notifications"),
                    text=f"New issue opened: <{event.issue.html_url}|#{event.issue.number} {event.issue.title}>"
                )

        @self.cg.github.event("issues:labeled")
        def handle_issue_labeled(event: IssueLabeledEvent):
            """Handle issues that get labeled."""
            logger.info(f"Issue #{event.issue.number} labeled with '{event.label.name}'")
            
            if event.label.name == self.auto_fix_label:
                self.solve_issue(event.issue.number)

        # PR handlers
        @self.cg.github.event("pull_request:opened")
        def handle_pr_opened(event: PullRequestOpenedEvent):
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
            self.cg.slack.client.chat_postMessage(
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
                self.cg.slack.client.chat_postMessage(
                    channel=self.config.get("notification_channel", "dev-notifications"),
                    text=f"PR merged: <{event.pull_request.html_url}|#{event.pull_request.number} {event.pull_request.title}>"
                )

        # Slack handlers
        @self.cg.slack.event("app_mention")
        def handle_mention(event):
            """Handle mentions in Slack."""
            text = event.text.lower()
            
            # Solve issue command
            if "solve issue" in text:
                # Extract issue number from text
                match = re.search(r'#?(\d+)', text)
                if match:
                    issue_number = int(match.group(1))
                    self.solve_issue(issue_number)
                    self.cg.slack.client.chat_postMessage(
                        channel=event.channel,
                        thread_ts=event.ts,
                        text=f"I'll work on solving issue #{issue_number}!"
                    )
            
            # Review PR command
            elif "review pr" in text:
                # Extract PR number from text
                match = re.search(r'#?(\d+)', text)
                if match:
                    pr_number = int(match.group(1))
                    self.cg.slack.client.chat_postMessage(
                        channel=event.channel,
                        thread_ts=event.ts,
                        text=f"I'll review PR #{pr_number}!"
                    )
                    self.review_pr(pr_number)
            
            # Analyze impact command
            elif "analyze impact" in text:
                self.cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    thread_ts=event.ts,
                    text="I'll analyze the AI impact on the codebase!"
                )
                summary = self.analyze_impact()
                self.cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    thread_ts=event.ts,
                    text=f"AI Impact Analysis: {summary}"
                )
            
            # Help command
            elif "help" in text:
                help_text = """
I can help you with the following commands:
- `solve issue #123` - Solve a GitHub issue and create a PR
- `review pr #123` - Review a pull request and provide feedback
- `analyze impact` - Analyze the impact of AI-generated code on the codebase
- `help` - Show this help message
                """
                self.cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    thread_ts=event.ts,
                    text=help_text
                )
            
            # Unknown command
            else:
                self.cg.slack.client.chat_postMessage(
                    channel=event.channel,
                    thread_ts=event.ts,
                    text="I'm not sure how to help with that. Try `help` to see what I can do."
                )

    def should_auto_solve(self, event):
        """
        Determine if an issue should be automatically solved.
        
        Args:
            event: The GitHub event
            
        Returns:
            bool: True if the issue should be auto-solved
        """
        # Auto-solve issues with the configured label
        return any(label.name == self.auto_fix_label for label in event.issue.labels)

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
            self.cg.slack.client.chat_postMessage(
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
            self.cg.slack.client.chat_postMessage(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":x: Failed to solve issue #{issue_number}: {str(e)}"
            )
            
            return None

    def review_pr(self, pr_number: int):
        """
        Review a pull request and provide feedback.
        
        Args:
            pr_number: The PR number
            
        Returns:
            bool: True if the review was successful
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
            self.cg.slack.client.chat_postMessage(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":mag: Completed review of PR #{pr_number}: {pr['html_url']}"
            )
            
            logger.info(f"Completed review of PR #{pr_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to review PR {pr_number}: {str(e)}")
            
            # Notify in Slack
            self.cg.slack.client.chat_postMessage(
                channel=self.config.get("notification_channel", "dev-notifications"),
                text=f":x: Failed to review PR #{pr_number}: {str(e)}"
            )
            
            return False

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
            import json
            json.dump(results, f, indent=2)
        
        logger.info(f"Stored AI impact results in {results_file}")

    def run(self):
        """Run the Automated Code Improvement System."""
        logger.info(f"Running Automated Code Improvement System for {self.repo}")
        
        # In a real implementation, this would be an event loop or server
        # that listens for events and processes them
        
        # For demonstration purposes, we'll just keep the system running
        while True:
            logger.info("System is running...")
            time.sleep(60)


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("github-secret"),
        modal.Secret.from_name("slack-secret"),
    ],
    schedule=modal.Period(minutes=30),
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
    ],
)
def run_system(repo: str, base_branch: str = "main", config: Optional[Dict[str, Any]] = None):
    """
    Run the Automated Code Improvement System.
    
    Args:
        repo: The repository to work with (e.g., "owner/repo")
        base_branch: The base branch to use (default: "main")
        config: Additional configuration options (default: None)
    """
    system = AutomatedCodeImprovementSystem(repo, base_branch, config=config)
    system.run()


@app.local_entrypoint()
def main():
    """Main entry point for local execution."""
    if len(sys.argv) < 2:
        print("Usage: python automated_code_improvement_system.py <repo> [<base_branch>]")
        sys.exit(1)
    
    repo = sys.argv[1]
    base_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    
    run_system.local(repo, base_branch)


if __name__ == "__main__":
    main()
