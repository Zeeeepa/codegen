"""
Commit Analysis Module for Codegen-on-OSS

This module provides functionality for analyzing and comparing commits,
determining if a commit is properly implemented, and identifying potential issues.
"""

import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple, Union, Any
from pathlib import Path
import difflib
import re
from dataclasses import dataclass, field

from codegen import Codebase
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import EdgeType, SymbolType

from codegen_on_oss.analysis.analysis import CodeAnalyzer


@dataclass
class CommitIssue:
    """Represents an issue found in a commit.
    issue_type: str
    severity: str  # "critical", "warning", "info"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the issue to a dictionary.
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
        }


@dataclass
class CommitAnalysisResult:
    """Result of a commit analysis.
    is_properly_implemented: bool
    issues: List[CommitIssue] = field(default_factory=list)
    metrics_diff: Dict[str, Any] = field(default_factory=dict)
    files_added: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_removed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary.
        return {
            "is_properly_implemented": self.is_properly_implemented,
            "issues": [issue.to_dict() for issue in self.issues],
            "metrics_diff": self.metrics_diff,
            "files_added": self.files_added,
            "files_modified": self.files_modified,
            "files_removed": self.files_removed,
        }
    
    def get_summary(self) -> str:
        """Get a summary of the analysis result.
        status = "✅ Properly implemented" if self.is_properly_implemented else "❌ Issues found"
        
        summary = f"Commit Analysis Summary: {status}\n\n"
        
        if self.files_added:
            summary += f"Files Added ({len(self.files_added)}):\n"
            for file in self.files_added[:5]:  # Limit to 5 files for brevity
                summary += f"  - {file}\n"
            if len(self.files_added) > 5:
                summary += f"  - ... and {len(self.files_added) - 5} more\n"
            summary += "\n"
            
        if self.files_modified:
            summary += f"Files Modified ({len(self.files_modified)}):\n"
            for file in self.files_modified[:5]:
                summary += f"  - {file}\n"
            if len(self.files_modified) > 5:
                summary += f"  - ... and {len(self.files_modified) - 5} more\n"
            summary += "\n"
            
        if self.files_removed:
            summary += f"Files Removed ({len(self.files_removed)}):\n"
            for file in self.files_removed[:5]:
                summary += f"  - {file}\n"
            if len(self.files_removed) > 5:
                summary += f"  - ... and {len(self.files_removed) - 5} more\n"
            summary += "\n"
        
        if self.issues:
            summary += f"Issues Found ({len(self.issues)}):\n"
            for issue in self.issues:
                location = f" at {issue.file_path}:{issue.line_number}" if issue.file_path else ""
                summary += f"  - [{issue.severity.upper()}] {issue.issue_type}{location}: {issue.message}\n"
            summary += "\n"
            
        if self.metrics_diff:
            summary += "Metrics Changes:\n"
            for metric, change in self.metrics_diff.items():
                if isinstance(change, dict) and "before" in change and "after" in change:
                    if isinstance(change["before"], (int, float)) and isinstance(change["after"], (int, float)):
                        diff = change["after"] - change["before"]
                        direction = "↑" if diff > 0 else "↓" if diff < 0 else "→"
                        summary += f"  - {metric}: {change['before']} → {change['after']} ({direction} {abs(diff):.2f})\n"
                    else:
                        summary += f"  - {metric}: {change['before']} → {change['after']}\n"
                else:
                    summary += f"  - {metric}: {change}\n"
        
        return summary


class CommitAnalyzer:
    
    Analyzer for comparing and evaluating commits.
    
    This class provides functionality to analyze two versions of a codebase (original and commit),
    compare them, and determine if the commit is properly implemented.
    
    
    def __init__(
        self, 
        original_codebase: Codebase, 
        commit_codebase: Codebase,
        original_path: Optional[str] = None,
        commit_path: Optional[str] = None
    ):
        
        Initialize the CommitAnalyzer.
        
        Args:
            original_codebase: The original codebase before the commit
            commit_codebase: The codebase after the commit
            original_path: Path to the original repository (optional)
            commit_path: Path to the commit repository (optional)
        
        self.original_codebase = original_codebase
        self.commit_codebase = commit_codebase
        self.original_path = original_path
        self.commit_path = commit_path
        
        # Create analyzers for both codebases
        self.original_analyzer = CodeAnalyzer(original_codebase)
        self.commit_analyzer = CodeAnalyzer(commit_codebase)
        
        # Initialize results
        self.issues = []
        self.metrics_diff = {}
        self.files_added = []
        self.files_modified = []
        self.files_removed = []
        
    @classmethod
    def from_paths(cls, original_path: str, commit_path: str) -> 'CommitAnalyzer':
        
        Create a CommitAnalyzer from repository paths.
        
        Args:
            original_path: Path to the original repository
            commit_path: Path to the commit repository
            
        Returns:
            A CommitAnalyzer instance
        
        original_codebase = Codebase.from_directory(original_path)
        commit_codebase = Codebase.from_directory(commit_path)
        
        return cls(
            original_codebase=original_codebase,
            commit_codebase=commit_codebase,
            original_path=original_path,
            commit_path=commit_path
        )
    
    @classmethod
    def from_repo_and_commit(cls, repo_url: str, commit_hash: str) -> 'CommitAnalyzer':
        
        Create a CommitAnalyzer from a repository URL and commit hash.
        
        Args:
            repo_url: URL of the repository
            commit_hash: Hash of the commit to analyze
            
        Returns:
            A CommitAnalyzer instance
        
        # Create temporary directories for the repositories
        original_dir = tempfile.mkdtemp()
        commit_dir = tempfile.mkdtemp()
        
        try:
            # Clone the repository
            subprocess.run(
                ["git", "clone", repo_url, original_dir],
                check=True,
                capture_output=True
            )
            
            # Clone the repository for the commit
            subprocess.run(
                ["git", "clone", repo_url, commit_dir],
                check=True,
                capture_output=True
            )
            
            # Checkout the commit
            subprocess.run(
                ["git", "-C", commit_dir, "checkout", commit_hash],
                check=True,
                capture_output=True
            )
            
            # Create codebases
            original_codebase = Codebase.from_directory(original_dir)
            commit_codebase = Codebase.from_directory(commit_dir)
            
            return cls(
                original_codebase=original_codebase,
                commit_codebase=commit_codebase,
                original_path=original_dir,
                commit_path=commit_dir
            )
        except Exception as e:
            # Clean up temporary directories
            if os.path.exists(original_dir):
                subprocess.run(["rm", "-rf", original_dir])
            if os.path.exists(commit_dir):
                subprocess.run(["rm", "-rf", commit_dir])
            raise e
    
    def analyze_commit(self) -> CommitAnalysisResult:
        
        Analyze the commit and determine if it's properly implemented.
        
        Returns:
            A CommitAnalysisResult object containing the analysis results
        
        # Identify file changes
        self._identify_file_changes()
        
        # Analyze code complexity changes
        self._analyze_complexity_changes()
        
        # Analyze import changes
        self._analyze_import_changes()
        
        # Check for syntax errors and other issues
        self._check_for_issues()
        
        # Determine if the commit is properly implemented
        is_properly_implemented = len([i for i in self.issues if i.severity == "critical"]) == 0
        
        # Create and return the result
        return CommitAnalysisResult(
            is_properly_implemented=is_properly_implemented,
            issues=self.issues,
            metrics_diff=self.metrics_diff,
            files_added=self.files_added,
            files_modified=self.files_modified,
            files_removed=self.files_removed
        )
    
    def _identify_file_changes(self):
        """Identify added, modified, and removed files between the two codebases.
        original_files = {file.path: file for file in self.original_codebase.files}
        commit_files = {file.path: file for file in self.commit_codebase.files}
        
        # Find added files
        self.files_added = [path for path in commit_files if path not in original_files]
        
        # Find removed files
        self.files_removed = [path for path in original_files if path not in commit_files]
        
        # Find modified files
        common_files = set(original_files.keys()) & set(commit_files.keys())
        self.files_modified = []
        
        for path in common_files:
            original_content = original_files[path].content
            commit_content = commit_files[path].content
            
            if original_content != commit_content:
                self.files_modified.append(path)
    
    def _analyze_complexity_changes(self):
        """Analyze changes in code complexity metrics.
        # Get complexity metrics for both codebases
        original_complexity = self.original_analyzer.analyze_complexity()
        commit_complexity = self.commit_analyzer.analyze_complexity()
        
        # Compare cyclomatic complexity
        self.metrics_diff["cyclomatic_complexity"] = {
            "before": original_complexity["cyclomatic_complexity"]["average"],
            "after": commit_complexity["cyclomatic_complexity"]["average"]
        }
        
        # Compare maintainability index
        if "maintainability_index" in original_complexity and "maintainability_index" in commit_complexity:
            self.metrics_diff["maintainability_index"] = {
                "before": original_complexity["maintainability_index"]["average"],
                "after": commit_complexity["maintainability_index"]["average"]
            }
        
        # Check for significant complexity increases in functions
        original_funcs = {f["name"]: f for f in original_complexity["cyclomatic_complexity"]["functions"]}
        commit_funcs = {f["name"]: f for f in commit_complexity["cyclomatic_complexity"]["functions"]}
        
        for name, func in commit_funcs.items():
            if name in original_funcs:
                original_complexity_val = original_funcs[name]["complexity"]
                commit_complexity_val = func["complexity"]
                
                # If complexity increased significantly, add an issue
                if commit_complexity_val > original_complexity_val * 1.5 and commit_complexity_val > 10:
                    self.issues.append(CommitIssue(
                        issue_type="complexity_increase",
                        severity="warning",
                        message=f"Function complexity increased from {original_complexity_val} to {commit_complexity_val}",
                        file_path=func.get("file_path"),
                        line_number=func.get("line_number")
                    ))
    
    def _analyze_import_changes(self):
        """Analyze changes in imports and dependencies.
        # Get import analysis for both codebases
        original_imports = self.original_analyzer.analyze_imports()
        commit_imports = self.commit_analyzer.analyze_imports()
        
        # Compare import cycles
        self.metrics_diff["import_cycles"] = {
            "before": len(original_imports["import_cycles"]),
            "after": len(commit_imports["import_cycles"])
        }
        
        # Check if new import cycles were introduced
        if len(commit_imports["import_cycles"]) > len(original_imports["import_cycles"]):
            self.issues.append(CommitIssue(
                issue_type="new_import_cycles",
                severity="warning",
                message=f"New import cycles introduced ({len(commit_imports['import_cycles']) - len(original_imports['import_cycles'])})"
            ))
    
    def _check_for_issues(self):
        """Check for various issues in the commit.
        # Check for syntax errors in added or modified files
        for file_path in self.files_added + self.files_modified:
            file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            if file and hasattr(file, "syntax_errors") and file.syntax_errors:
                for error in file.syntax_errors:
                    self.issues.append(CommitIssue(
                        issue_type="syntax_error",
                        severity="critical",
                        message=error.get("message", "Syntax error"),
                        file_path=file_path,
                        line_number=error.get("line_number")
                    ))
        
        # Check for broken references
        self._check_broken_references()
        
        # Check for test coverage (if tests exist)
        self._check_test_coverage()
        
        # Check for documentation updates
        self._check_documentation_updates()
    
    def _check_broken_references(self):
        """Check for broken references in the code.
        # This is a simplified implementation
        # In a real implementation, you would check for references to removed symbols
        
        # Get all symbols in both codebases
        original_symbols = {symbol.full_name: symbol for symbol in self.original_codebase.symbols}
        commit_symbols = {symbol.full_name: symbol for symbol in self.commit_codebase.symbols}
        
        # Find removed symbols
        removed_symbols = [name for name in original_symbols if name not in commit_symbols]
        
        # Check if any removed symbols are still referenced
        for file in self.commit_codebase.files:
            for symbol_usage in getattr(file, "symbol_usages", []):
                if symbol_usage in removed_symbols:
                    self.issues.append(CommitIssue(
                        issue_type="broken_reference",
                        severity="critical",
                        message=f"Reference to removed symbol '{symbol_usage}'",
                        file_path=file.path
                    ))
    
    def _check_test_coverage(self):
        """Check for test coverage changes.
        # This is a placeholder for test coverage analysis
        # In a real implementation, you would run tests and compare coverage
        
        # Check if tests were added or modified
        test_files_added = [f for f in self.files_added if "test" in f.lower()]
        test_files_modified = [f for f in self.files_modified if "test" in f.lower()]
        
        # Check if code was added/modified but no tests were added/modified
        code_files_added = [f for f in self.files_added if "test" not in f.lower()]
        code_files_modified = [f for f in self.files_modified if "test" not in f.lower()]
        
        if (code_files_added or code_files_modified) and not (test_files_added or test_files_modified):
            self.issues.append(CommitIssue(
                issue_type="missing_tests",
                severity="warning",
                message="Code changes without corresponding test changes"
            ))
    
    def _check_documentation_updates(self):
        """Check for documentation updates.
        # Check if code was added/modified but no documentation was updated
        doc_files_modified = [f for f in self.files_modified if f.endswith((".md", ".rst", ".txt"))]
        code_files_added = [f for f in self.files_added if f.endswith((".py", ".js", ".ts", ".java", ".c", ".cpp"))]
        
        # Check for docstrings in added functions
        missing_docstrings = []
        
        for file_path in self.files_added + self.files_modified:
            file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            if file and file.path.endswith(".py"):
                for func in getattr(file, "functions", []):
                    if not getattr(func, "docstring", None):
                        missing_docstrings.append(func.name)
        
        if missing_docstrings:
            self.issues.append(CommitIssue(
                issue_type="missing_docstrings",
                severity="info",
                message=f"Missing docstrings in {len(missing_docstrings)} functions"
            ))
        
        # If significant code was added but no documentation was updated
        if len(code_files_added) > 3 and not doc_files_modified:
            self.issues.append(CommitIssue(
                issue_type="missing_documentation",
                severity="info",
                message="Significant code additions without documentation updates"
            ))
    
    def get_diff_summary(self, file_path: str) -> str:
        
        Get a summary of changes for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            A string containing a summary of the changes
        
        if file_path in self.files_added:
            return f"File added: {file_path}"
        
        if file_path in self.files_removed:
            return f"File removed: {file_path}"
        
        if file_path in self.files_modified:
            original_file = next((f for f in self.original_codebase.files if f.path == file_path), None)
            commit_file = next((f for f in self.commit_codebase.files if f.path == file_path), None)
            
            if original_file and commit_file:
                original_lines = original_file.content.splitlines()
                commit_lines = commit_file.content.splitlines()
                
                diff = difflib.unified_diff(
                    original_lines,
                    commit_lines,
                    lineterm="",
                    n=3  # Context lines
                )
                
                return "\n".join(diff)
        
        return f"No changes found for {file_path}"
    
    def get_detailed_report(self) -> Dict[str, Any]:
        
        Get a detailed report of the commit analysis.
        
        Returns:
            A dictionary containing detailed analysis information
        
        # Analyze the commit if not already done
        if not hasattr(self, "result"):
            self.result = self.analyze_commit()
        
        # Create a detailed report
        report = {
            "summary": self.result.get_summary(),
            "is_properly_implemented": self.result.is_properly_implemented,
            "issues": [issue.to_dict() for issue in self.result.issues],
            "metrics_diff": self.result.metrics_diff,
            "file_changes": {
                "added": self.result.files_added,
                "modified": self.result.files_modified,
                "removed": self.result.files_removed
            },
            "diffs": {}
        }
        
        # Add diffs for modified files
        for file_path in self.result.files_modified[:10]:  # Limit to 10 files for brevity
            report["diffs"][file_path] = self.get_diff_summary(file_path)
        
        return report


