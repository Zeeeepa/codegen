"""
Commit Example Module

This module provides examples of how to use the commit analysis functionality.
"""

import argparse
import os
import subprocess
import tempfile
from typing import List


class CommitExampleRunner:
    """
    Runner for commit analysis examples.

    This class provides examples of how to use the commit analysis functionality
    in the analysis server.
    """

    def __init__(self, repo_url: str):
        """
        Initialize a new CommitExampleRunner.

        Args:
            repo_url: URL of the repository to analyze
        """
        self.repo_url = repo_url

    def analyze_commit(self, commit_hash: str) -> None:
        """
        Analyze a specific commit.

        Args:
            commit_hash: Hash of the commit to analyze
        """
        print(f"Analyzing commit {commit_hash} in repository {self.repo_url}")

        # Clone the repository to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the repository
            self._clone_repo(temp_dir)

            # Get the commit before the specified commit
            previous_commit = self._get_previous_commit(temp_dir, commit_hash)

            # Create directories for the two commits
            original_dir = os.path.join(temp_dir, "original")
            commit_dir = os.path.join(temp_dir, "commit")

            # Create the directories
            os.makedirs(original_dir, exist_ok=True)
            os.makedirs(commit_dir, exist_ok=True)

            # Checkout the previous commit to the original directory
            self._checkout_commit(temp_dir, previous_commit, original_dir)

            # Checkout the specified commit to the commit directory
            self._checkout_commit(temp_dir, commit_hash, commit_dir)

            # Analyze the commit
            self._analyze_commit_dirs(original_dir, commit_dir)

    def analyze_branch(self, branch_name: str) -> None:
        """
        Analyze a specific branch.

        Args:
            branch_name: Name of the branch to analyze
        """
        print(f"Analyzing branch {branch_name} in repository {self.repo_url}")

        # Clone the repository to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone the repository
            self._clone_repo(temp_dir)

            # Get the default branch
            default_branch = self._get_default_branch(temp_dir)

            # Create directories for the two branches
            original_dir = os.path.join(temp_dir, "original")
            branch_dir = os.path.join(temp_dir, "branch")

            # Create the directories
            os.makedirs(original_dir, exist_ok=True)
            os.makedirs(branch_dir, exist_ok=True)

            # Checkout the default branch to the original directory
            self._checkout_branch(temp_dir, default_branch, original_dir)

            # Checkout the specified branch to the branch directory
            self._checkout_branch(temp_dir, branch_name, branch_dir)

            # Analyze the branch
            self._analyze_commit_dirs(original_dir, branch_dir)

    def _clone_repo(self, temp_dir: str) -> None:
        """
        Clone the repository to a temporary directory.

        Args:
            temp_dir: Temporary directory to clone the repository to
        """
        subprocess.run(
            ["git", "clone", self.repo_url, temp_dir],
            check=True,
            capture_output=True,
            text=True,
        )

    def _get_previous_commit(self, repo_dir: str, commit_hash: str) -> str:
        """
        Get the commit before the specified commit.

        Args:
            repo_dir: Directory containing the repository
            commit_hash: Hash of the commit

        Returns:
            Hash of the previous commit
        """
        result = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", f"{commit_hash}^"],
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()

    def _get_default_branch(self, repo_dir: str) -> str:
        """
        Get the default branch of the repository.

        Args:
            repo_dir: Directory containing the repository

        Returns:
            Name of the default branch
        """
        result = subprocess.run(
            ["git", "-C", repo_dir, "symbolic-ref", "refs/remotes/origin/HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )

        # The output is in the format "refs/remotes/origin/main"
        return result.stdout.strip().split("/")[-1]

    def _checkout_commit(
        self, repo_dir: str, commit_hash: str, target_dir: str
    ) -> None:
        """
        Checkout a specific commit to a directory.

        Args:
            repo_dir: Directory containing the repository
            commit_hash: Hash of the commit to checkout
            target_dir: Directory to checkout the commit to
        """
        # Create a worktree for the commit
        subprocess.run(
            [
                "git",
                "-C",
                repo_dir,
                "worktree",
                "add",
                "--detach",
                target_dir,
                commit_hash,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def _checkout_branch(
        self, repo_dir: str, branch_name: str, target_dir: str
    ) -> None:
        """
        Checkout a specific branch to a directory.

        Args:
            repo_dir: Directory containing the repository
            branch_name: Name of the branch to checkout
            target_dir: Directory to checkout the branch to
        """
        # Create a worktree for the branch
        subprocess.run(
            ["git", "-C", repo_dir, "worktree", "add", target_dir, branch_name],
            check=True,
            capture_output=True,
            text=True,
        )

    def _analyze_commit_dirs(self, original_dir: str, commit_dir: str) -> None:
        """
        Analyze the differences between two directories.

        Args:
            original_dir: Directory containing the original code
            commit_dir: Directory containing the commit code
        """
        # Import here to avoid circular imports
        from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer

        # Create a commit analyzer
        analyzer = CommitAnalyzer.from_paths(original_dir, commit_dir)

        # Analyze the commit
        result = analyzer.analyze_commit()

        # Print the results
        print("\nAnalysis Results:")
        print(f"Is properly implemented: {result.is_properly_implemented}")

        if result.issues:
            print("\nIssues:")
            for issue in result.issues:
                print(f"- {issue.severity.upper()}: {issue.message}")

        if result.files_added:
            print("\nFiles Added:")
            for file_path in result.files_added[:5]:  # Limit to 5 files
                print(f"- {file_path}")

            if len(result.files_added) > 5:
                print(f"  ... and {len(result.files_added) - 5} more")

        if result.files_modified:
            print("\nFiles Modified:")
            for file_path in result.files_modified[:5]:  # Limit to 5 files
                print(f"- {file_path}")

            if len(result.files_modified) > 5:
                print(f"  ... and {len(result.files_modified) - 5} more")

        if result.files_removed:
            print("\nFiles Removed:")
            for file_path in result.files_removed[:5]:  # Limit to 5 files
                print(f"- {file_path}")

            if len(result.files_removed) > 5:
                print(f"  ... and {len(result.files_removed) - 5} more")


def main() -> None:
    """Main function to run the example."""
    parser = argparse.ArgumentParser(description="Commit Analysis Example")

    parser.add_argument("repo_url", help="URL of the repository to analyze")

    parser.add_argument("--commit", help="Hash of the commit to analyze")

    parser.add_argument("--branch", help="Name of the branch to analyze")

    args = parser.parse_args()

    runner = CommitExampleRunner(args.repo_url)

    if args.commit:
        runner.analyze_commit(args.commit)
    elif args.branch:
        runner.analyze_branch(args.branch)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
