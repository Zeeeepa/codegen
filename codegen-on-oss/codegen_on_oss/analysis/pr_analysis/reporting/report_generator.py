"""
Report generator for PR analysis.

This module provides the ReportGenerator class, which is responsible for
generating analysis reports from rule results.
"""

import logging
from typing import Dict, List, Optional, Any, Union

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.reporting.report_formatter import ReportFormatter
from codegen_on_oss.analysis.pr_analysis.reporting.visualization import (
    create_chart,
    create_graph,
    create_table,
)


logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generator for analysis reports.
    
    This class is responsible for generating analysis reports from rule results,
    including summary information, detailed results, and visualizations.
    
    Attributes:
        context: Analysis context
        formatter: Report formatter
    """
    
    def __init__(self, context: AnalysisContext):
        """
        Initialize the report generator.
        
        Args:
            context: Analysis context
        """
        self.context = context
        self.formatter = ReportFormatter(context)
    
    def generate_report(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate an analysis report from rule results.
        
        Args:
            rule_results: Dictionary of rule results by rule ID
            
        Returns:
            Analysis report
        """
        logger.info(f"Generating report for PR #{self.context.pull_request.number}")
        
        # Generate summary
        summary = self._generate_summary(rule_results)
        
        # Generate detailed results
        details = self._generate_details(rule_results)
        
        # Generate visualizations
        visualizations = self._generate_visualizations(rule_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(rule_results)
        
        # Return report
        return {
            'summary': summary,
            'details': details,
            'visualizations': visualizations,
            'recommendations': recommendations,
            'metadata': {
                'pr_number': self.context.pull_request.number,
                'pr_title': self.context.pull_request.title,
                'repository': self.context.repository.full_name,
                'generated_at': self.context.metadata.get('generated_at'),
            }
        }
    
    def _generate_summary(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of rule results.
        
        Args:
            rule_results: Dictionary of rule results by rule ID
            
        Returns:
            Summary information
        """
        # Count results by status
        status_counts = {'success': 0, 'warning': 0, 'error': 0}
        for rule_id, result in rule_results.items():
            status = result.get('status', 'error')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Determine overall status
        overall_status = 'success'
        if status_counts.get('error', 0) > 0:
            overall_status = 'error'
        elif status_counts.get('warning', 0) > 0:
            overall_status = 'warning'
        
        # Generate summary message
        if overall_status == 'success':
            summary_message = "All checks passed successfully!"
        elif overall_status == 'warning':
            summary_message = f"Found {status_counts.get('warning', 0)} warnings in the pull request."
        else:
            summary_message = f"Found {status_counts.get('error', 0)} errors and {status_counts.get('warning', 0)} warnings in the pull request."
        
        return {
            'status': overall_status,
            'message': summary_message,
            'status_counts': status_counts,
            'total_rules': len(rule_results),
        }
    
    def _generate_details(self, rule_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate detailed results for each rule.
        
        Args:
            rule_results: Dictionary of rule results by rule ID
            
        Returns:
            List of detailed rule results
        """
        details = []
        
        # Sort rules by severity and status
        severity_order = {'high': 0, 'medium': 1, 'low': 2, 'info': 3}
        status_order = {'error': 0, 'warning': 1, 'success': 2}
        
        sorted_results = sorted(
            rule_results.items(),
            key=lambda x: (
                status_order.get(x[1].get('status', 'error'), 3),
                severity_order.get(x[1].get('severity', 'medium'), 4),
                x[0]  # rule_id as tiebreaker
            )
        )
        
        # Generate details for each rule
        for rule_id, result in sorted_results:
            details.append({
                'rule_id': rule_id,
                'name': result.get('name', rule_id),
                'description': result.get('description', ''),
                'severity': result.get('severity', 'medium'),
                'status': result.get('status', 'error'),
                'message': result.get('message', ''),
                'details': result.get('details', {}),
            })
        
        return details
    
    def _generate_visualizations(self, rule_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate visualizations from rule results.
        
        Args:
            rule_results: Dictionary of rule results by rule ID
            
        Returns:
            Visualization data
        """
        # Count results by status
        status_counts = {'success': 0, 'warning': 0, 'error': 0}
        for rule_id, result in rule_results.items():
            status = result.get('status', 'error')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Generate status chart
        status_chart = create_chart(
            'Status Distribution',
            'pie',
            list(status_counts.keys()),
            list(status_counts.values())
        )
        
        # Count results by severity
        severity_counts = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for rule_id, result in rule_results.items():
            severity = result.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate severity chart
        severity_chart = create_chart(
            'Severity Distribution',
            'bar',
            list(severity_counts.keys()),
            list(severity_counts.values())
        )
        
        # Generate issue table
        issues = []
        for rule_id, result in rule_results.items():
            if result.get('status') in ('warning', 'error'):
                details = result.get('details', {})
                if 'issues' in details:
                    for issue in details['issues']:
                        issues.append({
                            'rule': result.get('name', rule_id),
                            'file': issue.get('file', ''),
                            'line': issue.get('line', 0),
                            'message': issue.get('message', ''),
                            'severity': result.get('severity', 'medium'),
                        })
                elif 'vulnerabilities' in details:
                    for vuln in details['vulnerabilities']:
                        issues.append({
                            'rule': result.get('name', rule_id),
                            'file': vuln.get('file', ''),
                            'line': vuln.get('line', 0),
                            'message': vuln.get('message', ''),
                            'severity': vuln.get('severity', result.get('severity', 'medium')),
                        })
                elif 'uncovered_files' in details:
                    for file in details['uncovered_files']:
                        issues.append({
                            'rule': result.get('name', rule_id),
                            'file': file,
                            'line': 0,
                            'message': 'File has no test coverage',
                            'severity': result.get('severity', 'medium'),
                        })
        
        issue_table = create_table(
            'Issues',
            ['Rule', 'File', 'Line', 'Message', 'Severity'],
            [[issue['rule'], issue['file'], issue['line'], issue['message'], issue['severity']] for issue in issues]
        )
        
        return {
            'status_chart': status_chart,
            'severity_chart': severity_chart,
            'issue_table': issue_table,
        }
    
    def _generate_recommendations(self, rule_results: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations from rule results.
        
        Args:
            rule_results: Dictionary of rule results by rule ID
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Generate recommendations based on rule results
        for rule_id, result in rule_results.items():
            if result.get('status') == 'error':
                recommendations.append(f"Fix the {result.get('name', rule_id)} issues: {result.get('message', '')}")
            elif result.get('status') == 'warning':
                recommendations.append(f"Consider addressing the {result.get('name', rule_id)} warnings: {result.get('message', '')}")
        
        return recommendations
    
    def format_report_for_github(self, report: Dict[str, Any]) -> str:
        """
        Format a report for GitHub comment.
        
        Args:
            report: Analysis report
            
        Returns:
            Formatted report as Markdown
        """
        return self.formatter.format_for_github(report)

