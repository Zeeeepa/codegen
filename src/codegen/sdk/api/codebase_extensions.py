"""Extensions for the Codebase class to provide integrated functionality."""

import logging
from typing import Any

from ..config.graph_sitter_config import DEFAULT_CONFIG, GraphSitterConfig
from ..context.enhanced_context import EnhancedContext
from ..diagnostics.diagnostic_types import Diagnostic
from ..diagnostics.unified_diagnostics import UnifiedDiagnostics

logger = logging.getLogger(__name__)


class CodebaseExtensions:
    """Extensions for the Codebase class providing integrated functionality.

    This class provides the user-facing API for accessing configured features:
    - codebase.diagnostics
    - codebase.docs
    - codebase.auto_resolve
    - codebase.enhanced_context
    """

    def __init__(self, codebase, config: GraphSitterConfig | None = None):
        """Initialize codebase extensions.

        Args:
            codebase: The codebase instance to extend
            config: Configuration for graph-sitter extensions
        """
        self.codebase = codebase
        self.config = config or DEFAULT_CONFIG

        # Lazy-loaded components
        self._diagnostics_system: UnifiedDiagnostics | None = None
        self._context_system: EnhancedContext | None = None
        self._doc_generator = None
        self._auto_resolver = None

        # Validate configuration
        if not self.config.is_valid():
            errors = self.config.validate()
            logger.warning(f"Configuration validation errors: {errors}")

    @property
    def diagnostics(self) -> UnifiedDiagnostics:
        """Access to unified diagnostics system.

        Usage:
            diagnostics = codebase.diagnostics
            all_issues = await diagnostics.collect_all_diagnostics()
            errors = diagnostics.get_diagnostics_by_severity(all_issues, DiagnosticSeverity.ERROR)
        """
        if not self.config.diagnostics:
            msg = "Diagnostics not enabled in configuration"
            raise RuntimeError(msg)

        if self._diagnostics_system is None:
            self._diagnostics_system = UnifiedDiagnostics(self.config)

        return self._diagnostics_system

    @property
    def enhanced_context(self) -> EnhancedContext:
        """Access to enhanced context retrieval system.

        Usage:
            context = codebase.enhanced_context
            symbol_context = context.get_extended_context(symbol, degree=3)
            error_context = context.get_error_context(error_info)
        """
        if not self.config.enhanced_context:
            msg = "Enhanced context not enabled in configuration"
            raise RuntimeError(msg)

        if self._context_system is None:
            self._context_system = EnhancedContext(self.config)

        return self._context_system

    @property
    def docs(self):
        """Access to documentation generation system.

        Usage:
            docs = codebase.docs
            full_docs = docs.generate_full_documentation()
            api_docs = docs.generate_api_documentation()
        """
        if not self.config.doc_gen:
            msg = "Documentation generation not enabled in configuration"
            raise RuntimeError(msg)

        if self._doc_generator is None:
            self._doc_generator = self._create_doc_generator()

        return self._doc_generator

    @property
    def auto_resolve(self):
        """Access to auto-resolution system.

        Usage:
            resolver = codebase.auto_resolve
            fixed_code = resolver.resolve_error(error_info)
            suggestions = resolver.get_fix_suggestions(diagnostics)
        """
        if not self.config.error_auto_resolve:
            msg = "Auto-resolution not enabled in configuration"
            raise RuntimeError(msg)

        if self._auto_resolver is None:
            self._auto_resolver = self._create_auto_resolver()

        return self._auto_resolver

    def _create_doc_generator(self):
        """Create documentation generator integrating all 15 tools."""
        try:
            # This would integrate all tools from the tools directory (placeholder imports)
            # from ..extensions.tools.generate_docs_json import generate_docs_json
            # from ..extensions.tools.mdx_docs_generation import generate_mdx_docs
            # from ..extensions.tools.reveal_symbol import reveal_symbol

            class DocumentationGenerator:
                """Integrated documentation generator using all tools."""

                def __init__(self, codebase, config):
                    self.codebase = codebase
                    self.config = config

                def generate_full_documentation(self) -> dict[str, Any]:
                    """Generate comprehensive documentation for the entire codebase."""
                    # This would orchestrate all 15 tools
                    return {
                        "status": "placeholder",
                        "message": "Full documentation generation not yet implemented",
                        "tools_available": [
                            "reveal_symbol", "generate_docs_json", "current_code_codebase",
                            "list_directory", "view_file", "mdx_docs_generation",
                            "bash", "reflection", "document_functions"
                        ]
                    }

                def generate_api_documentation(self) -> dict[str, Any]:
                    """Generate API documentation."""
                    return {
                        "status": "placeholder",
                        "message": "API documentation generation not yet implemented"
                    }

            return DocumentationGenerator(self.codebase, self.config)

        except ImportError as e:
            logger.exception(f"Could not import documentation tools: {e}")
            return None

    def _create_auto_resolver(self):
        """Create auto-resolution system."""
        try:
            from ..extensions.autogenlib._exception_handler import generate_fix_for_analysis_error

            class AutoResolver:
                """Intelligent error auto-resolution system."""

                def __init__(self, codebase, config, context_system):
                    self.codebase = codebase
                    self.config = config
                    self.context_system = context_system

                def resolve_error(self, error_info: dict[str, Any]) -> dict[str, Any]:
                    """Resolve an error using enhanced context."""
                    # Get enhanced context for the error
                    context = self.context_system.get_error_context(error_info)

                    # Generate fix using AutogenLib
                    fix_result = generate_fix_for_analysis_error(
                        error_info,
                        context.primary_content
                    )

                    return {
                        "original_error": error_info,
                        "context": context,
                        "fix_result": fix_result,
                        "status": "placeholder - not yet fully implemented"
                    }

                def get_fix_suggestions(self, diagnostics: list[Diagnostic]) -> list[dict[str, Any]]:
                    """Get fix suggestions for a list of diagnostics."""
                    suggestions = []

                    for diagnostic in diagnostics:
                        if diagnostic.is_fixable():
                            suggestions.append({
                                "diagnostic": diagnostic,
                                "suggestion": diagnostic.fix_suggestion,
                                "confidence": "placeholder"
                            })

                    return suggestions

            return AutoResolver(self.codebase, self.config, self.enhanced_context)

        except ImportError as e:
            logger.exception(f"Could not import auto-resolution components: {e}")
            return None

    def get_configuration(self) -> GraphSitterConfig:
        """Get current configuration."""
        return self.config

    def update_configuration(self, **kwargs) -> None:
        """Update configuration parameters.

        Args:
            **kwargs: Configuration parameters to update
        """
        # Create new configuration with updated values
        config_dict = {
            "lsp_server": kwargs.get("lsp_server", self.config.lsp_server),
            "diagnostics": kwargs.get("diagnostics", self.config.diagnostics),
            "error_auto_resolve": kwargs.get("error_auto_resolve", self.config.error_auto_resolve),
            "enhanced_context": kwargs.get("enhanced_context", self.config.enhanced_context),
            "doc_gen": kwargs.get("doc_gen", self.config.doc_gen),
            "max_context_tokens": kwargs.get("max_context_tokens", self.config.max_context_tokens),
            "context_degree": kwargs.get("context_degree", self.config.context_degree),
            "cache_enabled": kwargs.get("cache_enabled", self.config.cache_enabled),
            "debug_mode": kwargs.get("debug_mode", self.config.debug_mode),
        }

        self.config = GraphSitterConfig(**config_dict)

        # Reset lazy-loaded components to pick up new configuration
        self._diagnostics_system = None
        self._context_system = None
        self._doc_generator = None
        self._auto_resolver = None

        # Validate new configuration
        if not self.config.is_valid():
            errors = self.config.validate()
            logger.warning(f"Updated configuration validation errors: {errors}")

    def get_feature_status(self) -> dict[str, bool]:
        """Get status of all features."""
        return {
            "lsp_server": self.config.lsp_server,
            "diagnostics": self.config.diagnostics,
            "error_auto_resolve": self.config.error_auto_resolve,
            "enhanced_context": self.config.enhanced_context,
            "doc_gen": self.config.doc_gen,
        }

    def get_system_info(self) -> dict[str, Any]:
        """Get system information and status."""
        return {
            "config": self.config,
            "enabled_features": self.config.get_enabled_features(),
            "validation_errors": self.config.validate(),
            "directories": {
                "sdk_root": str(self.config.sdk_root),
                "extensions_root": str(self.config.extensions_root),
                "solidlsp_root": str(self.config.solidlsp_root),
                "serena_root": str(self.config.serena_root),
                "autogenlib_root": str(self.config.autogenlib_root),
                "tools_root": str(self.config.tools_root),
            },
            "components_loaded": {
                "diagnostics": self._diagnostics_system is not None,
                "context": self._context_system is not None,
                "docs": self._doc_generator is not None,
                "auto_resolve": self._auto_resolver is not None,
            }
        }
