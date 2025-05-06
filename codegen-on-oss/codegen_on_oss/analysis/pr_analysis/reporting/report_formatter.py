"""
Report formatter for PR analysis.

This module provides the ReportFormatter class, which is responsible for
formatting analysis reports for different output formats.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext


logger = logging.getLogger(__name__)


class ReportFormatter:
    """
    Formatter for analysis reports.
    
    This class is responsible for formatting analysis reports for different
    output formats, including Markdown, HTML, and JSON.
    
    Attributes:
        context: Analysis context
    """
    
    def __init__(self, context: AnalysisContext):
        """
        Initialize the report formatter.
        
        Args:
            context: Analysis context
        """
        self.context = context
    
    def format_for_github(self, report: Dict[str, Any]) -> str:
        """
        Format a report for GitHub comment.
        
        Args:
            report: Analysis report
            
        Returns:
            Formatted report as Markdown
        """
        logger.info(f"Formatting report for GitHub comment for PR #{self.context.pull_request.number}")
        
        # Get report components
        summary = report.get('summary', {})
        details = report.get('details', [])
        recommendations = report.get('recommendations', [])
        
        # Format summary
        status = summary.get('status', 'error')
        status_emoji = '✅' if status == 'success' else '⚠️' if status == 'warning' else '❌'
        
        markdown = f"# PR Analysis Report {status_emoji}\n\n"
        markdown += f"## Summary\n\n"
        markdown += f"{summary.get('message', 'No summary available.')}\n\n"
        
        # Format status counts
        status_counts = summary.get('status_counts', {})
        markdown += f"- ✅ Success: {status_counts.get('success', 0)}\n"
        markdown += f"- ⚠️ Warning: {status_counts.get('warning', 0)}\n"
        markdown += f"- ❌ Error: {status_counts.get('error', 0)}\n\n"
        
        # Format details
        if details:
            markdown += f"## Details\n\n"
            
            # Group details by status
            error_details = [d for d in details if d.get('status') == 'error']
            warning_details = [d for d in details if d.get('status') == 'warning']
            success_details = [d for d in details if d.get('status') == 'success']
            
            # Format error details
            if error_details:
                markdown += f"### Errors\n\n"
                for detail in error_details:
                    markdown += f"#### {detail.get('name', detail.get('rule_id', 'Unknown'))}\n\n"
                    markdown += f"{detail.get('message', 'No message available.')}\n\n"
                    
                    # Format issues
                    issues = detail.get('details', {}).get('issues', [])
                    if issues:
                        markdown += f"| File | Line | Message |\n"
                        markdown += f"|------|------|--------|\n"
                        for issue in issues[:10]:  # Limit to 10 issues
                            file = issue.get('file', '')
                            line = issue.get('line', 0)
                            message = issue.get('message', '')
                            markdown += f"| {file} | {line} | {message} |\n"
                        
                        if len(issues) > 10:
                            markdown += f"\n*...and {len(issues) - 10} more issues.*\n"
                    
                    # Format vulnerabilities
                    vulnerabilities = detail.get('details', {}).get('vulnerabilities', [])
                    if vulnerabilities:
                        markdown += f"| File | Line | Severity | Message |\n"
                        markdown += f"|------|------|----------|--------|\n"
                        for vuln in vulnerabilities[:10]:  # Limit to 10 vulnerabilities
                            file = vuln.get('file', '')
                            line = vuln.get('line', 0)
                            severity = vuln.get('severity', 'medium')
                            message = vuln.get('message', '')
                            markdown += f"| {file} | {line} | {severity} | {message} |\n"
                        
                        if len(vulnerabilities) > 10:
                            markdown += f"\n*...and {len(vulnerabilities) - 10} more vulnerabilities.*\n"
                    
                    # Format uncovered files
                    uncovered_files = detail.get('details', {}).get('uncovered_files', [])
                    if uncovered_files:
                        markdown += f"**Uncovered Files:**\n\n"
                        for file in uncovered_files[:10]:  # Limit to 10 files
                            markdown += f"- {file}\n"
                        
                        if len(uncovered_files) > 10:
                            markdown += f"\n*...and {len(uncovered_files) - 10} more files.*\n"
                    
                    markdown += "\n"
            
            # Format warning details
            if warning_details:
                markdown += f"### Warnings\n\n"
                for detail in warning_details:
                    markdown += f"#### {detail.get('name', detail.get('rule_id', 'Unknown'))}\n\n"
                    markdown += f"{detail.get('message', 'No message available.')}\n\n"
                    
                    # Format issues
                    issues = detail.get('details', {}).get('issues', [])
                    if issues:
                        markdown += f"| File | Line | Message |\n"
                        markdown += f"|------|------|--------|\n"
                        for issue in issues[:5]:  # Limit to 5 issues
                            file = issue.get('file', '')
                            line = issue.get('line', 0)
                            message = issue.get('message', '')
                            markdown += f"| {file} | {line} | {message} |\n"
                        
                        if len(issues) > 5:
                            markdown += f"\n*...and {len(issues) - 5} more issues.*\n"
                    
                    markdown += "\n"
            
            # Format success details (summarized)
            if success_details:
                markdown += f"### Successful Checks\n\n"
                for detail in success_details:
                    markdown += f"- ✅ {detail.get('name', detail.get('rule_id', 'Unknown'))}: {detail.get('message', 'No message available.')}\n"
                markdown += "\n"
        
        # Format recommendations
        if recommendations:
            markdown += f"## Recommendations\n\n"
            for recommendation in recommendations:
                markdown += f"- {recommendation}\n"
            markdown += "\n"
        
        # Add metadata
        metadata = report.get('metadata', {})
        markdown += f"---\n"
        markdown += f"*PR Analysis Report for [{metadata.get('repository', '')}#{metadata.get('pr_number', '')}]({self.context.pull_request.html_url})*\n"
        
        return markdown
    
    def format_for_html(self, report: Dict[str, Any]) -> str:
        """
        Format a report for HTML.
        
        Args:
            report: Analysis report
            
        Returns:
            Formatted report as HTML
        """
        logger.info(f"Formatting report for HTML for PR #{self.context.pull_request.number}")
        
        # This is a simplified implementation that generates basic HTML
        # In a real implementation, you would use a template engine or more
        # sophisticated HTML generation
        
        # Get report components
        summary = report.get('summary', {})
        details = report.get('details', [])
        visualizations = report.get('visualizations', {})
        recommendations = report.get('recommendations', [])
        
        # Format summary
        status = summary.get('status', 'error')
        status_class = 'success' if status == 'success' else 'warning' if status == 'warning' else 'error'
        status_emoji = '✅' if status == 'success' else '⚠️' if status == 'warning' else '❌'
        
        html = f"<!DOCTYPE html>\n<html>\n<head>\n"
        html += f"<title>PR Analysis Report</title>\n"
        html += f"<style>\n"
        html += f"body {{ font-family: Arial, sans-serif; margin: 20px; }}\n"
        html += f".success {{ color: green; }}\n"
        html += f".warning {{ color: orange; }}\n"
        html += f".error {{ color: red; }}\n"
        html += f"table {{ border-collapse: collapse; width: 100%; }}\n"
        html += f"th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}\n"
        html += f"th {{ background-color: #f2f2f2; }}\n"
        html += f"</style>\n"
        html += f"</head>\n<body>\n"
        
        html += f"<h1>PR Analysis Report {status_emoji}</h1>\n"
        html += f"<h2>Summary</h2>\n"
        html += f"<p class='{status_class}'>{summary.get('message', 'No summary available.')}</p>\n"
        
        # Format status counts
        status_counts = summary.get('status_counts', {})
        html += f"<ul>\n"
        html += f"<li class='success'>Success: {status_counts.get('success', 0)}</li>\n"
        html += f"<li class='warning'>Warning: {status_counts.get('warning', 0)}</li>\n"
        html += f"<li class='error'>Error: {status_counts.get('error', 0)}</li>\n"
        html += f"</ul>\n"
        
        # Format details
        if details:
            html += f"<h2>Details</h2>\n"
            
            # Group details by status
            error_details = [d for d in details if d.get('status') == 'error']
            warning_details = [d for d in details if d.get('status') == 'warning']
            success_details = [d for d in details if d.get('status') == 'success']
            
            # Format error details
            if error_details:
                html += f"<h3 class='error'>Errors</h3>\n"
                for detail in error_details:
                    html += f"<h4>{detail.get('name', detail.get('rule_id', 'Unknown'))}</h4>\n"
                    html += f"<p>{detail.get('message', 'No message available.')}</p>\n"
                    
                    # Format issues
                    issues = detail.get('details', {}).get('issues', [])
                    if issues:
                        html += f"<table>\n"
                        html += f"<tr><th>File</th><th>Line</th><th>Message</th></tr>\n"
                        for issue in issues[:10]:  # Limit to 10 issues
                            file = issue.get('file', '')
                            line = issue.get('line', 0)
                            message = issue.get('message', '')
                            html += f"<tr><td>{file}</td><td>{line}</td><td>{message}</td></tr>\n"
                        html += f"</table>\n"
                        
                        if len(issues) > 10:
                            html += f"<p><em>...and {len(issues) - 10} more issues.</em></p>\n"
            
            # Format warning details
            if warning_details:
                html += f"<h3 class='warning'>Warnings</h3>\n"
                for detail in warning_details:
                    html += f"<h4>{detail.get('name', detail.get('rule_id', 'Unknown'))}</h4>\n"
                    html += f"<p>{detail.get('message', 'No message available.')}</p>\n"
                    
                    # Format issues
                    issues = detail.get('details', {}).get('issues', [])
                    if issues:
                        html += f"<table>\n"
                        html += f"<tr><th>File</th><th>Line</th><th>Message</th></tr>\n"
                        for issue in issues[:5]:  # Limit to 5 issues
                            file = issue.get('file', '')
                            line = issue.get('line', 0)
                            message = issue.get('message', '')
                            html += f"<tr><td>{file}</td><td>{line}</td><td>{message}</td></tr>\n"
                        html += f"</table>\n"
                        
                        if len(issues) > 5:
                            html += f"<p><em>...and {len(issues) - 5} more issues.</em></p>\n"
            
            # Format success details (summarized)
            if success_details:
                html += f"<h3 class='success'>Successful Checks</h3>\n"
                html += f"<ul>\n"
                for detail in success_details:
                    html += f"<li>{detail.get('name', detail.get('rule_id', 'Unknown'))}: {detail.get('message', 'No message available.')}</li>\n"
                html += f"</ul>\n"
        
        # Format recommendations
        if recommendations:
            html += f"<h2>Recommendations</h2>\n"
            html += f"<ul>\n"
            for recommendation in recommendations:
                html += f"<li>{recommendation}</li>\n"
            html += f"</ul>\n"
        
        # Add metadata
        metadata = report.get('metadata', {})
        html += f"<hr>\n"
        html += f"<p><em>PR Analysis Report for <a href='{self.context.pull_request.html_url}'>{metadata.get('repository', '')}#{metadata.get('pr_number', '')}</a></em></p>\n"
        
        html += f"</body>\n</html>"
        
        return html
    
    def format_for_json(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a report for JSON.
        
        Args:
            report: Analysis report
            
        Returns:
            Formatted report as JSON-serializable dictionary
        """
        logger.info(f"Formatting report for JSON for PR #{self.context.pull_request.number}")
        
        # For JSON, we just return the report as is, since it's already a dictionary
        return report

