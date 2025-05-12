#!/usr/bin/env python3
"""
Error Analyzer Module (Legacy Interface)

This module provides a backwards-compatible interface to the new analyzer modules.
It serves as a bridge between old code using error_analyzer.py and the new modular
analysis system.

For new code, consider using the analyzers directly:
- codegen_on_oss.analyzers.code_quality_analyzer.CodeQualityAnalyzer
- codegen_on_oss.analyzers.dependency_analyzer.DependencyAnalyzer
"""

import json
import logging
import sys
import warnings

# Import from our new analyzers
try:
    from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer
    from codegen_on_oss.analyzers.code_quality_analyzer import CodeQualityAnalyzer
    from codegen_on_oss.analyzers.dependency_analyzer import DependencyAnalyzer
    from codegen_on_oss.analyzers.issue_types import (
        AnalysisType,
        Issue,
        IssueCategory,
        IssueSeverity,
    )
    from codegen_on_oss.codebase_visualizer import (
        CodebaseVisualizer,
        OutputFormat,
        VisualizationType,
    )
except ImportError:
    print("Error loading analyzer modules. Please make sure they are installed.")
    sys.exit(1)

# Import codegen SDK
try:
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.sdk.codebase.codebase_analysis import get_codebase_summary
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.sdk.core.codebase import Codebase
    from codegen.shared.enums.programming_language import ProgrammingLanguage
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Show deprecation warning
warnings.warn(
    "error_analyzer.py is deprecated. Please use analyzers directly from codegen_on_oss.analyzers package.",
    DeprecationWarning,
    stacklevel=2,
)


class CodebaseAnalyzer:
    """
    Legacy interface to the new analyzer modules.

    This class provides backwards compatibility with code that used the
    old CodebaseAnalyzer class from error_analyzer.py.
    """

    def __init__(
        self,
        repo_url: str | None = None,
        repo_path: str | None = None,
        language: str | None = None,
    ):
        """
        Initialize the CodebaseAnalyzer.

        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase
        """
        # Create instances of the new analyzers
        self.quality_analyzer = CodeQualityAnalyzer(
            repo_url=repo_url, repo_path=repo_path, language=language
        )

        self.dependency_analyzer = DependencyAnalyzer(
            repo_url=repo_url, repo_path=repo_path, language=language
        )

        # Set up legacy attributes
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.language = language
        self.codebase = self.quality_analyzer.base_codebase
        self.results = {}

        # Initialize visualizer
        self.visualizer = CodebaseVisualizer(codebase=self.codebase)

    def analyze(
        self,
        categories: list[str] | None = None,
        output_format: str = "json",
        output_file: str | None = None,
    ):
        """
        Perform a comprehensive analysis of the codebase.

        Args:
            categories: List of categories to analyze. If None, all categories are analyzed.
            output_format: Format of the output (json, html, console)
            output_file: Path to the output file

        Returns:
            Dict containing the analysis results
        """
        if not self.codebase:
            raise ValueError(
                "Codebase not initialized. Please initialize the codebase first."
            )

        # Map old category names to new analyzers
        category_map = {
            "codebase_structure": "dependency",
            "symbol_level": "code_quality",
            "dependency_flow": "dependency",
            "code_quality": "code_quality",
            "visualization": "visualization",
            "language_specific": "code_quality",
            "code_metrics": "code_quality",
        }

        # Initialize results with metadata
        self.results = {
            "metadata": {
                "repo_name": getattr(self.codebase.ctx, "repo_name", None),
                "analysis_time": str(datetime.now()),
                "language": str(
                    getattr(self.codebase.ctx, "programming_language", None)
                ),
                "codebase_summary": get_codebase_summary(self.codebase),
            },
            "categories": {},
        }

        # Determine categories to analyze
        if not categories:
            # If no categories are specified, run all analysis types
            analysis_types = ["code_quality", "dependency"]
        else:
            # Map the requested categories to analysis types
            analysis_types = set()
            for category in categories:
                if category in category_map:
                    analysis_types.add(category_map[category])

        # Run each analysis type
        if "code_quality" in analysis_types:
            quality_results = self.quality_analyzer.analyze(AnalysisType.CODE_QUALITY)

            # Add results to the legacy format
            for category in [
                "code_quality",
                "symbol_level",
                "language_specific",
                "code_metrics",
            ]:
                if category in categories or not categories:
                    self.results["categories"][category] = {}

                    # Map new results to old category structure
                    if category == "code_quality":
                        self.results["categories"][category].update({
                            "unused_functions": quality_results.get(
                                "dead_code", {}
                            ).get("unused_functions", []),
                            "unused_classes": quality_results.get("dead_code", {}).get(
                                "unused_classes", []
                            ),
                            "unused_variables": quality_results.get(
                                "dead_code", {}
                            ).get("unused_variables", []),
                            "unused_imports": quality_results.get("dead_code", {}).get(
                                "unused_imports", []
                            ),
                            "cyclomatic_complexity": quality_results.get(
                                "complexity", {}
                            ),
                            "cognitive_complexity": quality_results.get(
                                "complexity", {}
                            ),
                            "function_size_metrics": quality_results.get(
                                "style_issues", {}
                            ).get("long_functions", []),
                        })
                    elif category == "symbol_level":
                        self.results["categories"][category].update({
                            "function_parameter_analysis": [],
                            "function_complexity_metrics": quality_results.get(
                                "complexity", {}
                            ).get("function_complexity", []),
                        })
                    elif category == "code_metrics":
                        self.results["categories"][category].update({
                            "calculate_cyclomatic_complexity": quality_results.get(
                                "complexity", {}
                            ),
                            "calculate_maintainability_index": quality_results.get(
                                "maintainability", {}
                            ),
                        })

        if "dependency" in analysis_types:
            dependency_results = self.dependency_analyzer.analyze(
                AnalysisType.DEPENDENCY
            )

            # Add results to the legacy format
            for category in ["codebase_structure", "dependency_flow"]:
                if category in categories or not categories:
                    self.results["categories"][category] = {}

                    # Map new results to old category structure
                    if category == "codebase_structure":
                        self.results["categories"][category].update({
                            "import_dependency_map": dependency_results.get(
                                "import_dependencies", {}
                            ).get("module_dependencies", []),
                            "circular_imports": dependency_results.get(
                                "circular_dependencies", {}
                            ).get("circular_imports", []),
                            "module_coupling_metrics": dependency_results.get(
                                "module_coupling", {}
                            ),
                            "module_dependency_graph": dependency_results.get(
                                "import_dependencies", {}
                            ).get("module_dependencies", []),
                        })
                    elif category == "dependency_flow":
                        self.results["categories"][category].update({
                            "function_call_relationships": [],
                            "entry_point_analysis": [],
                            "dead_code_detection": quality_results.get("dead_code", {})
                            if "code_quality" in analysis_types
                            else {},
                        })

        # Output the results
        if output_format == "json":
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(self.results, f, indent=2)
                logger.info(f"Results saved to {output_file}")
            else:
                return self.results
        elif output_format == "html":
            self._generate_html_report(output_file)
        elif output_format == "console":
            self._print_console_report()

        return self.results

    def _generate_html_report(self, output_file: str | None = None):
        """
        Generate an HTML report of the analysis results.

        Args:
            output_file: Path to the output file
        """
        # Simple HTML report for backwards compatibility
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .section {{ margin-bottom: 20px; }}
                .issues {{ margin-top: 10px; }}
                .issue {{ margin-bottom: 5px; padding: 5px; border-radius: 5px; }}
                .error {{ background-color: #ffebee; }}
                .warning {{ background-color: #fff8e1; }}
                .info {{ background-color: #e8f5e9; }}
            </style>
        </head>
        <body>
            <h1>Codebase Analysis Report</h1>
            <div class="section">
                <h2>Metadata</h2>
                <p><b>Repository:</b> {self.results["metadata"].get("repo_name", "Unknown")}</p>
                <p><b>Analysis Time:</b> {self.results["metadata"].get("analysis_time", "Unknown")}</p>
                <p><b>Language:</b> {self.results["metadata"].get("language", "Unknown")}</p>
            </div>
        """

        # Add issues section
        html_content += """
            <div class="section">
                <h2>Issues</h2>
                <div class="issues">
        """

        # Collect all issues
        all_issues = []
        if hasattr(self.quality_analyzer, "issues"):
            all_issues.extend(self.quality_analyzer.issues)
        if hasattr(self.dependency_analyzer, "issues"):
            all_issues.extend(self.dependency_analyzer.issues)

        # Sort issues by severity
        all_issues.sort(
            key=lambda x: {
                IssueSeverity.CRITICAL: 0,
                IssueSeverity.ERROR: 1,
                IssueSeverity.WARNING: 2,
                IssueSeverity.INFO: 3,
            }.get(x.severity, 4)
        )

        # Add issues to HTML
        for issue in all_issues:
            severity_class = issue.severity.value
            html_content += f"""
                    <div class="issue {severity_class}">
                        <p><b>{issue.severity.value.upper()}:</b> {issue.message}</p>
                        <p><b>File:</b> {issue.file} {f"(Line {issue.line})" if issue.line else ""}</p>
                        <p><b>Symbol:</b> {issue.symbol or "N/A"}</p>
                        <p><b>Suggestion:</b> {issue.suggestion or "N/A"}</p>
                    </div>
            """

        html_content += """
                </div>
            </div>
        """

        # Add summary of results
        html_content += """
            <div class="section">
                <h2>Analysis Results</h2>
        """

        for category, results in self.results.get("categories", {}).items():
            html_content += f"""
                <h3>{category}</h3>
                <pre>{json.dumps(results, indent=2)}</pre>
            """

        html_content += """
            </div>
        </body>
        </html>
        """

        # Save HTML to file or print to console
        if output_file:
            with open(output_file, "w") as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_file}")
        else:
            print(html_content)

    def _print_console_report(self):
        """Print a summary of the analysis results to the console."""
        print("\n📊 Codebase Analysis Report 📊")
        print("=" * 50)

        # Print metadata
        print(
            f"\n📌 Repository: {self.results['metadata'].get('repo_name', 'Unknown')}"
        )
        print(
            f"📆 Analysis Time: {self.results['metadata'].get('analysis_time', 'Unknown')}"
        )
        print(f"🔤 Language: {self.results['metadata'].get('language', 'Unknown')}")

        # Print summary of issues
        print("\n🚨 Issues Summary")
        print("-" * 50)

        # Collect all issues
        all_issues = []
        if hasattr(self.quality_analyzer, "issues"):
            all_issues.extend(self.quality_analyzer.issues)
        if hasattr(self.dependency_analyzer, "issues"):
            all_issues.extend(self.dependency_analyzer.issues)

        # Print issue counts by severity
        severity_counts = {
            IssueSeverity.CRITICAL: 0,
            IssueSeverity.ERROR: 0,
            IssueSeverity.WARNING: 0,
            IssueSeverity.INFO: 0,
        }

        for issue in all_issues:
            severity_counts[issue.severity] += 1

        print(f"Critical: {severity_counts[IssueSeverity.CRITICAL]}")
        print(f"Errors: {severity_counts[IssueSeverity.ERROR]}")
        print(f"Warnings: {severity_counts[IssueSeverity.WARNING]}")
        print(f"Info: {severity_counts[IssueSeverity.INFO]}")
        print(f"Total: {len(all_issues)}")

        # Print top issues by severity
        if all_issues:
            print("\n🔍 Top Issues")
            print("-" * 50)

            # Sort issues by severity
            all_issues.sort(
                key=lambda x: {
                    IssueSeverity.CRITICAL: 0,
                    IssueSeverity.ERROR: 1,
                    IssueSeverity.WARNING: 2,
                    IssueSeverity.INFO: 3,
                }.get(x.severity, 4)
            )

            # Print top 10 issues
            for i, issue in enumerate(all_issues[:10]):
                print(f"{i + 1}. [{issue.severity.value.upper()}] {issue.message}")
                print(
                    f"   File: {issue.file} {f'(Line {issue.line})' if issue.line else ''}"
                )
                print(f"   Symbol: {issue.symbol or 'N/A'}")
                print(f"   Suggestion: {issue.suggestion or 'N/A'}")
                print()

        # Print summary of results by category
        for category, results in self.results.get("categories", {}).items():
            print(f"\n📋 {category.replace('_', ' ').title()}")
            print("-" * 50)

            # Print key statistics for each category
            if category == "code_quality":
                unused_funcs = len(results.get("unused_functions", []))
                unused_vars = len(results.get("unused_variables", []))
                print(f"Unused Functions: {unused_funcs}")
                print(f"Unused Variables: {unused_vars}")

                # Print complexity stats if available
                complexity = results.get("cyclomatic_complexity", {})
                if "function_complexity" in complexity:
                    high_complexity = [
                        f
                        for f in complexity["function_complexity"]
                        if f.get("complexity", 0) > 10
                    ]
                    print(f"High Complexity Functions: {len(high_complexity)}")

            elif category == "codebase_structure":
                circular_imports = len(results.get("circular_imports", []))
                print(f"Circular Imports: {circular_imports}")

                module_deps = results.get("module_dependency_graph", [])
                print(f"Module Dependencies: {len(module_deps)}")

            elif category == "dependency_flow":
                dead_code = results.get("dead_code_detection", {})
                total_dead = (
                    len(dead_code.get("unused_functions", []))
                    + len(dead_code.get("unused_classes", []))
                    + len(dead_code.get("unused_variables", []))
                )
                print(f"Dead Code Items: {total_dead}")


# For backwards compatibility, expose the CodebaseAnalyzer class as the main interface
__all__ = ["CodebaseAnalyzer"]
