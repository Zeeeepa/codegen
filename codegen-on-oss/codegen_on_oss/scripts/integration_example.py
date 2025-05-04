#!/usr/bin/env python3
"""
Integration Example Script

This script demonstrates how to use the code metrics functionality from
codegen-on-oss with the examples from codegen-examples.
"""

import argparse
import json

from codegen_on_oss.analysis.code_metrics import analyze_codebase_metrics

from codegen import Codebase


def analyze_repository(
    repo_url: str,
    commit_hash: str = None,
    output_format: str = "text",
    output_file: str = None,
) -> dict:
    """
    Analyze a repository using code metrics functionality

    Args:
        repo_url: URL of the repository to analyze
        commit_hash: Optional commit hash to analyze
        output_format: Format for output (text, json, or html)
        output_file: Optional file to write output to

    Returns:
        Dictionary containing metrics data
    """
    print(f"Analyzing repository: {repo_url}")
    if commit_hash:
        print(f"Using commit: {commit_hash}")

    # Parse the repository URL to get the repo name
    repo_parts = repo_url.strip("/").split("/")
    if len(repo_parts) >= 2:
        repo_name = f"{repo_parts[-2]}/{repo_parts[-1]}"
    else:
        repo_name = repo_url

    # Load the codebase
    print("Loading codebase...")
    codebase = Codebase.from_repo(repo_name, commit=commit_hash)

    # Analyze the codebase
    print("Analyzing codebase metrics...")
    files_dict = {str(f.path): f.content for f in codebase.files}
    metrics = analyze_codebase_metrics(files_dict)

    # Format and output the results
    if output_format == "json":
        output = json.dumps(metrics, indent=2)
    elif output_format == "html":
        output = generate_html_report(metrics, repo_name)
    else:  # text format
        output = format_text_report(metrics, repo_name)

    # Write to file or print to console
    if output_file:
        with open(output_file, "w") as f:
            f.write(output)
        print(f"Results written to {output_file}")
    else:
        print(output)

    return metrics


def format_text_report(metrics: dict, repo_name: str) -> str:
    """
    Format metrics as a text report

    Args:
        metrics: Dictionary containing metrics data
        repo_name: Name of the repository

    Returns:
        Formatted text report
    """
    lines = []
    lines.append(f"Code Metrics Analysis for {repo_name}")
    lines.append("=" * 79)
    lines.append("")

    # Overall statistics
    lines.append("Overall Statistics:")
    lines.append(f"  Total Files: {metrics['total_files']}")
    lines.append(f"  Total Functions: {metrics['function_count']}")
    lines.append(f"  Total Lines of Code: {metrics['total_lines']}")
    lines.append(f"  Code Lines: {metrics['code_lines']}")
    lines.append(f"  Comment Lines: {metrics['comment_lines']}")
    lines.append(f"  Blank Lines: {metrics['blank_lines']}")
    lines.append(f"  Comment Ratio: {metrics['comment_ratio']}%")
    lines.append(f"  Average Complexity: {metrics['avg_complexity']}")
    lines.append(
        f"  Average Maintainability: {metrics['avg_maintainability']}"
    )
    lines.append("")

    # File details
    lines.append("File Details:")
    for path, file_metrics in list(metrics["files"].items())[:10]:  # Top 10
        lines.append(f"  {path}")
        lines.append(f"    Complexity: {file_metrics['complexity']}")
        lines.append(
            f"    Maintainability: {file_metrics['maintainability']:.2f}"
        )
        lines.append(
            f"    Lines: {file_metrics['line_metrics']['total_lines']}"
        )
        lines.append("")

    return "\n".join(lines)


def generate_html_report(metrics: dict, repo_name: str) -> str:
    """
    Generate an HTML report from the metrics

    Args:
        metrics: Dictionary containing metrics data
        repo_name: Name of the repository

    Returns:
        HTML report as a string
    """
    # HTML header and style
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"    <title>Code Metrics Report - {repo_name}</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; }",
        "        h1, h2, h3 { color: #333; }",
        "        .container { max-width: 1200px; margin: 0 auto; }",
        "        .stats { display: flex; flex-wrap: wrap; gap: 20px; }",
        "        .stat-card { background: #f5f5f5; border-radius: 5px; ",
        "                     padding: 15px; flex: 1; min-width: 200px; }",
        "        .stat-value { font-size: 24px; font-weight: bold; ",
        "                      margin: 10px 0; }",
        "        table { width: 100%; border-collapse: collapse; ",
        "                margin: 20px 0; }",
        "        th, td { padding: 10px; text-align: left; ",
        "                 border-bottom: 1px solid #ddd; }",
        "        th { background-color: #f2f2f2; }",
        "        tr:hover { background-color: #f5f5f5; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        f"        <h1>Code Metrics Report - {repo_name}</h1>",
        "",
        "        <h2>Overall Statistics</h2>",
        "        <div class=\"stats\">",
    ]

    # Overall statistics cards
    stats = [
        ("Files", metrics["total_files"]),
        ("Functions", metrics["function_count"]),
        ("Total Lines", metrics["total_lines"]),
        ("Code Lines", metrics["code_lines"]),
        ("Comment Lines", metrics["comment_lines"]),
        ("Blank Lines", metrics["blank_lines"]),
        ("Comment Ratio", f"{metrics['comment_ratio']}%"),
        ("Avg Complexity", metrics["avg_complexity"]),
        ("Avg Maintainability", f"{metrics['avg_maintainability']:.2f}"),
    ]

    for label, value in stats:
        html.extend([
            "            <div class=\"stat-card\">",
            f"                <div>{label}</div>",
            f"                <div class=\"stat-value\">{value}</div>",
            "            </div>",
        ])

    html.append("        </div>")

    # File details table
    html.extend([
        "",
        "        <h2>File Details</h2>",
        "        <table>",
        "            <tr>",
        "                <th>File</th>",
        "                <th>Complexity</th>",
        "                <th>Maintainability</th>",
        "                <th>Total Lines</th>",
        "                <th>Code Lines</th>",
        "                <th>Comment Lines</th>",
        "                <th>Functions</th>",
        "            </tr>",
    ])

    # Add file rows (top 20 files)
    for path, file_metrics in list(metrics["files"].items())[:20]:
        html.append("            <tr>")
        html.append(f"                <td>{path}</td>")
        html.append(f"                <td>{file_metrics['complexity']}</td>")
        html.append(
            f"                <td>{file_metrics['maintainability']:.2f}</td>"
        )
        line_metrics = file_metrics['line_metrics']
        total_lines = line_metrics['total_lines']
        code_lines = line_metrics['code_lines']
        comment_lines = line_metrics['comment_lines']
        html.append(f"                <td>{total_lines}</td>")
        html.append(f"                <td>{code_lines}</td>")
        html.append(f"                <td>{comment_lines}</td>")
        func_count = file_metrics['function_metrics']['count']
        html.append(f"                <td>{func_count}</td>")
        html.append("            </tr>")

    # HTML footer
    html.extend([
        "        </table>",
        "    </div>",
        "</body>",
        "</html>",
    ])

    return "\n".join(html)


def main() -> None:
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="Analyze code metrics for a repository"
    )
    parser.add_argument("repo_url", help="URL of the repository to analyze")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Output file (default: print to console)"
    )

    args = parser.parse_args()

    analyze_repository(
        args.repo_url,
        commit_hash=args.commit,
        output_format=args.format,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
