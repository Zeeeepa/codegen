"""
Commit Example Module

This module provides examples of how to use the commit analysis functionality.
"""

import argparse
import codegen
import os
import subprocess
import tempfile
from typing import Dict, List, Optional

from codegen import Codebase


class CommitAnalyzer:
    """
    Analyzer for git commits.
    
    This class provides functionality to analyze git commits for code quality
    and other metrics.
    """
    
    def __init__(self, repo_path: str):
        """
        Initialize a CommitAnalyzer.
        
        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = os.path.abspath(repo_path)
        if not os.path.isdir(os.path.join(self.repo_path, ".git")):
            raise ValueError(f"Not a git repository: {self.repo_path}")
    
    def get_commit_diff(self, commit_hash: str) -> str:
        """
        Get the diff for a commit.
        
        Args:
            commit_hash: The commit hash
            
        Returns:
            The commit diff as a string
        """
        cmd = ["git", "show", "--pretty=format:", commit_hash]
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True, check=True)
        return result.stdout
    
    def get_commit_files(self, commit_hash: str) -> List[str]:
        """
        Get the files changed in a commit.
        
        Args:
            commit_hash: The commit hash
            
        Returns:
            List of file paths changed in the commit
        """
        cmd = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash]
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True, check=True)
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    
    def checkout_commit(self, commit_hash: str) -> str:
        """
        Checkout a specific commit to a temporary directory.
        
        Args:
            commit_hash: The commit hash
            
        Returns:
            Path to the temporary directory containing the checked out code
        """
        temp_dir = tempfile.mkdtemp()
        cmd = ["git", "clone", self.repo_path, temp_dir]
        subprocess.run(cmd, capture_output=True, check=True)
        
        cmd = ["git", "checkout", commit_hash]
        subprocess.run(cmd, cwd=temp_dir, capture_output=True, check=True)
        
        return temp_dir
    
    def analyze_commit(self, commit_hash: str) -> Dict:
        """
        Analyze a commit.
        
        Args:
            commit_hash: The commit hash
            
        Returns:
            Dict containing analysis results
        """
        # Get the files changed in the commit
        files = self.get_commit_files(commit_hash)
        
        # Checkout the commit to a temporary directory
        temp_dir = self.checkout_commit(commit_hash)
        
        try:
            # Create a codebase from the temporary directory
            codebase = Codebase(temp_dir)
            
            # Perform analysis on the codebase
            # This is a placeholder for actual analysis
            results = {
                "commit_hash": commit_hash,
                "files_changed": files,
                "file_count": len(files),
                # Add more analysis results here
            }
            
            return results
        finally:
            # Clean up the temporary directory
            subprocess.run(["rm", "-rf", temp_dir], check=True)


@codegen.function("codegen-on-oss-commit-analysis")
def run(repo_path: str, commit_hash: Optional[str] = None):
    """
    Analyze a git commit.
    
    This function:
    1. Initializes a CommitAnalyzer for the repository
    2. If a commit hash is provided, analyzes that commit
    3. Otherwise, analyzes the latest commit
    4. Returns the analysis results
    
    Args:
        repo_path: Path to the git repository
        commit_hash: Optional commit hash to analyze
        
    Returns:
        dict: The analysis results
    """
    analyzer = CommitAnalyzer(repo_path)
    
    if not commit_hash:
        # Get the latest commit hash
        cmd = ["git", "rev-parse", "HEAD"]
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
        commit_hash = result.stdout.strip()
        print(f"No commit hash provided. Using latest commit: {commit_hash}")
    
    print(f"Analyzing commit {commit_hash}...")
    results = analyzer.analyze_commit(commit_hash)
    
    print("Analysis complete!")
    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Commit Analysis Example")
    parser.add_argument("--repo", required=True, help="Path to the git repository")
    parser.add_argument("--commit", help="Commit hash to analyze (defaults to latest)")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    results = run(args.repo, args.commit)
    
    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        import json
        print(json.dumps(results, indent=2))

