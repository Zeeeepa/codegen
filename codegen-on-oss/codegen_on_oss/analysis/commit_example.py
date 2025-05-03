"""
Commit Analysis Example

This script demonstrates how to use the commit analysis functionality.
"""

import os
import sys
import tempfile
import subprocess
from typing import Dict, Any, Optional

from codegen_on_oss.analysis.commit_analyzer import CommitAnalyzer
from codegen_on_oss.analysis.commit_analysis import (
    CommitAnalysisOptions,
)

def main():
    """Main function to run the example."""
    print("Commit Analysis Examples")
    print("=======================")
    
    # Example 1: Analyze a local Git repository
    print("\nExample 1: Analyze a local Git repository")
    
    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize a Git repository
        repo_path = os.path.join(temp_dir, "example_repo")
        os.makedirs(repo_path)
        
        try:
            # Initialize the repository
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            
            # Create a sample file
            with open(os.path.join(repo_path, "sample.py"), "w") as f:
                f.write("print('Hello, World!')")
            
            # Add and commit the file
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=repo_path,
                check=True
            )
            
            # Create a commit analyzer
            analyzer = CommitAnalyzer(repo_path)
            
            # Analyze the commit
            analysis = analyzer.analyze_commit("HEAD")
            
            # Print the analysis result
            print("Commit analysis result:")
            print(f"  Commit hash: {analysis.commit_hash}")
            print(f"  Author: {analysis.author}")
            print(f"  Date: {analysis.date}")
            print(f"  Message: {analysis.message}")
            print(f"  Files changed: {len(analysis.files_changed)}")
            
            for file_change in analysis.files_changed:
                print(f"    {file_change.status}: {file_change.filepath}")
        
        except Exception as e:
            print(f"Error in Example 1: {e}")
    
    # Example 2: Analyze a commit with options
    print("\nExample 2: Analyze a commit with options")
    
    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize a Git repository
        repo_path = os.path.join(temp_dir, "example_repo_2")
        os.makedirs(repo_path)
        
        try:
            # Initialize the repository
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            
            # Create a sample file
            with open(os.path.join(repo_path, "sample.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b\n")
            
            # Add and commit the file
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=repo_path,
                check=True
            )
            
            # Modify the file
            with open(os.path.join(repo_path, "sample.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n")
            
            # Add and commit the changes
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add subtract function"],
                cwd=repo_path,
                check=True
            )
            
            # Create a commit analyzer
            analyzer = CommitAnalyzer(repo_path)
            
            # Set analysis options
            options = CommitAnalysisOptions(
                include_diff=True,
                include_file_content=True,
                include_function_changes=True
            )
            
            # Analyze the commit
            analysis = analyzer.analyze_commit("HEAD", options)
            
            # Print the analysis result
            print("Commit analysis result with options:")
            print(f"  Commit hash: {analysis.commit_hash}")
            print(f"  Author: {analysis.author}")
            print(f"  Date: {analysis.date}")
            print(f"  Message: {analysis.message}")
            print(f"  Files changed: {len(analysis.files_changed)}")
            
            for file_change in analysis.files_changed:
                print(f"    {file_change.status}: {file_change.filepath}")
                
                if file_change.diff:
                    print(f"    Diff: {file_change.diff[:50]}...")
                
                if file_change.functions_added:
                    print(f"    Functions added: {len(file_change.functions_added)}")
                    for func in file_change.functions_added:
                        print(f"      {func}")
        
        except Exception as e:
            print(f"Error in Example 2: {e}")
    
    # Example 3: Compare commits
    print("\nExample 3: Compare commits")
    
    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize a Git repository
        repo_path = os.path.join(temp_dir, "example_repo_3")
        os.makedirs(repo_path)
        
        try:
            # Initialize the repository
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            
            # Create a sample file
            with open(os.path.join(repo_path, "sample.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b\n")
            
            # Add and commit the file
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=repo_path,
                check=True
            )
            
            # Get the first commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            first_commit = result.stdout.strip()
            
            # Modify the file
            with open(os.path.join(repo_path, "sample.py"), "w") as f:
                f.write("def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n")
            
            # Add and commit the changes
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Add subtract function"],
                cwd=repo_path,
                check=True
            )
            
            # Get the second commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            second_commit = result.stdout.strip()
            
            # Create a commit analyzer
            analyzer = CommitAnalyzer(repo_path)
            
            # Compare the commits
            comparison = analyzer.compare_commits(first_commit, second_commit)
            
            # Print the comparison result
            print("Commit comparison result:")
            print(f"  Base commit: {comparison.base_commit_hash}")
            print(f"  Compare commit: {comparison.compare_commit_hash}")
            print(f"  Files changed: {len(comparison.files_changed)}")
            
            for file_change in comparison.files_changed:
                print(f"    {file_change.status}: {file_change.filepath}")
                
                if file_change.functions_added:
                    print(f"    Functions added: {len(file_change.functions_added)}")
                    for func in file_change.functions_added:
                        print(f"      {func}")
        
        except Exception as e:
            print(f"Error in Example 3: {e}")
    
    print("\nCommit analysis examples completed!")


if __name__ == "__main__":
    main()
