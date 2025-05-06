"""
Core analysis functionality for codebases.

This module provides functions for analyzing codebases, commits, and PRs.
It serves as the central analysis engine for the codebase analysis system.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from codegen import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_file_summary,
    get_function_summary,
    get_symbol_summary,
)
from graph_sitter.codebase.codebase_context import CodebaseContext
from graph_sitter.core.codebase import Codebase as GraphSitterCodebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.file import SourceFile
from graph_sitter.enums import SymbolType, EdgeType
from graph_sitter.shared.enums.programming_language import ProgrammingLanguage

from codegen_on_oss.analysis.code_integrity import validate_code_integrity
from codegen_on_oss.analysis.commit_analysis import analyze_commit_history

logger = logging.getLogger(__name__)


def analyze_codebase(codebase: Codebase) -> Dict[str, Any]:
    """
    Analyze a codebase.

    Args:
        codebase: Codebase to analyze

    Returns:
        Analysis results
    """
    logger.info(f"Analyzing codebase: {codebase.root_path}")
    
    # Create a graph-sitter codebase for advanced analysis
    gs_codebase = GraphSitterCodebase(codebase.root_path)
    
    # Get codebase summary
    summary = get_codebase_summary(gs_codebase)
    
    # Get file statistics
    file_stats = _get_file_statistics(gs_codebase)
    
    # Get symbol statistics
    symbol_stats = _get_symbol_statistics(gs_codebase)
    
    # Get dependency graph
    dependency_graph = _get_dependency_graph(gs_codebase)
    
    # Get code quality metrics
    code_quality = _get_code_quality_metrics(gs_codebase)
    
    # Combine results
    results = {
        "summary": summary,
        "file_stats": file_stats,
        "symbol_stats": symbol_stats,
        "dependency_graph": dependency_graph,
        "code_quality": code_quality,
    }
    
    logger.info("Codebase analysis completed")
    return results


def _get_file_statistics(codebase: GraphSitterCodebase) -> Dict[str, Any]:
    """
    Get file statistics.

    Args:
        codebase: GraphSitter codebase

    Returns:
        File statistics
    """
    file_stats = {
        "total_files": len(codebase.files),
        "files_by_language": {},
        "lines_of_code": 0,
        "average_file_size": 0,
    }
    
    # Count files by language
    for file in codebase.files:
        lang = file.language.name if file.language else "Unknown"
        if lang not in file_stats["files_by_language"]:
            file_stats["files_by_language"][lang] = 0
        file_stats["files_by_language"][lang] += 1
        
        # Count lines of code
        if os.path.exists(file.path):
            with open(file.path, "r", encoding="utf-8", errors="ignore") as f:
                try:
                    lines = len(f.readlines())
                    file_stats["lines_of_code"] += lines
                except Exception:
                    pass
    
    # Calculate average file size
    if file_stats["total_files"] > 0:
        file_stats["average_file_size"] = file_stats["lines_of_code"] / file_stats["total_files"]
    
    return file_stats


def _get_symbol_statistics(codebase: GraphSitterCodebase) -> Dict[str, Any]:
    """
    Get symbol statistics.

    Args:
        codebase: GraphSitter codebase

    Returns:
        Symbol statistics
    """
    symbol_stats = {
        "classes": 0,
        "functions": 0,
        "methods": 0,
        "variables": 0,
        "imports": 0,
        "exports": 0,
    }
    
    # Count symbols by type
    for file in codebase.files:
        for symbol in file.symbols:
            if symbol.symbol_type == SymbolType.CLASS:
                symbol_stats["classes"] += 1
            elif symbol.symbol_type == SymbolType.FUNCTION:
                if hasattr(symbol, "is_method") and symbol.is_method:
                    symbol_stats["methods"] += 1
                else:
                    symbol_stats["functions"] += 1
            elif symbol.symbol_type == SymbolType.VARIABLE:
                symbol_stats["variables"] += 1
            elif symbol.symbol_type == SymbolType.IMPORT:
                symbol_stats["imports"] += 1
            elif symbol.symbol_type == SymbolType.EXPORT:
                symbol_stats["exports"] += 1
    
    return symbol_stats


def _get_dependency_graph(codebase: GraphSitterCodebase) -> Dict[str, Any]:
    """
    Get dependency graph.

    Args:
        codebase: GraphSitter codebase

    Returns:
        Dependency graph
    """
    dependency_graph = {
        "nodes": [],
        "edges": [],
    }
    
    # Add nodes (files)
    for file in codebase.files:
        dependency_graph["nodes"].append({
            "id": file.path,
            "type": "file",
            "name": os.path.basename(file.path),
            "path": file.path,
            "language": file.language.name if file.language else "Unknown",
        })
    
    # Add edges (imports)
    for file in codebase.files:
        for edge in file.edges:
            if edge.edge_type == EdgeType.IMPORTS:
                dependency_graph["edges"].append({
                    "source": file.path,
                    "target": edge.target.path if hasattr(edge.target, "path") else str(edge.target),
                    "type": "imports",
                })
    
    return dependency_graph


def _get_code_quality_metrics(codebase: GraphSitterCodebase) -> Dict[str, Any]:
    """
    Get code quality metrics.

    Args:
        codebase: GraphSitter codebase

    Returns:
        Code quality metrics
    """
    code_quality = {
        "complexity": {
            "average_function_complexity": 0,
            "max_function_complexity": 0,
            "complex_functions": [],
        },
        "maintainability": {
            "average_file_size": 0,
            "large_files": [],
            "average_function_size": 0,
            "large_functions": [],
        },
    }
    
    # Calculate complexity metrics
    function_complexities = []
    for file in codebase.files:
        for symbol in file.symbols:
            if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                # Calculate cyclomatic complexity (simplified)
                complexity = _calculate_function_complexity(symbol)
                function_complexities.append(complexity)
                
                if complexity > 10:  # Threshold for complex functions
                    code_quality["complexity"]["complex_functions"].append({
                        "name": symbol.name,
                        "file": file.path,
                        "complexity": complexity,
                    })
                
                if complexity > code_quality["complexity"]["max_function_complexity"]:
                    code_quality["complexity"]["max_function_complexity"] = complexity
    
    # Calculate average function complexity
    if function_complexities:
        code_quality["complexity"]["average_function_complexity"] = sum(function_complexities) / len(function_complexities)
    
    # Calculate maintainability metrics
    file_sizes = []
    function_sizes = []
    for file in codebase.files:
        if os.path.exists(file.path):
            try:
                with open(file.path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = len(f.readlines())
                    file_sizes.append(lines)
                    
                    if lines > 500:  # Threshold for large files
                        code_quality["maintainability"]["large_files"].append({
                            "path": file.path,
                            "lines": lines,
                        })
            except Exception:
                pass
        
        for symbol in file.symbols:
            if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
                # Calculate function size
                size = _calculate_function_size(symbol)
                function_sizes.append(size)
                
                if size > 50:  # Threshold for large functions
                    code_quality["maintainability"]["large_functions"].append({
                        "name": symbol.name,
                        "file": file.path,
                        "lines": size,
                    })
    
    # Calculate average file size
    if file_sizes:
        code_quality["maintainability"]["average_file_size"] = sum(file_sizes) / len(file_sizes)
    
    # Calculate average function size
    if function_sizes:
        code_quality["maintainability"]["average_function_size"] = sum(function_sizes) / len(function_sizes)
    
    return code_quality


def _calculate_function_complexity(function_symbol) -> int:
    """
    Calculate function complexity (simplified).

    Args:
        function_symbol: Function symbol

    Returns:
        Complexity score
    """
    # This is a simplified calculation
    # In a real implementation, we would parse the AST and count branches
    complexity = 1  # Base complexity
    
    # Add complexity for each control flow statement
    if hasattr(function_symbol, "source_code"):
        source_code = function_symbol.source_code
        complexity += source_code.count("if ") 
        complexity += source_code.count("else ") 
        complexity += source_code.count("for ") 
        complexity += source_code.count("while ") 
        complexity += source_code.count("switch ") 
        complexity += source_code.count("case ") 
        complexity += source_code.count("&&") 
        complexity += source_code.count("||") 
        complexity += source_code.count("?") 
    
    return complexity


def _calculate_function_size(function_symbol) -> int:
    """
    Calculate function size in lines.

    Args:
        function_symbol: Function symbol

    Returns:
        Function size in lines
    """
    # This is a simplified calculation
    if hasattr(function_symbol, "source_code"):
        source_code = function_symbol.source_code
        return len(source_code.split("\n"))
    return 0


def analyze_commit(codebase: Codebase, commit: str) -> Dict[str, Any]:
    """
    Analyze a commit.

    Args:
        codebase: Codebase to analyze
        commit: Commit SHA

    Returns:
        Analysis results
    """
    logger.info(f"Analyzing commit: {commit}")
    
    # Get commit details
    commit_details = analyze_commit_history(codebase, [commit])
    
    # Get changed files
    changed_files = _get_changed_files(codebase, commit)
    
    # Analyze changes
    changes_analysis = _analyze_changes(codebase, changed_files)
    
    # Validate code integrity for changed files
    integrity_results = validate_code_integrity(codebase, changed_files)
    
    # Combine results
    results = {
        "commit_details": commit_details,
        "changed_files": changed_files,
        "changes_analysis": changes_analysis,
        "integrity_results": integrity_results,
    }
    
    logger.info("Commit analysis completed")
    return results


def _get_changed_files(codebase: Codebase, commit: str) -> List[Dict[str, Any]]:
    """
    Get changed files in a commit.

    Args:
        codebase: Codebase
        commit: Commit SHA

    Returns:
        List of changed files
    """
    changed_files = []
    
    # Get changed files using git
    try:
        import subprocess
        
        # Get list of changed files
        cmd = ["git", "show", "--name-status", "--pretty=format:", commit]
        result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
        
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]
                    
                    changed_files.append({
                        "path": file_path,
                        "status": status,
                    })
        
        # Get diff for each file
        for file_info in changed_files:
            file_path = file_info["path"]
            cmd = ["git", "show", f"{commit}:{file_path}"]
            try:
                result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
                file_info["content"] = result.stdout
            except subprocess.CalledProcessError:
                file_info["content"] = ""
    
    except Exception as e:
        logger.error(f"Error getting changed files: {str(e)}")
    
    return changed_files


def _analyze_changes(codebase: Codebase, changed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze changes in files.

    Args:
        codebase: Codebase
        changed_files: List of changed files

    Returns:
        Analysis of changes
    """
    changes_analysis = {
        "added_files": 0,
        "modified_files": 0,
        "deleted_files": 0,
        "added_lines": 0,
        "deleted_lines": 0,
        "file_types": {},
    }
    
    for file_info in changed_files:
        status = file_info["status"]
        file_path = file_info["path"]
        
        # Count files by status
        if status.startswith("A"):
            changes_analysis["added_files"] += 1
        elif status.startswith("M"):
            changes_analysis["modified_files"] += 1
        elif status.startswith("D"):
            changes_analysis["deleted_files"] += 1
        
        # Count file types
        file_ext = os.path.splitext(file_path)[1]
        if file_ext:
            if file_ext not in changes_analysis["file_types"]:
                changes_analysis["file_types"][file_ext] = 0
            changes_analysis["file_types"][file_ext] += 1
        
        # Count lines
        try:
            import subprocess
            
            cmd = ["git", "diff", "--numstat", "HEAD~1", "HEAD", "--", file_path]
            result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
            
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        try:
                            added = int(parts[0]) if parts[0] != "-" else 0
                            deleted = int(parts[1]) if parts[1] != "-" else 0
                        
                            changes_analysis["added_lines"] += added
                            changes_analysis["deleted_lines"] += deleted
                        except ValueError:
                            pass
        except Exception:
            pass
    
    return changes_analysis


def analyze_pr(codebase: Codebase, pr_number: int, access_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze a PR.

    Args:
        codebase: Codebase to analyze
        pr_number: PR number
        access_token: GitHub access token

    Returns:
        Analysis results
    """
    logger.info(f"Analyzing PR: {pr_number}")
    
    # Get PR details from GitHub
    pr_details = _get_pr_details(codebase, pr_number, access_token)
    
    # Get changed files
    changed_files = _get_pr_changed_files(codebase, pr_number, access_token)
    
    # Analyze changes
    changes_analysis = _analyze_changes(codebase, changed_files)
    
    # Validate code integrity for changed files
    integrity_results = validate_code_integrity(codebase, changed_files)
    
    # Combine results
    results = {
        "pr_details": pr_details,
        "changed_files": changed_files,
        "changes_analysis": changes_analysis,
        "integrity_results": integrity_results,
    }
    
    logger.info("PR analysis completed")
    return results


def _get_pr_details(codebase: Codebase, pr_number: int, access_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Get PR details from GitHub.

    Args:
        codebase: Codebase
        pr_number: PR number
        access_token: GitHub access token

    Returns:
        PR details
    """
    pr_details = {
        "number": pr_number,
        "title": "",
        "description": "",
        "author": "",
        "created_at": "",
        "updated_at": "",
        "state": "",
        "base_branch": "",
        "head_branch": "",
    }
    
    try:
        import requests
        
        # Get repository info
        import subprocess
        cmd = ["git", "config", "--get", "remote.origin.url"]
        result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
        repo_url = result.stdout.strip()
        
        # Extract owner and repo from URL
        import re
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", repo_url)
        if match:
            owner = match.group(1)
            repo = match.group(2)
            
            # Get PR details from GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
            headers = {}
            if access_token:
                headers["Authorization"] = f"token {access_token}"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                pr_data = response.json()
                
                pr_details["title"] = pr_data.get("title", "")
                pr_details["description"] = pr_data.get("body", "")
                pr_details["author"] = pr_data.get("user", {}).get("login", "")
                pr_details["created_at"] = pr_data.get("created_at", "")
                pr_details["updated_at"] = pr_data.get("updated_at", "")
                pr_details["state"] = pr_data.get("state", "")
                pr_details["base_branch"] = pr_data.get("base", {}).get("ref", "")
                pr_details["head_branch"] = pr_data.get("head", {}).get("ref", "")
    
    except Exception as e:
        logger.error(f"Error getting PR details: {str(e)}")
    
    return pr_details


def _get_pr_changed_files(codebase: Codebase, pr_number: int, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get changed files in a PR.

    Args:
        codebase: Codebase
        pr_number: PR number
        access_token: GitHub access token

    Returns:
        List of changed files
    """
    changed_files = []
    
    try:
        import requests
        
        # Get repository info
        import subprocess
        cmd = ["git", "config", "--get", "remote.origin.url"]
        result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
        repo_url = result.stdout.strip()
        
        # Extract owner and repo from URL
        import re
        match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", repo_url)
        if match:
            owner = match.group(1)
            repo = match.group(2)
            
            # Get PR files from GitHub API
            url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
            headers = {}
            if access_token:
                headers["Authorization"] = f"token {access_token}"
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                files_data = response.json()
                
                for file_data in files_data:
                    changed_files.append({
                        "path": file_data.get("filename", ""),
                        "status": file_data.get("status", ""),
                        "additions": file_data.get("additions", 0),
                        "deletions": file_data.get("deletions", 0),
                        "changes": file_data.get("changes", 0),
                    })
    
    except Exception as e:
        logger.error(f"Error getting PR changed files: {str(e)}")
    
    return changed_files


def compare_branches(codebase: Codebase, base_branch: str, head_branch: str) -> Dict[str, Any]:
    """
    Compare branches.

    Args:
        codebase: Codebase to analyze
        base_branch: Base branch name
        head_branch: Head branch name

    Returns:
        Comparison results
    """
    logger.info(f"Comparing branches: {base_branch} and {head_branch}")
    
    # Get changed files between branches
    changed_files = _get_changed_files_between_branches(codebase, base_branch, head_branch)
    
    # Analyze changes
    changes_analysis = _analyze_branch_changes(codebase, changed_files)
    
    # Get commits between branches
    commits = _get_commits_between_branches(codebase, base_branch, head_branch)
    
    # Validate code integrity for changed files
    integrity_results = validate_code_integrity(codebase, changed_files)
    
    # Combine results
    results = {
        "base_branch": base_branch,
        "head_branch": head_branch,
        "changed_files": changed_files,
        "changes_analysis": changes_analysis,
        "commits": commits,
        "integrity_results": integrity_results,
    }
    
    logger.info("Branch comparison completed")
    return results


def _get_changed_files_between_branches(codebase: Codebase, base_branch: str, head_branch: str) -> List[Dict[str, Any]]:
    """
    Get changed files between branches.

    Args:
        codebase: Codebase
        base_branch: Base branch name
        head_branch: Head branch name

    Returns:
        List of changed files
    """
    changed_files = []
    
    try:
        import subprocess
        
        # Get list of changed files
        cmd = ["git", "diff", "--name-status", f"{base_branch}...{head_branch}"]
        result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
        
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]
                    
                    changed_files.append({
                        "path": file_path,
                        "status": status,
                    })
    
    except Exception as e:
        logger.error(f"Error getting changed files between branches: {str(e)}")
    
    return changed_files


def _analyze_branch_changes(codebase: Codebase, changed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze changes between branches.

    Args:
        codebase: Codebase
        changed_files: List of changed files

    Returns:
        Analysis of changes
    """
    changes_analysis = {
        "added_files": 0,
        "modified_files": 0,
        "deleted_files": 0,
        "file_types": {},
    }
    
    for file_info in changed_files:
        status = file_info["status"]
        file_path = file_info["path"]
        
        # Count files by status
        if status.startswith("A"):
            changes_analysis["added_files"] += 1
        elif status.startswith("M"):
            changes_analysis["modified_files"] += 1
        elif status.startswith("D"):
            changes_analysis["deleted_files"] += 1
        
        # Count file types
        file_ext = os.path.splitext(file_path)[1]
        if file_ext:
            if file_ext not in changes_analysis["file_types"]:
                changes_analysis["file_types"][file_ext] = 0
            changes_analysis["file_types"][file_ext] += 1
    
    return changes_analysis


def _get_commits_between_branches(codebase: Codebase, base_branch: str, head_branch: str) -> List[Dict[str, Any]]:
    """
    Get commits between branches.

    Args:
        codebase: Codebase
        base_branch: Base branch name
        head_branch: Head branch name

    Returns:
        List of commits
    """
    commits = []
    
    try:
        import subprocess
        
        # Get list of commits
        cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%at|%s", f"{base_branch}..{head_branch}"]
        result = subprocess.run(cmd, cwd=codebase.root_path, capture_output=True, text=True, check=True)
        
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("|")
                if len(parts) >= 5:
                    commit_hash = parts[0]
                    author_name = parts[1]
                    author_email = parts[2]
                    timestamp = parts[3]
                    message = parts[4]
                    
                    import datetime
                    date = datetime.datetime.fromtimestamp(int(timestamp)).isoformat()
                    
                    commits.append({
                        "hash": commit_hash,
                        "author_name": author_name,
                        "author_email": author_email,
                        "date": date,
                        "message": message,
                    })
    
    except Exception as e:
        logger.error(f"Error getting commits between branches: {str(e)}")
    
    return commits


def get_codebase_summary(codebase_path: str) -> Dict[str, Any]:
    """
    Get a summary of the codebase.

    Args:
        codebase_path: Path to the codebase

    Returns:
        Codebase summary
    """
    # Create a graph-sitter codebase for advanced analysis
    gs_codebase = GraphSitterCodebase(codebase_path)
    
    # Get codebase summary using graph-sitter
    summary = get_codebase_summary(gs_codebase)
    
    return summary
