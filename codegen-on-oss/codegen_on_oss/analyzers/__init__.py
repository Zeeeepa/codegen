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

# Codebase access modules
from codegen_on_oss.analyzers.current_code_codebase import get_selected_codebase
from codegen_on_oss.analyzers.codegen_sdk_codebase import get_codegen_sdk_codebase, get_codegen_sdk_subdirectories

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
    
    # Codebase access
    'get_selected_codebase',
    'get_codegen_sdk_codebase',
    'get_codegen_sdk_subdirectories',

    # Legacy interfaces (for backward compatibility)
    'BaseCodeAnalyzer',
    'CodebaseAnalyzer',
    'ErrorAnalyzer',
]
