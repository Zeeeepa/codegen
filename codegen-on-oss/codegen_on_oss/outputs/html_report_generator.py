"""
HTML Report Generator for Code Integrity Analysis

This module provides functionality to generate HTML reports from code integrity analysis results.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

def generate_html_report(results: Dict[str, Any], output_path: str, mode: str = "single") -> None:
    """Generate an HTML report from code integrity analysis results.
    
    Args:
        results: Analysis results dictionary containing required keys based on mode
        output_path: Path to save the HTML report
        mode: Analysis mode (single, compare, or pr)
        
    Raises:
        ValueError: If mode is invalid or required keys are missing in results
        IOError: If file operations fail
    """
    if not isinstance(results, dict):
        raise ValueError("Results must be a dictionary")
    
    _validate_results(results, mode)
    Generate an HTML report from code integrity analysis results.
    
    Args:
        results: Analysis results
        output_path: Path to save the HTML report
        mode: Analysis mode (single, compare, or pr)
    """
    # Create HTML content based on the analysis mode
    if mode == "single":
        html_content = _generate_single_branch_report(results)
    elif mode == "compare":
        html_content = _generate_branch_comparison_report(results)
    elif mode == "pr":
        html_content = _generate_pr_analysis_report(results)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    # Write HTML content to file
    with open(output_path, 'w') as f:
        f.write(html_content)


def _generate_single_branch_report(results: Dict[str, Any]) -> str:
    """
    Generate HTML report for single branch analysis.
    
    Args:
        results: Analysis results
    
    Returns:
        HTML content as a string
    """
    # Extract data from results
    total_functions = results.get("total_functions", 0)
    total_classes = results.get("total_classes", 0)
    total_files = results.get("total_files", 0)
    total_errors = results.get("total_errors", 0)
    errors = results.get("errors", [])
    codebase_summary = results.get("codebase_summary", "")
    execution_time = results.get("execution_time", 0)
    
    # Group errors by type
    error_types = {}
    for error in errors:
        error_type = error.get("error_type", "unknown")
        if error_type not in error_types:
            error_types[error_type] = []
        error_types[error_type].append(error)
    
    # Generate HTML content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Code Integrity Analysis Report</title>
        <style>
            {_get_css_styles()}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Code Integrity Analysis Report</h1>
            <p class="timestamp">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
            <div class="summary-box">
                <h2>Summary</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-value">{total_functions}</span>
                        <span class="summary-label">Functions</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">{total_classes}</span>
                        <span class="summary-label">Classes</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">{total_files}</span>
                        <span class="summary-label">Files</span>
                    </div>
                    <div class="summary-item {_get_error_class(total_errors)}">
                        <span class="summary-value">{total_errors}</span>
                        <span class="summary-label">Errors</span>
                    </div>
                </div>
                <p class="execution-time">Analysis completed in {execution_time:.2f} seconds</p>
            </div>
    
            <div class="tabs">
                <div class="tab-buttons">
                    <button class="tab-button active" onclick="openTab(event, 'errors-tab')">Errors</button>
                    <button class="tab-button" onclick="openTab(event, 'summary-tab')">Codebase Summary</button>
                </div>
    
                <div id="errors-tab" class="tab-content active">
                    <h2>Errors by Type</h2>
                    <div class="error-type-list">
                        {_generate_error_type_list(error_types)}
                    </div>
    
                    <h2>All Errors</h2>
                    <div class="error-list">
                        {_generate_error_list(errors)}
                    </div>
                </div>
    
                <div id="summary-tab" class="tab-content">
                    <h2>Codebase Summary</h2>
                    <pre class="codebase-summary">{codebase_summary}</pre>
                </div>
            </div>
        </div>
    
        <script>
            {_get_javascript()}
        </script>
    </body>
    </html>
    """
    
    return html


def _generate_branch_comparison_report(results: Dict[str, Any]) -> str:
    """
    Generate HTML report for branch comparison analysis.
    
    Args:
        results: Comparison results
    
    Returns:
        HTML content as a string
    """
    # Extract data from results
    main_error_count = results.get("main_error_count", 0)
    branch_error_count = results.get("branch_error_count", 0)
    error_diff = results.get("error_diff", 0)
    new_errors = results.get("new_errors", [])
    fixed_errors = results.get("fixed_errors", [])
    main_summary = results.get("main_summary", "")
    branch_summary = results.get("branch_summary", "")
    execution_time = results.get("execution_time", 0)
    
    # Generate HTML content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Branch Comparison Report</title>
        <style>
            {_get_css_styles()}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Branch Comparison Report</h1>
            <p class="timestamp">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
            <div class="summary-box">
                <h2>Comparison Summary</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-value">{main_error_count}</span>
                        <span class="summary-label">Main Branch Errors</span>
                    </div>
                    <div class="summary-item {_get_error_class(branch_error_count)}">
                        <span class="summary-value">{branch_error_count}</span>
                        <span class="summary-label">Feature Branch Errors</span>
                    </div>
                    <div class="summary-item {_get_diff_class(error_diff)}">
                        <span class="summary-value">{error_diff:+d}</span>
                        <span class="summary-label">Error Difference</span>
                    </div>
                </div>
                <p class="execution-time">Comparison completed in {execution_time:.2f} seconds</p>
            </div>
    
            <div class="tabs">
                <div class="tab-buttons">
                    <button class="tab-button active" onclick="openTab(event, 'new-errors-tab')">New Errors ({len(new_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'fixed-errors-tab')">Fixed Errors ({len(fixed_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'main-summary-tab')">Main Branch Summary</button>
                    <button class="tab-button" onclick="openTab(event, 'feature-summary-tab')">Feature Branch Summary</button>
                </div>
    
                <div id="new-errors-tab" class="tab-content active">
                    <h2>New Errors in Feature Branch</h2>
                    <div class="error-list">
                        {_generate_error_list(new_errors)}
                    </div>
                </div>
    
                <div id="fixed-errors-tab" class="tab-content">
                    <h2>Errors Fixed in Feature Branch</h2>
                    <div class="error-list">
                        {_generate_error_list(fixed_errors)}
                    </div>
                </div>
    
                <div id="main-summary-tab" class="tab-content">
                    <h2>Main Branch Summary</h2>
                    <pre class="codebase-summary">{main_summary}</pre>
                </div>
    
                <div id="feature-summary-tab" class="tab-content">
                    <h2>Feature Branch Summary</h2>
                    <pre class="codebase-summary">{branch_summary}</pre>
                </div>
            </div>
        </div>
    
        <script>
            {_get_javascript()}
        </script>
    </body>
    </html>
    """
    
    return html


def _generate_pr_analysis_report(results: Dict[str, Any]) -> str:
    """
    Generate HTML report for PR analysis.
    
    Args:
        results: PR analysis results
    
    Returns:
        HTML content as a string
    """
    # Extract data from results
    comparison = results.get("comparison", {})
    new_functions = results.get("new_functions", 0)
    new_classes = results.get("new_classes", 0)
    modified_functions = results.get("modified_functions", 0)
    modified_classes = results.get("modified_classes", 0)
    new_function_errors = results.get("new_function_errors", [])
    new_class_errors = results.get("new_class_errors", [])
    modified_function_errors = results.get("modified_function_errors", [])
    modified_class_errors = results.get("modified_class_errors", [])
    total_new_errors = results.get("total_new_errors", 0)
    execution_time = results.get("execution_time", 0)
    
    # Generate HTML content
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pull Request Analysis Report</title>
        <style>
            {_get_css_styles()}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Pull Request Analysis Report</h1>
            <p class="timestamp">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
            <div class="summary-box">
                <h2>PR Summary</h2>
                <div class="summary-grid">
                    <div class="summary-item">
                        <span class="summary-value">{new_functions}</span>
                        <span class="summary-label">New Functions</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">{new_classes}</span>
                        <span class="summary-label">New Classes</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">{modified_functions}</span>
                        <span class="summary-label">Modified Functions</span>
                    </div>
                    <div class="summary-item">
                        <span class="summary-value">{modified_classes}</span>
                        <span class="summary-label">Modified Classes</span>
                    </div>
                    <div class="summary-item {_get_error_class(total_new_errors)}">
                        <span class="summary-value">{total_new_errors}</span>
                        <span class="summary-label">Total New Errors</span>
                    </div>
                </div>
                <p class="execution-time">Analysis completed in {execution_time:.2f} seconds</p>
            </div>
    
            <div class="tabs">
                <div class="tab-buttons">
                    <button class="tab-button active" onclick="openTab(event, 'new-function-errors-tab')">New Function Errors ({len(new_function_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'new-class-errors-tab')">New Class Errors ({len(new_class_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'modified-function-errors-tab')">Modified Function Errors ({len(modified_function_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'modified-class-errors-tab')">Modified Class Errors ({len(modified_class_errors)})</button>
                    <button class="tab-button" onclick="openTab(event, 'comparison-tab')">Branch Comparison</button>
                </div>
    
                <div id="new-function-errors-tab" class="tab-content active">
                    <h2>Errors in New Functions</h2>
                    <div class="error-list">
                        {_generate_error_list(new_function_errors)}
                    </div>
                </div>
    
                <div id="new-class-errors-tab" class="tab-content">
                    <h2>Errors in New Classes</h2>
                    <div class="error-list">
                        {_generate_error_list(new_class_errors)}
                    </div>
                </div>
    
                <div id="modified-function-errors-tab" class="tab-content">
                    <h2>Errors in Modified Functions</h2>
                    <div class="error-list">
                        {_generate_error_list(modified_function_errors)}
                    </div>
                </div>
    
                <div id="modified-class-errors-tab" class="tab-content">
                    <h2>Errors in Modified Classes</h2>
                    <div class="error-list">
                        {_generate_error_list(modified_class_errors)}
                    </div>
                </div>
    
                <div id="comparison-tab" class="tab-content">
                    <h2>Branch Comparison</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <span class="summary-value">{comparison.get("main_error_count", 0)}</span>
                            <span class="summary-label">Main Branch Errors</span>
                        </div>
                        <div class="summary-item {_get_error_class(comparison.get("branch_error_count", 0))}">
                            <span class="summary-value">{comparison.get("branch_error_count", 0)}</span>
                            <span class="summary-label">PR Branch Errors</span>
                        </div>
                        <div class="summary-item {_get_diff_class(comparison.get("error_diff", 0))}">
                            <span class="summary-value">{comparison.get("error_diff", 0):+d}</span>
                            <span class="summary-label">Error Difference</span>
                        </div>
                    </div>
                    <h3>New Errors in PR Branch</h3>
                    <div class="error-list">
                        {_generate_error_list(comparison.get("new_errors", []))}
                    </div>
                    <h3>Errors Fixed in PR Branch</h3>
                    <div class="error-list">
                        {_generate_error_list(comparison.get("fixed_errors", []))}
                    </div>
                </div>
            </div>
        </div>
    
        <script>
            {_get_javascript()}
        </script>
    </body>
    </html>
    """
    
    return html


def _generate_error_list(errors: List[Dict[str, Any]]) -> str:
    """
    Generate HTML for a list of errors.
    
    Args:
        errors: List of error dictionaries
    
    Returns:
        HTML content as a string
    """
    if not errors:
        return "<p class='no-errors'>No errors found.</p>"
    
    html = "<table class='error-table'>"
    html += "<tr><th>Type</th><th>File</th><th>Line</th><th>Message</th><th>Severity</th></tr>"
    
    for error in errors:
        error_type = error.get("error_type", "unknown")
        filepath = error.get("filepath", "")
        line = error.get("line", "")
        message = error.get("message", "")
        severity = error.get("severity", "warning")
        
        html += f"<tr class='{severity}-row'>"
        html += f"<td>{error_type}</td>"
        html += f"<td>{filepath}</td>"
        html += f"<td>{line}</td>"
        html += f"<td>{message}</td>"
        html += f"<td class='{severity}'>{severity.upper()}</td>"
        html += "</tr>"
    
    html += "</table>"
    return html


def _generate_error_type_list(error_types: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Generate HTML for errors grouped by type.
    
    Args:
        error_types: Dictionary mapping error types to lists of errors
    
    Returns:
        HTML content as a string
    """
    if not error_types:
        return "<p class='no-errors'>No errors found.</p>"
    
    html = "<div class='error-type-grid'>"
    
    for error_type, errors in error_types.items():
        error_count = len(errors)
        severity_class = _get_severity_class(errors)
        
        html += f"<div class='error-type-item {severity_class}'>"
        html += f"<h3>{error_type}</h3>"
        html += f"<p class='error-count'>{error_count} error{'s' if error_count != 1 else ''}</p>"
        html += "</div>"
    
    html += "</div>"
    return html


def _get_severity_class(errors: List[Dict[str, Any]]) -> str:
    """
    Get the highest severity class for a list of errors.
    
    Args:
        errors: List of error dictionaries
    
    Returns:
        CSS class name for the severity
    """
    if any(error.get("severity") == "error" for error in errors):
        return "error"
    elif any(error.get("severity") == "warning" for error in errors):
        return "warning"
    else:
        return "info"


def _get_error_class(error_count: int) -> str:
    """
    Get the CSS class for an error count.
    
    Args:
        error_count: Number of errors
    
    Returns:
        CSS class name
    """
    if error_count > 50:
        return "error"
    elif error_count > 10:
        return "warning"
    else:
        return ""


def _get_diff_class(diff: int) -> str:
    """
    Get the CSS class for an error difference.
    
    Args:
        diff: Error difference
    
    Returns:
        CSS class name
    """
    if diff > 0:
        return "error"
    elif diff < 0:
        return "success"
    else:
        return ""


def _get_css_styles() -> str:
    """
    Get CSS styles for the HTML report.
    
    Returns:
        CSS styles as a string
    """
    return """
        :root {
            --primary-color: #4a6fa5;
            --secondary-color: #6c757d;
            --success-color: #28a745;
            --info-color: #17a2b8;
            --warning-color: #ffc107;
            --error-color: #dc3545;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
            --border-color: #dee2e6;
            --border-radius: 4px;
            --box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.5;
            color: #333;
            background-color: #f5f5f5;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            padding: 20px;
        }

        h1, h2, h3 {
            margin-bottom: 15px;
            color: var(--primary-color);
        }

        h1 {
            font-size: 24px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
        }

        h2 {
            font-size: 20px;
            margin-top: 20px;
        }

        h3 {
            font-size: 18px;
            margin-top: 15px;
        }

        .timestamp {
            color: var(--secondary-color);
            font-size: 14px;
            margin-bottom: 20px;
        }

        .execution-time {
            color: var(--secondary-color);
            font-size: 14px;
            margin-top: 10px;
            text-align: right;
        }

        .summary-box {
            background-color: var(--light-color);
            border-radius: var(--border-radius);
            padding: 15px;
            margin-bottom: 20px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }

        .summary-item {
            background-color: white;
            border-radius: var(--border-radius);
            padding: 15px;
            text-align: center;
            box-shadow: var(--box-shadow);
        }

        .summary-value {
            display: block;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .summary-label {
            display: block;
            font-size: 14px;
            color: var(--secondary-color);
        }

        .tabs {
            margin-top: 20px;
        }

        .tab-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 15px;
        }

        .tab-button {
            background-color: var(--light-color);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: 8px 15px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.2s;
        }

        .tab-button:hover {
            background-color: #e9ecef;
        }

        .tab-button.active {
            background-color: var(--primary-color);
            color: white;
            border-color: var(--primary-color);
        }

        .tab-content {
            display: none;
            padding: 15px;
            background-color: var(--light-color);
            border-radius: var(--border-radius);
        }

        .tab-content.active {
            display: block;
        }

        .error-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }

        .error-table th, .error-table td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }

        .error-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }

        .error-table tr:hover {
            background-color: #f8f9fa;
        }

        .error-type-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .error-type-item {
            background-color: white;
            border-radius: var(--border-radius);
            padding: 15px;
            box-shadow: var(--box-shadow);
        }

        .error-type-item h3 {
            margin-top: 0;
            font-size: 16px;
        }

        .error-count {
            font-size: 14px;
            color: var(--secondary-color);
        }

        .codebase-summary {
            background-color: white;
            padding: 15px;
            border-radius: var(--border-radius);
            overflow-x: auto;
            font-family: monospace;
            font-size: 14px;
            white-space: pre-wrap;
        }

        .no-errors {
            color: var(--success-color);
            font-style: italic;
        }

        .error {
            color: var(--error-color);
        }

        .warning {
            color: var(--warning-color);
        }

        .info {
            color: var(--info-color);
        }

        .success {
            color: var(--success-color);
        }

        .error-row {
            background-color: rgba(220, 53, 69, 0.1);
        }

        .warning-row {
            background-color: rgba(255, 193, 7, 0.1);
        }

        .info-row {
            background-color: rgba(23, 162, 184, 0.1);
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }

            .summary-grid {
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            }

            .error-type-grid {
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            }

            .tab-button {
                padding: 6px 10px;
                font-size: 12px;
            }

            .error-table {
                font-size: 12px;
            }

            .error-table th, .error-table td {
                padding: 6px 8px;
            }
        }
    """


def _get_javascript() -> str:
    """
    Get JavaScript for the HTML report.
    
    Returns:
        JavaScript as a string
    """
    return """
        function openTab(evt, tabId) {
            // Hide all tab content
            var tabContents = document.getElementsByClassName("tab-content");
            for (var i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove("active");
            }
    
            // Remove active class from all tab buttons
            var tabButtons = document.getElementsByClassName("tab-button");
            for (var i = 0; i < tabButtons.length; i++) {
                tabButtons[i].classList.remove("active");
            }
    
            // Show the selected tab content and mark the button as active
            document.getElementById(tabId).classList.add("active");
            evt.currentTarget.classList.add("active");
        }
    """
