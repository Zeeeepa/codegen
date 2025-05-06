"""
PR Analyzer Module

This module provides the main orchestrator for PR analysis.
"""

import logging
import tempfile
import os
import subprocess
from typing import Dict, List, Any, Optional

from ..github.models import PullRequestContext
from ..github.pr_client import GitHubClient
from .rule_engine import RuleEngine
from .analysis_context import AnalysisContext, DiffContext
from ..reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class PRAnalyzer:
    """Main orchestrator for PR analysis."""
    
    def __init__(self, github_client: GitHubClient, rule_engine: RuleEngine, report_generator: ReportGenerator):
        """
        Initialize a new PR analyzer.
        
        Args:
            github_client: Client for interacting with GitHub
            rule_engine: Engine for applying analysis rules
            report_generator: Generator for analysis reports
        """
        self.github_client = github_client
        self.rule_engine = rule_engine
        self.report_generator = report_generator
        
    def analyze_pr(self, pr_number: int, repository: str) -> Dict[str, Any]:
        """
        Analyze a PR and return results.
        
        Args:
            pr_number: Number of the PR to analyze
            repository: Full name of the repository (e.g., "owner/repo")
            
        Returns:
            Analysis results as a dictionary
        """
        # Get PR data
        logger.info(f"Analyzing PR #{pr_number} in {repository}")
        pr_data = self.github_client.get_pr(pr_number, repository)
        
        # Create analysis contexts
        logger.info("Creating analysis contexts")
        base_context = self._create_analysis_context(pr_data.base)
        head_context = self._create_analysis_context(pr_data.head)
        
        # Create diff context
        logger.info("Creating diff context")
        diff_context = DiffContext(base_context, head_context)
        
        # Apply rules
        logger.info("Applying rules")
        results = self.rule_engine.apply_rules(diff_context)
        
        # Generate report
        logger.info("Generating report")
        return self.report_generator.generate_report(results, pr_data)
    
    def _create_analysis_context(self, pr_part_context) -> AnalysisContext:
        """
        Create an analysis context for a PR part.
        
        Args:
            pr_part_context: PR part context (base or head)
            
        Returns:
            Analysis context
        """
        # Clone the repository
        repo_path = self._clone_repository(pr_part_context.repo_name, pr_part_context.ref)
        
        # Create a codebase context
        from ..utils.integration import create_codebase_context
        codebase = create_codebase_context(repo_path)
        
        # Create an analysis context
        return AnalysisContext(codebase, pr_part_context)
    
    def _clone_repository(self, repo_name: str, ref: str) -> str:
        """
        Clone a repository to a temporary directory.
        
        Args:
            repo_name: Name of the repository (e.g., "owner/repo")
            ref: Reference to checkout (e.g., branch name, commit SHA)
            
        Returns:
            Path to the cloned repository
        """
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning {repo_name} ({ref}) to {temp_dir}")
        
        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", f"https://github.com/{repo_name}.git", temp_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            
            # Checkout the reference
            subprocess.run(
                ["git", "checkout", ref],
                cwd=temp_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            
            return temp_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository: {e.stderr}")
            raise
    
    def comment_on_pr(self, pr_number: int, repository: str, report: Dict[str, Any]) -> None:
        """
        Add a comment to a PR with the analysis results.
        
        Args:
            pr_number: Number of the PR to comment on
            repository: Full name of the repository (e.g., "owner/repo")
            report: Analysis report
        """
        # Convert report to markdown
        markdown = self.report_generator.format_report_as_markdown(report)
        
        # Add comment to PR
        self.github_client.comment_on_pr(pr_number, repository, markdown)

