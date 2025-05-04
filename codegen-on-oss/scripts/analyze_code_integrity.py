#!/usr/bin/env python3
"""
Script to analyze code integrity in a repository.

This script analyzes code integrity in a repository, including:
- Finding all functions and classes
- Identifying errors in functions and classes
- Detecting improper parameter usage
- Finding incorrect function callback points
- Comparing error counts between branches
- Analyzing code complexity and duplication
- Checking for type hint usage
- Detecting unused imports
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

import yaml

from codegen import Codebase
from codegen.sdk.core.codebase import Codebase

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from codegen_on_oss.analysis.code_integrity_analyzer import (
    CodeIntegrityAnalyzer,
    analyze_pr,
    compare_branches,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_codebase(
    repo_path: str, branch: Optional[str] = None, commit: Optional[str] = None
) -> Codebase:
    """
    Load a codebase from a repository.

    Args:
        repo_path: Path to the repository
        branch: Optional branch to load
        commit: Optional commit to load

    Returns:
        Loaded codebase
    """
    logger.info(f"Loading codebase from {repo_path}")

    if branch:
        logger.info(f"Using branch: {branch}")

    if commit:
        logger.info(f"Using commit: {commit}")

    # Load the codebase
    codebase = Codebase.from_repo(repo_path, branch=branch, commit=commit)

    logger.info(f"Loaded codebase with {len(list(codebase.files))} files")

    return codebase


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_file: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    if not config_file:
        return {}

    logger.info(f"Loading configuration from {config_file}")

    config = {}
    try:
        with open(config_file, "r") as f:
            if config_file.endswith(".json"):
                config = json.load(f)
            elif config_file.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            else:
                logger.warning(f"Unknown configuration file format: {config_file}")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")

    return config


def analyze_codebase(
    codebase: Codebase, config: Dict[str, Any] = None, output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a codebase for integrity issues.

    Args:
        codebase: The codebase to analyze
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Analysis results
    """
    logger.info("Analyzing codebase for integrity issues")

    # Create analyzer
    analyzer = CodeIntegrityAnalyzer(codebase, config)

    # Analyze codebase
    results = analyzer.analyze()

    # Print summary
    logger.info(
        f"Found {results['total_errors']} errors in {results['total_functions']} functions and {results['total_classes']} classes"
    )
    logger.info(f"Function errors: {results['function_errors']}")
    logger.info(f"Class errors: {results['class_errors']}")
    logger.info(f"Parameter errors: {results['parameter_errors']}")
    logger.info(f"Callback errors: {results['callback_errors']}")
    logger.info(f"Import errors: {results['import_errors']}")
    logger.info(f"Complexity errors: {results['complexity_errors']}")
    logger.info(f"Type hint errors: {results['type_hint_errors']}")
    logger.info(f"Duplication errors: {results['duplication_errors']}")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

    return results


def compare_codebases(
    main_codebase: Codebase,
    branch_codebase: Codebase,
    config: Dict[str, Any] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare two codebases for integrity issues.

    Args:
        main_codebase: The main branch codebase
        branch_codebase: The feature branch codebase
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Comparison results
    """
    logger.info("Comparing codebases for integrity issues")

    # Create analyzers with the same configuration
    main_analyzer = CodeIntegrityAnalyzer(main_codebase, config)
    branch_analyzer = CodeIntegrityAnalyzer(branch_codebase, config)

    # Analyze both codebases
    main_analyzer.analyze()
    branch_analyzer.analyze()

    # Compare branches
    comparison = compare_branches(main_codebase, branch_codebase)

    # Print summary
    logger.info(f"Main branch has {comparison['main_error_count']} errors")
    logger.info(f"Feature branch has {comparison['branch_error_count']} errors")
    logger.info(f"Difference: {comparison['error_diff']} errors")
    logger.info(f"New errors: {len(comparison['new_errors'])}")
    logger.info(f"Fixed errors: {len(comparison['fixed_errors'])}")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(comparison, f, indent=2)

    return comparison


def analyze_pull_request(
    main_codebase: Codebase,
    pr_codebase: Codebase,
    config: Dict[str, Any] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a pull request for integrity issues.

    Args:
        main_codebase: The main branch codebase
        pr_codebase: The PR branch codebase
        config: Configuration options for the analyzer
        output_file: Optional file to write the results to

    Returns:
        Analysis results
    """
    logger.info("Analyzing pull request for integrity issues")

    # Create analyzers with the same configuration
    main_analyzer = CodeIntegrityAnalyzer(main_codebase, config)
    pr_analyzer = CodeIntegrityAnalyzer(pr_codebase, config)

    # Analyze both codebases
    main_analyzer.analyze()
    pr_analyzer.analyze()

    # Analyze PR
    pr_analysis = analyze_pr(main_codebase, pr_codebase)

    # Print summary
    logger.info(
        f"PR adds {pr_analysis['new_functions']} new functions and {pr_analysis['new_classes']} new classes"
    )
    logger.info(
        f"PR modifies {pr_analysis['modified_functions']} functions and {pr_analysis['modified_classes']} classes"
    )
    logger.info(f"PR introduces {pr_analysis['total_new_errors']} new errors")

    # Write results to file if requested
    if output_file:
        logger.info(f"Writing results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(pr_analysis, f, indent=2)

    return pr_analysis


def generate_html_report(results: Dict[str, Any], output_file: str) -> None:
    """
    Generate an HTML report from analysis results.

    Args:
        results: Analysis results
        output_file: File to write the report to
    """
    logger.info(f"Generating HTML report to {output_file}")

    # Generate HTML
    html = (
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Integrity Analysis Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .summary {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }
            .error-list {
                margin-top: 20px;
            }
            .error-item {
                background-color: #fff;
                padding: 10px;
                margin-bottom: 10px;
                border-left: 4px solid #e74c3c;
                border-radius: 3px;
            }
            .error-item.warning {
                border-left-color: #f39c12;
            }
            .error-item h4 {
                margin-top: 0;
                margin-bottom: 5px;
            }
            .error-item p {
                margin: 5px 0;
            }
            .error-item .location {
                font-family: monospace;
                color: #7f8c8d;
            }
            .tabs {
                display: flex;
                margin-bottom: 20px;
                border-bottom: 1px solid #ddd;
            }
            .tab {
                padding: 10px 15px;
                cursor: pointer;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-bottom: none;
                margin-right: 5px;
                border-radius: 3px 3px 0 0;
            }
            .tab.active {
                background-color: #fff;
                border-bottom: 1px solid #fff;
                margin-bottom: -1px;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
            .stats {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 20px;
            }
            .stat-box {
                background-color: #ecf0f1;
                padding: 10px;
                border-radius: 5px;
                min-width: 150px;
                text-align: center;
            }
            .stat-box h3 {
                margin: 0;
                font-size: 24px;
            }
            .stat-box p {
                margin: 5px 0 0 0;
                font-size: 14px;
            }
            .severity-error {
                color: #e74c3c;
            }
            .severity-warning {
                color: #f39c12;
            }
            .filter-controls {
                margin-bottom: 15px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .filter-controls select, .filter-controls input {
                margin-right: 10px;
                padding: 5px;
            }
            .progress-bar {
                height: 20px;
                background-color: #ecf0f1;
                border-radius: 10px;
                margin-bottom: 20px;
                overflow: hidden;
            }
            .progress-bar-fill {
                height: 100%;
                background-color: #2ecc71;
                width: 0%;
                transition: width 0.5s ease-in-out;
            }
        </style>
    </head>
    <body>
        <h1>Code Integrity Analysis Report</h1>

        <div class="tabs">
            <div class="tab active" onclick="showTab('summary')">Summary</div>
            <div class="tab" onclick="showTab('errors')">Errors</div>
            <div class="tab" onclick="showTab('codebase')">Codebase</div>
        </div>

        <div id="summary" class="tab-content active">
            <div class="summary">
                <h2>Analysis Summary</h2>
                <div class="stats">
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("total_errors", 0))
        + """</h3>
                        <p>Total Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("total_functions", 0))
        + """</h3>
                        <p>Functions</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("total_classes", 0))
        + """</h3>
                        <p>Classes</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("total_files", 0))
        + """</h3>
                        <p>Files</p>
                    </div>
                </div>

                <h3>Error Breakdown</h3>
                <div class="stats">
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("function_errors", 0))
        + """</h3>
                        <p>Function Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("class_errors", 0))
        + """</h3>
                        <p>Class Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("parameter_errors", 0))
        + """</h3>
                        <p>Parameter Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("callback_errors", 0))
        + """</h3>
                        <p>Callback Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("import_errors", 0))
        + """</h3>
                        <p>Import Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("complexity_errors", 0))
        + """</h3>
                        <p>Complexity Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("type_hint_errors", 0))
        + """</h3>
                        <p>Type Hint Errors</p>
                    </div>
                    <div class="stat-box">
                        <h3>"""
        + str(results.get("duplication_errors", 0))
        + """</h3>
                        <p>Duplication Errors</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="errors" class="tab-content">
            <div class="filter-controls">
                <h3>Filter Errors</h3>
                <select id="error-type-filter">
                    <option value="all">All Error Types</option>
                    <option value="function_error">Function Errors</option>
                    <option value="class_error">Class Errors</option>
                    <option value="parameter_error">Parameter Errors</option>
                    <option value="callback_error">Callback Errors</option>
                    <option value="import_error">Import Errors</option>
                    <option value="complexity_error">Complexity Errors</option>
                    <option value="type_hint_error">Type Hint Errors</option>
                    <option value="duplication_error">Duplication Errors</option>
                </select>
                <select id="severity-filter">
                    <option value="all">All Severities</option>
                    <option value="error">Errors Only</option>
                    <option value="warning">Warnings Only</option>
                </select>
                <input type="text" id="search-filter" placeholder="Search by name or file...">
                <button onclick="applyFilters()">Apply Filters</button>
            </div>

            <div class="error-list">
    """
    )

    # Add error items
    for error in results.get("errors", []):
        severity_class = (
            "warning" if error.get("severity", "error") == "warning" else ""
        )
        severity_text = f"<span class='severity-{error.get('severity', 'error')}'>{error.get('severity', 'error').upper()}</span>"

        html += f"""
                <div class="error-item {severity_class}" data-type="{error.get("type", "")}" data-severity="{error.get("severity", "error")}">
                    <h4>{error.get("error_type", "Unknown Error").replace("_", " ").title()} - {severity_text}</h4>
                    <p>{error.get("message", "No message")}</p>
                    <p class="location">File: {error.get("filepath", "Unknown")} (Line {error.get("line", "N/A")})</p>
                </div>
        """

    html += (
        """
            </div>
        </div>

        <div id="codebase" class="tab-content">
            <div class="summary">
                <h2>Codebase Summary</h2>
                <pre>"""
        + results.get("codebase_summary", "No codebase summary available")
        + """</pre>
            </div>
        </div>

        <script>
            function showTab(tabId) {
                // Hide all tab contents
                var tabContents = document.getElementsByClassName('tab-content');
                for (var i = 0; i < tabContents.length; i++) {
                    tabContents[i].classList.remove('active');
                }

                // Deactivate all tabs
                var tabs = document.getElementsByClassName('tab');
                for (var i = 0; i < tabs.length; i++) {
                    tabs[i].classList.remove('active');
                }

                // Show the selected tab content
                document.getElementById(tabId).classList.add('active');

                // Activate the clicked tab
                var clickedTab = document.querySelector('.tab[onclick="showTab(\\''+tabId+'\\')"]');
                clickedTab.classList.add('active');
            }

            function applyFilters() {
                var typeFilter = document.getElementById('error-type-filter').value;
                var severityFilter = document.getElementById('severity-filter').value;
                var searchFilter = document.getElementById('search-filter').value.toLowerCase();

                var errorItems = document.getElementsByClassName('error-item');
                for (var i = 0; i < errorItems.length; i++) {
                    var item = errorItems[i];
                    var type = item.getAttribute('data-type');
                    var severity = item.getAttribute('data-severity');
                    var text = item.textContent.toLowerCase();

                    var typeMatch = typeFilter === 'all' || type === typeFilter;
                    var severityMatch = severityFilter === 'all' || severity === severityFilter;
                    var searchMatch = searchFilter === '' || text.includes(searchFilter);

                    if (typeMatch && severityMatch && searchMatch) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                }
            }

            // Initialize progress bar
            window.onload = function() {
                var progressBar = document.querySelector('.progress-bar-fill');
                if (progressBar) {
                    progressBar.style.width = '100%';
                }
            };
        </script>
    </body>
    </html>
    """
    )

    # Write HTML to file
    with open(output_file, "w") as f:
        f.write(html)

    logger.info(f"HTML report generated at {output_file}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze code integrity in a repository"
    )

    parser.add_argument("--repo", required=True, help="Path to the repository")
    parser.add_argument(
        "--mode",
        choices=["analyze", "compare", "pr"],
        default="analyze",
        help="Mode of operation: analyze a single codebase, compare branches, or analyze a PR",
    )
    parser.add_argument(
        "--main-branch", help="Main branch name (for compare and pr modes)"
    )
    parser.add_argument(
        "--feature-branch", help="Feature branch name (for compare and pr modes)"
    )
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--html", help="Output file for HTML report")
    parser.add_argument("--config", help="Configuration file (JSON or YAML)")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = load_config(args.config)

    # Process based on mode
    if args.mode == "analyze":
        # Analyze a single codebase
        codebase = load_codebase(args.repo)
        results = analyze_codebase(codebase, config, args.output)

        # Generate HTML report if requested
        if args.html:
            generate_html_report(results, args.html)

    elif args.mode == "compare":
        # Compare branches
        if not args.main_branch or not args.feature_branch:
            logger.error(
                "Both --main-branch and --feature-branch are required for compare mode"
            )
            sys.exit(1)

        # Load codebases
        main_codebase = load_codebase(args.repo, args.main_branch)
        feature_codebase = load_codebase(args.repo, args.feature_branch)

        # Compare codebases
        comparison = compare_codebases(
            main_codebase, feature_codebase, config, args.output
        )

        # Generate HTML report if requested
        if args.html:
            generate_html_report(comparison, args.html)

    elif args.mode == "pr":
        # Analyze a PR
        if not args.main_branch or not args.feature_branch:
            logger.error(
                "Both --main-branch and --feature-branch are required for PR mode"
            )
            sys.exit(1)

        # Load codebases
        main_codebase = load_codebase(args.repo, args.main_branch)
        pr_codebase = load_codebase(args.repo, args.feature_branch)

        # Analyze PR
        pr_analysis = analyze_pull_request(
            main_codebase, pr_codebase, config, args.output
        )

        # Generate HTML report if requested
        if args.html:
            generate_html_report(pr_analysis, args.html)


if __name__ == "__main__":
    main()
