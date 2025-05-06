"""
Analysis Context Module

This module provides the AnalysisContext class, which holds all necessary data for PR analysis.
"""

from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """
    Represents a result from applying an analysis rule.
    """
    rule_id: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    severity: str = "info"  # "error", "warning", "info"
    category: str = "general"  # "code_integrity", "parameter", "implementation"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalysisContext:
    """
    Holds all necessary data for PR analysis.
    """

    def __init__(
        self,
        base_ref: str,
        head_ref: str,
        repo_path: str,
        pr_number: Optional[int] = None,
        repo_name: Optional[str] = None
    ):
        """
        Initialize the analysis context.

        Args:
            base_ref: The base reference (branch or commit SHA)
            head_ref: The head reference (branch or commit SHA)
            repo_path: Path to the repository
            pr_number: Pull request number (if applicable)
            repo_name: Repository name (if applicable)
        """
        self.base_ref = base_ref
        self.head_ref = head_ref
        self.repo_path = repo_path
        self.pr_number = pr_number
        self.repo_name = repo_name
        
        # Store information about changed files
        self._changed_files: List[str] = []
        self._file_diffs: Dict[str, str] = {}
        self._file_contents: Dict[str, Dict[str, str]] = {}  # {file_path: {ref: content}}
        
        # Store analysis results
        self._results: List[AnalysisResult] = []
        
        # Additional metadata
        self.metadata: Dict[str, Any] = {}

    def add_changed_file(self, file_path: str) -> None:
        """
        Add a changed file to the context.

        Args:
            file_path: Path to the changed file
        """
        if file_path not in self._changed_files:
            self._changed_files.append(file_path)

    def set_changed_files(self, file_paths: List[str]) -> None:
        """
        Set the list of changed files.

        Args:
            file_paths: List of paths to changed files
        """
        self._changed_files = file_paths

    def get_changed_files(self) -> List[str]:
        """
        Get all files changed in the PR/commit.

        Returns:
            List of paths to changed files
        """
        return self._changed_files

    def add_file_content(self, file_path: str, ref: str, content: str) -> None:
        """
        Add file content for a specific reference.

        Args:
            file_path: Path to the file
            ref: Reference (branch or commit SHA)
            content: File content
        """
        if file_path not in self._file_contents:
            self._file_contents[file_path] = {}
        self._file_contents[file_path][ref] = content

    def get_file_content(self, file_path: str, ref: str) -> Optional[str]:
        """
        Get content of a file at a specific reference.

        Args:
            file_path: Path to the file
            ref: Reference (branch or commit SHA)

        Returns:
            File content or None if not available
        """
        if file_path in self._file_contents and ref in self._file_contents[file_path]:
            return self._file_contents[file_path][ref]
        return None

    def add_file_diff(self, file_path: str, diff: str) -> None:
        """
        Add diff for a specific file.

        Args:
            file_path: Path to the file
            diff: Diff content
        """
        self._file_diffs[file_path] = diff

    def get_diff(self, file_path: str) -> Optional[str]:
        """
        Get diff for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            Diff content or None if not available
        """
        return self._file_diffs.get(file_path)

    def add_result(self, result: AnalysisResult) -> None:
        """
        Add a result to the context.

        Args:
            result: Analysis result
        """
        self._results.append(result)

    def get_results(self) -> List[AnalysisResult]:
        """
        Get all analysis results.

        Returns:
            List of analysis results
        """
        return self._results

    def get_results_by_severity(self, severity: str) -> List[AnalysisResult]:
        """
        Get results filtered by severity.

        Args:
            severity: Severity level ("error", "warning", "info")

        Returns:
            List of analysis results with the specified severity
        """
        return [r for r in self._results if r.severity == severity]

    def get_results_by_category(self, category: str) -> List[AnalysisResult]:
        """
        Get results filtered by category.

        Args:
            category: Category of the results

        Returns:
            List of analysis results in the specified category
        """
        return [r for r in self._results if r.category == category]

    def get_results_by_file(self, file_path: str) -> List[AnalysisResult]:
        """
        Get results for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of analysis results for the specified file
        """
        return [r for r in self._results if r.file_path == file_path]

    def get_error_count(self) -> int:
        """
        Get the number of errors.

        Returns:
            Number of error results
        """
        return len(self.get_results_by_severity("error"))

    def get_warning_count(self) -> int:
        """
        Get the number of warnings.

        Returns:
            Number of warning results
        """
        return len(self.get_results_by_severity("warning"))

    def get_info_count(self) -> int:
        """
        Get the number of info messages.

        Returns:
            Number of info results
        """
        return len(self.get_results_by_severity("info"))

    def has_errors(self) -> bool:
        """
        Check if there are any errors.

        Returns:
            True if there are errors, False otherwise
        """
        return self.get_error_count() > 0

    def has_warnings(self) -> bool:
        """
        Check if there are any warnings.

        Returns:
            True if there are warnings, False otherwise
        """
        return self.get_warning_count() > 0

