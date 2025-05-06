"""
PR Analyzer

Main orchestrator for the PR analysis process.
"""

import logging
from typing import Any, Dict, List, Optional

from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.git.models.pull_request_context import PullRequestContext

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.core.rule_engine import RuleEngine
from codegen_on_oss.analysis.pr_analysis.github.pr_client import PRClient
from codegen_on_oss.analysis.pr_analysis.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class PRAnalyzer:
    """
    Main orchestrator for the PR analysis process.

    This class coordinates the analysis of a pull request by:
    1. Fetching PR data from GitHub
    2. Creating an analysis context
    3. Running analysis rules
    4. Generating and posting reports
    """

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        pr_client: Optional[PRClient] = None,
        report_generator: Optional[ReportGenerator] = None,
    ):
        """
        Initialize the PR analyzer.

        Args:
            rule_engine: The rule engine to use for analysis
            pr_client: The client for interacting with GitHub PRs
            report_generator: The generator for analysis reports
        """
        self.rule_engine = rule_engine or RuleEngine()
        self.pr_client = pr_client or PRClient()
        self.report_generator = report_generator or ReportGenerator()

    def analyze_pr(self, pr_context: PullRequestContext) -> Dict[str, Any]:
        """
        Analyze a pull request and return the results.

        Args:
            pr_context: The pull request context to analyze

        Returns:
            A dictionary containing the analysis results
        """
        logger.info(f"Analyzing PR #{pr_context.number}: {pr_context.title}")

        # Create analysis context
        analysis_context = self._create_analysis_context(pr_context)

        # Run analysis rules
        analysis_results = self.rule_engine.run_rules(analysis_context)

        # Generate report
        report = self.report_generator.generate_report(analysis_context, analysis_results)

        # Post results to GitHub if configured to do so
        if analysis_context.config.get("post_to_github", False):
            self.pr_client.post_comment(pr_context.number, report)

        return {
            "pr_number": pr_context.number,
            "results": analysis_results,
            "report": report,
        }

    def _create_analysis_context(self, pr_context: PullRequestContext) -> AnalysisContext:
        """
        Create an analysis context for the given PR.

        Args:
            pr_context: The pull request context

        Returns:
            An analysis context for the PR
        """
        # Fetch PR data
        pr_data = self.pr_client.get_pr_data(pr_context.number)

        # Create base and head codebase contexts
        base_codebase = self._create_codebase_context(pr_context.base.sha)
        head_codebase = self._create_codebase_context(pr_context.head.sha)

        # Create and return analysis context
        return AnalysisContext(
            pr_context=pr_context,
            pr_data=pr_data,
            base_codebase=base_codebase,
            head_codebase=head_codebase,
            config=self._get_config(),
        )

    def _create_codebase_context(self, commit_sha: str) -> CodebaseContext:
        """
        Create a codebase context for the given commit.

        Args:
            commit_sha: The commit SHA to create a context for

        Returns:
            A codebase context for the commit
        """
        # This would be implemented to create a CodebaseContext for the given commit
        # For now, we'll return a placeholder
        raise NotImplementedError("Creating codebase context not implemented yet")

    def _get_config(self) -> Dict[str, Any]:
        """
        Get the configuration for the analysis.

        Returns:
            A dictionary containing configuration options
        """
        # This would be implemented to load configuration from a file or environment
        # For now, we'll return a default configuration
        return {
            "post_to_github": True,
            "severity_threshold": "warning",
            "max_comments": 10,
        }
