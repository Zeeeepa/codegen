#!/usr/bin/env python3
"""
Integrated AI Development Workflow

This example demonstrates how to create a complete AI-powered development workflow
by integrating multiple components from the Codegen toolkit.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import modal
from dotenv import load_dotenv

# Import Codegen components
from codegen import Codebase
from codegen.agents.issue_solver import IssueSolverAgent, Issue
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.issues import IssueOpenedEvent
from codegen.extensions.github.types.pull_request import PullRequestOpenedEvent
from codegen.extensions.attribution.cli import analyze_ai_impact

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
)


class IntegratedWorkflow:
    """
    Integrated AI Development Workflow that combines:
    - Issue Solver Agent
    - PR Review Bot
    - Event Handlers
    - Knowledge Transfer Visualization
    """

    def __init__(self, repo: str, base_branch: str = "main"):
        """
        Initialize the integrated workflow.

        Args:
            repo: The repository to work with (e.g., "owner/repo")
            base_branch: The base branch to use (default: "main")
        """
        self.repo = repo
        self.base_branch = base_branch
        self.issue_solver = IssueSolverAgent()
        self.cg = CodegenApp()
        
        # Register event handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register event handlers for GitHub, Slack, and Linear events."""
        
        @self.cg.github.event("issues:opened")
        def handle_new_issue(event: IssueOpenedEvent):
            """Handle new GitHub issues."""
            if self.should_auto_solve(event):
                self.solve_issue(event.issue.number)
        
        @self.cg.github.event("pull_request:opened")
        def handle_new_pr(event: PullRequestOpenedEvent):
            """Handle new pull requests."""
            self.review_pr(event.pull_request.number)
        
        @self.cg.github.event("pull_request:closed")
        def handle_pr_merged(event):
            """Handle merged pull requests."""
            if event.pull_request.merged:
                # Run impact analysis after merges
                self.analyze_impact()
    
    def should_auto_solve(self, event):
        """
        Determine if an issue should be automatically solved.
        
        Args:
            event: The GitHub event
            
        Returns:
            bool: True if the issue should be auto-solved
        """
        # Auto-solve issues with the "auto-fix" label
        return any(label.name == "auto-fix" for label in event.issue.labels)
    
    def solve_issue(self, issue_number: int):
        """
        Solve a GitHub issue and create a PR with the solution.
        
        Args:
            issue_number: The GitHub issue number
        """
        print(f"Solving issue #{issue_number}...")
        
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
    
    def review_pr(self, pr_number: int):
        """
        Review a pull request and provide feedback.
        
        Args:
            pr_number: The PR number
        """
        print(f"Reviewing PR #{pr_number}...")
        
        # Get the PR details
        pr = self.cg.github.client.get_pull_request(self.repo, pr_number)
        
        # Get the diff
        diff = self.cg.github.client.get_pull_request_diff(self.repo, pr_number)
        
        # Analyze the diff
        feedback = self.analyze_pr(diff, pr)
        
        # Comment on the PR
        self.cg.github.client.create_pr_comment(
            repo=self.repo,
            pr_number=pr_number,
            body=f"## Automated Code Review\n\n{feedback}"
        )
    
    def analyze_pr(self, diff: str, pr: Dict[str, Any]) -> str:
        """
        Analyze a PR diff and generate feedback.
        
        Args:
            diff: The PR diff
            pr: The PR details
            
        Returns:
            str: The feedback
        """
        # This is a simplified version - in a real implementation,
        # you would use a more sophisticated analysis
        
        feedback = []
        
        # Check for basic issues
        if "TODO" in diff:
            feedback.append("- ⚠️ PR contains TODOs that should be addressed before merging")
        
        if "console.log" in diff:
            feedback.append("- ⚠️ PR contains console.log statements that should be removed")
        
        if "print(" in diff and ".py" in diff:
            feedback.append("- ⚠️ PR contains print statements in Python code")
        
        # Add positive feedback
        feedback.append("- ✅ Code follows project structure")
        
        if "test" in diff:
            feedback.append("- ✅ PR includes tests")
        
        # Add suggestions
        feedback.append("\n### Suggestions\n")
        feedback.append("- Consider adding more documentation for complex logic")
        feedback.append("- Ensure error handling is comprehensive")
        
        return "\n".join(feedback)
    
    def analyze_impact(self):
        """Analyze the impact of AI-generated code on the codebase."""
        print("Analyzing AI impact...")
        
        # Get the codebase
        codebase = self.cg.get_codebase()
        
        # Define AI authors
        ai_authors = ["github-actions[bot]", "dependabot[bot]", "codegen-bot"]
        
        # Run the analysis
        results = analyze_ai_impact(codebase, ai_authors)
        
        # In a real implementation, you would store or visualize the results
        print(f"AI Impact Analysis Results: {results}")


@app.function(image=image, secrets=[modal.Secret.from_name("github-secret")])
def run_workflow(repo: str, base_branch: str = "main"):
    """
    Run the integrated workflow.
    
    Args:
        repo: The repository to work with (e.g., "owner/repo")
        base_branch: The base branch to use (default: "main")
    """
    workflow = IntegratedWorkflow(repo, base_branch)
    
    # In a real implementation, this would be an event loop or server
    print(f"Integrated workflow initialized for {repo}")
    print("Listening for events...")


@app.local_entrypoint()
def main():
    """Main entry point for local execution."""
    if len(sys.argv) < 2:
        print("Usage: python app.py <repo> [<base_branch>]")
        sys.exit(1)
    
    repo = sys.argv[1]
    base_branch = sys.argv[2] if len(sys.argv) > 2 else "main"
    
    run_workflow.local(repo, base_branch)


if __name__ == "__main__":
    main()
