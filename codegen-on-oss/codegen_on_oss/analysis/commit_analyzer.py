"""Commit Analyzer Module

This module provides functionality for analyzing Git commits by comparing
the codebase before and after the commit.
"""

import subprocess
from typing import Optional

from codegen_on_oss.analysis.commit_analysis import CommitAnalysisOptions, CommitAnalysisResult, CommitComparisonResult, FileChange


class CommitAnalyzer:
    """Analyzer for comparing and evaluating commits.

    This class provides functionality for analyzing Git commits by comparing
    the codebase before and after the commit.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize a new CommitAnalyzer.

        Args:
            repo_path: Optional path to a local repository
        """
        self.repo_path = repo_path
        self.temp_dir = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    def cleanup(self):
        """Clean up temporary directories."""
        if self.temp_dir:
            self.temp_dir.cleanup()
            self.temp_dir = None

    def analyze_commit(self, commit_hash: str, options: Optional[CommitAnalysisOptions] = None) -> CommitAnalysisResult:
        """Analyze a specific commit in the repository.

        Args:
            commit_hash: Hash of the commit to analyze
            options: Options for the analysis

        Returns:
            A CommitAnalysisResult with the analysis results
        """
        # Use default options if none provided
        if options is None:
            options = CommitAnalysisOptions()

        # Get commit metadata
        commit_info = self._get_commit_info(commit_hash)

        # Get the files changed in the commit
        files_changed = self._get_files_changed(commit_hash, options)

        # Create the analysis result
        return CommitAnalysisResult(
            commit_hash=commit_hash, author=commit_info.get("author", ""), date=commit_info.get("date", ""), message=commit_info.get("message", ""), files_changed=files_changed
        )

    def compare_commits(self, base_commit: str, compare_commit: str, options: Optional[CommitAnalysisOptions] = None) -> CommitComparisonResult:
        """Compare two commits in the repository.

        Args:
            base_commit: Hash of the base commit
            compare_commit: Hash of the commit to compare against the base
            options: Options for the comparison

        Returns:
            A CommitComparisonResult with the comparison results
        """
        # Use default options if none provided
        if options is None:
            options = CommitAnalysisOptions()

        # Get the files changed between the commits
        files_changed = self._get_files_changed_between_commits(base_commit, compare_commit, options)

        # Create the comparison result
        return CommitComparisonResult(base_commit_hash=base_commit, compare_commit_hash=compare_commit, files_changed=files_changed)

    def _get_commit_info(self, commit_hash: str) -> dict[str, str]:
        """Get metadata for a commit.

        Args:
            commit_hash: Hash of the commit

        Returns:
            A dictionary with commit metadata
        """
        # Run git show to get commit info
        result = subprocess.run(["git", "-C", self.repo_path, "show", "--no-patch", "--format=%an%n%ad%n%s", commit_hash], capture_output=True, text=True, check=True)

        # Parse the output
        lines = result.stdout.strip().split("\n")

        if len(lines) >= 3:
            return {"author": lines[0], "date": lines[1], "message": lines[2]}

        return {"author": "", "date": "", "message": ""}

    def _get_files_changed(self, commit_hash: str, options: CommitAnalysisOptions) -> list[FileChange]:
        """Get the files changed in a commit.

        Args:
            commit_hash: Hash of the commit
            options: Options for the analysis

        Returns:
            A list of FileChange objects
        """
        # Run git show to get changed files
        result = subprocess.run(["git", "-C", self.repo_path, "show", "--name-status", commit_hash], capture_output=True, text=True, check=True)

        # Parse the output
        lines = result.stdout.strip().split("\n")
        files_changed = []

        # Skip the commit message lines
        start_index = 0
        for i, line in enumerate(lines):
            if line.strip() == "":
                start_index = i + 1
                break

        # Process file changes
        for line in lines[start_index:]:
            if not line.strip():
                continue

            parts = line.strip().split("\t")

            if len(parts) >= 2:
                status = parts[0]
                filepath = parts[1]

                # Map git status to our status
                status_map = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied"}

                status_code = status[0]  # Take first character for status
                mapped_status = status_map.get(status_code, "modified")

                # Get file content if needed
                content = None
                if options.include_file_content and mapped_status != "deleted":
                    content = self._get_file_content(commit_hash, filepath)

                # Get diff if needed
                diff = None
                if options.include_diff and mapped_status != "added":
                    diff = self._get_file_diff(commit_hash, filepath)

                # Get function changes if needed
                functions_added = []
                functions_modified = []
                functions_removed = []

                if options.include_function_changes:
                    # This would require parsing the file to identify functions
                    # For simplicity, we'll just use a placeholder implementation
                    if mapped_status == "added" and content:
                        functions_added = self._extract_functions(content)
                    elif mapped_status == "modified" and diff:
                        # This is a simplified approach
                        functions_added, functions_modified, functions_removed = self._analyze_function_changes(diff)

                # Create the file change object
                file_change = FileChange(
                    filepath=filepath, status=mapped_status, content=content, diff=diff, functions_added=functions_added, functions_modified=functions_modified, functions_removed=functions_removed
                )

                files_changed.append(file_change)

        return files_changed

    def _get_files_changed_between_commits(self, base_commit: str, compare_commit: str, options: CommitAnalysisOptions) -> list[FileChange]:
        """Get the files changed between two commits.

        Args:
            base_commit: Hash of the base commit
            compare_commit: Hash of the commit to compare against the base
            options: Options for the comparison

        Returns:
            A list of FileChange objects
        """
        # Run git diff to get changed files
        result = subprocess.run(["git", "-C", self.repo_path, "diff", "--name-status", f"{base_commit}..{compare_commit}"], capture_output=True, text=True, check=True)

        # Parse the output
        lines = result.stdout.strip().split("\n")
        files_changed = []

        # Process file changes
        for line in lines:
            if not line.strip():
                continue

            parts = line.strip().split("\t")

            if len(parts) >= 2:
                status = parts[0]
                filepath = parts[1]

                # Map git status to our status
                status_map = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied"}

                status_code = status[0]  # Take first character for status
                mapped_status = status_map.get(status_code, "modified")

                # Get file content if needed
                content = None
                if options.include_file_content and mapped_status != "deleted":
                    content = self._get_file_content(compare_commit, filepath)

                # Get diff if needed
                diff = None
                if options.include_diff:
                    diff = self._get_file_diff_between_commits(base_commit, compare_commit, filepath)

                # Get function changes if needed
                functions_added = []
                functions_modified = []
                functions_removed = []

                if options.include_function_changes:
                    # This would require parsing the file to identify functions
                    # For simplicity, we'll just use a placeholder implementation
                    if mapped_status == "added" and content:
                        functions_added = self._extract_functions(content)
                    elif mapped_status == "modified" and diff:
                        # This is a simplified approach
                        functions_added, functions_modified, functions_removed = self._analyze_function_changes(diff)

                # Create the file change object
                file_change = FileChange(
                    filepath=filepath, status=mapped_status, content=content, diff=diff, functions_added=functions_added, functions_modified=functions_modified, functions_removed=functions_removed
                )

                files_changed.append(file_change)

        return files_changed

    def _get_file_content(self, commit_hash: str, filepath: str) -> Optional[str]:
        """Get the content of a file at a specific commit.

        Args:
            commit_hash: Hash of the commit
            filepath: Path to the file

        Returns:
            The file content, or None if the file doesn't exist
        """
        try:
            result = subprocess.run(["git", "-C", self.repo_path, "show", f"{commit_hash}:{filepath}"], capture_output=True, text=True, check=True)

            return result.stdout
        except subprocess.CalledProcessError:
            return None

    def _get_file_diff(self, commit_hash: str, filepath: str) -> Optional[str]:
        """Get the diff for a file in a commit.

        Args:
            commit_hash: Hash of the commit
            filepath: Path to the file

        Returns:
            The file diff, or None if there's no diff
        """
        try:
            result = subprocess.run(["git", "-C", self.repo_path, "show", "--patch", commit_hash, "--", filepath], capture_output=True, text=True, check=True)

            return result.stdout
        except subprocess.CalledProcessError:
            return None

    def _get_file_diff_between_commits(self, base_commit: str, compare_commit: str, filepath: str) -> Optional[str]:
        """Get the diff for a file between two commits.

        Args:
            base_commit: Hash of the base commit
            compare_commit: Hash of the commit to compare against the base
            filepath: Path to the file

        Returns:
            The file diff, or None if there's no diff
        """
        try:
            result = subprocess.run(["git", "-C", self.repo_path, "diff", "--patch", f"{base_commit}..{compare_commit}", "--", filepath], capture_output=True, text=True, check=True)

            return result.stdout
        except subprocess.CalledProcessError:
            return None

    def _extract_functions(self, content: str) -> list[str]:
        """Extract function names from file content.

        Args:
            content: The file content

        Returns:
            A list of function names
        """
        # This is a simplified implementation that just looks for "def " or "function "
        functions = []

        for line in content.split("\n"):
            line = line.strip()

            if line.startswith("def "):
                # Python function
                function_name = line[4:].split("(")[0].strip()
                functions.append(function_name)
            elif line.startswith("function "):
                # JavaScript/TypeScript function
                function_name = line[9:].split("(")[0].strip()
                functions.append(function_name)

        return functions

    def _analyze_function_changes(self, diff: str) -> tuple[list[str], list[str], list[str]]:
        """Analyze function changes from a diff.

        Args:
            diff: The file diff

        Returns:
            A tuple of (added_functions, modified_functions, removed_functions)
        """
        # This is a simplified implementation
        added_functions = []
        modified_functions = []
        removed_functions = []

        for line in diff.split("\n"):
            if line.startswith("+") and "def " in line:
                # Added Python function
                function_name = line.split("def ")[1].split("(")[0].strip()
                added_functions.append(function_name)
            elif line.startswith("-") and "def " in line:
                # Removed Python function
                function_name = line.split("def ")[1].split("(")[0].strip()
                removed_functions.append(function_name)
            elif line.startswith("+") and "function " in line:
                # Added JavaScript/TypeScript function
                function_name = line.split("function ")[1].split("(")[0].strip()
                added_functions.append(function_name)
            elif line.startswith("-") and "function " in line:
                # Removed JavaScript/TypeScript function
                function_name = line.split("function ")[1].split("(")[0].strip()
                removed_functions.append(function_name)

        # For simplicity, we're not detecting modified functions

        return added_functions, modified_functions, removed_functions
