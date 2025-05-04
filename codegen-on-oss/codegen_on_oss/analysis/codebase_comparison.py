"""
Codebase Comparison Module

This module provides enhanced functionality for comparing codebases,
including original codebase and PR version codebase.
"""

import difflib
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple

from codegen_on_oss.analysis.diff_analyzer import DiffAnalyzer
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)


class CodebaseComparison:
    """
    Enhanced codebase comparison functionality.
    """

    def __init__(
        self,
        base_snapshot: CodebaseSnapshot,
        head_snapshot: CodebaseSnapshot,
    ):
        """
        Initialize a new CodebaseComparison.

        Args:
            base_snapshot: Base codebase snapshot
            head_snapshot: Head codebase snapshot
        """
        self.base_snapshot = base_snapshot
        self.head_snapshot = head_snapshot
        self.diff_analyzer = DiffAnalyzer(base_snapshot, head_snapshot)

    def compare_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Compare files between base and head snapshots.

        Returns:
            Dict mapping file paths to comparison results
        """
        base_files = set(self.base_snapshot.get_file_paths())
        head_files = set(self.head_snapshot.get_file_paths())

        added_files = head_files - base_files
        removed_files = base_files - head_files
        common_files = base_files.intersection(head_files)

        results = {}

        # Process added files
        for file_path in added_files:
            # Use chunked processing for large files
            content = self.head_snapshot.get_file_content(file_path)
            line_count = self._count_lines_safely(content)
            
            results[file_path] = {
                "status": "added",
                "content": content if len(content) < 1024 * 1024 else f"Large file: {line_count} lines",
                "lines_added": line_count,
                "lines_removed": 0,
            }

        # Process removed files
        for file_path in removed_files:
            # Use chunked processing for large files
            content = self.base_snapshot.get_file_content(file_path)
            line_count = self._count_lines_safely(content)
            
            results[file_path] = {
                "status": "removed",
                "content": content if len(content) < 1024 * 1024 else f"Large file: {line_count} lines",
                "lines_added": 0,
                "lines_removed": line_count,
            }

        # Process modified files
        for file_path in common_files:
            base_content = self.base_snapshot.get_file_content(file_path)
            head_content = self.head_snapshot.get_file_content(file_path)

            if base_content == head_content:
                # File not modified
                continue

            # Check file size before processing
            if len(base_content) > 10 * 1024 * 1024 or len(head_content) > 10 * 1024 * 1024:
                # For very large files, just report the size difference
                base_lines = self._count_lines_safely(base_content)
                head_lines = self._count_lines_safely(head_content)
                lines_added = max(0, head_lines - base_lines)
                lines_removed = max(0, base_lines - head_lines)
                
                results[file_path] = {
                    "status": "modified",
                    "diff": f"Large file: {base_lines} lines -> {head_lines} lines",
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "is_large_file": True,
                }
                continue

            # For smaller files, calculate diff
            try:
                # Calculate diff using chunked processing
                diff = list(
                    difflib.unified_diff(
                        base_content.splitlines(),
                        head_content.splitlines(),
                        lineterm="",
                    )
                )

                # Count added and removed lines
                lines_added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
                lines_removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

                results[file_path] = {
                    "status": "modified",
                    "diff": "\n".join(diff) if len(diff) < 1000 else f"Large diff: {len(diff)} lines",
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                }
            except MemoryError:
                # Fallback for memory errors
                logger.warning(f"Memory error processing diff for {file_path}, using size-based comparison")
                base_lines = self._count_lines_safely(base_content)
                head_lines = self._count_lines_safely(head_content)
                lines_added = max(0, head_lines - base_lines)
                lines_removed = max(0, base_lines - head_lines)
                
                results[file_path] = {
                    "status": "modified",
                    "diff": f"Large file: {base_lines} lines -> {head_lines} lines",
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "is_large_file": True,
                }

        return results
        
    def _count_lines_safely(self, content: str) -> int:
        """
        Count lines in content safely, handling large files.
        
        Args:
            content: File content
            
        Returns:
            Number of lines
        """
        # For small files, use splitlines
        if len(content) < 1024 * 1024:  # 1MB
            return len(content.splitlines())
        
        # For large files, count newlines manually in chunks
        line_count = 1  # Start with 1 for the last line that might not end with newline
        chunk_size = 1024 * 1024  # 1MB chunks
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            line_count += chunk.count('\n')
            
        return line_count

    def compare_functions(self) -> Dict[str, Dict[str, Any]]:
        """
        Compare functions between base and head snapshots.

        Returns:
            Dict mapping function names to comparison results
        """
        # Use the diff analyzer to get function changes
        function_changes = self.diff_analyzer.analyze_function_changes()

        # Enhance function changes with additional information
        results = {}
        for func_name, change_type in function_changes.items():
            if change_type == "added":
                # Function added in head
                results[func_name] = {
                    "status": "added",
                    "complexity": self._get_function_complexity(func_name, self.head_snapshot),
                    "parameters": self._get_function_parameters(func_name, self.head_snapshot),
                    "return_type": self._get_function_return_type(func_name, self.head_snapshot),
                }
            elif change_type == "removed":
                # Function removed in head
                results[func_name] = {
                    "status": "removed",
                    "complexity": self._get_function_complexity(func_name, self.base_snapshot),
                    "parameters": self._get_function_parameters(func_name, self.base_snapshot),
                    "return_type": self._get_function_return_type(func_name, self.base_snapshot),
                }
            elif change_type == "modified":
                # Function modified in head
                base_complexity = self._get_function_complexity(func_name, self.base_snapshot)
                head_complexity = self._get_function_complexity(func_name, self.head_snapshot)
                base_params = self._get_function_parameters(func_name, self.base_snapshot)
                head_params = self._get_function_parameters(func_name, self.head_snapshot)
                base_return = self._get_function_return_type(func_name, self.base_snapshot)
                head_return = self._get_function_return_type(func_name, self.head_snapshot)

                results[func_name] = {
                    "status": "modified",
                    "complexity_change": head_complexity - base_complexity if base_complexity and head_complexity else None,
                    "parameter_changes": self._compare_parameters(base_params, head_params),
                    "return_type_changed": base_return != head_return,
                }

        return results

    def compare_classes(self) -> Dict[str, Dict[str, Any]]:
        """
        Compare classes between base and head snapshots.

        Returns:
            Dict mapping class names to comparison results
        """
        base_classes = self._get_classes(self.base_snapshot)
        head_classes = self._get_classes(self.head_snapshot)

        added_classes = head_classes - base_classes
        removed_classes = base_classes - head_classes
        common_classes = base_classes.intersection(head_classes)

        results = {}

        # Process added classes
        for class_name in added_classes:
            results[class_name] = {
                "status": "added",
                "methods": self._get_class_methods(class_name, self.head_snapshot),
                "attributes": self._get_class_attributes(class_name, self.head_snapshot),
            }

        # Process removed classes
        for class_name in removed_classes:
            results[class_name] = {
                "status": "removed",
                "methods": self._get_class_methods(class_name, self.base_snapshot),
                "attributes": self._get_class_attributes(class_name, self.base_snapshot),
            }

        # Process modified classes
        for class_name in common_classes:
            base_methods = self._get_class_methods(class_name, self.base_snapshot)
            head_methods = self._get_class_methods(class_name, self.head_snapshot)
            base_attrs = self._get_class_attributes(class_name, self.base_snapshot)
            head_attrs = self._get_class_attributes(class_name, self.head_snapshot)

            if base_methods == head_methods and base_attrs == head_attrs:
                # Class not modified
                continue

            results[class_name] = {
                "status": "modified",
                "methods_added": list(set(head_methods) - set(base_methods)),
                "methods_removed": list(set(base_methods) - set(head_methods)),
                "attributes_added": list(set(head_attrs) - set(base_attrs)),
                "attributes_removed": list(set(base_attrs) - set(head_attrs)),
            }

        return results

    def analyze_impact(self) -> Dict[str, Any]:
        """
        Analyze the impact of changes between base and head snapshots.

        Returns:
            Dict containing impact analysis results
        """
        # Get file, function, and class comparisons
        file_comparison = self.compare_files()
        function_comparison = self.compare_functions()
        class_comparison = self.compare_classes()

        # Calculate statistics
        total_files_changed = len(file_comparison)
        total_functions_changed = len(function_comparison)
        total_classes_changed = len(class_comparison)

        files_added = sum(1 for f in file_comparison.values() if f["status"] == "added")
        files_removed = sum(1 for f in file_comparison.values() if f["status"] == "removed")
        files_modified = sum(1 for f in file_comparison.values() if f["status"] == "modified")

        functions_added = sum(1 for f in function_comparison.values() if f["status"] == "added")
        functions_removed = sum(1 for f in function_comparison.values() if f["status"] == "removed")
        functions_modified = sum(1 for f in function_comparison.values() if f["status"] == "modified")

        classes_added = sum(1 for c in class_comparison.values() if c["status"] == "added")
        classes_removed = sum(1 for c in class_comparison.values() if c["status"] == "removed")
        classes_modified = sum(1 for c in class_comparison.values() if c["status"] == "modified")

        total_lines_added = sum(f.get("lines_added", 0) for f in file_comparison.values())
        total_lines_removed = sum(f.get("lines_removed", 0) for f in file_comparison.values())

        # Calculate complexity changes
        complexity_changes = self.diff_analyzer.analyze_complexity_changes()
        avg_complexity_change = (
            sum(complexity_changes.values()) / len(complexity_changes)
            if complexity_changes
            else 0
        )

        # Assess risk
        risk_assessment = self.diff_analyzer.assess_risk()

        # Compile results
        return {
            "statistics": {
                "total_files_changed": total_files_changed,
                "total_functions_changed": total_functions_changed,
                "total_classes_changed": total_classes_changed,
                "files_added": files_added,
                "files_removed": files_removed,
                "files_modified": files_modified,
                "functions_added": functions_added,
                "functions_removed": functions_removed,
                "functions_modified": functions_modified,
                "classes_added": classes_added,
                "classes_removed": classes_removed,
                "classes_modified": classes_modified,
                "total_lines_added": total_lines_added,
                "total_lines_removed": total_lines_removed,
                "net_line_change": total_lines_added - total_lines_removed,
            },
            "complexity": {
                "average_change": avg_complexity_change,
                "details": complexity_changes,
            },
            "risk_assessment": risk_assessment,
        }

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive comparison report.

        Returns:
            Dict containing the comparison report
        """
        # Get file, function, and class comparisons
        file_comparison = self.compare_files()
        function_comparison = self.compare_functions()
        class_comparison = self.compare_classes()

        # Get impact analysis
        impact_analysis = self.analyze_impact()

        # Generate summary
        summary = self._generate_summary(impact_analysis)

        # Compile report
        return {
            "base_info": {
                "repo_url": self.base_snapshot.repo_url,
                "branch": self.base_snapshot.branch,
                "commit": self.base_snapshot.commit,
            },
            "head_info": {
                "repo_url": self.head_snapshot.repo_url,
                "branch": self.head_snapshot.branch,
                "commit": self.head_snapshot.commit,
            },
            "summary": summary,
            "impact_analysis": impact_analysis,
            "file_changes": file_comparison,
            "function_changes": function_comparison,
            "class_changes": class_comparison,
        }

    def _generate_summary(self, impact_analysis: Dict[str, Any]) -> str:
        """
        Generate a summary of the comparison.

        Args:
            impact_analysis: Impact analysis results

        Returns:
            Summary string
        """
        stats = impact_analysis["statistics"]
        risk = impact_analysis["risk_assessment"]

        summary = (
            f"Comparison between {self.base_snapshot.repo_url} ({self.base_snapshot.branch}) "
            f"and {self.head_snapshot.repo_url} ({self.head_snapshot.branch}).\n\n"
        )

        summary += "## Changes Summary\n"
        summary += f"- Files: {stats['files_added']} added, {stats['files_removed']} removed, {stats['files_modified']} modified\n"
        summary += f"- Functions: {stats['functions_added']} added, {stats['functions_removed']} removed, {stats['functions_modified']} modified\n"
        summary += f"- Classes: {stats['classes_added']} added, {stats['classes_removed']} removed, {stats['classes_modified']} modified\n"
        summary += f"- Lines: {stats['total_lines_added']} added, {stats['total_lines_removed']} removed (net: {stats['net_line_change']})\n\n"

        summary += "## Risk Assessment\n"
        for category, assessment in risk.items():
            summary += f"- {category}: {assessment}\n"

        return summary

    def _get_function_complexity(
        self, func_name: str, snapshot: CodebaseSnapshot
    ) -> Optional[float]:
        """
        Get the complexity of a function.

        Args:
            func_name: Function name
            snapshot: Codebase snapshot

        Returns:
            Function complexity or None if not available
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get the function's complexity
        return None

    def _get_function_parameters(
        self, func_name: str, snapshot: CodebaseSnapshot
    ) -> List[Dict[str, str]]:
        """
        Get the parameters of a function.

        Args:
            func_name: Function name
            snapshot: Codebase snapshot

        Returns:
            List of parameter dictionaries
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get the function's parameters
        return []

    def _get_function_return_type(
        self, func_name: str, snapshot: CodebaseSnapshot
    ) -> Optional[str]:
        """
        Get the return type of a function.

        Args:
            func_name: Function name
            snapshot: Codebase snapshot

        Returns:
            Return type or None if not available
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get the function's return type
        return None

    def _compare_parameters(
        self, base_params: List[Dict[str, str]], head_params: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Compare function parameters.

        Args:
            base_params: Base parameters
            head_params: Head parameters

        Returns:
            Parameter comparison results
        """
        # This is a placeholder - in a real implementation, you would
        # compare the parameters and return the differences
        return {
            "added": [],
            "removed": [],
            "modified": [],
        }

    def _get_classes(self, snapshot: CodebaseSnapshot) -> Set[str]:
        """
        Get all classes in a snapshot.

        Args:
            snapshot: Codebase snapshot

        Returns:
            Set of class names
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get all classes
        return set()

    def _get_class_methods(
        self, class_name: str, snapshot: CodebaseSnapshot
    ) -> List[str]:
        """
        Get the methods of a class.

        Args:
            class_name: Class name
            snapshot: Codebase snapshot

        Returns:
            List of method names
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get the class's methods
        return []

    def _get_class_attributes(
        self, class_name: str, snapshot: CodebaseSnapshot
    ) -> List[str]:
        """
        Get the attributes of a class.

        Args:
            class_name: Class name
            snapshot: Codebase snapshot

        Returns:
            List of attribute names
        """
        # This is a placeholder - in a real implementation, you would
        # use the snapshot to get the class's attributes
        return []
