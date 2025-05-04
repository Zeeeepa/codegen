"""
Diff Analyzer for Code Comparison

This module provides a DiffAnalyzer class for comparing two codebases
and analyzing the differences between them.
"""

import difflib
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """
    Analyzer for comparing two codebases and analyzing the differences.
    """

    def __init__(
        self,
        base_snapshot: CodebaseSnapshot,
        head_snapshot: CodebaseSnapshot,
    ):
        """
        Initialize a new DiffAnalyzer.

        Args:
            base_snapshot: Base codebase snapshot
            head_snapshot: Head codebase snapshot
        """
        self.base_snapshot = base_snapshot
        self.head_snapshot = head_snapshot
        self.base_files = set(base_snapshot.get_file_paths())
        self.head_files = set(head_snapshot.get_file_paths())
        self.common_files = self.base_files.intersection(self.head_files)
        self.added_files = self.head_files - self.base_files
        self.removed_files = self.base_files - self.head_files
        self.modified_files = self._get_modified_files()
        
        # Cache for analysis results
        self._file_changes_cache = None
        self._function_changes_cache = None
        self._complexity_changes_cache = None
        self._risk_assessment_cache = None
        self._detailed_metrics_cache = None
        self._detailed_diff_cache = {}

    def _get_modified_files(self) -> Set[str]:
        """
        Get the set of modified files.

        Returns:
            Set of modified file paths
        """
        modified_files = set()
        for file_path in self.common_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            head_content = self.head_snapshot.get_file_content(file_path)
            if base_content != head_content:
                modified_files.add(file_path)
        return modified_files

    def analyze_file_changes(self) -> Dict[str, str]:
        """
        Analyze file changes between the two codebases.

        Returns:
            Dict mapping file paths to change types
        """
        if self._file_changes_cache is not None:
            return self._file_changes_cache
            
        file_changes = {}
        
        # Added files
        for file_path in self.added_files:
            file_changes[file_path] = "added"
            
        # Removed files
        for file_path in self.removed_files:
            file_changes[file_path] = "removed"
            
        # Modified files
        for file_path in self.modified_files:
            file_changes[file_path] = "modified"
            
        self._file_changes_cache = file_changes
        return file_changes

    def analyze_function_changes(self) -> Dict[str, str]:
        """
        Analyze function changes between the two codebases.

        Returns:
            Dict mapping function names to change types
        """
        if self._function_changes_cache is not None:
            return self._function_changes_cache
            
        function_changes = {}
        
        # Get functions from base snapshot
        base_functions = self.base_snapshot.get_functions()
        base_function_names = {f"{func['file']}:{func['name']}" for func in base_functions}
        
        # Get functions from head snapshot
        head_functions = self.head_snapshot.get_functions()
        head_function_names = {f"{func['file']}:{func['name']}" for func in head_functions}
        
        # Added functions
        for func in head_functions:
            func_key = f"{func['file']}:{func['name']}"
            if func_key not in base_function_names:
                function_changes[func_key] = "added"
                
        # Removed functions
        for func in base_functions:
            func_key = f"{func['file']}:{func['name']}"
            if func_key not in head_function_names:
                function_changes[func_key] = "removed"
                
        # Modified functions
        for func in head_functions:
            func_key = f"{func['file']}:{func['name']}"
            if func_key in base_function_names:
                # Find corresponding function in base
                base_func = next(
                    (f for f in base_functions if f"{f['file']}:{f['name']}" == func_key),
                    None,
                )
                if base_func and base_func.get("body") != func.get("body"):
                    function_changes[func_key] = "modified"
                    
        self._function_changes_cache = function_changes
        return function_changes

    def analyze_complexity_changes(self) -> Dict[str, float]:
        """
        Analyze complexity changes between the two codebases.

        Returns:
            Dict mapping file paths to complexity changes
        """
        if self._complexity_changes_cache is not None:
            return self._complexity_changes_cache
            
        complexity_changes = {}
        
        # Get complexity metrics for base snapshot
        base_complexity = self.base_snapshot.get_complexity_metrics()
        
        # Get complexity metrics for head snapshot
        head_complexity = self.head_snapshot.get_complexity_metrics()
        
        # Calculate changes
        for file_path in self.common_files:
            if file_path in base_complexity and file_path in head_complexity:
                base_value = base_complexity[file_path]
                head_value = head_complexity[file_path]
                complexity_changes[file_path] = head_value - base_value
                
        # Added files
        for file_path in self.added_files:
            if file_path in head_complexity:
                complexity_changes[file_path] = head_complexity[file_path]
                
        self._complexity_changes_cache = complexity_changes
        return complexity_changes

    def assess_risk(self) -> Dict[str, Any]:
        """
        Assess the risk of the changes.

        Returns:
            Dict containing risk assessment
        """
        if self._risk_assessment_cache is not None:
            return self._risk_assessment_cache
            
        # Get file changes
        file_changes = self.analyze_file_changes()
        
        # Get function changes
        function_changes = self.analyze_function_changes()
        
        # Get complexity changes
        complexity_changes = self.analyze_complexity_changes()
        
        # Calculate risk metrics
        num_added_files = sum(1 for change in file_changes.values() if change == "added")
        num_removed_files = sum(1 for change in file_changes.values() if change == "removed")
        num_modified_files = sum(1 for change in file_changes.values() if change == "modified")
        
        num_added_functions = sum(1 for change in function_changes.values() if change == "added")
        num_removed_functions = sum(1 for change in function_changes.values() if change == "removed")
        num_modified_functions = sum(1 for change in function_changes.values() if change == "modified")
        
        total_complexity_change = sum(complexity_changes.values())
        avg_complexity_change = total_complexity_change / len(complexity_changes) if complexity_changes else 0
        
        # Assess risk
        risk_assessment = {
            "overall_risk": self._calculate_overall_risk(
                num_added_files,
                num_removed_files,
                num_modified_files,
                num_added_functions,
                num_removed_functions,
                num_modified_functions,
                total_complexity_change,
            ),
            "file_risk": self._calculate_file_risk(
                num_added_files,
                num_removed_files,
                num_modified_files,
            ),
            "function_risk": self._calculate_function_risk(
                num_added_functions,
                num_removed_functions,
                num_modified_functions,
            ),
            "complexity_risk": self._calculate_complexity_risk(
                total_complexity_change,
                avg_complexity_change,
            ),
            "metrics": {
                "num_added_files": num_added_files,
                "num_removed_files": num_removed_files,
                "num_modified_files": num_modified_files,
                "num_added_functions": num_added_functions,
                "num_removed_functions": num_removed_functions,
                "num_modified_functions": num_modified_functions,
                "total_complexity_change": total_complexity_change,
                "avg_complexity_change": avg_complexity_change,
            },
        }
        
        self._risk_assessment_cache = risk_assessment
        return risk_assessment

    def _calculate_overall_risk(
        self,
        num_added_files: int,
        num_removed_files: int,
        num_modified_files: int,
        num_added_functions: int,
        num_removed_functions: int,
        num_modified_functions: int,
        total_complexity_change: float,
    ) -> str:
        """
        Calculate the overall risk of the changes.

        Args:
            num_added_files: Number of added files
            num_removed_files: Number of removed files
            num_modified_files: Number of modified files
            num_added_functions: Number of added functions
            num_removed_functions: Number of removed functions
            num_modified_functions: Number of modified functions
            total_complexity_change: Total complexity change

        Returns:
            Risk level (low, medium, high)
        """
        # Calculate risk score
        risk_score = 0
        
        # File changes
        risk_score += num_added_files * 1
        risk_score += num_removed_files * 1
        risk_score += num_modified_files * 0.5
        
        # Function changes
        risk_score += num_added_functions * 0.5
        risk_score += num_removed_functions * 0.5
        risk_score += num_modified_functions * 0.25
        
        # Complexity changes
        risk_score += max(0, total_complexity_change * 0.1)
        
        # Determine risk level
        if risk_score < 5:
            return "low"
        elif risk_score < 15:
            return "medium"
        else:
            return "high"

    def _calculate_file_risk(
        self,
        num_added_files: int,
        num_removed_files: int,
        num_modified_files: int,
    ) -> str:
        """
        Calculate the file risk of the changes.

        Args:
            num_added_files: Number of added files
            num_removed_files: Number of removed files
            num_modified_files: Number of modified files

        Returns:
            Risk level (low, medium, high)
        """
        # Calculate risk score
        risk_score = num_added_files * 1 + num_removed_files * 1 + num_modified_files * 0.5
        
        # Determine risk level
        if risk_score < 3:
            return "low"
        elif risk_score < 10:
            return "medium"
        else:
            return "high"

    def _calculate_function_risk(
        self,
        num_added_functions: int,
        num_removed_functions: int,
        num_modified_functions: int,
    ) -> str:
        """
        Calculate the function risk of the changes.

        Args:
            num_added_functions: Number of added functions
            num_removed_functions: Number of removed functions
            num_modified_functions: Number of modified functions

        Returns:
            Risk level (low, medium, high)
        """
        # Calculate risk score
        risk_score = (
            num_added_functions * 0.5 + num_removed_functions * 0.5 + num_modified_functions * 0.25
        )
        
        # Determine risk level
        if risk_score < 5:
            return "low"
        elif risk_score < 15:
            return "medium"
        else:
            return "high"

    def _calculate_complexity_risk(
        self,
        total_complexity_change: float,
        avg_complexity_change: float,
    ) -> str:
        """
        Calculate the complexity risk of the changes.

        Args:
            total_complexity_change: Total complexity change
            avg_complexity_change: Average complexity change

        Returns:
            Risk level (low, medium, high)
        """
        # Calculate risk score
        risk_score = max(0, total_complexity_change * 0.1)
        
        # Determine risk level
        if risk_score < 2:
            return "low"
        elif risk_score < 5:
            return "medium"
        else:
            return "high"

    def format_summary_text(self) -> str:
        """
        Format a summary of the changes as text.

        Returns:
            Summary text
        """
        # Get file changes
        file_changes = self.analyze_file_changes()
        
        # Get function changes
        function_changes = self.analyze_function_changes()
        
        # Get complexity changes
        complexity_changes = self.analyze_complexity_changes()
        
        # Get risk assessment
        risk_assessment = self.assess_risk()
        
        # Format summary
        summary = []
        
        # File changes
        num_added_files = sum(1 for change in file_changes.values() if change == "added")
        num_removed_files = sum(1 for change in file_changes.values() if change == "removed")
        num_modified_files = sum(1 for change in file_changes.values() if change == "modified")
        
        summary.append(
            f"Files: {num_added_files} added, {num_removed_files} removed, {num_modified_files} modified"
        )
        
        # Function changes
        num_added_functions = sum(1 for change in function_changes.values() if change == "added")
        num_removed_functions = sum(1 for change in function_changes.values() if change == "removed")
        num_modified_functions = sum(1 for change in function_changes.values() if change == "modified")
        
        summary.append(
            f"Functions: {num_added_functions} added, {num_removed_functions} removed, {num_modified_functions} modified"
        )
        
        # Complexity changes
        total_complexity_change = sum(complexity_changes.values())
        avg_complexity_change = total_complexity_change / len(complexity_changes) if complexity_changes else 0
        
        summary.append(
            f"Complexity: {total_complexity_change:.2f} total change, {avg_complexity_change:.2f} average change"
        )
        
        # Risk assessment
        summary.append(
            f"Risk: {risk_assessment['overall_risk']} overall, {risk_assessment['file_risk']} file, "
            f"{risk_assessment['function_risk']} function, {risk_assessment['complexity_risk']} complexity"
        )
        
        return "\n".join(summary)
        
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        Get detailed metrics about the changes.
        
        Returns:
            Dict containing detailed metrics
        """
        if self._detailed_metrics_cache is not None:
            return self._detailed_metrics_cache
            
        # Get file changes
        file_changes = self.analyze_file_changes()
        
        # Get function changes
        function_changes = self.analyze_function_changes()
        
        # Get complexity changes
        complexity_changes = self.analyze_complexity_changes()
        
        # Get risk assessment
        risk_assessment = self.assess_risk()
        
        # Calculate additional metrics
        file_extensions = {}
        for file_path in file_changes:
            ext = os.path.splitext(file_path)[1]
            if ext:
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
        # Calculate line changes
        line_changes = self._calculate_line_changes()
        
        # Calculate code churn
        code_churn = sum(abs(added + removed) for added, removed in line_changes.values())
        
        # Calculate change impact
        change_impact = self._calculate_change_impact()
        
        # Compile detailed metrics
        detailed_metrics = {
            "file_changes": {
                "total": len(file_changes),
                "added": sum(1 for change in file_changes.values() if change == "added"),
                "removed": sum(1 for change in file_changes.values() if change == "removed"),
                "modified": sum(1 for change in file_changes.values() if change == "modified"),
                "by_extension": file_extensions,
            },
            "function_changes": {
                "total": len(function_changes),
                "added": sum(1 for change in function_changes.values() if change == "added"),
                "removed": sum(1 for change in function_changes.values() if change == "removed"),
                "modified": sum(1 for change in function_changes.values() if change == "modified"),
            },
            "complexity_changes": {
                "total": sum(complexity_changes.values()),
                "average": sum(complexity_changes.values()) / len(complexity_changes) if complexity_changes else 0,
                "max_increase": max(complexity_changes.values()) if complexity_changes else 0,
                "max_decrease": min(complexity_changes.values()) if complexity_changes else 0,
            },
            "line_changes": {
                "total_added": sum(added for added, _ in line_changes.values()),
                "total_removed": sum(removed for _, removed in line_changes.values()),
                "net_change": sum(added - removed for added, removed in line_changes.values()),
                "code_churn": code_churn,
            },
            "change_impact": change_impact,
            "risk_assessment": risk_assessment,
        }
        
        self._detailed_metrics_cache = detailed_metrics
        return detailed_metrics
        
    def _calculate_line_changes(self) -> Dict[str, Tuple[int, int]]:
        """
        Calculate line changes for each modified file.
        
        Returns:
            Dict mapping file paths to tuples of (added_lines, removed_lines)
        """
        line_changes = {}
        
        # Calculate line changes for modified files
        for file_path in self.modified_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            head_content = self.head_snapshot.get_file_content(file_path)
            
            if base_content is None or head_content is None:
                continue
                
            base_lines = base_content.splitlines()
            head_lines = head_content.splitlines()
            
            diff = difflib.unified_diff(
                base_lines,
                head_lines,
                n=0,  # No context lines
            )
            
            added_lines = 0
            removed_lines = 0
            
            for line in diff:
                if line.startswith("+") and not line.startswith("+++"):
                    added_lines += 1
                elif line.startswith("-") and not line.startswith("---"):
                    removed_lines += 1
                    
            line_changes[file_path] = (added_lines, removed_lines)
            
        # Calculate line changes for added files
        for file_path in self.added_files:
            head_content = self.head_snapshot.get_file_content(file_path)
            
            if head_content is None:
                continue
                
            head_lines = head_content.splitlines()
            line_changes[file_path] = (len(head_lines), 0)
            
        # Calculate line changes for removed files
        for file_path in self.removed_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            
            if base_content is None:
                continue
                
            base_lines = base_content.splitlines()
            line_changes[file_path] = (0, len(base_lines))
            
        return line_changes
        
    def _calculate_change_impact(self) -> Dict[str, Any]:
        """
        Calculate the impact of the changes.
        
        Returns:
            Dict containing change impact metrics
        """
        # Get function changes
        function_changes = self.analyze_function_changes()
        
        # Calculate dependencies
        base_dependencies = self.base_snapshot.get_dependencies()
        head_dependencies = self.head_snapshot.get_dependencies()
        
        # Calculate changed dependencies
        changed_dependencies = {}
        for func_key, change_type in function_changes.items():
            if change_type in ("modified", "removed"):
                # Function was modified or removed, check what depends on it
                if func_key in base_dependencies:
                    changed_dependencies[func_key] = base_dependencies[func_key]
                    
        # Calculate impact metrics
        num_impacted_functions = sum(len(deps) for deps in changed_dependencies.values())
        max_impacted_functions = max((len(deps) for deps in changed_dependencies.values()), default=0)
        
        return {
            "impacted_functions": num_impacted_functions,
            "max_impacted_functions": max_impacted_functions,
            "changed_dependencies": changed_dependencies,
        }
        
    def get_detailed_diff(self, format: str = "unified") -> Dict[str, Any]:
        """
        Get detailed diff information.
        
        Args:
            format: Diff format (unified, side-by-side)
            
        Returns:
            Dict containing detailed diff information
        """
        if format in self._detailed_diff_cache:
            return self._detailed_diff_cache[format]
            
        detailed_diff = {}
        
        # Generate diffs for modified files
        for file_path in self.modified_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            head_content = self.head_snapshot.get_file_content(file_path)
            
            if base_content is None or head_content is None:
                continue
                
            base_lines = base_content.splitlines()
            head_lines = head_content.splitlines()
            
            if format == "unified":
                diff_lines = list(difflib.unified_diff(
                    base_lines,
                    head_lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    lineterm="",
                ))
                detailed_diff[file_path] = "\n".join(diff_lines)
            elif format == "side-by-side":
                diff = difflib.Differ().compare(base_lines, head_lines)
                detailed_diff[file_path] = "\n".join(diff)
            else:
                # Default to unified diff
                diff_lines = list(difflib.unified_diff(
                    base_lines,
                    head_lines,
                    fromfile=f"a/{file_path}",
                    tofile=f"b/{file_path}",
                    lineterm="",
                ))
                detailed_diff[file_path] = "\n".join(diff_lines)
                
        # Add information for added files
        for file_path in self.added_files:
            head_content = self.head_snapshot.get_file_content(file_path)
            
            if head_content is None:
                continue
                
            detailed_diff[file_path] = f"New file: {file_path}\n\n{head_content}"
            
        # Add information for removed files
        for file_path in self.removed_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            
            if base_content is None:
                continue
                
            detailed_diff[file_path] = f"Deleted file: {file_path}\n\n{base_content}"
            
        self._detailed_diff_cache[format] = detailed_diff
        return detailed_diff
