"""
Example script demonstrating the use of the commit analysis functionality.

This script shows how to use the CommitAnalyzer class to analyze and compare
commits in a repository.
"""

import os
import tempfile
import subprocess
from pathlib import Path

from codegen import Codebase
from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.analysis.commit_analysis import CommitAnalyzer, CommitAnalysisResult


def analyze_commit_from_repo_url(repo_url: str, commit_hash: str):
    """
    Analyze a commit from a repository URL and commit hash.
    
    Args:
        repo_url: URL of the repository
        commit_hash: Hash of the commit to analyze
    """
    print(f"Analyzing commit {commit_hash} in repository {repo_url}...")
    
    # Use the class method to analyze the commit
    result = CodeAnalyzer.analyze_commit_from_repo_and_commit(repo_url, commit_hash)
    
    # Print the analysis summary
    print("\n" + "=" * 80)
    print(result.get_summary())
    print("=" * 80)
    
    # Return the result for further processing if needed
    return result


def analyze_commit_from_local_repos(original_path: str, commit_path: str):
    """
    Analyze a commit by comparing two local repository paths.
    
    Args:
        original_path: Path to the original repository
        commit_path: Path to the commit repository
    """
    print(f"Analyzing commit by comparing repositories:")
    print(f"  Original: {original_path}")
    print(f"  Commit: {commit_path}")
    
    # Create a CommitAnalyzer instance from paths
    analyzer = CommitAnalyzer.from_paths(original_path, commit_path)
    
    # Analyze the commit
    result = analyzer.analyze_commit()
    
    # Print the analysis summary
    print("\n" + "=" * 80)
    print(result.get_summary())
    print("=" * 80)
    
    # Return the result for further processing if needed
    return result


def analyze_commit_with_codebases(original_codebase: Codebase, commit_codebase: Codebase):
    """
    Analyze a commit by comparing two codebases.
    
    Args:
        original_codebase: The original codebase before the commit
        commit_codebase: The codebase after the commit
    """
    print("Analyzing commit by comparing codebases...")
    
    # Create a CommitAnalyzer instance
    analyzer = CommitAnalyzer(
        original_codebase=original_codebase,
        commit_codebase=commit_codebase
    )
    
    # Analyze the commit
    result = analyzer.analyze_commit()
    
    # Print the analysis summary
    print("\n" + "=" * 80)
    print(result.get_summary())
    print("=" * 80)
    
    # Return the result for further processing if needed
    return result


def clone_repo_at_different_commits(repo_url: str, before_commit: str, after_commit: str):
    """
    Clone a repository at two different commits for comparison.
    
    Args:
        repo_url: URL of the repository
        before_commit: Commit hash for the "before" state
        after_commit: Commit hash for the "after" state
        
    Returns:
        Tuple of (original_path, commit_path)
    """
    # Create temporary directories
    original_dir = tempfile.mkdtemp()
    commit_dir = tempfile.mkdtemp()
    
    try:
        # Clone the repository for the "before" state
        subprocess.run(
            ["git", "clone", repo_url, original_dir],
            check=True,
            capture_output=True
        )
        
        # Checkout the "before" commit
        subprocess.run(
            ["git", "-C", original_dir, "checkout", before_commit],
            check=True,
            capture_output=True
        )
        
        # Clone the repository for the "after" state
        subprocess.run(
            ["git", "clone", repo_url, commit_dir],
            check=True,
            capture_output=True
        )
        
        # Checkout the "after" commit
        subprocess.run(
            ["git", "-C", commit_dir, "checkout", after_commit],
            check=True,
            capture_output=True
        )
        
        return original_dir, commit_dir
    except Exception as e:
        # Clean up temporary directories on error
        if os.path.exists(original_dir):
            subprocess.run(["rm", "-rf", original_dir])
        if os.path.exists(commit_dir):
            subprocess.run(["rm", "-rf", commit_dir])
        raise e


def main():
    """
    Main function demonstrating different ways to use the commit analysis functionality.
    """
    # Example 1: Analyze a commit from a repository URL and commit hash
    print("Example 1: Analyze a commit from a repository URL and commit hash")
    repo_url = "https://github.com/fastapi/fastapi"
    commit_hash = "HEAD"  # Use the latest commit
    
    try:
        result1 = analyze_commit_from_repo_url(repo_url, commit_hash)
    except Exception as e:
        print(f"Error in Example 1: {e}")
    
    # Example 2: Analyze a commit by comparing two local repository paths
    print("\nExample 2: Analyze a commit by comparing two local repository paths")
    
    try:
        # Clone a repository at two different commits
        repo_url = "https://github.com/fastapi/fastapi"
        before_commit = "HEAD~5"  # 5 commits before HEAD
        after_commit = "HEAD"     # Latest commit
        
        original_path, commit_path = clone_repo_at_different_commits(
            repo_url, before_commit, after_commit
        )
        
        result2 = analyze_commit_from_local_repos(original_path, commit_path)
        
        # Clean up temporary directories
        subprocess.run(["rm", "-rf", original_path])
        subprocess.run(["rm", "-rf", commit_path])
    except Exception as e:
        print(f"Error in Example 2: {e}")
    
    # Example 3: Analyze a commit by comparing two codebases
    print("\nExample 3: Analyze a commit by comparing two codebases")
    
    try:
        # Create codebases from directories
        repo_url = "https://github.com/fastapi/fastapi"
        before_commit = "HEAD~3"  # 3 commits before HEAD
        after_commit = "HEAD"     # Latest commit
        
        original_path, commit_path = clone_repo_at_different_commits(
            repo_url, before_commit, after_commit
        )
        
        original_codebase = Codebase.from_directory(original_path)
        commit_codebase = Codebase.from_directory(commit_path)
        
        result3 = analyze_commit_with_codebases(original_codebase, commit_codebase)
        
        # Clean up temporary directories
        subprocess.run(["rm", "-rf", original_path])
        subprocess.run(["rm", "-rf", commit_path])
    except Exception as e:
        print(f"Error in Example 3: {e}")
    
    print("\nCommit analysis examples completed!")


if __name__ == "__main__":
    main()

