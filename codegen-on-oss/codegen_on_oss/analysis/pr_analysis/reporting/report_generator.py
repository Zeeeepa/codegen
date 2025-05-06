"""
Report Generator

Generator for analysis reports.
"""

import logging
from typing import Dict, Any, List

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext
from codegen_on_oss.analysis.pr_analysis.github.comment_formatter import CommentFormatter
from codegen_on_oss.analysis.pr_analysis.reporting.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generator for analysis reports.
    
    This class generates reports from analysis results in various formats.
    """
    
    def __init__(
        self,
        comment_formatter: CommentFormatter = None,
        report_formatter: ReportFormatter = None
    ):
        """
        Initialize the report generator.
        
        Args:
            comment_formatter: The formatter for GitHub comments
            report_formatter: The formatter for general reports
        """
        self.comment_formatter = comment_formatter or CommentFormatter()
        self.report_formatter = report_formatter or ReportFormatter()
    
    def generate_report(
        self,
        context: AnalysisContext,
        results: Dict[str, Any],
        format: str = "markdown"
    ) -> str:
        """
        Generate a report from analysis results.
        
        Args:
            context: The analysis context
            results: The analysis results
            format: The format of the report ("markdown", "html", or "text")
            
        Returns:
            The generated report as a string
        """
        if format == "markdown":
            return self.generate_markdown_report(context, results)
        elif format == "html":
            return self.generate_html_report(context, results)
        elif format == "text":
            return self.generate_text_report(context, results)
        else:
            raise ValueError(f"Unsupported report format: {format}")
    
    def generate_markdown_report(self, context: AnalysisContext, results: Dict[str, Any]) -> str:
        """
        Generate a markdown report from analysis results.
        
        Args:
            context: The analysis context
            results: The analysis results
            
        Returns:
            The generated report as a markdown string
        """
        return self.comment_formatter.format_summary_comment(results)
    
    def generate_html_report(self, context: AnalysisContext, results: Dict[str, Any]) -> str:
        """
        Generate an HTML report from analysis results.
        
        Args:
            context: The analysis context
            results: The analysis results
            
        Returns:
            The generated report as an HTML string
        """
        return self.report_formatter.format_html_report(context, results)
    
    def generate_text_report(self, context: AnalysisContext, results: Dict[str, Any]) -> str:
        """
        Generate a plain text report from analysis results.
        
        Args:
            context: The analysis context
            results: The analysis results
            
        Returns:
            The generated report as a plain text string
        """
        return self.report_formatter.format_text_report(context, results)
    
    def generate_inline_comments(self, results: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate inline comments for issues.
        
        Args:
            results: The analysis results
            
        Returns:
            A dictionary mapping file paths to lists of comment objects
        """
        comments = {}
        
        for rule_id, rule_result in results.items():
            for issue in rule_result.get("issues", []):
                file_path = issue.get("file_path")
                if not file_path:
                    continue
                
                line_number = issue.get("line_number")
                if not line_number:
                    continue
                
                comment_text = self.comment_formatter.format_inline_comment(issue)
                
                if file_path not in comments:
                    comments[file_path] = []
                
                comments[file_path].append({
                    "line": line_number,
                    "body": comment_text
                })
        
        return comments

