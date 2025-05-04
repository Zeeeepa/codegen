"""
Public API for the codegen-on-oss component.

This module defines the public API for the codegen-on-oss component, providing
a clean interface for external consumers to interact with the system.
"""

from typing import Dict, List, Optional, Union, Any, Callable

from codegen_on_oss.analysis.analysis import (
    analyze_codebase,
    analyze_code_integrity,
)
from codegen_on_oss.analysis.codebase_context import CodebaseContext
from codegen_on_oss.analysis.commit_analyzer import analyze_commit
from codegen_on_oss.analysis.diff_analyzer import analyze_diff
from codegen_on_oss.parser import parse_repository
from codegen_on_oss.snapshot.snapshot import create_snapshot, compare_snapshots
from codegen_on_oss.sources.source import RepositorySource


class CodegenOnOSS:
    """Main entry point for the codegen-on-oss public API.
    
    This class provides a unified interface to the various capabilities of the
    codegen-on-oss system, including repository parsing, code analysis, and
    snapshot management.
    
    Examples:
        ```python
        from codegen_on_oss.api.public_api import CodegenOnOSS
        
        # Initialize the API
        codegen = CodegenOnOSS()
        
        # Parse a repository
        repo_data = codegen.parse_repository("https://github.com/org/repo")
        
        # Analyze the codebase
        analysis = codegen.analyze_codebase(repo_data)
        
        # Create a snapshot
        snapshot_id = codegen.create_snapshot(repo_data)
        ```
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the CodegenOnOSS API.
        
        Args:
            config: Optional configuration dictionary for customizing behavior.
        """
        self.config = config or {}
    
    def parse_repository(
        self, 
        repo_url: str, 
        branch: Optional[str] = None,
        depth: int = 1,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Parse a repository and return its structure.
        
        Args:
            repo_url: URL of the repository to parse.
            branch: Optional branch to parse (defaults to main/master).
            depth: Git clone depth.
            include_patterns: Optional list of file patterns to include.
            exclude_patterns: Optional list of file patterns to exclude.
            
        Returns:
            Dictionary containing the parsed repository data.
        """
        source = RepositorySource(repo_url, branch=branch)
        return parse_repository(
            source, 
            depth=depth,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
    
    def analyze_codebase(
        self, 
        repo_data: Dict[str, Any],
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """Analyze a codebase and return insights.
        
        Args:
            repo_data: Repository data from parse_repository.
            analysis_type: Type of analysis to perform (full, quick, dependencies).
            
        Returns:
            Dictionary containing analysis results.
        """
        return analyze_codebase(repo_data, analysis_type=analysis_type)
    
    def analyze_code_integrity(
        self,
        repo_data: Dict[str, Any],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Analyze code integrity based on predefined or custom rules.
        
        Args:
            repo_data: Repository data from parse_repository.
            rules: Optional list of custom rules to apply.
            
        Returns:
            Dictionary containing integrity analysis results.
        """
        return analyze_code_integrity(repo_data, rules=rules)
    
    def analyze_commit(
        self,
        repo_url: str,
        commit_hash: str,
    ) -> Dict[str, Any]:
        """Analyze a specific commit.
        
        Args:
            repo_url: URL of the repository.
            commit_hash: Hash of the commit to analyze.
            
        Returns:
            Dictionary containing commit analysis results.
        """
        return analyze_commit(repo_url, commit_hash)
    
    def analyze_diff(
        self,
        repo_url: str,
        base_ref: str,
        head_ref: str,
    ) -> Dict[str, Any]:
        """Analyze the diff between two references.
        
        Args:
            repo_url: URL of the repository.
            base_ref: Base reference (commit, branch, tag).
            head_ref: Head reference (commit, branch, tag).
            
        Returns:
            Dictionary containing diff analysis results.
        """
        return analyze_diff(repo_url, base_ref, head_ref)
    
    def create_snapshot(
        self,
        repo_data: Dict[str, Any],
        snapshot_name: Optional[str] = None,
    ) -> str:
        """Create a snapshot of the repository.
        
        Args:
            repo_data: Repository data from parse_repository.
            snapshot_name: Optional name for the snapshot.
            
        Returns:
            Snapshot ID.
        """
        return create_snapshot(repo_data, name=snapshot_name)
    
    def compare_snapshots(
        self,
        snapshot_id_1: str,
        snapshot_id_2: str,
    ) -> Dict[str, Any]:
        """Compare two snapshots and return the differences.
        
        Args:
            snapshot_id_1: ID of the first snapshot.
            snapshot_id_2: ID of the second snapshot.
            
        Returns:
            Dictionary containing comparison results.
        """
        return compare_snapshots(snapshot_id_1, snapshot_id_2)
    
    def get_codebase_context(
        self,
        repo_data: Dict[str, Any],
    ) -> CodebaseContext:
        """Get a CodebaseContext object for advanced analysis.
        
        Args:
            repo_data: Repository data from parse_repository.
            
        Returns:
            CodebaseContext object.
        """
        return CodebaseContext(repo_data)


# Convenience functions for direct imports
parse_repository_func = CodegenOnOSS().parse_repository
analyze_codebase_func = CodegenOnOSS().analyze_codebase
analyze_code_integrity_func = CodegenOnOSS().analyze_code_integrity
analyze_commit_func = CodegenOnOSS().analyze_commit
analyze_diff_func = CodegenOnOSS().analyze_diff
create_snapshot_func = CodegenOnOSS().create_snapshot
compare_snapshots_func = CodegenOnOSS().compare_snapshots

