#!/usr/bin/env python3
"""
Unified Codegen-on-OSS Example.

This script demonstrates a comprehensive integration of all the codegen-on-oss features,
including repository analysis, commit analysis, PR analysis, code integrity validation,
and snapshot management.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add the parent directory to the path so we can import the codegen_on_oss package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from codegen_on_oss.api import (
    UnifiedAPI,
    analyze_repository,
    analyze_commit,
    analyze_pull_request,
    compare_branches,
    create_snapshot,
    compare_snapshots,
    analyze_code_integrity,
)


def generate_report(
    repo_results: Dict[str, Any],
    commit_results: Optional[Dict[str, Any]] = None,
    pr_results: Optional[Dict[str, Any]] = None,
    branch_results: Optional[Dict[str, Any]] = None,
    snapshot_results: Optional[Dict[str, Any]] = None,
    integrity_results: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a comprehensive HTML report of the analysis results.

    Args:
        repo_results: Repository analysis results
        commit_results: Optional commit analysis results
        pr_results: Optional PR analysis results
        branch_results: Optional branch comparison results
        snapshot_results: Optional snapshot comparison results
        integrity_results: Optional code integrity validation results
        output_path: Optional path to save the report

    Returns:
        HTML report as a string
    """
    # Create the HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Codegen-on-OSS Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .section {{ margin-bottom: 30px; }}
            .metric {{ margin-bottom: 20px; }}
            .metric-title {{ font-weight: bold; }}
            pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .issue {{ margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
            .high {{ background-color: #ffdddd; }}
            .medium {{ background-color: #ffffdd; }}
            .low {{ background-color: #ddffdd; }}
        </style>
    </head>
    <body>
        <h1>Codegen-on-OSS Analysis Report</h1>
        <div class="section">
            <h2>Repository Analysis</h2>
            <p><strong>Repository:</strong> {repo_results.get('repo_url', 'N/A')}</p>
            <p><strong>Analysis Time:</strong> {datetime.now().isoformat()}</p>
            
            <h3>Summary</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Files</td>
                    <td>{repo_results.get('summary', {}).get('file_count', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Functions</td>
                    <td>{repo_results.get('summary', {}).get('function_count', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Classes</td>
                    <td>{repo_results.get('summary', {}).get('class_count', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Average Complexity</td>
                    <td>{repo_results.get('complexity', {}).get('average_complexity', 'N/A')}</td>
                </tr>
            </table>
        </div>
    """

    # Add commit analysis section if available
    if commit_results:
        html += f"""
        <div class="section">
            <h2>Commit Analysis</h2>
            <p><strong>Commit Hash:</strong> {commit_results.get('commit_hash', 'N/A')}</p>
            
            <h3>Quality Assessment</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Is Properly Implemented</td>
                    <td>{commit_results.get('quality_assessment', {}).get('is_properly_implemented', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Score</td>
                    <td>{commit_results.get('quality_assessment', {}).get('score', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Overall Assessment</td>
                    <td>{commit_results.get('quality_assessment', {}).get('overall_assessment', 'N/A')}</td>
                </tr>
            </table>
            
            <h3>Changes</h3>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Files Added</td>
                    <td>{len(commit_results.get('changes', {}).get('files_added', []))}</td>
                </tr>
                <tr>
                    <td>Files Modified</td>
                    <td>{len(commit_results.get('changes', {}).get('files_modified', []))}</td>
                </tr>
                <tr>
                    <td>Files Removed</td>
                    <td>{len(commit_results.get('changes', {}).get('files_removed', []))}</td>
                </tr>
            </table>
            
            <h3>Issues</h3>
        """

        # Add issues if available
        issues = commit_results.get('issues', [])
        if issues:
            for issue in issues[:5]:  # Show only the first 5 issues
                severity = issue.get('severity', 'medium')
                html += f"""
                <div class="issue {severity}">
                    <h4>{issue.get('title', 'Unnamed Issue')}</h4>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Location:</strong> {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}</p>
                    <p><strong>Description:</strong> {issue.get('description', 'No description')}</p>
                </div>
                """
            if len(issues) > 5:
                html += f"<p>... and {len(issues) - 5} more issues</p>"
        else:
            html += "<p>No issues found.</p>"

        html += "</div>"

    # Add PR analysis section if available
    if pr_results:
        html += f"""
        <div class="section">
            <h2>Pull Request Analysis</h2>
            <p><strong>PR Number:</strong> {pr_results.get('pr_number', 'N/A')}</p>
            
            <h3>Quality Assessment</h3>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Is Properly Implemented</td>
                    <td>{pr_results.get('quality_assessment', {}).get('is_properly_implemented', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Score</td>
                    <td>{pr_results.get('quality_assessment', {}).get('score', 'N/A')}</td>
                </tr>
                <tr>
                    <td>Overall Assessment</td>
                    <td>{pr_results.get('quality_assessment', {}).get('overall_assessment', 'N/A')}</td>
                </tr>
            </table>
            
            <h3>Changes</h3>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Files Added</td>
                    <td>{len(pr_results.get('changes', {}).get('files_added', []))}</td>
                </tr>
                <tr>
                    <td>Files Modified</td>
                    <td>{len(pr_results.get('changes', {}).get('files_modified', []))}</td>
                </tr>
                <tr>
                    <td>Files Removed</td>
                    <td>{len(pr_results.get('changes', {}).get('files_removed', []))}</td>
                </tr>
            </table>
            
            <h3>Issues</h3>
        """

        # Add issues if available
        issues = pr_results.get('issues', [])
        if issues:
            for issue in issues[:5]:  # Show only the first 5 issues
                severity = issue.get('severity', 'medium')
                html += f"""
                <div class="issue {severity}">
                    <h4>{issue.get('title', 'Unnamed Issue')}</h4>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Location:</strong> {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}</p>
                    <p><strong>Description:</strong> {issue.get('description', 'No description')}</p>
                </div>
                """
            if len(issues) > 5:
                html += f"<p>... and {len(issues) - 5} more issues</p>"
        else:
            html += "<p>No issues found.</p>"

        html += "</div>"

    # Add branch comparison section if available
    if branch_results:
        html += f"""
        <div class="section">
            <h2>Branch Comparison</h2>
            <p><strong>Base Branch:</strong> {branch_results.get('base_branch', 'N/A')}</p>
            <p><strong>Head Branch:</strong> {branch_results.get('head_branch', 'N/A')}</p>
            <p><strong>Summary:</strong> {branch_results.get('summary', 'N/A')}</p>
            
            <h3>Changes</h3>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Files Added</td>
                    <td>{len(branch_results.get('changes', {}).get('files_added', []))}</td>
                </tr>
                <tr>
                    <td>Files Modified</td>
                    <td>{len(branch_results.get('changes', {}).get('files_modified', []))}</td>
                </tr>
                <tr>
                    <td>Files Removed</td>
                    <td>{len(branch_results.get('changes', {}).get('files_removed', []))}</td>
                </tr>
            </table>
        </div>
        """

    # Add snapshot comparison section if available
    if snapshot_results:
        html += f"""
        <div class="section">
            <h2>Snapshot Comparison</h2>
            <p><strong>Snapshot 1:</strong> {snapshot_results.get('snapshot_1', 'N/A')}</p>
            <p><strong>Snapshot 2:</strong> {snapshot_results.get('snapshot_2', 'N/A')}</p>
            <p><strong>Summary:</strong> {snapshot_results.get('summary', 'N/A')}</p>
            
            <h3>Changes</h3>
            <table>
                <tr>
                    <th>Type</th>
                    <th>Count</th>
                </tr>
                <tr>
                    <td>Files Added</td>
                    <td>{len(snapshot_results.get('changes', {}).get('files_added', []))}</td>
                </tr>
                <tr>
                    <td>Files Modified</td>
                    <td>{len(snapshot_results.get('changes', {}).get('files_modified', []))}</td>
                </tr>
                <tr>
                    <td>Files Removed</td>
                    <td>{len(snapshot_results.get('changes', {}).get('files_removed', []))}</td>
                </tr>
            </table>
        </div>
        """

    # Add code integrity section if available
    if integrity_results:
        html += f"""
        <div class="section">
            <h2>Code Integrity Analysis</h2>
            <p><strong>Timestamp:</strong> {integrity_results.get('timestamp', 'N/A')}</p>
            <p><strong>Summary:</strong> {integrity_results.get('summary', 'N/A')}</p>
            
            <h3>Issues</h3>
        """

        # Add issues if available
        issues = integrity_results.get('issues', [])
        if issues:
            for issue in issues[:5]:  # Show only the first 5 issues
                severity = issue.get('severity', 'medium')
                html += f"""
                <div class="issue {severity}">
                    <h4>{issue.get('title', 'Unnamed Issue')}</h4>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Location:</strong> {issue.get('file', 'N/A')}:{issue.get('line', 'N/A')}</p>
                    <p><strong>Description:</strong> {issue.get('description', 'No description')}</p>
                </div>
                """
            if len(issues) > 5:
                html += f"<p>... and {len(issues) - 5} more issues</p>"
        else:
            html += "<p>No issues found.</p>"

        html += "</div>"

    # Close the HTML
    html += """
    </body>
    </html>
    """

    # Save the report if output path is provided
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_path, "w") as f:
            f.write(html)

    return html


def run_unified_example(
    repo_url: str,
    output_dir: str,
    commit_hash: Optional[str] = None,
    pr_number: Optional[int] = None,
    base_branch: str = "main",
    head_branch: str = "develop",
    github_token: Optional[str] = None,
) -> None:
    """
    Run the unified example.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to save the analysis results
        commit_hash: Optional commit hash to analyze
        pr_number: Optional PR number to analyze
        base_branch: Base branch for comparison (default: main)
        head_branch: Head branch for comparison (default: develop)
        github_token: Optional GitHub token for accessing private repositories
    """
    print(f"Running unified example for repository: {repo_url}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Initialize the API
    api = UnifiedAPI(github_token=github_token)

    # Analyze the repository
    print("Analyzing repository...")
    repo_results = api.analyze_repository(
        repo_url=repo_url,
        output_path=os.path.join(output_dir, "repo_analysis.json"),
        include_integrity=True,
    )

    # Initialize variables for optional analyses
    commit_results = None
    pr_results = None
    branch_results = None
    snapshot_results = None
    integrity_results = None

    # Analyze a commit if specified
    if commit_hash:
        print(f"Analyzing commit: {commit_hash}")
        commit_results = api.analyze_commit(
            repo_url=repo_url,
            commit_hash=commit_hash,
            output_path=os.path.join(output_dir, "commit_analysis.json"),
        )

    # Analyze a PR if specified
    if pr_number and github_token:
        print(f"Analyzing PR #{pr_number}")
        pr_results = api.analyze_pull_request(
            repo_url=repo_url,
            pr_number=pr_number,
            output_path=os.path.join(output_dir, "pr_analysis.json"),
        )

    # Compare branches
    try:
        print(f"Comparing branches: {base_branch} -> {head_branch}")
        branch_results = api.compare_branches(
            repo_url=repo_url,
            base_branch=base_branch,
            head_branch=head_branch,
            output_path=os.path.join(output_dir, "branch_comparison.json"),
        )
    except Exception as e:
        print(f"Error comparing branches: {e}")

    # Create and compare snapshots
    try:
        print("Creating snapshots...")
        snapshot_id_1 = api.create_snapshot(
            repo_url=repo_url,
            branch=base_branch,
            snapshot_name=f"{base_branch}-snapshot",
            output_path=os.path.join(output_dir, f"{base_branch}_snapshot.json"),
        )

        snapshot_id_2 = api.create_snapshot(
            repo_url=repo_url,
            branch=head_branch,
            snapshot_name=f"{head_branch}-snapshot",
            output_path=os.path.join(output_dir, f"{head_branch}_snapshot.json"),
        )

        print("Comparing snapshots...")
        snapshot_results = api.compare_snapshots(
            snapshot_id_1=os.path.join(output_dir, f"{base_branch}_snapshot.json"),
            snapshot_id_2=os.path.join(output_dir, f"{head_branch}_snapshot.json"),
            output_path=os.path.join(output_dir, "snapshot_comparison.json"),
        )
    except Exception as e:
        print(f"Error creating or comparing snapshots: {e}")

    # Analyze code integrity
    print("Analyzing code integrity...")
    integrity_results = api.analyze_code_integrity(
        repo_url=repo_url,
        output_path=os.path.join(output_dir, "code_integrity.json"),
    )

    # Generate a comprehensive report
    print("Generating comprehensive report...")
    generate_report(
        repo_results=repo_results,
        commit_results=commit_results,
        pr_results=pr_results,
        branch_results=branch_results,
        snapshot_results=snapshot_results,
        integrity_results=integrity_results,
        output_path=os.path.join(output_dir, "comprehensive_report.html"),
    )

    print(f"Analysis complete! Results saved to {output_dir}")
    print(f"Comprehensive report: {os.path.join(output_dir, 'comprehensive_report.html')}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Codegen-on-OSS Example")
    parser.add_argument("--repo", required=True, help="URL of the repository to analyze")
    parser.add_argument("--output-dir", default="output", help="Directory to save the analysis results")
    parser.add_argument("--commit", help="Commit hash to analyze")
    parser.add_argument("--pr", type=int, help="PR number to analyze")
    parser.add_argument("--base-branch", default="main", help="Base branch for comparison")
    parser.add_argument("--head-branch", default="develop", help="Head branch for comparison")
    parser.add_argument("--github-token", help="GitHub token for accessing private repositories")

    args = parser.parse_args()

    run_unified_example(
        repo_url=args.repo,
        output_dir=args.output_dir,
        commit_hash=args.commit,
        pr_number=args.pr,
        base_branch=args.base_branch,
        head_branch=args.head_branch,
        github_token=args.github_token,
    )


if __name__ == "__main__":
    main()

