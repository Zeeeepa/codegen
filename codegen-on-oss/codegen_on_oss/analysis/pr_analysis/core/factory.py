"""
Factory Module

This module provides factories for creating core components.
"""

from typing import List, Dict, Any
from .pr_analyzer import PRAnalyzer
from .rule_engine import RuleEngine
from ..rules.base_rule import BaseRule
from ..github.pr_client import GitHubClient
from ..reporting.report_generator import ReportGenerator
from ..reporting.report_generator import MarkdownReportFormatter, HTMLReportFormatter, JSONReportFormatter


def create_rule_engine(rules: List[BaseRule] = None) -> RuleEngine:
    """
    Create a rule engine with the given rules.
    
    Args:
        rules: List of rules to apply
        
    Returns:
        RuleEngine instance
    """
    return RuleEngine(rules)


def create_pr_analyzer(
    github_client: GitHubClient,
    rule_engine: RuleEngine,
    report_generator: ReportGenerator
) -> PRAnalyzer:
    """
    Create a PR analyzer.
    
    Args:
        github_client: Client for interacting with GitHub
        rule_engine: Engine for applying analysis rules
        report_generator: Generator for analysis reports
        
    Returns:
        PRAnalyzer instance
    """
    return PRAnalyzer(github_client, rule_engine, report_generator)


def create_report_formatter(format_type: str):
    """
    Create a report formatter for the given format type.
    
    Args:
        format_type: Type of formatter to create ("markdown", "html", or "json")
        
    Returns:
        Report formatter instance
    """
    if format_type == "markdown":
        return MarkdownReportFormatter()
    elif format_type == "html":
        return HTMLReportFormatter()
    elif format_type == "json":
        return JSONReportFormatter()
    else:
        raise ValueError(f"Unknown format type: {format_type}")


def create_report_generator(format_type: str = "markdown") -> ReportGenerator:
    """
    Create a report generator with the given format type.
    
    Args:
        format_type: Type of formatter to use ("markdown", "html", or "json")
        
    Returns:
        ReportGenerator instance
    """
    formatter = create_report_formatter(format_type)
    return ReportGenerator(formatter)

