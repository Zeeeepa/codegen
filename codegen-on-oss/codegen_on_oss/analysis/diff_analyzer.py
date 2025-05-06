"""
Diff Analyzer Module

This module provides functionality for comparing two codebase snapshots
and analyzing the differences between them.
"""

import difflib
import logging
from typing import Any, Dict, List, Optional

# Import the CodebaseSnapshot class
from codegen_on_oss.snapshot.codebase_snapshot import CodebaseSnapshot

logger = logging.getLogger(__name__)


class DiffAnalyzer:
    """
    A class for analyzing differences between two codebase snapshots.
    """

    def __init__(self, original_snapshot: CodebaseSnapshot, modified_snapshot: CodebaseSnapshot):
        """
        Initialize a new DiffAnalyzer.

        Args:
            original_snapshot: The original/base codebase snapshot
            modified_snapshot: The modified/new codebase snapshot
        """
        self.original = original_snapshot
        self.modified = modified_snapshot

        # Cache for diff results
        self._file_diffs = None
        self._function_diffs = None
        self._class_diffs = None
        self._import_diffs = None
        self._complexity_changes = None

    def analyze_file_changes(self) -> Dict[str, str]:
        """
        Analyze changes to files between the two snapshots.

        Returns:
            A dictionary mapping file paths to change types:
            - 'added': File exists in modified but not in original
            - 'deleted': File exists in original but not in modified
            - 'modified': File exists in both but has changed
            - 'unchanged': File exists in both and has not changed
        """
        if self._file_diffs is not None:
            return self._file_diffs

        original_files = set(self.original.file_metrics.keys())
        modified_files = set(self.modified.file_metrics.keys())

        added_files = modified_files - original_files
        deleted_files = original_files - modified_files
        common_files = original_files.intersection(modified_files)

        self._file_diffs = {}

        # Mark added files
        for filepath in added_files:
            self._file_diffs[filepath] = "added"

        # Mark deleted files
        for filepath in deleted_files:
            self._file_diffs[filepath] = "deleted"

        # Check common files for modifications
        for filepath in common_files:
            original_hash = self.original.file_metrics[filepath]["content_hash"]
            modified_hash = self.modified.file_metrics[filepath]["content_hash"]

            if original_hash != modified_hash:
                self._file_diffs[filepath] = "modified"
            else:
                self._file_diffs[filepath] = "unchanged"

        return self._file_diffs

    def analyze_function_changes(self) -> Dict[str, str]:
        """
        Analyze changes to functions between the two snapshots.

        Returns:
            A dictionary mapping function qualified names to change types:
            - 'added': Function exists in modified but not in original
            - 'deleted': Function exists in original but not in modified
            - 'modified': Function exists in both but has changed
            - 'unchanged': Function exists in both and has not changed
            - 'moved': Function exists in both but has moved to a different file
        """
        if self._function_diffs is not None:
            return self._function_diffs

        original_functions = set(self.original.function_metrics.keys())
        modified_functions = set(self.modified.function_metrics.keys())

        added_functions = modified_functions - original_functions
        deleted_functions = original_functions - modified_functions
        common_functions = original_functions.intersection(modified_functions)

        self._function_diffs = {}

        # Mark added functions
        for func_name in added_functions:
            self._function_diffs[func_name] = "added"

        # Mark deleted functions
        for func_name in deleted_functions:
            self._function_diffs[func_name] = "deleted"

        # Check common functions for modifications or moves
        for func_name in common_functions:
            original_func = self.original.function_metrics[func_name]
            modified_func = self.modified.function_metrics[func_name]

            # Check if the function has moved to a different file
            if original_func["filepath"] != modified_func["filepath"]:
                self._function_diffs[func_name] = "moved"
            # Check if the function has changed (parameters, complexity, etc.)
            elif (
                original_func["parameter_count"] != modified_func["parameter_count"]
                or original_func["line_count"] != modified_func["line_count"]
                or original_func["cyclomatic_complexity"] != modified_func["cyclomatic_complexity"]
            ):
                self._function_diffs[func_name] = "modified"
            else:
                self._function_diffs[func_name] = "unchanged"

        return self._function_diffs

    def analyze_class_changes(self) -> Dict[str, str]:
        """
        Analyze changes to classes between the two snapshots.

        Returns:
            A dictionary mapping class qualified names to change types:
            - 'added': Class exists in modified but not in original
            - 'deleted': Class exists in original but not in modified
            - 'modified': Class exists in both but has changed
            - 'unchanged': Class exists in both and has not changed
            - 'moved': Class exists in both but has moved to a different file
        """
        if self._class_diffs is not None:
            return self._class_diffs

        original_classes = set(self.original.class_metrics.keys())
        modified_classes = set(self.modified.class_metrics.keys())

        added_classes = modified_classes - original_classes
        deleted_classes = original_classes - modified_classes
        common_classes = original_classes.intersection(modified_classes)

        self._class_diffs = {}

        # Mark added classes
        for class_name in added_classes:
            self._class_diffs[class_name] = "added"

        # Mark deleted classes
        for class_name in deleted_classes:
            self._class_diffs[class_name] = "deleted"

        # Check common classes for modifications or moves
        for class_name in common_classes:
            original_class = self.original.class_metrics[class_name]
            modified_class = self.modified.class_metrics[class_name]

            # Check if the class has moved to a different file
            if original_class["filepath"] != modified_class["filepath"]:
                self._class_diffs[class_name] = "moved"
            # Check if the class has changed (methods, attributes, etc.)
            elif (
                original_class["method_count"] != modified_class["method_count"]
                or original_class["attribute_count"] != modified_class["attribute_count"]
                or original_class["parent_class_count"] != modified_class["parent_class_count"]
            ):
                self._class_diffs[class_name] = "modified"
            else:
                self._class_diffs[class_name] = "unchanged"

        return self._class_diffs

    def analyze_import_changes(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Analyze changes to imports between the two snapshots.

        Returns:
            A dictionary with file paths as keys and dictionaries as values.
            Each inner dictionary has keys 'added', 'deleted', and 'unchanged',
            with lists of import names as values.
        """
        if self._import_diffs is not None:
            return self._import_diffs

        self._import_diffs = {}

        # Get all files from both snapshots
        all_files = set(self.original.import_metrics.keys()).union(
            set(self.modified.import_metrics.keys())
        )

        for filepath in all_files:
            original_imports = set(self.original.import_metrics.get(filepath, []))
            modified_imports = set(self.modified.import_metrics.get(filepath, []))

            added_imports = modified_imports - original_imports
            deleted_imports = original_imports - modified_imports
            unchanged_imports = original_imports.intersection(modified_imports)

            self._import_diffs[filepath] = {
                "added": list(added_imports),
                "deleted": list(deleted_imports),
                "unchanged": list(unchanged_imports),
            }

        return self._import_diffs

    def analyze_complexity_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze changes in cyclomatic complexity between the two snapshots.

        Returns:
            A dictionary mapping function qualified names to dictionaries with:
            - 'original': Original complexity
            - 'modified': Modified complexity
            - 'delta': Change in complexity (modified - original)
            - 'percent_change': Percentage change in complexity
        """
        if self._complexity_changes is not None:
            return self._complexity_changes

        self._complexity_changes = {}

        # Get functions that exist in both snapshots
        function_diffs = self.analyze_function_changes()
        common_functions = [
            func_name
            for func_name, change_type in function_diffs.items()
            if change_type in ["modified", "unchanged", "moved"]
        ]

        for func_name in common_functions:
            original_complexity = self.original.function_metrics[func_name]["cyclomatic_complexity"]
            modified_complexity = self.modified.function_metrics[func_name]["cyclomatic_complexity"]

            delta = modified_complexity - original_complexity

            # Calculate percent change, avoiding division by zero
            if original_complexity == 0:
                percent_change = float("inf") if delta > 0 else 0
            else:
                percent_change = (delta / original_complexity) * 100

            self._complexity_changes[func_name] = {
                "original": original_complexity,
                "modified": modified_complexity,
                "delta": delta,
                "percent_change": percent_change,
            }

        return self._complexity_changes

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all changes between the two snapshots.

        Returns:
            A dictionary with summary statistics for different types of changes.
        """
        file_changes = self.analyze_file_changes()
        function_changes = self.analyze_function_changes()
        class_changes = self.analyze_class_changes()
        complexity_changes = self.analyze_complexity_changes()

        # Count file changes by type
        file_counts = {
            "added": sum(1 for change_type in file_changes.values() if change_type == "added"),
            "deleted": sum(1 for change_type in file_changes.values() if change_type == "deleted"),
            "modified": sum(
                1 for change_type in file_changes.values() if change_type == "modified"
            ),
            "unchanged": sum(
                1 for change_type in file_changes.values() if change_type == "unchanged"
            ),
            "total": len(file_changes),
        }

        # Count function changes by type
        function_counts = {
            "added": sum(1 for change_type in function_changes.values() if change_type == "added"),
            "deleted": sum(
                1 for change_type in function_changes.values() if change_type == "deleted"
            ),
            "modified": sum(
                1 for change_type in function_changes.values() if change_type == "modified"
            ),
            "moved": sum(1 for change_type in function_changes.values() if change_type == "moved"),
            "unchanged": sum(
                1 for change_type in function_changes.values() if change_type == "unchanged"
            ),
            "total": len(function_changes),
        }

        # Count class changes by type
        class_counts = {
            "added": sum(1 for change_type in class_changes.values() if change_type == "added"),
            "deleted": sum(1 for change_type in class_changes.values() if change_type == "deleted"),
            "modified": sum(
                1 for change_type in class_changes.values() if change_type == "modified"
            ),
            "moved": sum(1 for change_type in class_changes.values() if change_type == "moved"),
            "unchanged": sum(
                1 for change_type in class_changes.values() if change_type == "unchanged"
            ),
            "total": len(class_changes),
        }

        # Calculate complexity change statistics
        complexity_stats = {
            "increased": sum(1 for change in complexity_changes.values() if change["delta"] > 0),
            "decreased": sum(1 for change in complexity_changes.values() if change["delta"] < 0),
            "unchanged": sum(1 for change in complexity_changes.values() if change["delta"] == 0),
            "total": len(complexity_changes),
        }

        if complexity_stats["total"] > 0:
            complexity_stats["avg_delta"] = (
                sum(change["delta"] for change in complexity_changes.values())
                / complexity_stats["total"]
            )
            complexity_stats["max_increase"] = max(
                (change["delta"] for change in complexity_changes.values()), default=0
            )
            complexity_stats["max_decrease"] = min(
                (change["delta"] for change in complexity_changes.values()), default=0
            )
        else:
            complexity_stats["avg_delta"] = 0
            complexity_stats["max_increase"] = 0
            complexity_stats["max_decrease"] = 0

        return {
            "file_changes": file_counts,
            "function_changes": function_counts,
            "class_changes": class_counts,
            "complexity_changes": complexity_stats,
            "original_snapshot_id": self.original.snapshot_id,
            "modified_snapshot_id": self.modified.snapshot_id,
            "original_commit": self.original.commit_sha,
            "modified_commit": self.modified.commit_sha,
        }

    def get_detailed_file_diff(self, filepath: str) -> Optional[List[str]]:
        """
        Get a detailed line-by-line diff for a specific file.

        Args:
            filepath: The path of the file to diff

        Returns:
            A list of diff lines, or None if the file doesn't exist in both snapshots
        """
        # Check if the file exists in both snapshots
        if filepath not in self.original.file_metrics or filepath not in self.modified.file_metrics:
            return None

        # Get the file content from the codebases
        original_file = None
        for file in self.original.codebase.files:
            if file.filepath == filepath:
                original_file = file
                break

        modified_file = None
        for file in self.modified.codebase.files:
            if file.filepath == filepath:
                modified_file = file
                break

        if not original_file or not modified_file:
            return None

        # Generate the diff
        original_lines = original_file.content.splitlines()
        modified_lines = modified_file.content.splitlines()

        diff = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f"a/{filepath}",
                tofile=f"b/{filepath}",
                lineterm="",
            )
        )

        return diff

    def get_high_risk_changes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify high-risk changes that might need special attention.

        Returns:
            A dictionary with categories of high-risk changes and lists of affected items.
        """
        high_risk = {
            "complexity_increases": [],
            "core_file_changes": [],
            "interface_changes": [],
            "dependency_changes": [],
        }

        # Identify functions with significant complexity increases
        complexity_changes = self.analyze_complexity_changes()
        for func_name, change in complexity_changes.items():
            # Consider a 30% increase or an absolute increase of 5 as high risk
            if change["percent_change"] > 30 or change["delta"] > 5:
                high_risk["complexity_increases"].append(
                    {
                        "function": func_name,
                        "original": change["original"],
                        "modified": change["modified"],
                        "delta": change["delta"],
                        "percent_change": change["percent_change"],
                    }
                )

        # Identify changes to core files (files with many dependencies)
        file_changes = self.analyze_file_changes()
        for filepath, change_type in file_changes.items():
            if change_type in ["modified", "deleted"] and filepath in self.original.file_metrics:
                # Consider files with many symbols as core files
                if self.original.file_metrics[filepath]["symbol_count"] > 10:
                    high_risk["core_file_changes"].append(
                        {
                            "filepath": filepath,
                            "change_type": change_type,
                            "symbol_count": self.original.file_metrics[filepath]["symbol_count"],
                        }
                    )

        # Identify interface changes (changes to function parameters)
        function_changes = self.analyze_function_changes()
        for func_name, change_type in function_changes.items():
            if change_type == "modified" and func_name in self.original.function_metrics:
                original_params = self.original.function_metrics[func_name]["parameter_count"]
                modified_params = self.modified.function_metrics[func_name]["parameter_count"]

                if original_params != modified_params:
                    high_risk["interface_changes"].append(
                        {
                            "function": func_name,
                            "original_params": original_params,
                            "modified_params": modified_params,
                        }
                    )

        # Identify dependency changes (changes to imports)
        import_changes = self.analyze_import_changes()
        for filepath, changes in import_changes.items():
            if changes["added"] or changes["deleted"]:
                high_risk["dependency_changes"].append(
                    {
                        "filepath": filepath,
                        "added_imports": changes["added"],
                        "deleted_imports": changes["deleted"],
                    }
                )

        return high_risk

    def format_summary_text(self) -> str:
        """
        Format a summary text of the comparison.

        Returns:
            Formatted summary text
        """
        summary = self.get_summary()

        text = f"""
Diff Analysis Summary
=====================

Original Snapshot: {summary["original_snapshot_id"]} (Commit: {summary["original_commit"] or "N/A"})
Modified Snapshot: {summary["modified_snapshot_id"]} (Commit: {summary["modified_commit"] or "N/A"})

File Changes:
- Added: {summary["file_changes"]["added"]}
- Deleted: {summary["file_changes"]["deleted"]}
- Modified: {summary["file_changes"]["modified"]}
- Unchanged: {summary["file_changes"]["unchanged"]}
- Total Files: {summary["file_changes"]["total"]}

Function Changes:
- Added: {summary["function_changes"]["added"]}
- Deleted: {summary["function_changes"]["deleted"]}
- Modified: {summary["function_changes"]["modified"]}
- Moved: {summary["function_changes"]["moved"]}
- Unchanged: {summary["function_changes"]["unchanged"]}
- Total Functions: {summary["function_changes"]["total"]}

Class Changes:
- Added: {summary["class_changes"]["added"]}
- Deleted: {summary["class_changes"]["deleted"]}
- Modified: {summary["class_changes"]["modified"]}
- Moved: {summary["class_changes"]["moved"]}
- Unchanged: {summary["class_changes"]["unchanged"]}
- Total Classes: {summary["class_changes"]["total"]}

Complexity Changes:
- Functions with increased complexity: {summary["complexity_changes"]["increased"]}
- Functions with decreased complexity: {summary["complexity_changes"]["decreased"]}
- Functions with unchanged complexity: {summary["complexity_changes"]["unchanged"]}
- Average complexity change: {summary["complexity_changes"]["avg_delta"]:.2f}
- Maximum complexity increase: {summary["complexity_changes"]["max_increase"]}
- Maximum complexity decrease: {summary["complexity_changes"]["max_decrease"]}
"""

        # Add high risk changes
        high_risk = self.get_high_risk_changes()

        if high_risk["complexity_increases"]:
            text += "\nHigh Risk - Significant Complexity Increases:\n"
            for item in high_risk["complexity_increases"]:
                text += f"- {item['function']}: {item['original']} → {item['modified']} ({item['delta']:+d}, {item['percent_change']:.1f}%)\n"

        if high_risk["core_file_changes"]:
            text += "\nHigh Risk - Core File Changes:\n"
            for item in high_risk["core_file_changes"]:
                text += f"- {item['filepath']} ({item['change_type']}, {item['symbol_count']} symbols)\n"

        if high_risk["interface_changes"]:
            text += "\nHigh Risk - Interface Changes:\n"
            for item in high_risk["interface_changes"]:
                text += f"- {item['function']}: Parameters changed from {item['original_params']} to {item['modified_params']}\n"

        if high_risk["dependency_changes"]:
            text += "\nHigh Risk - Dependency Changes:\n"
            for item in high_risk["dependency_changes"]:
                text += f"- {item['filepath']}:\n"
                if item["added_imports"]:
                    text += f"  - Added: {', '.join(item['added_imports'][:3])}"
                    if len(item["added_imports"]) > 3:
                        text += f" and {len(item['added_imports']) - 3} more"
                    text += "\n"
                if item["deleted_imports"]:
                    text += f"  - Deleted: {', '.join(item['deleted_imports'][:3])}"
                    if len(item["deleted_imports"]) > 3:
                        text += f" and {len(item['deleted_imports']) - 3} more"
                    text += "\n"

        return text

def perform_detailed_analysis(self) -> Dict[str, Any]:
    """Perform a detailed analysis of the differences between the two snapshots."""
    results = self._initialize_analysis_results()
    results.update(self._analyze_files_and_functions())
    results.update(self._analyze_complexity())
    results.update(self._analyze_risks())
    results['recommendations'] = self._generate_recommendations(results)
    return results

def _initialize_analysis_results(self) -> Dict[str, Any]:
    """Initialize the analysis results dictionary."""
    return {
            "added_files": [],
            "removed_files": [],
            "modified_files": [],
            "added_functions": [],
            "removed_functions": [],
            "modified_functions": [],
            "complexity_increases": [],
            "complexity_decreases": [],
            "potential_issues": [],
            "recommendations": [],
        }
