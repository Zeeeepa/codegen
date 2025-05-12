#!/usr/bin/env python3
"""
Codebase Visualizer Module

This module provides a unified interface to all visualization capabilities
for codebases. It integrates the specialized visualizers into a single,
easy-to-use API for generating various types of visualizations.
"""

import argparse
import logging
import os
import sys

from .analysis_visualizer import AnalysisVisualizer
from .code_visualizer import CodeVisualizer
from .visualizer import (
    OutputFormat,
    VisualizationConfig,
    VisualizationType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CodebaseVisualizer:
    """
    Main visualizer class providing a unified interface to all visualization capabilities.

    This class acts as a facade to the specialized visualizers, simplifying
    the generation of different types of visualizations for codebases.
    """

    def __init__(self, analyzer=None, codebase=None, context=None, config=None):
        """
        Initialize the CodebaseVisualizer.

        Args:
            analyzer: Optional analyzer with analysis results
            codebase: Optional codebase to visualize
            context: Optional context providing graph representation
            config: Visualization configuration options
        """
        self.analyzer = analyzer
        self.codebase = codebase or (analyzer.base_codebase if analyzer else None)
        self.context = context or (analyzer.base_context if analyzer else None)
        self.config = config or VisualizationConfig()

        # Initialize specialized visualizers
        self.code_visualizer = CodeVisualizer(
            analyzer=analyzer,
            codebase=self.codebase,
            context=self.context,
            config=self.config,
        )

        self.analysis_visualizer = AnalysisVisualizer(
            analyzer=analyzer,
            codebase=self.codebase,
            context=self.context,
            config=self.config,
        )

        # Create visualization directory if specified
        if self.config.output_directory:
            os.makedirs(self.config.output_directory, exist_ok=True)

        # Initialize codebase if needed
        if not self.codebase and not self.context:
            try:
                from codegen_on_oss.analyzers.context_codebase import CodebaseContext
                from codegen_on_oss.current_code_codebase import get_selected_codebase

                logger.info(
                    "No codebase or context provided, initializing from current directory"
                )
                self.codebase = get_selected_codebase()
                self.context = CodebaseContext(
                    codebase=self.codebase, base_path=os.getcwd()
                )

                # Update specialized visualizers
                self.code_visualizer.codebase = self.codebase
                self.code_visualizer.context = self.context
                self.analysis_visualizer.codebase = self.codebase
                self.analysis_visualizer.context = self.context
            except ImportError:
                logger.exception(
                    "Could not automatically initialize codebase. Please provide a codebase or context."
                )

    def visualize(self, visualization_type: VisualizationType, **kwargs):
        """
        Generate a visualization of the specified type.

        Args:
            visualization_type: Type of visualization to generate
            **kwargs: Additional arguments for the specific visualization

        Returns:
            Visualization data or path to saved file
        """
        # Route to the appropriate specialized visualizer based on visualization type
        if visualization_type in [
            VisualizationType.CALL_GRAPH,
            VisualizationType.DEPENDENCY_GRAPH,
            VisualizationType.BLAST_RADIUS,
            VisualizationType.CLASS_METHODS,
            VisualizationType.MODULE_DEPENDENCIES,
        ]:
            # Code structure visualizations
            return self._visualize_code_structure(visualization_type, **kwargs)
        elif visualization_type in [
            VisualizationType.DEAD_CODE,
            VisualizationType.CYCLOMATIC_COMPLEXITY,
            VisualizationType.ISSUES_HEATMAP,
            VisualizationType.PR_COMPARISON,
        ]:
            # Analysis result visualizations
            return self._visualize_analysis_results(visualization_type, **kwargs)
        else:
            logger.error(f"Unsupported visualization type: {visualization_type}")
            return None

    def _visualize_code_structure(
        self, visualization_type: VisualizationType, **kwargs
    ):
        """
        Generate a code structure visualization.

        Args:
            visualization_type: Type of visualization to generate
            **kwargs: Additional arguments for the specific visualization

        Returns:
            Visualization data or path to saved file
        """
        if visualization_type == VisualizationType.CALL_GRAPH:
            return self.code_visualizer.visualize_call_graph(
                function_name=kwargs.get("entity"), max_depth=kwargs.get("max_depth")
            )
        elif visualization_type == VisualizationType.DEPENDENCY_GRAPH:
            return self.code_visualizer.visualize_dependency_graph(
                symbol_name=kwargs.get("entity"), max_depth=kwargs.get("max_depth")
            )
        elif visualization_type == VisualizationType.BLAST_RADIUS:
            return self.code_visualizer.visualize_blast_radius(
                symbol_name=kwargs.get("entity"), max_depth=kwargs.get("max_depth")
            )
        elif visualization_type == VisualizationType.CLASS_METHODS:
            return self.code_visualizer.visualize_class_methods(
                class_name=kwargs.get("entity")
            )
        elif visualization_type == VisualizationType.MODULE_DEPENDENCIES:
            return self.code_visualizer.visualize_module_dependencies(
                module_path=kwargs.get("entity")
            )

    def _visualize_analysis_results(
        self, visualization_type: VisualizationType, **kwargs
    ):
        """
        Generate an analysis results visualization.

        Args:
            visualization_type: Type of visualization to generate
            **kwargs: Additional arguments for the specific visualization

        Returns:
            Visualization data or path to saved file
        """
        if not self.analyzer:
            logger.error(f"Analyzer required for {visualization_type} visualization")
            return None

        if visualization_type == VisualizationType.DEAD_CODE:
            return self.analysis_visualizer.visualize_dead_code(
                path_filter=kwargs.get("path_filter")
            )
        elif visualization_type == VisualizationType.CYCLOMATIC_COMPLEXITY:
            return self.analysis_visualizer.visualize_cyclomatic_complexity(
                path_filter=kwargs.get("path_filter")
            )
        elif visualization_type == VisualizationType.ISSUES_HEATMAP:
            return self.analysis_visualizer.visualize_issues_heatmap(
                severity=kwargs.get("severity"), path_filter=kwargs.get("path_filter")
            )
        elif visualization_type == VisualizationType.PR_COMPARISON:
            return self.analysis_visualizer.visualize_pr_comparison()

    # Convenience methods for common visualizations
    def visualize_call_graph(self, function_name: str, max_depth: int | None = None):
        """Convenience method for call graph visualization."""
        return self.visualize(
            VisualizationType.CALL_GRAPH, entity=function_name, max_depth=max_depth
        )

    def visualize_dependency_graph(
        self, symbol_name: str, max_depth: int | None = None
    ):
        """Convenience method for dependency graph visualization."""
        return self.visualize(
            VisualizationType.DEPENDENCY_GRAPH, entity=symbol_name, max_depth=max_depth
        )

    def visualize_blast_radius(self, symbol_name: str, max_depth: int | None = None):
        """Convenience method for blast radius visualization."""
        return self.visualize(
            VisualizationType.BLAST_RADIUS, entity=symbol_name, max_depth=max_depth
        )

    def visualize_class_methods(self, class_name: str):
        """Convenience method for class methods visualization."""
        return self.visualize(VisualizationType.CLASS_METHODS, entity=class_name)

    def visualize_module_dependencies(self, module_path: str):
        """Convenience method for module dependencies visualization."""
        return self.visualize(VisualizationType.MODULE_DEPENDENCIES, entity=module_path)

    def visualize_dead_code(self, path_filter: str | None = None):
        """Convenience method for dead code visualization."""
        return self.visualize(VisualizationType.DEAD_CODE, path_filter=path_filter)

    def visualize_cyclomatic_complexity(self, path_filter: str | None = None):
        """Convenience method for cyclomatic complexity visualization."""
        return self.visualize(
            VisualizationType.CYCLOMATIC_COMPLEXITY, path_filter=path_filter
        )

    def visualize_issues_heatmap(self, severity=None, path_filter: str | None = None):
        """Convenience method for issues heatmap visualization."""
        return self.visualize(
            VisualizationType.ISSUES_HEATMAP, severity=severity, path_filter=path_filter
        )

    def visualize_pr_comparison(self):
        """Convenience method for PR comparison visualization."""
        return self.visualize(VisualizationType.PR_COMPARISON)


# Command-line interface
def main():
    """
    Command-line interface for the codebase visualizer.

    This function parses command-line arguments and generates visualizations
    based on the specified parameters.
    """
    parser = argparse.ArgumentParser(
        description="Generate visualizations of codebase structure and analysis."
    )

    # Repository options
    repo_group = parser.add_argument_group("Repository Options")
    repo_group.add_argument("--repo-url", help="URL of the repository to analyze")
    repo_group.add_argument(
        "--repo-path", help="Local path to the repository to analyze"
    )
    repo_group.add_argument("--language", help="Programming language of the codebase")

    # Visualization options
    viz_group = parser.add_argument_group("Visualization Options")
    viz_group.add_argument(
        "--type",
        choices=[t.value for t in VisualizationType],
        required=True,
        help="Type of visualization to generate",
    )
    viz_group.add_argument(
        "--entity", help="Name of the entity to visualize (function, class, file, etc.)"
    )
    viz_group.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Maximum depth for recursive visualizations",
    )
    viz_group.add_argument(
        "--ignore-external", action="store_true", help="Ignore external dependencies"
    )
    viz_group.add_argument("--severity", help="Filter issues by severity")
    viz_group.add_argument("--path-filter", help="Filter by file path")

    # PR options
    pr_group = parser.add_argument_group("PR Options")
    pr_group.add_argument("--pr-number", type=int, help="PR number to analyze")
    pr_group.add_argument(
        "--base-branch", default="main", help="Base branch for comparison"
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output-format",
        choices=[f.value for f in OutputFormat],
        default="json",
        help="Output format for the visualization",
    )
    output_group.add_argument(
        "--output-directory", help="Directory to save visualizations"
    )
    output_group.add_argument(
        "--layout",
        choices=["spring", "kamada_kawai", "spectral"],
        default="spring",
        help="Layout algorithm for graph visualization",
    )

    args = parser.parse_args()

    # Create visualizer configuration
    config = VisualizationConfig(
        max_depth=args.max_depth,
        ignore_external=args.ignore_external,
        output_format=OutputFormat(args.output_format),
        output_directory=args.output_directory,
        layout_algorithm=args.layout,
    )

    try:
        # Import analyzer only if needed
        if (
            args.type
            in ["pr_comparison", "dead_code", "cyclomatic_complexity", "issues_heatmap"]
            or args.pr_number
        ):
            from codegen_on_oss.analyzers.codebase_analyzer import CodebaseAnalyzer

            # Create analyzer
            analyzer = CodebaseAnalyzer(
                repo_url=args.repo_url,
                repo_path=args.repo_path,
                base_branch=args.base_branch,
                pr_number=args.pr_number,
                language=args.language,
            )
        else:
            analyzer = None
    except ImportError:
        logger.warning(
            "CodebaseAnalyzer not available. Some visualizations may not work."
        )
        analyzer = None

    # Create visualizer
    visualizer = CodebaseVisualizer(analyzer=analyzer, config=config)

    # Generate visualization based on type
    viz_type = VisualizationType(args.type)
    result = None

    # Process specific requirements for each visualization type
    if (
        viz_type
        in [
            VisualizationType.CALL_GRAPH,
            VisualizationType.DEPENDENCY_GRAPH,
            VisualizationType.BLAST_RADIUS,
            VisualizationType.CLASS_METHODS,
            VisualizationType.MODULE_DEPENDENCIES,
        ]
        and not args.entity
    ):
        logger.error(f"Entity name required for {viz_type} visualization")
        sys.exit(1)

    if (
        viz_type == VisualizationType.PR_COMPARISON
        and not args.pr_number
        and not (analyzer and hasattr(analyzer, "pr_number"))
    ):
        logger.error("PR number required for PR comparison visualization")
        sys.exit(1)

    # Generate visualization
    result = visualizer.visualize(
        viz_type,
        entity=args.entity,
        max_depth=args.max_depth,
        severity=args.severity,
        path_filter=args.path_filter,
    )

    # Output result
    if result:
        logger.info(f"Visualization completed: {result}")
    else:
        logger.error("Failed to generate visualization")
        sys.exit(1)


if __name__ == "__main__":
    main()
