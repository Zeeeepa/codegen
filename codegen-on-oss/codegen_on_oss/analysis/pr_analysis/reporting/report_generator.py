"""
Report Generator Module

This module provides functionality for generating analysis reports.
"""

import logging
from typing import Dict, List, Any

from ..github.models import PullRequestContext
from ..rules.base_rule import AnalysisResult

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generator for analysis reports."""
    
    def __init__(self, formatter=None):
        """
        Initialize a new report generator.
        
        Args:
            formatter: Optional formatter for the report
        """
        self.formatter = formatter
    
    def generate_report(self, results: List[AnalysisResult], pr_data: PullRequestContext) -> Dict[str, Any]:
        """
        Generate a report from analysis results.
        
        Args:
            results: Analysis results
            pr_data: Pull request data
            
        Returns:
            Report as a dictionary
        """
        # Group results by severity
        errors = [r for r in results if r.severity == "error"]
        warnings = [r for r in results if r.severity == "warning"]
        info = [r for r in results if r.severity == "info"]
        
        # Group results by rule
        results_by_rule = {}
        for result in results:
            if result.rule_id not in results_by_rule:
                results_by_rule[result.rule_id] = []
            results_by_rule[result.rule_id].append(result)
        
        # Group results by file
        results_by_file = {}
        for result in results:
            if result.file_path:
                if result.file_path not in results_by_file:
                    results_by_file[result.file_path] = []
                results_by_file[result.file_path].append(result)
        
        # Create report
        report = {
            "pr": {
                "number": pr_data.number,
                "title": pr_data.title,
                "body": pr_data.body,
                "state": pr_data.state,
                "html_url": pr_data.html_url,
                "user": pr_data.user,
            },
            "summary": {
                "total_results": len(results),
                "error_count": len(errors),
                "warning_count": len(warnings),
                "info_count": len(info),
                "rule_count": len(results_by_rule),
                "file_count": len(results_by_file),
            },
            "results": {
                "errors": errors,
                "warnings": warnings,
                "info": info,
                "by_rule": results_by_rule,
                "by_file": results_by_file,
            },
            "timestamp": self._get_timestamp(),
        }
        
        return report
    
    def format_report_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format a report as markdown.
        
        Args:
            report: Report to format
            
        Returns:
            Markdown string
        """
        # Use custom formatter if provided
        if self.formatter:
            return self.formatter.format_as_markdown(report)
        
        # Default markdown formatting
        pr = report["pr"]
        summary = report["summary"]
        results = report["results"]
        
        markdown = f"""# PR Analysis Report

## Summary

- **PR**: [{pr['number']}]({pr['html_url']}) - {pr['title']}
- **Total Results**: {summary['total_results']}
- **Errors**: {summary['error_count']}
- **Warnings**: {summary['warning_count']}
- **Info**: {summary['info_count']}
- **Rules Applied**: {summary['rule_count']}
- **Files Analyzed**: {summary['file_count']}

"""
        
        # Add errors section if there are any
        if results["errors"]:
            markdown += "## Errors\n\n"
            for error in results["errors"]:
                location = f"{error.file_path}:{error.line_number}" if error.file_path and error.line_number else "N/A"
                markdown += f"- **{error.rule_id}**: {error.message} ({location})\n"
            markdown += "\n"
        
        # Add warnings section if there are any
        if results["warnings"]:
            markdown += "## Warnings\n\n"
            for warning in results["warnings"]:
                location = f"{warning.file_path}:{warning.line_number}" if warning.file_path and warning.line_number else "N/A"
                markdown += f"- **{warning.rule_id}**: {warning.message} ({location})\n"
            markdown += "\n"
        
        # Add results by file section
        if results["by_file"]:
            markdown += "## Results by File\n\n"
            for file_path, file_results in results["by_file"].items():
                markdown += f"### {file_path}\n\n"
                for result in file_results:
                    line = f":{result.line_number}" if result.line_number else ""
                    markdown += f"- **{result.severity.upper()}**: {result.message} (line{line})\n"
                markdown += "\n"
        
        return markdown
    
    def format_report_as_html(self, report: Dict[str, Any]) -> str:
        """
        Format a report as HTML.
        
        Args:
            report: Report to format
            
        Returns:
            HTML string
        """
        # Use custom formatter if provided
        if self.formatter:
            return self.formatter.format_as_html(report)
        
        # Default HTML formatting
        pr = report["pr"]
        summary = report["summary"]
        results = report["results"]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PR Analysis Report - #{pr['number']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
        .error {{ color: #d9534f; }}
        .warning {{ color: #f0ad4e; }}
        .info {{ color: #5bc0de; }}
        .file {{ margin-top: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }}
        .file h3 {{ margin-top: 0; }}
    </style>
</head>
<body>
    <h1>PR Analysis Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>PR</strong>: <a href="{pr['html_url']}">#{pr['number']}</a> - {pr['title']}</p>
        <p><strong>Total Results</strong>: {summary['total_results']}</p>
        <p><strong>Errors</strong>: {summary['error_count']}</p>
        <p><strong>Warnings</strong>: {summary['warning_count']}</p>
        <p><strong>Info</strong>: {summary['info_count']}</p>
        <p><strong>Rules Applied</strong>: {summary['rule_count']}</p>
        <p><strong>Files Analyzed</strong>: {summary['file_count']}</p>
    </div>
"""
        
        # Add errors section if there are any
        if results["errors"]:
            html += """
    <h2>Errors</h2>
    <ul>
"""
            for error in results["errors"]:
                location = f"{error.file_path}:{error.line_number}" if error.file_path and error.line_number else "N/A"
                html += f"""        <li class="error"><strong>{error.rule_id}</strong>: {error.message} ({location})</li>
"""
            html += """    </ul>
"""
        
        # Add warnings section if there are any
        if results["warnings"]:
            html += """
    <h2>Warnings</h2>
    <ul>
"""
            for warning in results["warnings"]:
                location = f"{warning.file_path}:{warning.line_number}" if warning.file_path and warning.line_number else "N/A"
                html += f"""        <li class="warning"><strong>{warning.rule_id}</strong>: {warning.message} ({location})</li>
"""
            html += """    </ul>
"""
        
        # Add results by file section
        if results["by_file"]:
            html += """
    <h2>Results by File</h2>
"""
            for file_path, file_results in results["by_file"].items():
                html += f"""
    <div class="file">
        <h3>{file_path}</h3>
        <ul>
"""
                for result in file_results:
                    line = f":{result.line_number}" if result.line_number else ""
                    html += f"""            <li class="{result.severity}"><strong>{result.severity.upper()}</strong>: {result.message} (line{line})</li>
"""
                html += """        </ul>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html
    
    def _get_timestamp(self) -> str:
        """
        Get the current timestamp.
        
        Returns:
            Current timestamp as a string
        """
        from datetime import datetime
        return datetime.now().isoformat()


class MarkdownReportFormatter:
    """Formatter for markdown reports."""
    
    def format_as_markdown(self, report: Dict[str, Any]) -> str:
        """
        Format a report as markdown.
        
        Args:
            report: Report to format
            
        Returns:
            Markdown string
        """
        # Implementation similar to ReportGenerator.format_report_as_markdown
        pass


class HTMLReportFormatter:
    """Formatter for HTML reports."""
    
    def format_as_html(self, report: Dict[str, Any]) -> str:
        """
        Format a report as HTML.
        
        Args:
            report: Report to format
            
        Returns:
            HTML string
        """
        # Implementation similar to ReportGenerator.format_report_as_html
        pass


class JSONReportFormatter:
    """Formatter for JSON reports."""
    
    def format_as_json(self, report: Dict[str, Any]) -> str:
        """
        Format a report as JSON.
        
        Args:
            report: Report to format
            
        Returns:
            JSON string
        """
        import json
        return json.dumps(report, default=lambda o: o.__dict__, indent=2)

