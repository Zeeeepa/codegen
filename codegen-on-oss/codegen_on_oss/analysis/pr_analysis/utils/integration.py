"""
Integration Module

This module provides integration with existing code.
"""

from typing import Dict, Any
from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.git.models.pull_request_context import PullRequestContext as GSPullRequestContext
from graph_sitter.git.clients.github_client import GithubClient as GSGithubClient
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer

from ..github.models import PullRequestContext, PRPartContext
from ..github.pr_client import GitHubClient


def create_codebase_context(repo_path: str, base_path: str = None) -> CodebaseContext:
    """
    Create a codebase context from a repository path.
    
    Args:
        repo_path: Path to the repository
        base_path: Base path within the repository
        
    Returns:
        CodebaseContext instance
    """
    from graph_sitter.codebase.config import ProjectConfig
    from graph_sitter.shared.enums.programming_language import ProgrammingLanguage
    from graph_sitter.git.repo_operator.repo_operator import RepoOperator
    
    # Create a repo operator
    repo_operator = RepoOperator(repo_path)
    
    # Determine the programming language
    # This is a simplified version; in practice, you would need to analyze the repository
    programming_language = ProgrammingLanguage.PYTHON
    
    # Create a project config
    project_config = ProjectConfig(
        repo_operator=repo_operator,
        programming_language=programming_language,
        base_path=base_path,
    )
    
    # Create a codebase context
    return CodebaseContext([project_config])


def convert_pull_request_context(gs_pr_context: GSPullRequestContext) -> PullRequestContext:
    """
    Convert a graph-sitter PullRequestContext to our PullRequestContext.
    
    Args:
        gs_pr_context: graph-sitter PullRequestContext
        
    Returns:
        Our PullRequestContext
    """
    # Convert base and head
    base = PRPartContext(
        ref=gs_pr_context.base.ref,
        sha=gs_pr_context.base.sha,
        repo_name=gs_pr_context.base.repo_name,
    )
    
    head = PRPartContext(
        ref=gs_pr_context.head.ref,
        sha=gs_pr_context.head.sha,
        repo_name=gs_pr_context.head.repo_name,
    )
    
    # Convert user
    user = {
        'login': gs_pr_context.user.login,
        'id': gs_pr_context.user.id,
        'html_url': gs_pr_context.user.html_url,
    }
    
    # Create our PullRequestContext
    return PullRequestContext(
        number=gs_pr_context.number,
        title=gs_pr_context.title,
        body=gs_pr_context.body,
        state=gs_pr_context.state,
        base=base,
        head=head,
        user=user,
        html_url=gs_pr_context.html_url,
    )


def create_github_client(token: str) -> GitHubClient:
    """
    Create a GitHub client.
    
    Args:
        token: GitHub API token
        
    Returns:
        GitHubClient instance
    """
    # Create a graph-sitter GitHub client
    gs_client = GSGithubClient(token)
    
    # Create our GitHub client
    return GitHubClient(gs_client)


def create_diff_analyzer(base_codebase, head_codebase) -> DiffAnalyzer:
    """
    Create a diff analyzer.
    
    Args:
        base_codebase: Base codebase
        head_codebase: Head codebase
        
    Returns:
        DiffAnalyzer instance
    """
    from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot
    
    # Create snapshots
    base_snapshot = CodebaseSnapshot.from_codebase(base_codebase)
    head_snapshot = CodebaseSnapshot.from_codebase(head_codebase)
    
    # Create a diff analyzer
    return DiffAnalyzer(base_snapshot, head_snapshot)


def create_code_integrity_analyzer(codebase) -> CodeIntegrityAnalyzer:
    """
    Create a code integrity analyzer.
    
    Args:
        codebase: Codebase to analyze
        
    Returns:
        CodeIntegrityAnalyzer instance
    """
    # Create a code integrity analyzer
    return CodeIntegrityAnalyzer(codebase)

