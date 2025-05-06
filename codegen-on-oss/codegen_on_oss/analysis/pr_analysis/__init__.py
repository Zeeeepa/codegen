"""
PR Analysis Package

This package provides functionality for analyzing pull requests.
"""

# Import core components
from .core import (
    PRAnalyzer,
    RuleEngine,
    AnalysisContext,
    DiffContext,
    create_rule_engine,
    create_pr_analyzer,
    create_report_formatter,
    create_report_generator,
)

# Import rules
from .rules import (
    BaseRule,
    AnalysisResult,
    ComplexityRule,
    StyleRule,
    DocstringRule,
)

# Import GitHub components
from .github import (
    PullRequestContext,
    PRPartContext,
    FileChange,
    PRDiff,
    GitHubClient,
)

# Import reporting components
from .reporting import (
    ReportGenerator,
    MarkdownReportFormatter,
    HTMLReportFormatter,
    JSONReportFormatter,
)

# Export all components
__all__ = [
    # Core
    'PRAnalyzer',
    'RuleEngine',
    'AnalysisContext',
    'DiffContext',
    'create_rule_engine',
    'create_pr_analyzer',
    'create_report_formatter',
    'create_report_generator',
    
    # Rules
    'BaseRule',
    'AnalysisResult',
    'ComplexityRule',
    'StyleRule',
    'DocstringRule',
    
    # GitHub
    'PullRequestContext',
    'PRPartContext',
    'FileChange',
    'PRDiff',
    'GitHubClient',
    
    # Reporting
    'ReportGenerator',
    'MarkdownReportFormatter',
    'HTMLReportFormatter',
    'JSONReportFormatter',
]

