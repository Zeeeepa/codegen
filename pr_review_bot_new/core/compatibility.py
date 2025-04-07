"""
Compatibility layer for the PR Review Bot.
Provides compatibility with optional dependencies.
"""

import os
import sys
import logging
import importlib.util
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Union

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
U = TypeVar('U')

def is_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        True if the package is installed, False otherwise
    """
    return importlib.util.find_spec(package_name) is not None

def import_optional(
    module_path: str, 
    fallback: Optional[Any] = None, 
    warning_message: Optional[str] = None
) -> Any:
    """
    Import an optional module, with a fallback if not available.
    
    Args:
        module_path: Full import path of the module
        fallback: Value to return if import fails
        warning_message: Custom warning message to log if import fails
        
    Returns:
        Imported module or fallback value
    """
    try:
        module_parts = module_path.split('.')
        if len(module_parts) == 1:
            return __import__(module_path)
        
        base_module = __import__(module_path, fromlist=[module_parts[-1]])
        return getattr(base_module, module_parts[-1])
    except (ImportError, AttributeError) as e:
        if warning_message:
            logger.warning(warning_message)
        else:
            logger.warning(f"Could not import {module_path}, using fallback")
        
        return fallback

# Check for codegen SDK
HAS_CODEGEN = is_package_installed("codegen.sdk")
if not HAS_CODEGEN:
    logger.warning("Could not import codegen.sdk, using mock implementation")

# Check for agentgen
HAS_AGENTGEN = is_package_installed("agentgen.agents")
if not HAS_AGENTGEN:
    logger.warning("Could not import agentgen.agents, AI review will be limited")

# Check for LangChain
HAS_LANGCHAIN = is_package_installed("langchain_core")
if not HAS_LANGCHAIN:
    logger.warning("Could not import langchain_core, AI review will be limited")

# Import or create mock implementations
class MockCodebase:
    """
    Mock implementation of the Codebase class from codegen.sdk.core.codebase.
    Provides basic functionality for PR review operations.
    """
    
    def __init__(self, repo_path: str, language: str = "python"):
        """
        Initialize the mock codebase.
        
        Args:
            repo_path: Repository path in format "owner/repo"
            language: Programming language of the codebase
        """
        self.repo_path = repo_path
        self.language = language
        self.repo_operator = MockRepoOperator(repo_path)

class MockRepoOperator:
    """
    Mock implementation of the RepoOperator class.
    Provides basic functionality for PR operations.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize the mock repo operator.
        
        Args:
            repo_path: Repository path in format "owner/repo"
        """
        self.repo_path = repo_path
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
        
        # Import GitHub only when needed
        from github import Github
        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(repo_path)
    
    def create_pr_comment(self, pr_number: int, comment: str):
        """
        Create a comment on a pull request.
        
        Args:
            pr_number: Pull request number
            comment: Comment text
            
        Returns:
            Created comment
        """
        pr = self.repo.get_pull(pr_number)
        return pr.create_issue_comment(comment)
    
    def get_pr(self, pr_number: int):
        """
        Get a pull request.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Pull request
        """
        return self.repo.get_pull(pr_number)
    
    def merge_pr(self, pr_number: int, commit_title: str, commit_message: str, merge_method: str = "merge"):
        """
        Merge a pull request.
        
        Args:
            pr_number: Pull request number
            commit_title: Commit title
            commit_message: Commit message
            merge_method: Merge method
            
        Returns:
            Merge result
        """
        pr = self.repo.get_pull(pr_number)
        return pr.merge(
            commit_title=commit_title,
            commit_message=commit_message,
            merge_method=merge_method
        )

# Import or use mock implementations
Codebase = import_optional(
    "codegen.sdk.core.codebase.Codebase", 
    MockCodebase,
    "Could not import codegen.sdk.core.codebase.Codebase, using mock implementation"
)

CodeAgent = import_optional(
    "agentgen.agents.code_agent.CodeAgent",
    None,
    "Could not import agentgen.agents.code_agent.CodeAgent, AI review will be limited"
)

GithubViewPRTool = import_optional(
    "agentgen.extensions.langchain.tools.GithubViewPRTool",
    None
)

GithubCreatePRCommentTool = import_optional(
    "agentgen.extensions.langchain.tools.GithubCreatePRCommentTool",
    None
)

GithubCreatePRReviewCommentTool = import_optional(
    "agentgen.extensions.langchain.tools.GithubCreatePRReviewCommentTool",
    None
)

# LangChain imports
ChatPromptTemplate = import_optional(
    "langchain_core.prompts.ChatPromptTemplate",
    None
)

ChatAnthropic = import_optional(
    "langchain_anthropic.ChatAnthropic",
    None
)

ChatOpenAI = import_optional(
    "langchain_openai.ChatOpenAI",
    None
)
