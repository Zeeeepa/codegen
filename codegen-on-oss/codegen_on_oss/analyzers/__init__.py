"""
Codebase Analysis Module

This package provides comprehensive codebase analysis tools for static code analysis,
quality checking, dependency analysis, and PR validation. It's designed to be used
as an API backend for frontend applications.
"""

# Main API interface
from codegen_on_oss.analyzers.api import (
    CodegenAnalyzerAPI,
    create_api,
    api_analyze_codebase,
    api_analyze_pr,
    api_get_visualization,
    api_get_static_errors
)

# Modern analyzer architecture
from codegen_on_oss.analyzers.analyzer import (
    AnalyzerManager,
    AnalyzerPlugin,
    AnalyzerRegistry,
    CodeQualityPlugin,
    DependencyPlugin
)

# Issue tracking system
from codegen_on_oss.analyzers.issues import (
    Issue,
    IssueCollection,
    IssueSeverity,
    AnalysisType,
    IssueCategory,
    CodeLocation
)

# Analysis result models
from codegen_on_oss.analyzers.models.analysis_result import (
    AnalysisResult,
    CodeQualityResult,
    DependencyResult,
    PrAnalysisResult
)

# Core analysis modules
from codegen_on_oss.analyzers.code_quality import CodeQualityAnalyzer
from codegen_on_oss.analyzers.dependencies import DependencyAnalyzer
from codegen_on_oss.analyzers.codebase_ai import (
    CodebaseAI,
    generate_system_prompt,
    generate_flag_system_prompt,
    generate_context,
    generate_tools,
    generate_flag_tools
)

# Legacy analyzer interfaces (for backward compatibility)
from codegen_on_oss.analyzers.base_analyzer import BaseCodeAnalyzer
from codegen_on_oss.analyzers.codebase_analyzer import CodebaseAnalyzer
from codegen_on_oss.analyzers.error_analyzer import CodebaseAnalyzer as ErrorAnalyzer

__all__ = [
    # Main API
    'CodegenAnalyzerAPI',
    'create_api',
    'api_analyze_codebase',
    'api_analyze_pr',
    'api_get_visualization',
    'api_get_static_errors',

    # Modern architecture
    'AnalyzerManager',
    'AnalyzerPlugin',
    'AnalyzerRegistry',
    'CodeQualityPlugin',
    'DependencyPlugin',

    # Issue tracking
    'Issue',
    'IssueCollection',
    'IssueSeverity',
    'AnalysisType',
    'IssueCategory',
    'CodeLocation',

    # Analysis results
    'AnalysisResult',
    'CodeQualityResult',
    'DependencyResult',
    'PrAnalysisResult',

    # Core analyzers
    'CodeQualityAnalyzer',
    'DependencyAnalyzer',
    'CodebaseAI',
    'generate_system_prompt',
    'generate_flag_system_prompt',
    'generate_context',
    'generate_tools',
    'generate_flag_tools',

    # Legacy interfaces (for backward compatibility)
    'BaseCodeAnalyzer',
    'CodebaseAnalyzer',
    'ErrorAnalyzer',
]
