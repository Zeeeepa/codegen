#!/usr/bin/env python3
"""
Analyzer Manager Module

This module provides a centralized interface for running various codebase analyzers.
It coordinates the execution of different analyzer types and aggregates their results.
"""

import logging
import sys
from typing import Any

try:
    from codegen_on_oss.analyzers.issue_types import (
        AnalysisType,
        Issue,
        IssueCategory,
        IssueSeverity,
    )
    from codegen_on_oss.analyzers.unified_analyzer import (
        CodeQualityAnalyzerPlugin,
        DependencyAnalyzerPlugin,
        UnifiedCodeAnalyzer,
    )
except ImportError:
    print("Required analyzer modules not found.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AnalyzerManager:
    """
    Central manager for running different types of code analysis.

    This class provides a unified interface for running various analyzers
    and aggregating their results.
    """

    def __init__(
        self,
        repo_url: str | None = None,
        repo_path: str | None = None,
        language: str | None = None,
        base_branch: str = "main",
        pr_number: int | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the analyzer manager.

        Args:
            repo_url: URL of the repository to analyze
            repo_path: Local path to the repository to analyze
            language: Programming language of the codebase
            base_branch: Base branch for comparison
            pr_number: PR number to analyze
            config: Additional configuration options
        """
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.language = language
        self.base_branch = base_branch
        self.pr_number = pr_number
        self.config = config or {}

        # Initialize the unified analyzer
        self.analyzer = UnifiedCodeAnalyzer(
            repo_url=repo_url,
            repo_path=repo_path,
            base_branch=base_branch,
            pr_number=pr_number,
            language=language,
            config=config,
        )

        # Register additional analyzers (if any)
        self._register_custom_analyzers()

    def _register_custom_analyzers(self):
        """Register custom analyzers with the registry."""
        # The default analyzers (CODE_QUALITY and DEPENDENCY) are registered automatically
        # This method can be overridden by subclasses to register additional analyzers
        pass

    def run_analysis(
        self,
        analysis_types: list[AnalysisType] | None = None,
        output_file: str | None = None,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Run analysis on the codebase.

        Args:
            analysis_types: Types of analysis to run (defaults to CODE_QUALITY and DEPENDENCY)
            output_file: Path to save results to (None for no save)
            output_format: Format for output file (json, html, console)

        Returns:
            Dictionary containing analysis results
        """
        # Default to code quality and dependency analysis
        if analysis_types is None:
            analysis_types = [AnalysisType.CODE_QUALITY, AnalysisType.DEPENDENCY]

        try:
            # Run the analysis
            logger.info(
                f"Running analysis: {', '.join([at.value for at in analysis_types])}"
            )
            results = self.analyzer.analyze(analysis_types)

            # Save results if output file is specified
            if output_file:
                logger.info(f"Saving results to {output_file}")
                self.analyzer.save_results(output_file, output_format)

            return results

        except Exception as e:
            logger.exception(f"Error running analysis: {e}")
            import traceback

            traceback.print_exc()
            raise

    def get_issues(
        self,
        severity: IssueSeverity | None = None,
        category: IssueCategory | None = None,
    ) -> list[Issue]:
        """
        Get issues from the analyzer.

        Args:
            severity: Filter issues by severity
            category: Filter issues by category

        Returns:
            List of issues matching the filters
        """
        return self.analyzer.get_issues(severity, category)

    def generate_report(
        self, report_type: str = "summary", output_file: str | None = None
    ) -> str:
        """
        Generate a report from the analysis results.

        Args:
            report_type: Type of report to generate (summary, detailed, issues)
            output_file: Path to save report to (None for returning as string)

        Returns:
            Report as a string (if output_file is None)
        """
        if not hasattr(self.analyzer, "results") or not self.analyzer.results:
            raise ValueError("No analysis results available. Run analysis first.")

        report = ""

        if report_type == "summary":
            report = self._generate_summary_report()
        elif report_type == "detailed":
            report = self._generate_detailed_report()
        elif report_type == "issues":
            report = self._generate_issues_report()
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        if output_file:
            with open(output_file, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_file}")
            return ""
        else:
            return report

    def _generate_summary_report(self) -> str:
        """Generate a summary report of the analysis results."""
        results = self.analyzer.results

        report = "===== Codebase Analysis Summary Report =====\n\n"

        # Add metadata
        report += "Metadata:\n"
        report += f"  Repository: {results['metadata'].get('repo_name', 'Unknown')}\n"
        report += f"  Language: {results['metadata'].get('language', 'Unknown')}\n"
        report += (
            f"  Analysis Time: {results['metadata'].get('analysis_time', 'Unknown')}\n"
        )
        report += f"  Analysis Types: {', '.join(results['metadata'].get('analysis_types', []))}\n"

        # Add issue statistics
        report += "\nIssue Statistics:\n"
        report += f"  Total Issues: {results['issue_stats']['total']}\n"
        report += (
            f"  Critical: {results['issue_stats']['by_severity'].get('critical', 0)}\n"
        )
        report += f"  Errors: {results['issue_stats']['by_severity'].get('error', 0)}\n"
        report += (
            f"  Warnings: {results['issue_stats']['by_severity'].get('warning', 0)}\n"
        )
        report += f"  Info: {results['issue_stats']['by_severity'].get('info', 0)}\n"

        # Add codebase summary
        if "summary" in results:
            report += "\nCodebase Summary:\n"
            summary = results["summary"]
            report += f"  Files: {summary.get('file_count', 0)}\n"
            report += f"  Lines of Code: {summary.get('total_loc', 0)}\n"
            report += f"  Functions: {summary.get('function_count', 0)}\n"
            report += f"  Classes: {summary.get('class_count', 0)}\n"

        # Add analysis summaries
        for analysis_type, analysis_results in results.get("results", {}).items():
            report += f"\n{analysis_type.title()} Analysis Summary:\n"

            if analysis_type == "code_quality":
                if "dead_code" in analysis_results:
                    dead_code = analysis_results["dead_code"]
                    report += f"  Dead Code Items: {dead_code['summary']['total_dead_code_count']}\n"
                    report += f"    Unused Functions: {dead_code['summary']['unused_functions_count']}\n"
                    report += f"    Unused Classes: {dead_code['summary']['unused_classes_count']}\n"
                    report += f"    Unused Variables: {dead_code['summary']['unused_variables_count']}\n"
                    report += f"    Unused Imports: {dead_code['summary']['unused_imports_count']}\n"

                if "complexity" in analysis_results:
                    complexity = analysis_results["complexity"]
                    report += f"  Average Complexity: {complexity.get('average_complexity', 0):.2f}\n"
                    report += f"  High Complexity Functions: {len(complexity.get('high_complexity_functions', []))}\n"

                    # Distribution
                    dist = complexity.get("complexity_distribution", {})
                    report += "  Complexity Distribution:\n"
                    report += f"    Low: {dist.get('low', 0)}\n"
                    report += f"    Medium: {dist.get('medium', 0)}\n"
                    report += f"    High: {dist.get('high', 0)}\n"
                    report += f"    Very High: {dist.get('very_high', 0)}\n"

            elif analysis_type == "dependency":
                if "circular_dependencies" in analysis_results:
                    circular = analysis_results["circular_dependencies"]
                    report += f"  Circular Dependencies: {circular.get('circular_dependencies_count', 0)}\n"
                    report += f"  Affected Modules: {len(circular.get('affected_modules', []))}\n"

                if "module_coupling" in analysis_results:
                    coupling = analysis_results["module_coupling"]
                    report += f"  Average Coupling: {coupling.get('average_coupling', 0):.2f}\n"
                    report += f"  High Coupling Modules: {len(coupling.get('high_coupling_modules', []))}\n"
                    report += f"  Low Coupling Modules: {len(coupling.get('low_coupling_modules', []))}\n"

        return report

    def _generate_detailed_report(self) -> str:
        """Generate a detailed report of the analysis results."""
        results = self.analyzer.results

        report = "===== Codebase Analysis Detailed Report =====\n\n"

        # Add metadata
        report += "Metadata:\n"
        report += f"  Repository: {results['metadata'].get('repo_name', 'Unknown')}\n"
        report += f"  Language: {results['metadata'].get('language', 'Unknown')}\n"
        report += (
            f"  Analysis Time: {results['metadata'].get('analysis_time', 'Unknown')}\n"
        )
        report += f"  Analysis Types: {', '.join(results['metadata'].get('analysis_types', []))}\n"

        # Add detailed analysis sections
        for analysis_type, analysis_results in results.get("results", {}).items():
            report += f"\n{analysis_type.title()} Analysis:\n"

            # Add relevant sections from each analysis type
            if analysis_type == "code_quality":
                # Dead code
                if "dead_code" in analysis_results:
                    dead_code = analysis_results["dead_code"]
                    report += "\n  Dead Code Analysis:\n"
                    report += f"    Total Dead Code Items: {dead_code['summary']['total_dead_code_count']}\n"

                    # Unused functions
                    if dead_code["unused_functions"]:
                        report += f"\n    Unused Functions ({len(dead_code['unused_functions'])}):\n"
                        for func in dead_code["unused_functions"][
                            :10
                        ]:  # Limit to top 10
                            report += f"      {func['name']} ({func['file']}:{func['line']})\n"
                        if len(dead_code["unused_functions"]) > 10:
                            report += f"      ... and {len(dead_code['unused_functions']) - 10} more\n"

                    # Unused classes
                    if dead_code["unused_classes"]:
                        report += f"\n    Unused Classes ({len(dead_code['unused_classes'])}):\n"
                        for cls in dead_code["unused_classes"][:10]:  # Limit to top 10
                            report += (
                                f"      {cls['name']} ({cls['file']}:{cls['line']})\n"
                            )
                        if len(dead_code["unused_classes"]) > 10:
                            report += f"      ... and {len(dead_code['unused_classes']) - 10} more\n"

                # Complexity
                if "complexity" in analysis_results:
                    complexity = analysis_results["complexity"]
                    report += "\n  Code Complexity Analysis:\n"
                    report += f"    Average Complexity: {complexity.get('average_complexity', 0):.2f}\n"

                    # High complexity functions
                    high_complexity = complexity.get("high_complexity_functions", [])
                    if high_complexity:
                        report += f"\n    High Complexity Functions ({len(high_complexity)}):\n"
                        for func in high_complexity[:10]:  # Limit to top 10
                            report += f"      {func['name']} (Complexity: {func['complexity']}, {func['file']}:{func['line']})\n"
                        if len(high_complexity) > 10:
                            report += (
                                f"      ... and {len(high_complexity) - 10} more\n"
                            )

                # Maintainability
                if "maintainability" in analysis_results:
                    maintain = analysis_results["maintainability"]
                    report += "\n  Maintainability Analysis:\n"
                    report += f"    Average Maintainability: {maintain.get('average_maintainability', 0):.2f}\n"

                    # Low maintainability functions
                    low_maintain = maintain.get("low_maintainability_functions", [])
                    if low_maintain:
                        report += f"\n    Low Maintainability Functions ({len(low_maintain)}):\n"
                        for func in low_maintain[:10]:  # Limit to top 10
                            report += f"      {func['name']} (Index: {func['maintainability']:.1f}, {func['file']}:{func['line']})\n"
                        if len(low_maintain) > 10:
                            report += f"      ... and {len(low_maintain) - 10} more\n"

            elif analysis_type == "dependency":
                # Circular dependencies
                if "circular_dependencies" in analysis_results:
                    circular = analysis_results["circular_dependencies"]
                    report += "\n  Circular Dependencies Analysis:\n"
                    report += f"    Total Circular Dependencies: {circular.get('circular_dependencies_count', 0)}\n"

                    # List circular import chains
                    if circular.get("circular_imports", []):
                        report += f"\n    Circular Import Chains ({len(circular['circular_imports'])}):\n"
                        for i, cycle in enumerate(
                            circular["circular_imports"][:5]
                        ):  # Limit to top 5
                            report += (
                                f"      Chain {i + 1} (Length: {cycle['length']}):\n"
                            )
                            for j, file_path in enumerate(cycle["files"]):
                                report += f"        {j + 1}. {file_path}\n"
                        if len(circular["circular_imports"]) > 5:
                            report += f"      ... and {len(circular['circular_imports']) - 5} more chains\n"

                # Module coupling
                if "module_coupling" in analysis_results:
                    coupling = analysis_results["module_coupling"]
                    report += "\n  Module Coupling Analysis:\n"
                    report += f"    Average Coupling: {coupling.get('average_coupling', 0):.2f}\n"

                    # High coupling modules
                    high_coupling = coupling.get("high_coupling_modules", [])
                    if high_coupling:
                        report += (
                            f"\n    High Coupling Modules ({len(high_coupling)}):\n"
                        )
                        for module in high_coupling[:10]:  # Limit to top 10
                            report += f"      {module['module']} (Ratio: {module['coupling_ratio']:.2f}, Files: {module['file_count']}, Imports: {module['import_count']})\n"
                        if len(high_coupling) > 10:
                            report += f"      ... and {len(high_coupling) - 10} more\n"

                # External dependencies
                if "external_dependencies" in analysis_results:
                    ext_deps = analysis_results["external_dependencies"]
                    most_used = ext_deps.get("most_used_external_modules", [])

                    if most_used:
                        report += "\n    Most Used External Modules:\n"
                        for module in most_used[:10]:
                            report += f"      {module['module']} (Used {module['usage_count']} times)\n"

        return report

    def _generate_issues_report(self) -> str:
        """Generate a report focused on issues found during analysis."""
        issues = self.analyzer.issues

        report = "===== Codebase Analysis Issues Report =====\n\n"

        # Issue statistics
        report += f"Total Issues: {len(issues)}\n"
        report += f"Critical: {sum(1 for issue in issues if issue.severity == IssueSeverity.CRITICAL)}\n"
        report += f"Errors: {sum(1 for issue in issues if issue.severity == IssueSeverity.ERROR)}\n"
        report += f"Warnings: {sum(1 for issue in issues if issue.severity == IssueSeverity.WARNING)}\n"
        report += f"Info: {sum(1 for issue in issues if issue.severity == IssueSeverity.INFO)}\n"

        # Group issues by severity
        issues_by_severity = {}
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.ERROR,
            IssueSeverity.WARNING,
            IssueSeverity.INFO,
        ]:
            issues_by_severity[severity] = [
                issue for issue in issues if issue.severity == severity
            ]

        # Format issues by severity
        for severity in [
            IssueSeverity.CRITICAL,
            IssueSeverity.ERROR,
            IssueSeverity.WARNING,
            IssueSeverity.INFO,
        ]:
            severity_issues = issues_by_severity[severity]

            if severity_issues:
                report += (
                    f"\n{severity.value.upper()} Issues ({len(severity_issues)}):\n"
                )

                for issue in severity_issues:
                    location = (
                        f"{issue.file}:{issue.line}" if issue.line else issue.file
                    )
                    category = f"[{issue.category.value}]" if issue.category else ""
                    report += f"- {location} {category} {issue.message}\n"
                    report += f"  Suggestion: {issue.suggestion}\n"

        return report


def main():
    """Command-line entry point for running analyzers."""
    import argparse

    parser = argparse.ArgumentParser(description="Codebase Analyzer Manager")

    # Repository source options
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--repo-url", help="URL of the repository to analyze")
    source_group.add_argument(
        "--repo-path", help="Local path to the repository to analyze"
    )

    # Analysis options
    parser.add_argument(
        "--analysis-types",
        nargs="+",
        choices=[at.value for at in AnalysisType],
        default=["code_quality", "dependency"],
        help="Types of analysis to perform",
    )
    parser.add_argument(
        "--language",
        choices=["python", "typescript"],
        help="Programming language (auto-detected if not provided)",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for PR comparison (default: main)",
    )
    parser.add_argument("--pr-number", type=int, help="PR number to analyze")

    # Output options
    parser.add_argument("--output-file", help="Path to the output file")
    parser.add_argument(
        "--output-format",
        choices=["json", "html", "console"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--report-type",
        choices=["summary", "detailed", "issues"],
        default="summary",
        help="Type of report to generate (default: summary)",
    )

    args = parser.parse_args()

    try:
        # Initialize the analyzer manager
        manager = AnalyzerManager(
            repo_url=args.repo_url,
            repo_path=args.repo_path,
            language=args.language,
            base_branch=args.base_branch,
            pr_number=args.pr_number,
        )

        # Run the analysis
        analysis_types = [AnalysisType(at) for at in args.analysis_types]
        manager.run_analysis(analysis_types, args.output_file, args.output_format)

        # Generate and print report
        if args.output_format == "console":
            report = manager.generate_report(args.report_type)
            print(report)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
