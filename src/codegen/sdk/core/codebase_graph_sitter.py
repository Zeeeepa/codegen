"""Graph-sitter extensions for the Codebase class."""

from functools import cached_property

from ..api.codebase_extensions import CodebaseExtensions
from ..config.graph_sitter_config import DEFAULT_CONFIG


def add_graph_sitter_extensions(codebase_class):
    """Add graph-sitter extensions to the Codebase class.

    This function adds the following properties to the Codebase class:
    - codebase.graph_sitter: Access to all graph-sitter functionality
    - codebase.diagnostics: Direct access to diagnostics system
    - codebase.enhanced_context: Direct access to enhanced context
    - codebase.docs: Direct access to documentation generation
    - codebase.auto_resolve: Direct access to auto-resolution
    """

    @cached_property
    def graph_sitter(self) -> CodebaseExtensions:
        """Access to graph-sitter SDK extensions.

        This provides access to all integrated functionality:
        - Unified diagnostics from SolidLSP + Serena + graph-sitter
        - Enhanced context retrieval combining all components
        - Auto-resolution using intelligent error analysis
        - Documentation generation using all 15 tools

        Usage:
            # Access all features through the main interface
            extensions = codebase.graph_sitter

            # Or access individual systems directly
            diagnostics = codebase.diagnostics
            context = codebase.enhanced_context
            docs = codebase.docs
            resolver = codebase.auto_resolve
        """
        return CodebaseExtensions(self, DEFAULT_CONFIG)

    @cached_property
    def diagnostics(self):
        """Direct access to unified diagnostics system.

        Usage:
            diagnostics = codebase.diagnostics
            all_issues = await diagnostics.collect_all_diagnostics()
            errors = diagnostics.get_diagnostics_by_severity(all_issues, DiagnosticSeverity.ERROR)
        """
        return self.graph_sitter.diagnostics

    @cached_property
    def enhanced_context(self):
        """Direct access to enhanced context retrieval system.

        Usage:
            context = codebase.enhanced_context
            symbol_context = context.get_extended_context(symbol, degree=3)
            error_context = context.get_error_context(error_info)
        """
        return self.graph_sitter.enhanced_context

    @cached_property
    def docs(self):
        """Direct access to documentation generation system.

        Usage:
            docs = codebase.docs
            full_docs = docs.generate_full_documentation()
            api_docs = docs.generate_api_documentation()
        """
        return self.graph_sitter.docs

    @cached_property
    def auto_resolve(self):
        """Direct access to auto-resolution system.

        Usage:
            resolver = codebase.auto_resolve
            fixed_code = resolver.resolve_error(error_info)
            suggestions = resolver.get_fix_suggestions(diagnostics)
        """
        return self.graph_sitter.auto_resolve

    # Add properties to the class
    codebase_class.graph_sitter = graph_sitter
    codebase_class.diagnostics = diagnostics
    codebase_class.enhanced_context = enhanced_context
    codebase_class.docs = docs
    codebase_class.auto_resolve = auto_resolve

    return codebase_class


# Apply extensions to Codebase class when this module is imported
def _apply_extensions():
    """Apply extensions to the Codebase class."""
    try:
        from .codebase import Codebase
        add_graph_sitter_extensions(Codebase)
    except ImportError:
        # Codebase class not available, skip extensions
        pass


# Auto-apply extensions when module is imported
_apply_extensions()
