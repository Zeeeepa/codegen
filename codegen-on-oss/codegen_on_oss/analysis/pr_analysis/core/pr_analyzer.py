"""
PR Analyzer Module

This module provides the PRAnalyzer class, which orchestrates the PR analysis process.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable

# Fix circular imports
from .analysis_context import AnalysisContext, AnalysisResult
from .rule_engine import RuleEngine, BaseRule

# Set up logging
logger = logging.getLogger(__name__)


class PRAnalyzer:
    """
    Main PR analysis orchestrator.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the PR analyzer.
        
        Args:
            config: Analyzer configuration
        """
        self.config = config or {}
        self.rule_engine = RuleEngine(config.get("rule_engine", {}))
        
        # Initialize dependencies
        self._init_dependencies()
    
    def _init_dependencies(self) -> None:
        """
        Initialize dependencies (Git clients, rule engine, etc.).
        """
        # This will be implemented when the Git integration is available
        # For now, we'll just log a message
        logger.info("Initializing PR analyzer dependencies")
        
        # Load rules if a rules directory is specified
        rules_dir = self.config.get("rules_dir")
        if rules_dir and os.path.isdir(rules_dir):
            self.rule_engine.load_rules_from_directory(rules_dir)
    
    def analyze_pr(
        self,
        pr_number: int,
        repo: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None
    ) -> AnalysisContext:
        """
        Analyze a specific PR in a repository.
        
        Args:
            pr_number: PR number
            repo: Repository name or URL
            base_ref: Base reference (branch or commit SHA)
            head_ref: Head reference (branch or commit SHA)
            
        Returns:
            Analysis context with results
        """
        logger.info(f"Analyzing PR #{pr_number} in repository {repo}")
        
        # Fetch PR data from Git
        # This will be implemented when the Git integration is available
        # For now, we'll create a dummy context
        context = self._create_pr_context(pr_number, repo, base_ref, head_ref)
        
        # Apply rules using the rule engine
        self.rule_engine.apply_rules(context)
        
        # Generate reports based on analysis results
        # This will be implemented when the reporting system is available
        
        return context
    
    def _create_pr_context(
        self,
        pr_number: int,
        repo: str,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None
    ) -> AnalysisContext:
        """
        Create an analysis context for a PR.
        
        Args:
            pr_number: PR number
            repo: Repository name or URL
            base_ref: Base reference (branch or commit SHA)
            head_ref: Head reference (branch or commit SHA)
            
        Returns:
            Analysis context
        """
        # This will be implemented when the Git integration is available
        # For now, we'll create a dummy context
        
        # Extract repo path and name
        repo_path = repo
        repo_name = os.path.basename(repo)
        
        # Use default refs if not provided
        base_ref = base_ref or "main"
        head_ref = head_ref or "HEAD"
        
        # Create the context
        context = AnalysisContext(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_path=repo_path,
            pr_number=pr_number,
            repo_name=repo_name
        )
        
        # Fetch changed files
        # This will be implemented when the Git integration is available
        # For now, we'll use dummy data
        context.set_changed_files([])
        
        return context
    
    def analyze_commit(
        self,
        commit_sha: str,
        repo: str,
        base_ref: Optional[str] = None
    ) -> AnalysisContext:
        """
        Analyze a specific commit.
        
        Args:
            commit_sha: Commit SHA
            repo: Repository name or URL
            base_ref: Base reference (branch or commit SHA)
            
        Returns:
            Analysis context with results
        """
        logger.info(f"Analyzing commit {commit_sha} in repository {repo}")
        
        # Use the parent commit as the base reference if not provided
        base_ref = base_ref or f"{commit_sha}^"
        
        # Create a context for the commit
        context = self._create_commit_context(commit_sha, repo, base_ref)
        
        # Apply rules using the rule engine
        self.rule_engine.apply_rules(context)
        
        # Generate reports based on analysis results
        # This will be implemented when the reporting system is available
        
        return context
    
    def _create_commit_context(
        self,
        commit_sha: str,
        repo: str,
        base_ref: str
    ) -> AnalysisContext:
        """
        Create an analysis context for a commit.
        
        Args:
            commit_sha: Commit SHA
            repo: Repository name or URL
            base_ref: Base reference (branch or commit SHA)
            
        Returns:
            Analysis context
        """
        # This will be implemented when the Git integration is available
        # For now, we'll create a dummy context
        
        # Extract repo path and name
        repo_path = repo
        repo_name = os.path.basename(repo)
        
        # Create the context
        context = AnalysisContext(
            base_ref=base_ref,
            head_ref=commit_sha,
            repo_path=repo_path,
            repo_name=repo_name
        )
        
        # Fetch changed files
        # This will be implemented when the Git integration is available
        # For now, we'll use dummy data
        context.set_changed_files([])
        
        return context
    
    def analyze_diff(
        self,
        base_ref: str,
        head_ref: str,
        repo: str
    ) -> AnalysisContext:
        """
        Analyze differences between two refs.
        
        Args:
            base_ref: Base reference (branch or commit SHA)
            head_ref: Head reference (branch or commit SHA)
            repo: Repository name or URL
            
        Returns:
            Analysis context with results
        """
        logger.info(f"Analyzing diff between {base_ref} and {head_ref} in repository {repo}")
        
        # Create a context for the diff
        context = self._create_diff_context(base_ref, head_ref, repo)
        
        # Apply rules using the rule engine
        self.rule_engine.apply_rules(context)
        
        # Generate reports based on analysis results
        # This will be implemented when the reporting system is available
        
        return context
    
    def _create_diff_context(
        self,
        base_ref: str,
        head_ref: str,
        repo: str
    ) -> AnalysisContext:
        """
        Create an analysis context for a diff.
        
        Args:
            base_ref: Base reference (branch or commit SHA)
            head_ref: Head reference (branch or commit SHA)
            repo: Repository name or URL
            
        Returns:
            Analysis context
        """
        # This will be implemented when the Git integration is available
        # For now, we'll create a dummy context
        
        # Extract repo path and name
        repo_path = repo
        repo_name = os.path.basename(repo)
        
        # Create the context
        context = AnalysisContext(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_path=repo_path,
            repo_name=repo_name
        )
        
        # Fetch changed files
        # This will be implemented when the Git integration is available
        # For now, we'll use dummy data
        context.set_changed_files([])
        
        return context
    
    def register_rule(
        self,
        rule: BaseRule,
        priority: int = 0,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """
        Register a rule with the rule engine.
        
        Args:
            rule: Rule to register
            priority: Rule priority (higher values run first)
            dependencies: List of rule IDs that this rule depends on
        """
        self.rule_engine.register_rule(rule, priority, dependencies)
    
    def get_results(self, context: AnalysisContext) -> List[AnalysisResult]:
        """
        Get all analysis results.
        
        Args:
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        return context.get_results()
    
    def get_error_count(self, context: AnalysisContext) -> int:
        """
        Get the number of errors.
        
        Args:
            context: Analysis context
            
        Returns:
            Number of error results
        """
        return context.get_error_count()
    
    def get_warning_count(self, context: AnalysisContext) -> int:
        """
        Get the number of warnings.
        
        Args:
            context: Analysis context
            
        Returns:
            Number of warning results
        """
        return context.get_warning_count()
    
    def has_errors(self, context: AnalysisContext) -> bool:
        """
        Check if there are any errors.
        
        Args:
            context: Analysis context
            
        Returns:
            True if there are errors, False otherwise
        """
        return context.has_errors()
    
    def has_warnings(self, context: AnalysisContext) -> bool:
        """
        Check if there are any warnings.
        
        Args:
            context: Analysis context
            
        Returns:
            True if there are warnings, False otherwise
        """
        return context.has_warnings()
