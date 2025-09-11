"""
Integration layer for unified SolidLSP, Serena, and Extensions functionality.

This module provides the core integration components that enable the unified
graph-sitter configuration with 5 new parameters:
- lsp_server: SolidLSP integration
- diagnostics: Diagnostic collection across all systems
- error_auto_resolve: Automatic error resolution
- enhanced_context: Enhanced context with autogenlib
- doc_gen: Documentation generation integration
"""

from .config import IntegrationConfig, GraphSitterIntegrationConfig
from .unified_api import from_repo, IntegratedCodebase
from .context_provider import EnhancedContextProvider
from .error_resolver import AutomaticErrorResolver
from .diagnostic_collector import UnifiedDiagnosticCollector
from .doc_generator import IntegratedDocumentationGenerator

__all__ = [
    'IntegrationConfig',
    'GraphSitterIntegrationConfig', 
    'from_repo',
    'IntegratedCodebase',
    'EnhancedContextProvider',
    'AutomaticErrorResolver',
    'UnifiedDiagnosticCollector',
    'IntegratedDocumentationGenerator'
]
