#!/usr/bin/env python
"""
Example script for using the CodeIntegrityAnalyzer.

This script demonstrates how to use the CodeIntegrityAnalyzer to analyze
code integrity for a repository.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from codegen_on_oss.analysis import CodeAnalyzer

from codegen import Codebase


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze code integrity for a repository"
    )
    parser.add_argument(
        "--repo", required=True, help="Path to the repository to analyze"
    )
    parser.add_argument("--output", help="Path to output JSON file")
    parser.add_argument("--html", help="Path to output HTML report")
    parser.add_argument("--config", help="Path to configuration file (JSON or YAML)")
    parser.add_argument(
        "--mode",
        choices=["single", "compare", "pr"],
        default="single",
        help="Analysis mode: single (default), compare branches, or analyze PR",
    )
    parser.add_argument(
        "--main-branch", help="Main branch for comparison or PR analysis"
    )
    parser.add_argument(
        "--feature-branch", help="Feature branch for comparison or PR analysis"
    )

    return parser.parse_args()


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    """
    Load configuration from a file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    if not config_path:
        return {}

    config_path = Path(config_path)
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        return {}

    if config_path.suffix.lower() in [".json"]:
        with open(config_path, "r") as f:
            return json.load(f)
    elif config_path.suffix.lower() in [".yaml", ".yml"]:
        try:
            import yaml

            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except ImportError:
            print(
                "PyYAML not installed. Please install it to use YAML configuration files."
            )
            return {}
    else:
        print(f"Unsupported configuration file format: {config_path.suffix}")
        return {}


def generate_html_report(results: Dict[str, Any], output_path: str):
    """
    Generate an HTML report from analysis results.

    Args:
        results: Analysis results
        output_path: Path to output HTML file
    """
    # Simple HTML report template
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Integrity Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .error {{ background-color: #ffebee; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .warning {{ background-color: #fff8e1; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .tabs {{ display: flex; margin-bottom: 10px; }}
        .tab {{ padding: 10px 15px; cursor: pointer; background-color: #eee; margin-right: 5px; border-radius: 3px 3px 0 0; }}
        .tab.active {{ background-color: #fff; border: 1px solid #ccc; border-bottom: none; }}
        .tab-content {{ display: none; padding: 15px; border: 1px solid #ccc; }}
        .tab-content.active {{ display: block; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].className = tabcontent[i].className.replace(" active", "");
            }}
            tablinks = document.getElementsByClassName("tab");
            for (i = 0; i < tablinks.length; i++) {{
                tablinks[i].className = tablinks[i].className.replace(" active", "");
            }}
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }}
    </script>
</head>
<body>
    <h1>Code Integrity Analysis Report</h1>

    <div class="tabs">
        <div class="tab active" onclick="openTab(event, 'summary')">Summary</div>
        <div class="tab" onclick="openTab(event, 'function-errors')">Function Errors</div>
        <div class="tab" onclick="openTab(event, 'class-errors')">Class Errors</div>
        <div class="tab" onclick="openTab(event, 'parameter-errors')">Parameter Errors</div>
        <div class="tab" onclick="openTab(event, 'callback-errors')">Callback Errors</div>
        <div class="tab" onclick="openTab(event, 'other-errors')">Other Errors</div>
        <div class="tab" onclick="openTab(event, 'codebase')">Codebase</div>
    </div>

    <div id="summary" class="tab-content active">
        <h2>Analysis Summary</h2>
        <div class="summary">
            <p><strong>Total Functions:</strong> {results.get("total_functions", 0)}</p>
            <p><strong>Total Classes:</strong> {results.get("total_classes", 0)}</p>
            <p><strong>Total Files:</strong> {results.get("total_files", 0)}</p>
            <p><strong>Total Errors:</strong> {results.get("total_errors", 0)}</p>
            <ul>
                <li><strong>Function Errors:</strong> {results.get("function_errors", 0)}</li>
                <li><strong>Class Errors:</strong> {results.get("class_errors", 0)}</li>
                <li><strong>Parameter Errors:</strong> {results.get("parameter_errors", 0)}</li>
                <li><strong>Callback Errors:</strong> {results.get("callback_errors", 0)}</li>
                <li><strong>Import Errors:</strong> {results.get("import_errors", 0)}</li>
                <li><strong>Complexity Errors:</strong> {results.get("complexity_errors", 0)}</li>
                <li><strong>Type Hint Errors:</strong> {results.get("type_hint_errors", 0)}</li>
                <li><strong>Duplication Errors:</strong> {results.get("duplication_errors", 0)}</li>
            </ul>
        </div>
    </div>

    <div id="function-errors" class="tab-content">
        <h2>Function Errors</h2>
        <table>
            <tr>
                <th>Function</th>
                <th>Error Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
            {generate_table_rows(results.get("errors", []), "function_error")}
        </table>
    </div>

    <div id="class-errors" class="tab-content">
        <h2>Class Errors</h2>
        <table>
            <tr>
                <th>Class</th>
                <th>Error Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
            {generate_table_rows(results.get("errors", []), "class_error")}
        </table>
    </div>

    <div id="parameter-errors" class="tab-content">
        <h2>Parameter Errors</h2>
        <table>
            <tr>
                <th>Function</th>
                <th>Error Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
            {generate_table_rows(results.get("errors", []), "parameter_error")}
        </table>
    </div>

    <div id="callback-errors" class="tab-content">
        <h2>Callback Errors</h2>
        <table>
            <tr>
                <th>Function</th>
                <th>Callback</th>
                <th>Error Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
            {generate_callback_table_rows(results.get("errors", []))}
        </table>
    </div>

    <div id="other-errors" class="tab-content">
        <h2>Other Errors</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Error Type</th>
                <th>Name</th>
                <th>File</th>
                <th>Line</th>
                <th>Message</th>
            </tr>
            {generate_other_table_rows(results.get("errors", []))}
        </table>
    </div>

    <div id="codebase" class="tab-content">
        <h2>Codebase Summary</h2>
        <pre>{results.get("codebase_summary", "")}</pre>
    </div>
</body>
</html>
"""

    with open(output_path, "w") as f:
        f.write(html)

    print(f"HTML report generated: {output_path}")


def generate_table_rows(errors, error_type):
    """Generate table rows for errors of a specific type."""
    rows = []
    for e in errors:
        if e.get("type") == error_type:
            row = f"<tr><td>{e.get('name', '')}</td>"
            row += f"<td>{e.get('error_type', '')}</td>"
            row += f"<td>{e.get('filepath', '')}</td>"
            row += f"<td>{e.get('line', '')}</td>"
            row += f"<td>{e.get('message', '')}</td></tr>"
            rows.append(row)
    return "".join(rows)


def generate_callback_table_rows(errors):
    """Generate table rows for callback errors."""
    rows = []
    for e in errors:
        if e.get("type") == "callback_error":
            row = f"<tr><td>{e.get('name', '')}</td>"
            row += f"<td>{e.get('callback_name', '')}</td>"
            row += f"<td>{e.get('error_type', '')}</td>"
            row += f"<td>{e.get('filepath', '')}</td>"
            row += f"<td>{e.get('line', '')}</td>"
            row += f"<td>{e.get('message', '')}</td></tr>"
            rows.append(row)
    return "".join(rows)


def generate_other_table_rows(errors):
    """Generate table rows for other types of errors."""
    rows = []
    for e in errors:
        if e.get("type") not in [
            "function_error",
            "class_error",
            "parameter_error",
            "callback_error",
        ]:
            row = f"<tr><td>{e.get('type', '')}</td>"
            row += f"<td>{e.get('error_type', '')}</td>"
            row += f"<td>{e.get('name', '')}</td>"
            row += f"<td>{e.get('filepath', '')}</td>"
            row += f"<td>{e.get('line', '')}</td>"
            row += f"<td>{e.get('message', '')}</td></tr>"
            rows.append(row)
    return "".join(rows)


def main():
    """Main function."""
    args = parse_args()

    # Load configuration
    config = load_config(args.config)

    # Create codebase
    try:
        codebase = Codebase.from_repo(args.repo)
    except Exception as e:
        print(f"Error creating codebase: {e}")
        return 1

    # Analyze based on mode
    if args.mode == "single":
        # Single codebase analysis
        analyzer = CodeAnalyzer(codebase)
        results = analyzer.analyze_code_integrity(config)
    elif args.mode == "compare":
        # Branch comparison
        if not args.main_branch or not args.feature_branch:
            print("Main branch and feature branch are required for comparison mode")
            return 1

        print(f"Comparing branches: {args.main_branch} vs {args.feature_branch}")
        print("Branch comparison is not fully implemented in this example script.")

        # This is a placeholder for branch comparison
        # In a real implementation, this would:
        # 1. Get the codebase for each branch
        # 2. Analyze each codebase
        # 3. Compare the results

        results = {
            "mode": "compare",
            "main_branch": args.main_branch,
            "feature_branch": args.feature_branch,
            "message": "Branch comparison not fully implemented in this example script",
        }
    elif args.mode == "pr":
        # PR analysis
        if not args.main_branch or not args.feature_branch:
            print("Main branch and PR branch are required for PR analysis mode")
            return 1

        print(f"Analyzing PR: {args.feature_branch} -> {args.main_branch}")
        print("PR analysis is not fully implemented in this example script.")

        # This is a placeholder for PR analysis
        # In a real implementation, this would:
        # 1. Get the codebase for each branch
        # 2. Analyze each codebase
        # 3. Compare the results with focus on changes in the PR

        results = {
            "mode": "pr",
            "main_branch": args.main_branch,
            "pr_branch": args.feature_branch,
            "message": "PR analysis not fully implemented in this example script",
        }
    else:
        print(f"Unknown mode: {args.mode}")
        return 1

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results written to: {args.output}")

    # Generate HTML report
    if args.html:
        generate_html_report(results, args.html)

    # Print summary to console
    print("\nAnalysis Summary:")
    print(f"Total Functions: {results.get('total_functions', 0)}")
    print(f"Total Classes: {results.get('total_classes', 0)}")
    print(f"Total Files: {results.get('total_files', 0)}")
    print(f"Total Errors: {results.get('total_errors', 0)}")
    print(f"  Function Errors: {results.get('function_errors', 0)}")
    print(f"  Class Errors: {results.get('class_errors', 0)}")
    print(f"  Parameter Errors: {results.get('parameter_errors', 0)}")
    print(f"  Callback Errors: {results.get('callback_errors', 0)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
