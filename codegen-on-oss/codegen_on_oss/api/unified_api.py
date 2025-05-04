"""
Unified API for codegen-on-oss.

This module provides a unified API for interacting with the codegen-on-oss package,
making it easier to use the various components for code analysis, snapshot management,
and code integrity validation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig

from codegen_on_oss.analysis.code_analyzer import CodeAnalyzer
from codegen_on_oss.analysis.code_integrity_analyzer import CodeIntegrityAnalyzer
from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.metrics import CodeMetrics
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class UnifiedAPI:
    """
    Unified API for codegen-on-oss.

    This class provides a unified interface for interacting with the various
    components of the codegen-on-oss package, making it easier to perform
    common tasks like code analysis, snapshot management, and code integrity
    validation.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the UnifiedAPI.

        Args:
            github_token: Optional GitHub token for accessing private repositories
        """
        self.github_token = github_token
        self.secrets = SecretsConfig(github_token=github_token) if github_token else None
        self.snapshots = {}  # Cache for snapshots

    def analyze_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        output_path: Optional[str] = None,
        include_integrity: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a repository and return comprehensive metrics.

        Args:
            repo_url: URL of the repository to analyze
            branch: Optional branch to analyze (default: default branch)
            commit: Optional commit to analyze (default: latest commit)
            output_path: Optional path to save the analysis results
            include_integrity: Whether to include code integrity analysis

        Returns:
            Dict containing analysis results
        """
        logger.info(f"Analyzing repository: {repo_url}")

        # Initialize codebase
        codebase = self._get_codebase(repo_url, branch, commit)

        # Initialize analyzers
        code_analyzer = CodeAnalyzer(codebase)
        metrics = CodeMetrics(codebase)

        # Perform analysis
        results = {
            "repo_url": repo_url,
            "branch": branch,
            "commit": commit,
            "summary": code_analyzer.get_codebase_summary(),
            "complexity": code_analyzer.analyze_complexity(),
            "imports": code_analyzer.analyze_imports(),
            "metrics": metrics.calculate_metrics(),
        }

        # Include code integrity analysis if requested
        if include_integrity:
            integrity_analyzer = CodeIntegrityAnalyzer(codebase)
            results["integrity"] = integrity_analyzer.analyze()

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def analyze_commit(
        self,
        repo_url: str,
        commit_hash: str,
        base_commit: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a commit and return the changes and quality assessment.

        Args:
            repo_url: URL of the repository to analyze
            commit_hash: Hash of the commit to analyze
            base_commit: Optional base commit to compare against (default: parent commit)
            output_path: Optional path to save the analysis results

        Returns:
            Dict containing commit analysis results
        """
        logger.info(f"Analyzing commit {commit_hash} in repository {repo_url}")

        # Initialize codebases
        if base_commit:
            base_codebase = self._get_codebase(repo_url, commit=base_commit)
        else:
            # Use parent commit as base
            base_codebase = self._get_codebase(repo_url, commit=f"{commit_hash}^")

        commit_codebase = self._get_codebase(repo_url, commit=commit_hash)

        # Initialize analyzer
        analyzer = CommitAnalyzer(original_codebase=base_codebase, commit_codebase=commit_codebase)

        # Analyze commit
        analysis_result = analyzer.analyze_commit()

        # Format results
        results = {
            "repo_url": repo_url,
            "commit_hash": commit_hash,
            "base_commit": base_commit,
            "quality_assessment": {
                "is_properly_implemented": analysis_result.is_properly_implemented,
                "score": analysis_result.get_score(),
                "overall_assessment": analysis_result.get_summary(),
            },
            "changes": {
                "files_added": analysis_result.files_added,
                "files_modified": analysis_result.files_modified,
                "files_removed": analysis_result.files_removed,
            },
            "issues": [issue.to_dict() for issue in analysis_result.issues],
            "metrics_diff": analysis_result.metrics_diff,
        }

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def analyze_pull_request(
        self,
        repo_url: str,
        pr_number: int,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request and return the changes and quality assessment.

        Args:
            repo_url: URL of the repository to analyze
            pr_number: Number of the pull request to analyze
            output_path: Optional path to save the analysis results

        Returns:
            Dict containing PR analysis results
        """
        logger.info(f"Analyzing PR #{pr_number} in repository {repo_url}")

        if not self.github_token:
            raise ValueError("GitHub token is required for PR analysis")

        # Get PR information
        from github import Github

        g = Github(self.github_token)
        repo_name = repo_url.split("github.com/")[1].rstrip(".git")
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        # Get base and head branches
        base_branch = pr.base.ref
        head_branch = pr.head.ref

        # Initialize codebases
        base_codebase = self._get_codebase(repo_url, branch=base_branch)
        head_codebase = self._get_codebase(repo_url, branch=head_branch)

        # Initialize analyzer
        analyzer = CommitAnalyzer(original_codebase=base_codebase, commit_codebase=head_codebase)

        # Analyze PR
        analysis_result = analyzer.analyze_commit()

        # Format results
        results = {
            "repo_url": repo_url,
            "pr_number": pr_number,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "quality_assessment": {
                "is_properly_implemented": analysis_result.is_properly_implemented,
                "score": analysis_result.get_score(),
                "overall_assessment": analysis_result.get_summary(),
            },
            "changes": {
                "files_added": analysis_result.files_added,
                "files_modified": analysis_result.files_modified,
                "files_removed": analysis_result.files_removed,
            },
            "issues": [issue.to_dict() for issue in analysis_result.issues],
            "metrics_diff": analysis_result.metrics_diff,
        }

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def compare_branches(
        self,
        repo_url: str,
        base_branch: str,
        head_branch: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare two branches and return the differences.

        Args:
            repo_url: URL of the repository to analyze
            base_branch: Base branch for comparison
            head_branch: Head branch for comparison
            output_path: Optional path to save the comparison results

        Returns:
            Dict containing branch comparison results
        """
        logger.info(f"Comparing branches {base_branch} and {head_branch} in repository {repo_url}")

        # Initialize codebases
        base_codebase = self._get_codebase(repo_url, branch=base_branch)
        head_codebase = self._get_codebase(repo_url, branch=head_branch)

        # Initialize analyzer
        analyzer = DiffAnalyzer(base_codebase, head_codebase)

        # Analyze differences
        diff_result = analyzer.analyze()

        # Format results
        results = {
            "repo_url": repo_url,
            "base_branch": base_branch,
            "head_branch": head_branch,
            "summary": diff_result.get_summary(),
            "changes": {
                "files_added": diff_result.files_added,
                "files_modified": diff_result.files_modified,
                "files_removed": diff_result.files_removed,
            },
            "metrics_diff": diff_result.metrics_diff,
        }

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def create_snapshot(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        snapshot_name: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Create a snapshot of a repository.

        Args:
            repo_url: URL of the repository to snapshot
            branch: Optional branch to snapshot (default: default branch)
            commit: Optional commit to snapshot (default: latest commit)
            snapshot_name: Optional name for the snapshot
            output_path: Optional path to save the snapshot

        Returns:
            Snapshot ID
        """
        logger.info(f"Creating snapshot of repository {repo_url}")

        # Initialize codebase
        codebase = self._get_codebase(repo_url, branch, commit)

        # Create snapshot
        snapshot_manager = SnapshotManager()
        snapshot = snapshot_manager.create_snapshot(codebase, commit_sha=commit, name=snapshot_name)

        # Generate snapshot ID
        snapshot_id = f"{repo_url}:{branch or 'default'}:{commit or 'latest'}:{snapshot_name or 'unnamed'}"

        # Cache snapshot
        self.snapshots[snapshot_id] = snapshot

        # Save snapshot if output path is provided
        if output_path:
            snapshot.save_to_file(output_path)

        return snapshot_id

    def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare two snapshots and return the differences.

        Args:
            snapshot_id_1: ID of the first snapshot
            snapshot_id_2: ID of the second snapshot
            output_path: Optional path to save the comparison results

        Returns:
            Dict containing snapshot comparison results
        """
        logger.info(f"Comparing snapshots {snapshot_id_1} and {snapshot_id_2}")

        # Get the snapshots
        snapshot_1 = self._get_snapshot(snapshot_id_1)
        snapshot_2 = self._get_snapshot(snapshot_id_2)

        # Initialize analyzer
        from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
        analyzer = DiffAnalyzer(snapshot_1, snapshot_2)

        # Get summary of differences
        results = {
            "snapshot_id_1": snapshot_id_1,
            "snapshot_id_2": snapshot_id_2,
            "summary": analyzer.get_summary(),
            "changes": {
                "files_added": analyzer.analyze_file_changes(),
                "files_modified": analyzer.analyze_file_changes(),
                "files_removed": analyzer.analyze_file_changes(),
            },
            "metrics_diff": analyzer.analyze_complexity_changes(),
        }

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def analyze_code_integrity(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        rules: Optional[List[Dict[str, Any]]] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze code integrity and return issues.

        Args:
            repo_url: URL of the repository to analyze
            branch: Optional branch to analyze (default: default branch)
            commit: Optional commit to analyze (default: latest commit)
            rules: Optional list of rules to check
            output_path: Optional path to save the analysis results

        Returns:
            Dict containing code integrity analysis results
        """
        logger.info(f"Analyzing code integrity for repository {repo_url}")

        # Initialize codebase
        codebase = self._get_codebase(repo_url, branch, commit)

        # Initialize analyzer
        analyzer = CodeIntegrityAnalyzer(codebase)

        # Analyze code integrity
        integrity_result = analyzer.analyze()

        # Format results
        results = {
            "repo_url": repo_url,
            "branch": branch,
            "commit": commit,
            "timestamp": str(integrity_result.get("timestamp", "")),
            "issues": integrity_result.get("issues", []),
            "summary": integrity_result.get("summary", ""),
        }

        # Save results if output path is provided
        if output_path:
            self._save_results(results, output_path)

        return results

    def batch_analyze_repositories(
        self,
        repo_urls: List[str],
        output_dir: Optional[str] = None,
        include_integrity: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple repositories in batch.

        Args:
            repo_urls: List of repository URLs to analyze
            output_dir: Optional directory to save the analysis results
            include_integrity: Whether to include code integrity analysis

        Returns:
            Dict mapping repository URLs to their analysis results
        """
        logger.info(f"Batch analyzing {len(repo_urls)} repositories")

        results = {}
        for repo_url in repo_urls:
            try:
                output_path = None
                if output_dir:
                    repo_name = repo_url.split("/")[-1].replace(".git", "")
                    output_path = os.path.join(output_dir, f"{repo_name}_analysis.json")

                result = self.analyze_repository(
                    repo_url=repo_url,
                    output_path=output_path,
                    include_integrity=include_integrity,
                )
                results[repo_url] = result
            except Exception as e:
                logger.error(f"Error analyzing repository {repo_url}: {e}")
                results[repo_url] = {"error": str(e)}

        return results

    def _get_codebase(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
    ) -> Codebase:
        """
        Get a codebase from a repository URL.

        Args:
            repo_url: URL of the repository
            branch: Optional branch to checkout
            commit: Optional commit to checkout

        Returns:
            Codebase instance
        """
        if branch and commit:
            raise ValueError("Cannot specify both branch and commit")

        if branch:
            return Codebase.from_repo(repo_url, branch=branch, secrets=self.secrets)
        elif commit:
            return Codebase.from_repo(repo_url, commit=commit, secrets=self.secrets)
        else:
            return Codebase.from_repo(repo_url, secrets=self.secrets)

    def _get_snapshot(self, snapshot_id: str) -> CodebaseSnapshot:
        """
        Get a snapshot by ID.

        Args:
            snapshot_id: ID of the snapshot

        Returns:
            CodebaseSnapshot instance
        """
        if snapshot_id in self.snapshots:
            return self.snapshots[snapshot_id]

        # If not in cache, try to load from file
        if os.path.exists(snapshot_id):
            snapshot = CodebaseSnapshot.load_from_file(snapshot_id)
            self.snapshots[snapshot_id] = snapshot
            return snapshot

        raise ValueError(f"Snapshot {snapshot_id} not found")

    def _save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """
        Save results to a file.

        Args:
            results: Results to save
            output_path: Path to save the results
        """
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")


# Convenience functions
def analyze_repository(
    repo_url: str,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
    output_path: Optional[str] = None,
    include_integrity: bool = False,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a repository and return comprehensive metrics.

    Args:
        repo_url: URL of the repository to analyze
        branch: Optional branch to analyze (default: default branch)
        commit: Optional commit to analyze (default: latest commit)
        output_path: Optional path to save the analysis results
        include_integrity: Whether to include code integrity analysis
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing analysis results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.analyze_repository(
        repo_url=repo_url,
        branch=branch,
        commit=commit,
        output_path=output_path,
        include_integrity=include_integrity,
    )


def analyze_commit(
    repo_url: str,
    commit_hash: str,
    base_commit: Optional[str] = None,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a commit and return the changes and quality assessment.

    Args:
        repo_url: URL of the repository to analyze
        commit_hash: Hash of the commit to analyze
        base_commit: Optional base commit to compare against (default: parent commit)
        output_path: Optional path to save the analysis results
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing commit analysis results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.analyze_commit(
        repo_url=repo_url,
        commit_hash=commit_hash,
        base_commit=base_commit,
        output_path=output_path,
    )


def analyze_pull_request(
    repo_url: str,
    pr_number: int,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a pull request and return the changes and quality assessment.

    Args:
        repo_url: URL of the repository to analyze
        pr_number: Number of the pull request to analyze
        output_path: Optional path to save the analysis results
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing PR analysis results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.analyze_pull_request(
        repo_url=repo_url,
        pr_number=pr_number,
        output_path=output_path,
    )


def compare_branches(
    repo_url: str,
    base_branch: str,
    head_branch: str,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare two branches and return the differences.

    Args:
        repo_url: URL of the repository to analyze
        base_branch: Base branch for comparison
        head_branch: Head branch for comparison
        output_path: Optional path to save the comparison results
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing branch comparison results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.compare_branches(
        repo_url=repo_url,
        base_branch=base_branch,
        head_branch=head_branch,
        output_path=output_path,
    )


def create_snapshot(
    repo_url: str,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
    snapshot_name: Optional[str] = None,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> str:
    """
    Create a snapshot of a repository.

    Args:
        repo_url: URL of the repository to snapshot
        branch: Optional branch to snapshot (default: default branch)
        commit: Optional commit to snapshot (default: latest commit)
        snapshot_name: Optional name for the snapshot
        output_path: Optional path to save the snapshot
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Snapshot ID
    """
    api = UnifiedAPI(github_token=github_token)
    return api.create_snapshot(
        repo_url=repo_url,
        branch=branch,
        commit=commit,
        snapshot_name=snapshot_name,
        output_path=output_path,
    )


def compare_snapshots(
    snapshot_id_1: str,
    snapshot_id_2: str,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare two snapshots and return the differences.

    Args:
        snapshot_id_1: ID of the first snapshot
        snapshot_id_2: ID of the second snapshot
        output_path: Optional path to save the comparison results
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing snapshot comparison results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.compare_snapshots(
        snapshot_id_1=snapshot_id_1,
        snapshot_id_2=snapshot_id_2,
        output_path=output_path,
    )


def analyze_code_integrity(
    repo_url: str,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
    rules: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[str] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze code integrity and return issues.

    Args:
        repo_url: URL of the repository to analyze
        branch: Optional branch to analyze (default: default branch)
        commit: Optional commit to analyze (default: latest commit)
        rules: Optional list of rules to check
        output_path: Optional path to save the analysis results
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict containing code integrity analysis results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.analyze_code_integrity(
        repo_url=repo_url,
        branch=branch,
        commit=commit,
        rules=rules,
        output_path=output_path,
    )


def batch_analyze_repositories(
    repo_urls: List[str],
    output_dir: Optional[str] = None,
    include_integrity: bool = False,
    github_token: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple repositories in batch.

    Args:
        repo_urls: List of repository URLs to analyze
        output_dir: Optional directory to save the analysis results
        include_integrity: Whether to include code integrity analysis
        github_token: Optional GitHub token for accessing private repositories

    Returns:
        Dict mapping repository URLs to their analysis results
    """
    api = UnifiedAPI(github_token=github_token)
    return api.batch_analyze_repositories(
        repo_urls=repo_urls,
        output_dir=output_dir,
        include_integrity=include_integrity,
    )
