#!/usr/bin/env python3
"""
Analyzer API Module

This module provides the API interface for the codegit-on-git frontend to interact
with the codebase analysis backend. It handles requests for analysis, visualization,
and data export.
"""

import logging
from typing import Any

# Import analyzer components
from codegen_on_oss.analyzers.analyzer import AnalyzerManager
from codegen_on_oss.analyzers.issues import (
    AnalysisType,
    IssueCategory,
    IssueSeverity,
)
from codegen_on_oss.analyzers.visualization import (
    Visualizer,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CodegenAnalyzerAPI:
    """
    Backend API for codegit-on-git.

    This class provides a unified interface for the frontend to interact with
    the codebase analysis backend, including analysis, visualization, and data export.
    """

    def __init__(self, repo_path: str | None = None, repo_url: str | None = None):
        """
        Initialize the API with a repository.

        Args:
            repo_path: Local path to the repository
            repo_url: URL of the repository
        """
        # Initialize analyzer
        self.analyzer = AnalyzerManager(repo_path=repo_path, repo_url=repo_url)

        # Initialize visualizer when needed
        self._visualizer = None

        # Cache for analysis results
        self._analysis_cache = {}

    @property
    def visualizer(self) -> Visualizer:
        """Get or initialize visualizer."""
        if self._visualizer is None:
            self._visualizer = Visualizer()
        return self._visualizer

    def analyze_codebase(
        self,
        analysis_types: list[str | AnalysisType] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Analyze the entire codebase.

        Args:
            analysis_types: Types of analysis to perform
            force_refresh: Whether to force a refresh of the analysis

        Returns:
            Analysis results
        """
        cache_key = str(analysis_types) if analysis_types else "default"

        # Check cache first
        if not force_refresh and cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        # Run analysis
        results = self.analyzer.analyze(analysis_types=analysis_types)

        # Cache results
        self._analysis_cache[cache_key] = results

        return results

    def analyze_pr(
        self,
        pr_number: int,
        analysis_types: list[str | AnalysisType] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Analyze a specific PR.

        Args:
            pr_number: PR number to analyze
            analysis_types: Types of analysis to perform
            force_refresh: Whether to force a refresh of the analysis

        Returns:
            Analysis results
        """
        cache_key = f"pr_{pr_number}_{analysis_types!s}"

        # Check cache first
        if not force_refresh and cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        # Set PR number
        self.analyzer.pr_number = pr_number

        # Use default analysis types if none provided
        if analysis_types is None:
            analysis_types = ["pr", "code_quality"]

        # Run analysis
        results = self.analyzer.analyze(analysis_types=analysis_types)

        # Cache results
        self._analysis_cache[cache_key] = results

        return results

    def get_issues(
        self,
        severity: str | IssueSeverity | None = None,
        category: str | IssueCategory | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get issues matching criteria.

        Args:
            severity: Issue severity to filter by
            category: Issue category to filter by

        Returns:
            List of matching issues
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase()

        # Convert string severity to enum if needed
        if isinstance(severity, str):
            severity = IssueSeverity(severity)

        # Convert string category to enum if needed
        if isinstance(category, str):
            category = IssueCategory(category)

        # Get issues
        issues = self.analyzer.get_issues(severity=severity, category=category)

        # Convert to dictionaries
        return [issue.to_dict() for issue in issues]

    def find_symbol(self, symbol_name: str) -> dict[str, Any] | None:
        """
        Find a specific symbol in the codebase.

        Args:
            symbol_name: Name of the symbol to find

        Returns:
            Symbol information if found, None otherwise
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase()

        # Get symbol
        symbol = self.analyzer.base_codebase.get_symbol(symbol_name)

        if symbol:
            # Convert to dictionary
            return self._symbol_to_dict(symbol)

        return None

    def get_module_dependencies(
        self,
        module_path: str | None = None,
        layout: str = "hierarchical",
        format: str = "json",
    ) -> dict[str, Any]:
        """
        Get module dependencies.

        Args:
            module_path: Path to the module to analyze
            layout: Layout algorithm to use
            format: Output format

        Returns:
            Module dependency visualization
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["dependency"])

        # Generate visualization
        viz = self.visualizer.generate_module_dependency_graph(
            codebase_context=self.analyzer.base_context,
            module_path=module_path,
            layout=layout,
        )

        # Export if needed
        if format != "json":
            return self.visualizer.export(viz, format=format)

        return viz

    def generate_dependency_graph(
        self,
        repo_path: str | None = None,
        module_path: str | None = None,
        layout: str = "hierarchical",
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Generate a dependency graph for the codebase.

        Args:
            repo_path: Path to the repository (optional, uses self.repo_path if not provided)
            module_path: Path to the specific module to analyze (optional)
            layout: Graph layout algorithm (hierarchical, force, circular)
            output_format: Output format (json, dot, graphml)

        Returns:
            Dictionary containing the dependency graph data
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["dependency"])

        # Generate visualization
        viz = self.visualizer.generate_module_dependency_graph(
            codebase_context=self.analyzer.base_context,
            module_path=module_path,
            layout=layout,
        )

        # Export if needed
        if output_format != "json":
            return self.visualizer.export(viz, format=output_format)

        return viz

    def get_function_call_graph(
        self,
        function_name: str | list[str],
        depth: int = 2,
        layout: str = "hierarchical",
        format: str = "json",
    ) -> dict[str, Any]:
        """
        Get function call graph.

        Args:
            function_name: Name of the function(s) to analyze
            depth: Maximum depth of the call graph
            layout: Layout algorithm to use
            format: Output format

        Returns:
            Function call graph visualization
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Generate visualization
        viz = self.visualizer.generate_function_call_graph(
            functions=function_name,
            codebase_context=self.analyzer.base_context,
            depth=depth,
            layout=layout,
        )

        # Export if needed
        if format != "json":
            return self.visualizer.export(viz, format=format)

        return viz

    def generate_call_graph(
        self,
        function_name: str | None = None,
        file_path: str | None = None,
        depth: int = 2,
        layout: str = "hierarchical",
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Generate a call graph for a specific function or file.

        Args:
            function_name: Name of the function to analyze
            file_path: Path to the file containing the function
            depth: Maximum depth of the call graph
            layout: Graph layout algorithm (hierarchical, force, circular)
            output_format: Output format (json, dot, graphml)

        Returns:
            Dictionary containing the call graph data
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Generate visualization
        viz = self.visualizer.generate_function_call_graph(
            functions=function_name,
            codebase_context=self.analyzer.base_context,
            depth=depth,
            layout=layout,
        )

        # Export if needed
        if output_format != "json":
            return self.visualizer.export(viz, format=output_format)

        return viz

    def get_pr_impact(
        self,
        pr_number: int | None = None,
        layout: str = "force",
        format: str = "json",
    ) -> dict[str, Any]:
        """
        Get PR impact visualization.

        Args:
            pr_number: PR number to analyze
            layout: Layout algorithm to use
            format: Output format

        Returns:
            PR impact visualization
        """
        # Analyze PR if needed
        if pr_number is not None:
            self.analyze_pr(pr_number, analysis_types=["pr"])
        elif self.analyzer.pr_number is None:
            raise ValueError("No PR number specified")

        # Generate visualization
        viz = self.visualizer.generate_pr_diff_visualization(
            pr_analysis=self.analyzer.results["results"]["pr"], layout=layout
        )

        # Export if needed
        if format != "json":
            return self.visualizer.export(viz, format=format)

        return viz

    def export_visualization(
        self,
        visualization: dict[str, Any],
        format: str = "json",
        filename: str | None = None,
    ) -> str | dict[str, Any]:
        """
        Export visualization in specified format.

        Args:
            visualization: Visualization to export
            format: Output format
            filename: Output filename

        Returns:
            Exported visualization or path to saved file
        """
        return self.visualizer.export(visualization, format=format, filename=filename)

    def get_static_errors(self) -> list[dict[str, Any]]:
        """
        Get static errors in the codebase.

        Returns:
            List of static errors
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Get errors
        errors = self.analyzer.get_issues(severity=IssueSeverity.ERROR)

        # Convert to dictionaries
        return [error.to_dict() for error in errors]

    def get_parameter_issues(self) -> list[dict[str, Any]]:
        """
        Get parameter-related issues.

        Returns:
            List of parameter issues
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Get parameter issues
        issues = self.analyzer.get_issues(category=IssueCategory.PARAMETER_MISMATCH)

        # Convert to dictionaries
        return [issue.to_dict() for issue in issues]

    def get_unimplemented_functions(self) -> list[dict[str, Any]]:
        """
        Get unimplemented functions.

        Returns:
            List of unimplemented functions
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Get implementation issues
        issues = self.analyzer.get_issues(category=IssueCategory.IMPLEMENTATION_ERROR)

        # Convert to dictionaries
        return [issue.to_dict() for issue in issues]

    def get_circular_dependencies(self) -> list[dict[str, Any]]:
        """
        Get circular dependencies.

        Returns:
            List of circular dependencies
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["dependency"])

        # Get circular dependencies
        if "dependency" in self.analyzer.results.get("results", {}):
            return (
                self.analyzer.results["results"]["dependency"]
                .get("circular_dependencies", {})
                .get("circular_imports", [])
            )

        return []

    def get_module_coupling(self) -> list[dict[str, Any]]:
        """
        Get module coupling metrics.

        Returns:
            Module coupling metrics
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["dependency"])

        # Get module coupling
        if "dependency" in self.analyzer.results.get("results", {}):
            return (
                self.analyzer.results["results"]["dependency"]
                .get("module_coupling", {})
                .get("high_coupling_modules", [])
            )

        return []

    def get_diff_analysis(self, pr_number: int) -> dict[str, Any]:
        """
        Get diff analysis for a PR.

        Args:
            pr_number: PR number to analyze

        Returns:
            Diff analysis results
        """
        # Analyze PR
        self.analyze_pr(pr_number, analysis_types=["pr"])

        # Get diff analysis
        if "pr" in self.analyzer.results.get("results", {}):
            return self.analyzer.results["results"]["pr"]

        return {}

    def clear_cache(self):
        """Clear the analysis cache."""
        self._analysis_cache = {}

    def _symbol_to_dict(self, symbol) -> dict[str, Any]:
        """Convert symbol to dictionary."""
        symbol_dict = {
            "name": symbol.name if hasattr(symbol, "name") else str(symbol),
            "type": str(symbol.symbol_type)
            if hasattr(symbol, "symbol_type")
            else "unknown",
            "file": symbol.file.file_path
            if hasattr(symbol, "file") and hasattr(symbol.file, "file_path")
            else "unknown",
            "line": symbol.line if hasattr(symbol, "line") else None,
        }

        # Add function-specific info
        if hasattr(symbol, "parameters"):
            symbol_dict["parameters"] = [
                {
                    "name": p.name if hasattr(p, "name") else str(p),
                    "type": str(p.type) if hasattr(p, "type") and p.type else None,
                    "has_default": p.has_default
                    if hasattr(p, "has_default")
                    else False,
                }
                for p in symbol.parameters
            ]

            symbol_dict["return_type"] = (
                str(symbol.return_type)
                if hasattr(symbol, "return_type") and symbol.return_type
                else None
            )
            symbol_dict["is_async"] = (
                symbol.is_async if hasattr(symbol, "is_async") else False
            )

        # Add class-specific info
        if hasattr(symbol, "superclasses"):
            symbol_dict["superclasses"] = [
                sc.name if hasattr(sc, "name") else str(sc)
                for sc in symbol.superclasses
            ]

        return symbol_dict

    def generate_class_diagram(
        self,
        class_name: str | None = None,
        module_name: str | None = None,
        include_methods: bool = True,
        include_attributes: bool = True,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Generate a class diagram for the codebase.

        Args:
            class_name: Name of the class to analyze (optional)
            module_name: Name of the module containing the class (optional)
            include_methods: Whether to include methods in the diagram
            include_attributes: Whether to include attributes in the diagram
            output_format: Output format (json, dot, graphml, plantuml)

        Returns:
            Dictionary containing the class diagram data
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["dependency"])

        # Generate visualization
        viz = self.visualizer.generate_class_diagram(
            codebase_context=self.analyzer.base_context,
            class_name=class_name,
            module_name=module_name,
            include_methods=include_methods,
            include_attributes=include_attributes,
        )

        # Export if needed
        if output_format != "json":
            return self.visualizer.export(viz, format=output_format)

        return viz

    def generate_sequence_diagram(
        self,
        function_name: str,
        file_path: str | None = None,
        max_depth: int = 3,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Generate a sequence diagram for a specific function.

        Args:
            function_name: Name of the function to analyze
            file_path: Path to the file containing the function (optional)
            max_depth: Maximum depth of the sequence diagram
            output_format: Output format (json, plantuml)

        Returns:
            Dictionary containing the sequence diagram data
        """
        # Run analysis if not already done
        if not self._analysis_cache:
            self.analyze_codebase(analysis_types=["code_quality"])

        # Generate visualization
        viz = self.visualizer.generate_sequence_diagram(
            codebase_context=self.analyzer.base_context,
            function_name=function_name,
            file_path=file_path,
            max_depth=max_depth,
        )

        # Export if needed
        if output_format != "json":
            return self.visualizer.export(viz, format=output_format)

        return viz


def create_api(
    repo_path: str | None = None, repo_url: str | None = None
) -> CodegenAnalyzerAPI:
    """
    Create an API instance.

    Args:
        repo_path: Local path to the repository
        repo_url: URL of the repository

    Returns:
        API instance
    """
    return CodegenAnalyzerAPI(repo_path=repo_path, repo_url=repo_url)


# API endpoints for Flask or FastAPI integration
def api_analyze_codebase(
    repo_path: str, analysis_types: list[str] | None = None
) -> dict[str, Any]:
    """
    API endpoint for codebase analysis.

    Args:
        repo_path: Path to the repository
        analysis_types: Types of analysis to perform

    Returns:
        Analysis results
    """
    api = create_api(repo_path=repo_path)
    return api.analyze_codebase(analysis_types=analysis_types)


def api_analyze_pr(repo_path: str, pr_number: int) -> dict[str, Any]:
    """
    API endpoint for PR analysis.

    Args:
        repo_path: Path to the repository
        pr_number: PR number to analyze

    Returns:
        Analysis results
    """
    api = create_api(repo_path=repo_path)
    return api.analyze_pr(pr_number=pr_number)


def api_get_visualization(
    repo_path: str, viz_type: str, params: dict[str, Any]
) -> dict[str, Any]:
    """
    API endpoint for visualizations.

    Args:
        repo_path: Path to the repository
        viz_type: Type of visualization
        params: Visualization parameters

    Returns:
        Visualization data
    """
    api = create_api(repo_path=repo_path)

    # Run appropriate analysis based on visualization type
    if viz_type == "module_dependencies":
        api.analyze_codebase(analysis_types=["dependency"])
    elif viz_type in ["function_calls", "code_quality"]:
        api.analyze_codebase(analysis_types=["code_quality"])
    elif viz_type == "pr_impact":
        api.analyze_pr(pr_number=params["pr_number"])

    # Generate visualization
    if viz_type == "module_dependencies":
        return api.get_module_dependencies(
            module_path=params.get("module_path"),
            layout=params.get("layout", "hierarchical"),
            format=params.get("format", "json"),
        )
    elif viz_type == "function_calls":
        return api.get_function_call_graph(
            function_name=params["function_name"],
            depth=params.get("depth", 2),
            layout=params.get("layout", "hierarchical"),
            format=params.get("format", "json"),
        )
    elif viz_type == "pr_impact":
        return api.get_pr_impact(
            pr_number=params.get("pr_number"),
            layout=params.get("layout", "force"),
            format=params.get("format", "json"),
        )
    else:
        raise ValueError(f"Unknown visualization type: {viz_type}")


def api_get_static_errors(repo_path: str) -> list[dict[str, Any]]:
    """
    API endpoint for static errors.

    Args:
        repo_path: Path to the repository

    Returns:
        List of static errors
    """
    api = create_api(repo_path=repo_path)
    return api.get_static_errors()


def api_get_function_issues(repo_path: str, function_name: str) -> list[dict[str, Any]]:
    """
    API endpoint for function issues.

    Args:
        repo_path: Path to the repository
        function_name: Name of the function

    Returns:
        List of function issues
    """
    api = create_api(repo_path=repo_path)
    api.analyze_codebase(analysis_types=["code_quality"])

    # Get symbol
    symbol = api.analyzer.base_codebase.get_symbol(function_name)

    if not symbol:
        return []

    # Get file path
    file_path = (
        symbol.file.file_path
        if hasattr(symbol, "file") and hasattr(symbol.file, "file_path")
        else None
    )

    if not file_path:
        return []

    # Get issues for this file and symbol
    issues = api.analyzer.get_issues()
    return [
        issue.to_dict()
        for issue in issues
        if issue.file == file_path
        and (
            issue.symbol == function_name
            or (
                hasattr(issue, "related_symbols")
                and function_name in issue.related_symbols
            )
        )
    ]
