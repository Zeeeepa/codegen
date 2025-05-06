"""
Analysis Context

Context for PR analysis containing all necessary data.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.git.models.pull_request_context import PullRequestContext


@dataclass
class AnalysisContext:
    """
    Context for PR analysis containing all necessary data.

    This class provides a unified interface for analysis rules to access
    information about the pull request and the codebase.
    """

    pr_context: PullRequestContext
    """The pull request context from graph-sitter."""

    pr_data: Dict[str, Any]
    """Additional PR data fetched from GitHub."""

    base_codebase: CodebaseContext
    """The codebase context for the base branch."""

    head_codebase: CodebaseContext
    """The codebase context for the head branch (PR changes)."""

    config: Dict[str, Any]
    """Configuration options for the analysis."""

    def get_changed_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about files changed in the PR.

        Returns:
            A dictionary mapping file paths to information about the changes
        """
        # This would be implemented to extract changed files from the PR data
        # For now, we'll return a placeholder
        return self.pr_data.get("changed_files", {})

    def get_diff_for_file(self, file_path: str) -> str:
        """
        Get the diff for a specific file.

        Args:
            file_path: The path of the file to get the diff for

        Returns:
            The diff for the file
        """
        # This would be implemented to extract the diff from the PR data
        # For now, we'll return a placeholder
        changed_files = self.get_changed_files()
        return changed_files.get(file_path, {}).get("diff", "")

    def get_file_content(self, file_path: str, revision: str = "head") -> Optional[str]:
        """
        Get the content of a file at a specific revision.

        Args:
            file_path: The path of the file to get the content for
            revision: The revision to get the content from ("head" or "base")

        Returns:
            The content of the file, or None if the file doesn't exist
        """
        # This would be implemented to get the file content from the appropriate codebase
        # For now, we'll return a placeholder
        codebase = self.head_codebase if revision == "head" else self.base_codebase
        # In a real implementation, we would use codebase to get the file content
        return None
