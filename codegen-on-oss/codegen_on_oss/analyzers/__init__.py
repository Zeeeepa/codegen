"""
Codebase Analysis Module

This package provides comprehensive codebase analysis tools for static code analysis,
quality checking, dependency analysis, and PR validation. It's designed to be used
as an API backend for frontend applications.
"""

# Modern analyzer architecture
from codegen_on_oss.analyzers.analyzer import (
    AnalyzerManager,
    AnalyzerPlugin,
    AnalyzerRegistry,
    CodeQualityPlugin,
    DependencyPlugin,
)
# Main API interface
from codegen_on_oss.analyzers.api import (
    CodegenAnalyzerAPI,
    api_analyze_codebase,
    api_analyze_pr,
    api_get_static_errors,
    api_get_visualization,
    create_api,
)

# Legacy analyzer interfaces (for backward compatibility)
from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer

# Core analysis modules
from codegen_on_oss.analyzers.code_quality import CodeQualityAnalyzer
from codegen_on_oss.analyzers.codebase_analysis import (
    get_class_summary,
    get_codebase_summary,
    get_dependency_graph,
    get_file_complexity_metrics,
    get_file_summary,
    get_function_summary,
    get_symbol_references,
    get_symbol_summary,
)
from codegen_on_oss.analyzers.codebase_analyzer import CodebaseAnalyzer
from codegen_on_oss.analyzers.dependencies import DependencyAnalyzer
# Diff tracking
from codegen_on_oss.analyzers.diff_lite import ChangeType, DiffLite
from codegen_on_oss.analyzers.error_analyzer import CodebaseAnalyzer as ErrorAnalyzer

# Issue tracking system
from codegen_on_oss.analyzers.issues import (
    AnalysisType,
    CodeLocation,
    Issue,
    IssueCategory,
    IssueCollection,
    IssueSeverity,
)
# Analysis result models
from codegen_on_oss.analyzers.models.analysis_result import (
    AnalysisResult,
    CodeQualityResult,
    DependencyResult,
    PrAnalysisResult,
)
# Parser module
from codegen_on_oss.analyzers.parser import (
    ASTNode,
    BaseParser,
    CodegenParser,
    JavaScriptParser,
    PythonParser,
    TypeScriptParser,
    create_parser,
    parse_code,
    parse_file,
)

__all__ = [
    # Main API
    "CodegenAnalyzerAPI",
    "create_api",
    "api_analyze_codebase",
    "api_analyze_pr",
    "api_get_visualization",
    "api_get_static_errors",
    # Modern architecture
    "AnalyzerManager",
    "AnalyzerPlugin",
    "AnalyzerRegistry",
    "CodeQualityPlugin",
    "DependencyPlugin",
    # Issue tracking
    "Issue",
    "IssueCollection",
    "IssueSeverity",
    "AnalysisType",
    "IssueCategory",
    "CodeLocation",
    # Analysis results
    "AnalysisResult",
    "CodeQualityResult",
    "DependencyResult",
    "PrAnalysisResult",
    # Core analyzers
    "CodeQualityAnalyzer",
    "DependencyAnalyzer",
    # Codebase analysis utilities
    "get_codebase_summary",
    "get_file_summary",
    "get_class_summary",
    "get_function_summary",
    "get_symbol_summary",
    "get_dependency_graph",
    "get_symbol_references",
    "get_file_complexity_metrics",
    # Diff tracking
    "ChangeType",
    "DiffLite",
    # Legacy interfaces (for backward compatibility)
    "BaseCodeAnalyzer",
    "CodebaseAnalyzer",
    "ErrorAnalyzer",
    # Parser module
    "ASTNode",
    "BaseParser",
    "CodegenParser",
    "JavaScriptParser",
    "PythonParser",
    "TypeScriptParser",
    "create_parser",
    "parse_code",
    "parse_file",
]
