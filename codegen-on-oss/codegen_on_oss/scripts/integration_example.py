#!/usr/bin/env python3
"""
Integration Example Script

This script demonstrates how to use the code metrics functionality from codegen-on-oss
with the examples from codegen-examples.
"""

import argparse
import json
import os
from pathlib import Path

from codegen import Codebase
from codegen_on_oss.analysis.code_metrics import (
    analyze_codebase_metrics,
    calculate_cyclomatic_complexity,
    calculate_maintainability_index,
    calculate_halstead_metrics,
    get_function_metrics
)

def analyze_repository(repo_url, commit_hash=None, output_format="text", output_file=None):
    """
    Analyze a repository using code metrics functionality
    
    Args:
        repo_url: URL of the repository to analyze
        commit_hash: Optional commit hash to analyze
        output_format: Format for output (text, json, or html)
        output_file: Optional file to write output to
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
    metrics = analyze_codebase_metrics(codebase)
    
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

def format_text_report(metrics, repo_name):
    """Format metrics as a text report"""
    lines = []
    lines.append(f"Code Metrics Analysis for {repo_name}")
    lines.append("=" * 80)
    lines.append("")
    
    # Overall statistics
    lines.append("Overall Statistics:")
    lines.append(f"  Total Files: {len(metrics['files'])}")
    lines.append(f"  Total Functions/Methods: {metrics['function_count']}")
    lines.append(f"  Total Classes: {metrics['class_count']}")
    lines.append(f"  Total Lines of Code: {metrics['total_lines']}")
    lines.append(f"  Overall Complexity: {metrics['overall_complexity']}")
    lines.append(f"  Average Complexity: {metrics['average_complexity']}")
    lines.append("")
    
    # Complexity distribution
    lines.append("Complexity Distribution:")
    for rank, data in metrics['complexity_distribution'].items():
        if isinstance(data, dict):
            lines.append(f"  {rank} ({data['description']}): {data['count']} functions ({data['percentage']}%)")
    lines.append("")
    
    # Maintainability distribution
    lines.append("Maintainability Distribution:")
    for level, data in metrics['maintainability_distribution'].items():
        if isinstance(data, dict):
            lines.append(f"  {level.capitalize()}: {data['count']} functions ({data['percentage']}%)")
    lines.append("")
    
    # Top hotspots
    lines.append("Top 10 Complexity Hotspots:")
    for i, hotspot in enumerate(metrics['hotspots'][:10], 1):
        lines.append(f"  {i}. {hotspot['name']} ({hotspot['type']})")
        lines.append(f"     File: {hotspot['file']}:{hotspot['line']}")
        lines.append(f"     Complexity: {hotspot['complexity']} (Rank {hotspot['rank']})")
        lines.append(f"     Maintainability: {hotspot['maintainability']:.2f}")
        lines.append("")
    
    return "\n".join(lines)

def generate_html_report(metrics, repo_name):
    """Generate an HTML report from the metrics"""
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Code Metrics Report - {repo_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .stats {{ display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: #f5f5f5; border-radius: 5px; padding: 15px; flex: 1; min-width: 200px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .progress-bar {{ height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }}
        .progress {{ height: 100%; border-radius: 10px; }}
        .rank-A {{ background-color: #4CAF50; }}
        .rank-B {{ background-color: #8BC34A; }}
        .rank-C {{ background-color: #FFEB3B; }}
        .rank-D {{ background-color: #FF9800; }}
        .rank-E {{ background-color: #FF5722; }}
        .rank-F {{ background-color: #F44336; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Code Metrics Report - {repo_name}</h1>
        
        <h2>Overall Statistics</h2>
        <div class="stats">
            <div class="stat-card">
                <div>Files</div>
                <div class="stat-value">{len(metrics['files'])}</div>
            </div>
            <div class="stat-card">
                <div>Functions/Methods</div>
                <div class="stat-value">{metrics['function_count']}</div>
            </div>
            <div class="stat-card">
                <div>Classes</div>
                <div class="stat-value">{metrics['class_count']}</div>
            </div>
            <div class="stat-card">
                <div>Lines of Code</div>
                <div class="stat-value">{metrics['total_lines']}</div>
            </div>
            <div class="stat-card">
                <div>Overall Complexity</div>
                <div class="stat-value">{metrics['overall_complexity']}</div>
            </div>
            <div class="stat-card">
                <div>Average Complexity</div>
                <div class="stat-value">{metrics['average_complexity']}</div>
            </div>
        </div>
        
        <h2>Complexity Distribution</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Description</th>
                <th>Count</th>
                <th>Percentage</th>
                <th>Distribution</th>
            </tr>
    """
    
    # Add complexity distribution rows
    for rank, data in metrics['complexity_distribution'].items():
        if isinstance(data, dict):
            html += f"""
            <tr>
                <td>{rank}</td>
                <td>{data['description']}</td>
                <td>{data['count']}</td>
                <td>{data['percentage']}%</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress rank-{rank}" style="width: {data['percentage']}%"></div>
                    </div>
                </td>
            </tr>
            """
    
    html += """
        </table>
        
        <h2>Maintainability Distribution</h2>
        <table>
            <tr>
                <th>Level</th>
                <th>Count</th>
                <th>Percentage</th>
                <th>Distribution</th>
            </tr>
    """
    
    # Add maintainability distribution rows
    colors = {"high": "#4CAF50", "medium": "#FFEB3B", "low": "#F44336"}
    for level, data in metrics['maintainability_distribution'].items():
        if isinstance(data, dict):
            html += f"""
            <tr>
                <td>{level.capitalize()}</td>
                <td>{data['count']}</td>
                <td>{data['percentage']}%</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress" style="width: {data['percentage']}%; background-color: {colors[level]}"></div>
                    </div>
                </td>
            </tr>
            """
    
    html += """
        </table>
        
        <h2>Top Complexity Hotspots</h2>
        <table>
            <tr>
                <th>#</th>
                <th>Name</th>
                <th>Type</th>
                <th>File</th>
                <th>Line</th>
                <th>Complexity</th>
                <th>Rank</th>
                <th>Maintainability</th>
            </tr>
    """
    
    # Add hotspot rows
    for i, hotspot in enumerate(metrics['hotspots'][:10], 1):
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{hotspot['name']}</td>
            <td>{hotspot['type'].capitalize()}</td>
            <td>{hotspot['file']}</td>
            <td>{hotspot['line']}</td>
            <td>{hotspot['complexity']}</td>
            <td>{hotspot['rank']}</td>
            <td>{hotspot['maintainability']:.2f}</td>
        </tr>
        """
    
    html += """
        </table>
    </div>
</body>
</html>
    """
    
    return html

def main():
    parser = argparse.ArgumentParser(description="Analyze code metrics for a repository")
    parser.add_argument("repo_url", help="URL of the repository to analyze")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument("--format", choices=["text", "json", "html"], default="text", 
                        help="Output format (default: text)")
    parser.add_argument("--output", help="Output file (default: print to console)")
    
    args = parser.parse_args()
    
    analyze_repository(
        args.repo_url,
        commit_hash=args.commit,
        output_format=args.format,
        output_file=args.output
    )

if __name__ == "__main__":
    main()

