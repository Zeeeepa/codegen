#!/usr/bin/env python3
"""
Analysis Visualizer Module

This module provides visualization capabilities for code analysis results
including dead code detection, cyclomatic complexity, and issue heatmaps.
"""

import logging

from .visualizer import BaseVisualizer, OutputFormat, VisualizationType

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    from matplotlib.colors import LinearSegmentedColormap
except ImportError:
    logging.warning(
        "Visualization dependencies not found. Please install them with: pip install networkx matplotlib"
    )

logger = logging.getLogger(__name__)


class AnalysisVisualizer(BaseVisualizer):
    """
    Visualizer for code analysis results.

    This class provides methods to visualize analysis results such as
    dead code detection, cyclomatic complexity, and issue heatmaps.
    """

    def __init__(self, analyzer=None, codebase=None, context=None, **kwargs):
        """
        Initialize the AnalysisVisualizer.

        Args:
            analyzer: Analyzer with analysis results
            codebase: Codebase instance to visualize
            context: Context providing graph representation
            **kwargs: Additional configuration options
        """
        super().__init__(**kwargs)
        self.analyzer = analyzer
        self.codebase = codebase or (analyzer.base_codebase if analyzer else None)
        self.context = context or (analyzer.base_context if analyzer else None)

    def visualize_dead_code(self, path_filter: str | None = None):
        """
        Generate a visualization of dead (unused) code in the codebase.

        Args:
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        entity_name = path_filter or "codebase"

        # Initialize graph
        self._initialize_graph()

        # Check for analyzer
        if not self.analyzer:
            logger.error("Analyzer required for dead code visualization")
            return None

        # Check for analysis results
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.error("Analysis results not available")
            return None

        # Extract dead code information from analysis results
        dead_code = {}
        if (
            "static_analysis" in self.analyzer.results
            and "dead_code" in self.analyzer.results["static_analysis"]
        ):
            dead_code = self.analyzer.results["static_analysis"]["dead_code"]

        if not dead_code:
            logger.warning("No dead code detected in analysis results")
            return None

        # Create file nodes for containing dead code
        file_nodes = {}

        # Process unused functions
        if "unused_functions" in dead_code:
            for unused_func in dead_code["unused_functions"]:
                file_path = unused_func.get("file", "")

                # Skip if path filter is specified and doesn't match
                if path_filter and not file_path.startswith(path_filter):
                    continue

                # Add file node if not already added
                if file_path not in file_nodes:
                    # Find file in codebase
                    file_obj = None
                    for file in self.codebase.files:
                        if hasattr(file, "path") and str(file.path) == file_path:
                            file_obj = file
                            break

                    if file_obj:
                        file_name = file_path.split("/")[-1]
                        self._add_node(
                            file_obj,
                            name=file_name,
                            color=self.config.color_palette.get("File"),
                            file_path=file_path,
                        )

                        file_nodes[file_path] = file_obj

                # Add unused function node
                func_name = unused_func.get("name", "")
                func_line = unused_func.get("line", None)

                # Create a placeholder for the function (we don't have the actual object)
                func_obj = {
                    "name": func_name,
                    "file_path": file_path,
                    "line": func_line,
                    "type": "Function",
                }

                self._add_node(
                    func_obj,
                    name=func_name,
                    color=self.config.color_palette.get("Dead"),
                    file_path=file_path,
                    line=func_line,
                    is_dead=True,
                )

                # Add edge from file to function
                if file_path in file_nodes:
                    self._add_edge(
                        file_nodes[file_path], func_obj, type="contains_dead"
                    )

        # Process unused variables
        if "unused_variables" in dead_code:
            for unused_var in dead_code["unused_variables"]:
                file_path = unused_var.get("file", "")

                # Skip if path filter is specified and doesn't match
                if path_filter and not file_path.startswith(path_filter):
                    continue

                # Add file node if not already added
                if file_path not in file_nodes:
                    # Find file in codebase
                    file_obj = None
                    for file in self.codebase.files:
                        if hasattr(file, "path") and str(file.path) == file_path:
                            file_obj = file
                            break

                    if file_obj:
                        file_name = file_path.split("/")[-1]
                        self._add_node(
                            file_obj,
                            name=file_name,
                            color=self.config.color_palette.get("File"),
                            file_path=file_path,
                        )

                        file_nodes[file_path] = file_obj

                # Add unused variable node
                var_name = unused_var.get("name", "")
                var_line = unused_var.get("line", None)

                # Create a placeholder for the variable
                var_obj = {
                    "name": var_name,
                    "file_path": file_path,
                    "line": var_line,
                    "type": "Variable",
                }

                self._add_node(
                    var_obj,
                    name=var_name,
                    color=self.config.color_palette.get("Dead"),
                    file_path=file_path,
                    line=var_line,
                    is_dead=True,
                )

                # Add edge from file to variable
                if file_path in file_nodes:
                    self._add_edge(file_nodes[file_path], var_obj, type="contains_dead")

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, entity_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.DEAD_CODE, entity_name, fig
            )

    def visualize_cyclomatic_complexity(self, path_filter: str | None = None):
        """
        Generate a heatmap visualization of cyclomatic complexity.

        Args:
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        entity_name = path_filter or "codebase"

        # Check for analyzer
        if not self.analyzer:
            logger.error("Analyzer required for complexity visualization")
            return None

        # Check for analysis results
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            logger.error("Analysis results not available")
            return None

        # Extract complexity information from analysis results
        complexity_data = {}
        if (
            "static_analysis" in self.analyzer.results
            and "code_complexity" in self.analyzer.results["static_analysis"]
        ):
            complexity_data = self.analyzer.results["static_analysis"][
                "code_complexity"
            ]

        if not complexity_data:
            logger.warning("No complexity data found in analysis results")
            return None

        # Extract function complexities
        functions = []
        if "function_complexity" in complexity_data:
            for func_data in complexity_data["function_complexity"]:
                # Skip if path filter is specified and doesn't match
                if path_filter and not func_data.get("file", "").startswith(
                    path_filter
                ):
                    continue

                functions.append({
                    "name": func_data.get("name", ""),
                    "file": func_data.get("file", ""),
                    "complexity": func_data.get("complexity", 1),
                    "line": func_data.get("line", None),
                })

        # Sort functions by complexity (descending)
        functions.sort(key=lambda x: x.get("complexity", 0), reverse=True)

        # Generate heatmap visualization
        plt.figure(figsize=(12, 10))

        # Extract data for heatmap
        func_names = [
            f"{func['name']} ({func['file'].split('/')[-1]})" for func in functions[:30]
        ]
        complexities = [func.get("complexity", 0) for func in functions[:30]]

        # Create horizontal bar chart
        bars = plt.barh(func_names, complexities)

        # Color bars by complexity
        norm = plt.Normalize(1, max(10, max(complexities)))
        cmap = plt.cm.get_cmap("YlOrRd")

        for i, bar in enumerate(bars):
            complexity = complexities[i]
            bar.set_color(cmap(norm(complexity)))

        # Add labels and title
        plt.xlabel("Cyclomatic Complexity")
        plt.title("Top Functions by Cyclomatic Complexity")
        plt.grid(axis="x", linestyle="--", alpha=0.6)

        # Add colorbar
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), label="Complexity")

        # Save and return visualization
        return self._save_visualization(
            VisualizationType.CYCLOMATIC_COMPLEXITY, entity_name, plt.gcf()
        )

    def visualize_issues_heatmap(self, severity=None, path_filter: str | None = None):
        """
        Generate a heatmap visualization of issues in the codebase.

        Args:
            severity: Optional severity level to filter issues
            path_filter: Optional path to filter files

        Returns:
            Visualization data or path to saved file
        """
        entity_name = f"{severity.value if severity else 'all'}_issues"

        # Check for analyzer
        if not self.analyzer:
            logger.error("Analyzer required for issues visualization")
            return None

        # Check for analysis results
        if (
            not hasattr(self.analyzer, "results")
            or "issues" not in self.analyzer.results
        ):
            logger.error("Issues not available in analysis results")
            return None

        issues = self.analyzer.results["issues"]

        # Filter issues by severity if specified
        if severity:
            issues = [issue for issue in issues if issue.get("severity") == severity]

        # Filter issues by path if specified
        if path_filter:
            issues = [
                issue
                for issue in issues
                if issue.get("file", "").startswith(path_filter)
            ]

        if not issues:
            logger.warning("No issues found matching the criteria")
            return None

        # Group issues by file
        file_issues = {}
        for issue in issues:
            file_path = issue.get("file", "")
            if file_path not in file_issues:
                file_issues[file_path] = []

            file_issues[file_path].append(issue)

        # Generate heatmap visualization
        plt.figure(figsize=(12, 10))

        # Extract data for heatmap
        files = list(file_issues.keys())
        file_names = [file_path.split("/")[-1] for file_path in files]
        issue_counts = [len(file_issues[file_path]) for file_path in files]

        # Sort by issue count
        sorted_data = sorted(
            zip(file_names, issue_counts, files, strict=False),
            key=lambda x: x[1],
            reverse=True,
        )
        file_names, issue_counts, files = zip(*sorted_data, strict=False)

        # Create horizontal bar chart
        bars = plt.barh(file_names[:20], issue_counts[:20])

        # Color bars by issue count
        norm = plt.Normalize(1, max(5, max(issue_counts[:20])))
        cmap = plt.cm.get_cmap("OrRd")

        for i, bar in enumerate(bars):
            count = issue_counts[i]
            bar.set_color(cmap(norm(count)))

        # Add labels and title
        plt.xlabel("Number of Issues")
        severity_text = f" ({severity.value})" if severity else ""
        plt.title(f"Files with the Most Issues{severity_text}")
        plt.grid(axis="x", linestyle="--", alpha=0.6)

        # Add colorbar
        plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), label="Issue Count")

        # Save and return visualization
        return self._save_visualization(
            VisualizationType.ISSUES_HEATMAP, entity_name, plt.gcf()
        )

    def visualize_pr_comparison(self):
        """
        Generate a visualization comparing base branch with PR.

        Returns:
            Visualization data or path to saved file
        """
        # Check for analyzer with PR data
        if (
            not self.analyzer
            or not hasattr(self.analyzer, "pr_codebase")
            or not self.analyzer.pr_codebase
            or not self.analyzer.base_codebase
        ):
            logger.error("PR comparison requires analyzer with PR data")
            return None

        entity_name = (
            f"pr_{self.analyzer.pr_number}"
            if hasattr(self.analyzer, "pr_number") and self.analyzer.pr_number
            else "pr_comparison"
        )

        # Check for analysis results
        if (
            not hasattr(self.analyzer, "results")
            or "comparison" not in self.analyzer.results
        ):
            logger.error("Comparison data not available in analysis results")
            return None

        comparison = self.analyzer.results["comparison"]

        # Initialize graph
        self._initialize_graph()

        # Process symbol comparison data
        if "symbol_comparison" in comparison:
            for symbol_data in comparison["symbol_comparison"]:
                symbol_name = symbol_data.get("name", "")
                in_base = symbol_data.get("in_base", False)
                in_pr = symbol_data.get("in_pr", False)

                # Create a placeholder for the symbol
                symbol_obj = {
                    "name": symbol_name,
                    "in_base": in_base,
                    "in_pr": in_pr,
                    "type": "Symbol",
                }

                # Determine node color based on presence in base and PR
                if in_base and in_pr:
                    color = "#A5D6A7"  # Light green (modified)
                elif in_base:
                    color = "#EF9A9A"  # Light red (removed)
                else:
                    color = "#90CAF9"  # Light blue (added)

                # Add node for symbol
                self._add_node(
                    symbol_obj,
                    name=symbol_name,
                    color=color,
                    in_base=in_base,
                    in_pr=in_pr,
                )

                # Process parameter changes if available
                if "parameter_changes" in symbol_data:
                    param_changes = symbol_data["parameter_changes"]

                    # Process removed parameters
                    for param in param_changes.get("removed", []):
                        param_obj = {
                            "name": param,
                            "change_type": "removed",
                            "type": "Parameter",
                        }

                        self._add_node(
                            param_obj,
                            name=param,
                            color="#EF9A9A",  # Light red (removed)
                            change_type="removed",
                        )

                        self._add_edge(symbol_obj, param_obj, type="removed_parameter")

                    # Process added parameters
                    for param in param_changes.get("added", []):
                        param_obj = {
                            "name": param,
                            "change_type": "added",
                            "type": "Parameter",
                        }

                        self._add_node(
                            param_obj,
                            name=param,
                            color="#90CAF9",  # Light blue (added)
                            change_type="added",
                        )

                        self._add_edge(symbol_obj, param_obj, type="added_parameter")

                # Process return type changes if available
                if "return_type_change" in symbol_data:
                    return_type_change = symbol_data["return_type_change"]
                    old_type = return_type_change.get("old", "None")
                    new_type = return_type_change.get("new", "None")

                    return_obj = {
                        "name": f"{old_type} -> {new_type}",
                        "old_type": old_type,
                        "new_type": new_type,
                        "type": "ReturnType",
                    }

                    self._add_node(
                        return_obj,
                        name=f"{old_type} -> {new_type}",
                        color="#FFD54F",  # Amber (changed)
                        old_type=old_type,
                        new_type=new_type,
                    )

                    self._add_edge(symbol_obj, return_obj, type="return_type_change")

                # Process call site issues if available
                if "call_site_issues" in symbol_data:
                    for issue in symbol_data["call_site_issues"]:
                        issue_file = issue.get("file", "")
                        issue_line = issue.get("line", None)
                        issue_text = issue.get("issue", "")

                        # Create a placeholder for the issue
                        issue_obj = {
                            "name": issue_text,
                            "file": issue_file,
                            "line": issue_line,
                            "type": "Issue",
                        }

                        self._add_node(
                            issue_obj,
                            name=f"{issue_file.split('/')[-1]}:{issue_line}",
                            color="#EF5350",  # Red (error)
                            file_path=issue_file,
                            line=issue_line,
                            issue_text=issue_text,
                        )

                        self._add_edge(symbol_obj, issue_obj, type="call_site_issue")

        # Generate visualization data
        if self.config.output_format == OutputFormat.JSON:
            data = self._convert_graph_to_json()
            return self._save_visualization(
                VisualizationType.PR_COMPARISON, entity_name, data
            )
        else:
            fig = self._plot_graph()
            return self._save_visualization(
                VisualizationType.PR_COMPARISON, entity_name, fig
            )
