"""
Public API for the codegen-on-oss package.

This module provides a clean, well-documented public API for interacting with
the codegen-on-oss component.
"""

from typing import Any, Dict, List, Optional, Union

from codegen import Codebase
from codegen.configs.models.secrets import SecretsConfig

from codegen_on_oss.analysis.analysis import CodeAnalyzer
from codegen_on_oss.parser import CodegenParser
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot, SnapshotManager


class CodegenOnOSS:
    """
    Main entry point for the codegen-on-oss component.
    
    This class provides a clean, well-documented public API for interacting with
    the codegen-on-oss component.
    """
    
    def __init__(self, snapshot_dir: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize a new CodegenOnOSS instance.
        
        Args:
            snapshot_dir: Optional directory for storing snapshots
            github_token: Optional GitHub token for accessing private repositories
        """
        self.snapshot_manager = SnapshotManager(snapshot_dir)
        self.github_token = github_token
    
    def parse_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        commit: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Parse a repository and return its structure.
        
        Args:
            repo_url: The URL of the repository to parse
            branch: Optional branch to parse
            commit: Optional commit to parse
            include_patterns: Optional list of patterns to include
            exclude_patterns: Optional list of patterns to exclude
            
        Returns:
            A dictionary containing the repository structure
        """
        # Create a parser
        parser = CodegenParser()
        
        # Parse the repository
        codebase = parser.parse(
            repo_url,
            branch=branch,
            commit=commit,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        
        # Convert the codebase to a dictionary
        return self._codebase_to_dict(codebase)
    
    def analyze_codebase(
        self,
        codebase_or_dict: Union[Codebase, Dict[str, Any]],
        analysis_type: str = "full",
    ) -> Dict[str, Any]:
        """
        Analyze a codebase and return the results.
        
        Args:
            codebase_or_dict: The codebase to analyze, either a Codebase object or a dictionary
            analysis_type: The type of analysis to perform ("full", "quick", or "dependencies")
            
        Returns:
            A dictionary containing the analysis results
        """
        # Convert dictionary to codebase if necessary
        codebase = self._ensure_codebase(codebase_or_dict)
        
        # Create an analyzer
        analyzer = CodeAnalyzer(codebase)
        
        # Perform the analysis
        if analysis_type == "full":
            return {
                "complexity": analyzer.analyze_complexity(),
                "dependencies": analyzer.analyze_imports(),
                "summary": analyzer.get_codebase_summary(),
            }
        elif analysis_type == "quick":
            return {
                "summary": analyzer.get_codebase_summary(),
            }
        elif analysis_type == "dependencies":
            return {
                "dependencies": analyzer.analyze_imports(),
            }
        else:
            raise ValueError(f"Invalid analysis_type: {analysis_type}")
    
    def analyze_code_integrity(
        self,
        codebase_or_dict: Union[Codebase, Dict[str, Any]],
        rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze code integrity and return the results.
        
        Args:
            codebase_or_dict: The codebase to analyze, either a Codebase object or a dictionary
            rules: Optional list of rules to check
            
        Returns:
            A dictionary containing the analysis results
        """
        # Convert dictionary to codebase if necessary
        codebase = self._ensure_codebase(codebase_or_dict)
        
        # Create an analyzer
        analyzer = CodeAnalyzer(codebase)
        
        # Perform the analysis
        complexity = analyzer.analyze_complexity()
        
        # Apply rules
        issues = []
        if rules:
            for rule in rules:
                rule_type = rule.get("type")
                max_value = rule.get("max_value")
                
                if rule_type == "complexity":
                    # Check function complexity
                    for func in complexity.get("functions", []):
                        if func.get("cyclomatic_complexity", 0) > max_value:
                            issues.append({
                                "severity": "warning",
                                "message": f"Function {func['name']} has cyclomatic complexity {func['cyclomatic_complexity']}, which exceeds the maximum of {max_value}",
                                "file": func.get("file"),
                                "line": func.get("start_line"),
                            })
                
                elif rule_type == "line_length":
                    # This is a placeholder; actual implementation would require parsing the file content
                    pass
        
        return {
            "issues": issues,
            "complexity": complexity,
        }
    
    def create_snapshot(
        self,
        codebase_or_dict: Union[Codebase, Dict[str, Any]],
        snapshot_name: Optional[str] = None,
        commit_sha: Optional[str] = None,
    ) -> str:
        """
        Create a snapshot of a codebase.
        
        Args:
            codebase_or_dict: The codebase to snapshot, either a Codebase object or a dictionary
            snapshot_name: Optional name for the snapshot
            commit_sha: Optional commit SHA for the snapshot
            
        Returns:
            The ID of the created snapshot
        """
        # Convert dictionary to codebase if necessary
        codebase = self._ensure_codebase(codebase_or_dict)
        
        # Create a snapshot
        snapshot = self.snapshot_manager.create_snapshot(
            codebase,
            name=snapshot_name,
            commit_sha=commit_sha,
        )
        
        return snapshot.id
    
    def compare_snapshots(self, snapshot_id_1: str, snapshot_id_2: str) -> Dict[str, Any]:
        """
        Compare two snapshots and return the differences.
        
        Args:
            snapshot_id_1: The ID of the first snapshot
            snapshot_id_2: The ID of the second snapshot
            
        Returns:
            A dictionary containing the differences
        """
        # Get the snapshots
        snapshot_1 = self.snapshot_manager.get_snapshot(snapshot_id_1)
        snapshot_2 = self.snapshot_manager.get_snapshot(snapshot_id_2)
        
        # Compare the snapshots
        diff = snapshot_1.compare(snapshot_2)
        
        return diff.to_dict()
    
    def analyze_commit(
        self,
        repo_url: str,
        commit_hash: str,
        base_commit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a commit and return the results.
        
        Args:
            repo_url: The URL of the repository
            commit_hash: The hash of the commit to analyze
            base_commit: Optional base commit to compare against
            
        Returns:
            A dictionary containing the analysis results
        """
        # Use the CommitAnalyzer to analyze the commit
        result = CodeAnalyzer.analyze_commit_from_repo_and_commit(
            repo_url=repo_url,
            commit_hash=commit_hash,
            base_commit=base_commit,
        )
        
        return result.to_dict()
    
    def analyze_pull_request(
        self,
        repo_url: str,
        pr_number: int,
    ) -> Dict[str, Any]:
        """
        Analyze a pull request and return the results.
        
        Args:
            repo_url: The URL of the repository
            pr_number: The number of the pull request
            
        Returns:
            A dictionary containing the analysis results
        """
        # This is a placeholder; actual implementation would require GitHub API integration
        # For now, we'll return a simple result
        return {
            "pr_number": pr_number,
            "repo_url": repo_url,
            "message": "Pull request analysis not implemented yet",
        }
    
    def _ensure_codebase(self, codebase_or_dict: Union[Codebase, Dict[str, Any]]) -> Codebase:
        """
        Ensure that we have a Codebase object.
        
        Args:
            codebase_or_dict: Either a Codebase object or a dictionary
            
        Returns:
            A Codebase object
        """
        if isinstance(codebase_or_dict, Codebase):
            return codebase_or_dict
        elif isinstance(codebase_or_dict, dict):
            # This is a placeholder; actual implementation would convert the dictionary to a Codebase
            raise NotImplementedError("Converting dictionary to Codebase is not implemented yet")
        else:
            raise TypeError(f"Expected Codebase or dict, got {type(codebase_or_dict)}")
    
    def _codebase_to_dict(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Convert a Codebase object to a dictionary.
        
        Args:
            codebase: The Codebase object to convert
            
        Returns:
            A dictionary representation of the codebase
        """
        # This is a simplified version; actual implementation would be more comprehensive
        return {
            "repo_name": codebase.repo_name,
            "files": [file.path for file in codebase.files],
            "functions": [func.name for func in codebase.functions],
            "classes": [cls.name for cls in codebase.classes],
        }


# Convenience functions for direct import
def parse_repository(
    repo_url: str,
    branch: Optional[str] = None,
    commit: Optional[str] = None,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Parse a repository and return its structure.
    
    Args:
        repo_url: The URL of the repository to parse
        branch: Optional branch to parse
        commit: Optional commit to parse
        include_patterns: Optional list of patterns to include
        exclude_patterns: Optional list of patterns to exclude
        github_token: Optional GitHub token for accessing private repositories
        
    Returns:
        A dictionary containing the repository structure
    """
    api = CodegenOnOSS(github_token=github_token)
    return api.parse_repository(
        repo_url=repo_url,
        branch=branch,
        commit=commit,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )


def analyze_codebase(
    codebase: Codebase,
    analysis_type: str = "full",
) -> Dict[str, Any]:
    """
    Analyze a codebase and return the results.
    
    Args:
        codebase: The codebase to analyze
        analysis_type: The type of analysis to perform ("full", "quick", or "dependencies")
        
    Returns:
        A dictionary containing the analysis results
    """
    api = CodegenOnOSS()
    return api.analyze_codebase(codebase, analysis_type)

