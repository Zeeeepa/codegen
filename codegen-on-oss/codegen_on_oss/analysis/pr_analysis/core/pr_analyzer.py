"""
PR analyzer for static analysis.

This module provides the PRAnalyzer class, which is the main orchestrator
for PR analysis. It coordinates the analysis process, including loading
repository data, applying rules, and generating reports.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.core.rule_engine import RuleEngine
from codegen_on_oss.analysis.pr_analysis.git.github_client import GitHubClient
from codegen_on_oss.analysis.pr_analysis.git.repo_operator import RepoOperator
from codegen_on_oss.analysis.pr_analysis.git.models import PullRequest, Repository
from codegen_on_oss.analysis.pr_analysis.reporting.report_generator import ReportGenerator
from codegen_on_oss.analysis.pr_analysis.utils.config_utils import load_config


logger = logging.getLogger(__name__)


class PRAnalyzer:
    """
    Main orchestrator for PR analysis.
    
    This class coordinates the analysis process, including loading repository data,
    applying rules, and generating reports.
    
    Attributes:
        config: Analysis configuration
        github_client: GitHub client
        repo_operator: Repository operator
        rule_engine: Rule engine
        report_generator: Report generator
        context: Analysis context
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the PR analyzer.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = load_config(config_path) if config_path else {}
        self.github_client = None
        self.repo_operator = None
        self.rule_engine = None
        self.report_generator = None
        self.context = None
    
    def initialize(self, repo_url: str, pr_number: int) -> None:
        """
        Initialize the analyzer with repository and PR information.
        
        Args:
            repo_url: Repository URL
            pr_number: Pull request number
        """
        logger.info(f"Initializing PR analyzer for {repo_url} PR #{pr_number}")
        
        # Initialize GitHub client
        self.github_client = GitHubClient(
            token=self.config.get('github', {}).get('token'),
            api_url=self.config.get('github', {}).get('api_url')
        )
        
        # Get repository and PR data
        repository = self.github_client.get_repository(repo_url)
        pull_request = self.github_client.get_pull_request(repository, pr_number)
        
        # Initialize repository operator
        self.repo_operator = RepoOperator(repository, self.config.get('git', {}))
        
        # Create analysis context
        self.context = AnalysisContext(
            repository=repository,
            pull_request=pull_request,
            config=self.config
        )
        
        # Initialize rule engine and report generator
        self.rule_engine = RuleEngine(self.context)
        self.report_generator = ReportGenerator(self.context)
        
        # Load rules from configuration
        if 'rules' in self.config:
            self.rule_engine.load_rules_from_config(self.config['rules'])
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the pull request.
        
        Returns:
            Analysis results
            
        Raises:
            RuntimeError: If the analyzer is not initialized
        """
        if not self.context:
            raise RuntimeError("PR analyzer is not initialized")
        
        logger.info(f"Analyzing PR #{self.context.pull_request.number} in {self.context.repository.full_name}")
        
        # Clone or update repository
        self.repo_operator.prepare_repository()
        
        # Checkout PR branch
        self.repo_operator.checkout_pull_request(self.context.pull_request)
        
        # Run all rules
        rule_results = self.rule_engine.run_all_rules()
        
        # Generate report
        report = self.report_generator.generate_report(rule_results)
        
        return {
            'rule_results': rule_results,
            'report': report
        }
    
    def post_results(self, results: Dict[str, Any]) -> None:
        """
        Post analysis results to GitHub.
        
        Args:
            results: Analysis results
            
        Raises:
            RuntimeError: If the analyzer is not initialized
        """
        if not self.context or not self.github_client:
            raise RuntimeError("PR analyzer is not initialized")
        
        logger.info(f"Posting analysis results for PR #{self.context.pull_request.number}")
        
        # Format report for GitHub comment
        report_markdown = self.report_generator.format_report_for_github(results['report'])
        
        # Post comment to PR
        self.github_client.post_pr_comment(
            self.context.repository,
            self.context.pull_request,
            report_markdown
        )
    
    def run(self, repo_url: str, pr_number: int) -> Dict[str, Any]:
        """
        Run the complete analysis process.
        
        Args:
            repo_url: Repository URL
            pr_number: Pull request number
            
        Returns:
            Analysis results
        """
        self.initialize(repo_url, pr_number)
        results = self.analyze()
        self.post_results(results)
        return results

