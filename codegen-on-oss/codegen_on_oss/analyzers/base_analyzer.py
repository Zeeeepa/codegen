#!/usr/bin/env python3
"""
Base Analyzer Module

This module provides the foundation for all code analyzers in the system.
It defines a common interface and shared functionality for codebase analysis.
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, TypeVar, cast
from abc import ABC, abstractmethod

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    
    # Import from our own modules
    from codegen_on_oss.context_codebase import CodebaseContext, get_node_classes, GLOBAL_FILE_IGNORE_LIST
    from codegen_on_oss.current_code_codebase import get_selected_codebase
    from codegen_on_oss.analyzers.issue_types import Issue, IssueSeverity, AnalysisType, IssueCategory
except ImportError:
    print("Codegen SDK or required modules not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class BaseCodeAnalyzer(ABC):
    """
    Base class for all code analyzers.
    
    This abstract class defines the common interface and shared functionality
    for all code analyzers in the system. Specific analyzers should inherit
    from this class and implement the abstract methods.
    """
    
    def __init__(
        self,
        repo_url: Optional[str] = None,
        repo_path: Optional[str] = None,
        base_branch: str = "main",
        pr_number: Optional[int] = None,
        language: Optional[str] = None,
        file_ignore_list: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base analyzer.
        
        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            base_branch: Base branch for comparison
            pr_number: PR number to analyze
            language: Programming language of the codebase
            file_ignore_list: List of file patterns to ignore
            config: Additional configuration options
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.base_branch = base_branch
        self.pr_number = pr_number
        self.language = language
        
        # Use custom ignore list or default global list
        self.file_ignore_list = file_ignore_list or GLOBAL_FILE_IGNORE_LIST
        
        # Configuration options
        self.config = config or {}
        
        # Codebase and context objects
        self.base_codebase = None
        self.pr_codebase = None
        self.base_context = None
        self.pr_context = None
        
        # Analysis results
        self.issues: List[Issue] = []
        self.results: Dict[str, Any] = {}
        
        # PR comparison data
        self.pr_diff = None
        self.commit_shas = None
        self.modified_symbols = None
        self.pr_branch = None
        
        # Initialize codebase(s) based on provided parameters
        if repo_url:
            self._init_from_url(repo_url, language)
        elif repo_path:
            self._init_from_path(repo_path, language)
        
        # If PR number is provided, initialize PR-specific data
        if self.pr_number is not None and self.base_codebase is not None:
            self._init_pr_data(self.pr_number)
        
        # Initialize contexts
        self._init_contexts()
    
    def _init_from_url(self, repo_url: str, language: Optional[str] = None):
        """
        Initialize codebase from a repository URL.
        
        Args:
            repo_url: URL of the repository
            language: Programming language of the codebase
        """
        try:
            # Extract repository information
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            parts = repo_url.rstrip('/').split('/')
            repo_name = parts[-1]
            owner = parts[-2]
            repo_full_name = f"{owner}/{repo_name}"
            
            # Create temporary directory for cloning
            tmp_dir = tempfile.mkdtemp(prefix="analyzer_")
            
            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_url}")
            
            self.base_codebase = Codebase.from_github(
                repo_full_name=repo_full_name,
                tmp_dir=tmp_dir,
                language=prog_lang,
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_url}")
            
        except Exception as e:
            logger.error(f"Error initializing codebase from URL: {e}")
            raise
    
    def _init_from_path(self, repo_path: str, language: Optional[str] = None):
        """
        Initialize codebase from a local repository path.
        
        Args:
            repo_path: Path to the repository
            language: Programming language of the codebase
        """
        try:
            # Set up configuration
            config = CodebaseConfig(
                debug=False,
                allow_external=True,
                py_resolve_syspath=True,
            )
            
            secrets = SecretsConfig()
            
            # Initialize the codebase
            logger.info(f"Initializing codebase from {repo_path}")
            
            # Determine programming language
            prog_lang = None
            if language:
                prog_lang = ProgrammingLanguage(language.upper())
            
            # Set up repository configuration
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_config.respect_gitignore = False
            repo_operator = RepoOperator(repo_config=repo_config, bot_commit=False)
            
            # Create project configuration
            project_config = ProjectConfig(
                repo_operator=repo_operator,
                programming_language=prog_lang if prog_lang else None
            )
            
            # Initialize codebase
            self.base_codebase = Codebase(
                projects=[project_config],
                config=config,
                secrets=secrets
            )
            
            logger.info(f"Successfully initialized codebase from {repo_path}")
            
        except Exception as e:
            logger.error(f"Error initializing codebase from path: {e}")
            raise
    
    def _init_pr_data(self, pr_number: int):
        """
        Initialize PR-specific data.
        
        Args:
            pr_number: PR number to analyze
        """
        try:
            logger.info(f"Fetching PR #{pr_number} data")
            result = self.base_codebase.get_modified_symbols_in_pr(pr_number)
            
            # Unpack the result tuple
            if len(result) >= 3:
                self.pr_diff, self.commit_shas, self.modified_symbols = result[:3]
                if len(result) >= 4:
                    self.pr_branch = result[3]
                
            logger.info(f"Found {len(self.modified_symbols)} modified symbols in PR")
            
            # Initialize PR codebase
            self._init_pr_codebase()
            
        except Exception as e:
            logger.error(f"Error initializing PR data: {e}")
            raise
    
    def _init_pr_codebase(self):
        """Initialize PR codebase by checking out the PR branch."""
        if not self.base_codebase or not self.pr_number:
            logger.error("Base codebase or PR number not initialized")
            return
            
        try:
            # Get PR data if not already fetched
            if not self.pr_branch:
                self._init_pr_data(self.pr_number)
                
            if not self.pr_branch:
                logger.error("Failed to get PR branch")
                return
                
            # Clone the base codebase
            self.pr_codebase = self.base_codebase
                
            # Checkout PR branch
            logger.info(f"Checking out PR branch: {self.pr_branch}")
            self.pr_codebase.checkout(self.pr_branch)
            
            logger.info("Successfully initialized PR codebase")
                
        except Exception as e:
            logger.error(f"Error initializing PR codebase: {e}")
            raise
    
    def _init_contexts(self):
        """Initialize CodebaseContext objects for both base and PR codebases."""
        if self.base_codebase:
            try:
                self.base_context = CodebaseContext(
                    codebase=self.base_codebase,
                    base_path=self.repo_path,
                    pr_branch=None,
                    base_branch=self.base_branch
                )
                logger.info("Successfully initialized base context")
            except Exception as e:
                logger.error(f"Error initializing base context: {e}")
        
        if self.pr_codebase:
            try:
                self.pr_context = CodebaseContext(
                    codebase=self.pr_codebase,
                    base_path=self.repo_path,
                    pr_branch=self.pr_branch,
                    base_branch=self.base_branch
                )
                logger.info("Successfully initialized PR context")
            except Exception as e:
                logger.error(f"Error initializing PR context: {e}")
    
    def add_issue(self, issue: Issue):
        """
        Add an issue to the list of detected issues.
        
        Args:
            issue: Issue to add
        """
        self.issues.append(issue)
    
    def get_issues(self, severity: Optional[IssueSeverity] = None, category: Optional[IssueCategory] = None) -> List[Issue]:
        """
        Get all issues matching the specified criteria.
        
        Args:
            severity: Optional severity level to filter by
            category: Optional category to filter by
            
        Returns:
            List of matching issues
        """
        filtered_issues = self.issues
        
        if severity:
            filtered_issues = [i for i in filtered_issues if i.severity == severity]
        
        if category:
            filtered_issues = [i for i in filtered_issues if i.category == category]
        
        return filtered_issues
    
    def save_results(self, output_file: str):
        """
        Save analysis results to a file.
        
        Args:
            output_file: Path to the output file
        """
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Results saved to {output_file}")
    
    @abstractmethod
    def analyze(self, analysis_type: AnalysisType) -> Dict[str, Any]:
        """
        Perform analysis on the codebase.
        
        Args:
            analysis_type: Type of analysis to perform
            
        Returns:
            Dictionary containing analysis results
        """
        pass