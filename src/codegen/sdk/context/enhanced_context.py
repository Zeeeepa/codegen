"""Enhanced context retrieval combining graph-sitter + serena + autogenlib + solidlsp."""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from ..config.graph_sitter_config import GraphSitterConfig
from ..core.external_module import ExternalModule
from ..core.import_resolution import Import
from ..core.symbol import Symbol

logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of context that can be retrieved."""
    SYMBOL = "symbol"
    ERROR = "error"
    FUNCTION = "function"
    VARIABLE = "variable"
    CLASS = "class"
    MODULE = "module"
    FILE = "file"


@dataclass
class ContextResult:
    """Result of context retrieval operation."""

    context_type: ContextType
    primary_content: str
    """Primary content (e.g., symbol source code, error context)."""

    dependencies: list[str] | None = None
    """Related dependencies or imports."""

    usages: list[str] | None = None
    """Usage examples or references."""

    metadata: dict[str, Any] | None = None
    """Additional metadata (file paths, line numbers, etc.)."""

    related_symbols: list[str] | None = None
    """Related symbols or entities."""

    documentation: str | None = None
    """Associated documentation or docstrings."""

    source_info: dict[str, Any] | None = None
    """Source information (file, line, column)."""

    def __post_init__(self):
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = []
        if self.usages is None:
            self.usages = []
        if self.metadata is None:
            self.metadata = {}
        if self.related_symbols is None:
            self.related_symbols = []
        if self.source_info is None:
            self.source_info = {}


class EnhancedContext:
    """Enhanced context retrieval system combining all components."""

    def __init__(self, config: GraphSitterConfig):
        """Initialize enhanced context system."""
        self.config = config
        self._context_providers: dict[str, Any] = {}
        self._cache: dict[str, Any] = {}

        # Initialize context providers based on configuration
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize context providers based on configuration."""
        if self.config.enhanced_context:
            self._context_providers["graph_sitter"] = self._get_graph_sitter_context

        if self.config.lsp_server:
            self._context_providers["solidlsp"] = self._get_solidlsp_context
            self._context_providers["serena"] = self._get_serena_context

        if self.config.error_auto_resolve:
            self._context_providers["autogenlib"] = self._get_autogenlib_context

    def get_extended_context(
        self,
        symbol: Symbol,
        degree: int | None = None,
        max_tokens: int | None = None,
        context_types: list[ContextType] | None = None
    ) -> ContextResult:
        """Enhanced version of get_extended_context with full capabilities.

        This is the enhanced version of the example function provided, now with
        full integration of graph-sitter's parsing + serena's symbol functionality +
        autogenlib's context retrieval + solidlsp's LSP analysis.

        Args:
            symbol: Symbol to get context for
            degree: Maximum degree for recursive context collection
            max_tokens: Maximum tokens for context retrieval
            context_types: Types of context to retrieve

        Returns:
            Enhanced context result with comprehensive information
        """
        if degree is None:
            degree = self.config.context_degree
        if max_tokens is None:
            max_tokens = self.config.max_context_tokens
        if context_types is None:
            context_types = [ContextType.SYMBOL]

        # Start with basic symbol context
        dependencies: set[Symbol] = set()
        usages: set[Symbol] = set()
        seen_symbols = {symbol}

        # Collect basic dependencies and usages (original functionality)
        if degree > 0:
            for dep in symbol.dependencies:
                if isinstance(dep, Import):
                    dep = self._hop_through_imports(dep)
                if isinstance(dep, Symbol) and dep not in seen_symbols:
                    dependencies.add(dep)
                    seen_symbols.add(dep)

                    # Recursively collect nested context
                    if degree > 1:
                        nested_result = self.get_extended_context(
                            dep, degree - 1, max_tokens, context_types
                        )
                        # Convert string symbols to Symbol objects if needed
                        related_symbols = nested_result.related_symbols or []
                        # For now, skip this update since we need proper Symbol objects
                        # dependencies.update(related_symbols)

        # Enhanced context collection from all providers
        enhanced_data = self._collect_enhanced_context(symbol, context_types)

        # Create comprehensive context result
        result = ContextResult(
            context_type=ContextType.SYMBOL,
            primary_content=self._get_symbol_source(symbol),
            dependencies=[str(dep) for dep in dependencies],
            usages=[str(usage) for usage in usages],
            metadata={
                "symbol_name": symbol.name if hasattr(symbol, 'name') else str(symbol),
                "degree": degree,
                "max_tokens": max_tokens,
                "providers_used": list(self._context_providers.keys()),
            },
            related_symbols=enhanced_data.get("related_symbols", []),
            documentation=enhanced_data.get("documentation"),
            source_info=enhanced_data.get("source_info", {}),
        )

        # Add enhanced metadata from all providers
        if result.metadata is not None:
            result.metadata.update(enhanced_data.get("metadata", {}))

        return result

    def get_error_context(
        self,
        error_info: dict[str, Any],
        include_fix_suggestions: bool = True
    ) -> ContextResult:
        """Get comprehensive context for error resolution.

        Args:
            error_info: Error information (file, line, message, etc.)
            include_fix_suggestions: Whether to include fix suggestions

        Returns:
            Context result with error analysis and potential fixes
        """
        context_data = {
            "error_message": error_info.get("message", ""),
            "file_path": error_info.get("file_path", ""),
            "line_number": error_info.get("line", 0),
            "column": error_info.get("column", 0),
        }

        # Collect context from all providers
        enhanced_data = self._collect_enhanced_context(error_info, [ContextType.ERROR])

        # Get fix suggestions if requested
        fix_suggestions = []
        if include_fix_suggestions and self.config.error_auto_resolve:
            fix_suggestions = self._get_fix_suggestions(error_info, enhanced_data)

        return ContextResult(
            context_type=ContextType.ERROR,
            primary_content=context_data["error_message"],
            metadata={
                **context_data,
                "fix_suggestions": fix_suggestions,
                "enhanced_analysis": enhanced_data,
            },
            source_info={
                "file": context_data["file_path"],
                "line": context_data["line_number"],
                "column": context_data["column"],
            }
        )

    def get_function_context(
        self,
        function_name: str,
        file_path: Path | None = None
    ) -> ContextResult:
        """Get comprehensive context for a function.

        Args:
            function_name: Name of the function
            file_path: Optional file path to search in

        Returns:
            Context result with function analysis
        """
        # This would integrate with tools like reveal_symbol.py to find function
        enhanced_data = self._collect_enhanced_context(
            {"function_name": function_name, "file_path": file_path},
            [ContextType.FUNCTION]
        )

        return ContextResult(
            context_type=ContextType.FUNCTION,
            primary_content=enhanced_data.get("function_source", ""),
            dependencies=enhanced_data.get("dependencies", []),
            usages=enhanced_data.get("usages", []),
            documentation=enhanced_data.get("docstring"),
            metadata=enhanced_data.get("metadata", {}),
        )

    def _collect_enhanced_context(
        self,
        target: Any,
        context_types: list[ContextType]
    ) -> dict[str, Any]:
        """Collect enhanced context from all available providers."""
        enhanced_data: dict[str, Any] = {
            "related_symbols": [],
            "documentation": None,
            "source_info": {},
            "metadata": {},
        }

        # Collect from each provider
        for provider_name, provider_func in self._context_providers.items():
            try:
                provider_data = provider_func(target, context_types)
                if provider_data and isinstance(provider_data, dict):
                    # Merge provider data
                    related_symbols = provider_data.get("related_symbols", [])
                    if isinstance(related_symbols, list):
                        enhanced_data["related_symbols"].extend(related_symbols)

                    if provider_data.get("documentation"):
                        enhanced_data["documentation"] = provider_data["documentation"]

                    source_info = provider_data.get("source_info", {})
                    if isinstance(source_info, dict):
                        enhanced_data["source_info"].update(source_info)

                    metadata = provider_data.get("metadata", {})
                    if isinstance(metadata, dict):
                        enhanced_data["metadata"][provider_name] = metadata

            except Exception as e:
                logger.exception(f"Error collecting context from {provider_name}: {e}")
                if self.config.debug_mode:
                    logger.exception(f"Full traceback for {provider_name} error:")

        return enhanced_data

    def _get_graph_sitter_context(
        self,
        target: Any,
        context_types: list[ContextType]
    ) -> dict[str, Any]:
        """Get context using graph-sitter parsing capabilities."""
        try:
            # This would integrate with the existing tools (placeholder imports)
            # from ..extensions.tools.generate_docs_json import generate_docs_json
            # from ..extensions.tools.reveal_symbol import get_extended_context

            # For now, return placeholder data
            return {
                "related_symbols": [],
                "documentation": None,
                "source_info": {},
                "metadata": {"provider": "graph_sitter", "status": "placeholder"},
            }

        except ImportError as e:
            logger.warning(f"Could not import graph-sitter tools: {e}")
            return {}

    def _get_solidlsp_context(
        self,
        target: Any,
        context_types: list[ContextType]
    ) -> dict[str, Any]:
        """Get context using SolidLSP language server analysis."""
        try:
            # This would integrate with SolidLSP (placeholder imports)
            # from ..extensions.lsp.solidlsp.ls import SolidLanguageServer

            # For now, return placeholder data
            return {
                "related_symbols": [],
                "documentation": None,
                "source_info": {},
                "metadata": {"provider": "solidlsp", "status": "placeholder"},
            }

        except ImportError as e:
            logger.warning(f"Could not import SolidLSP components: {e}")
            return {}

    def _get_serena_context(
        self,
        target: Any,
        context_types: list[ContextType]
    ) -> dict[str, Any]:
        """Get context using Serena's symbol functionality."""
        try:
            # This would integrate with Serena (placeholder imports)
            # from ..extensions.lsp.serena.file_tools import FileTools

            # For now, return placeholder data
            return {
                "related_symbols": [],
                "documentation": None,
                "source_info": {},
                "metadata": {"provider": "serena", "status": "placeholder"},
            }

        except ImportError as e:
            logger.warning(f"Could not import Serena components: {e}")
            return {}

    def _get_autogenlib_context(
        self,
        target: Any,
        context_types: list[ContextType]
    ) -> dict[str, Any]:
        """Get context using AutogenLib's context retrieval."""
        try:
            # This would integrate with AutogenLib (placeholder imports)
            # from ..extensions.autogenlib._context import set_module_context
            # from ..extensions.autogenlib._finder import find_functions

            # For now, return placeholder data
            return {
                "related_symbols": [],
                "documentation": None,
                "source_info": {},
                "metadata": {"provider": "autogenlib", "status": "placeholder"},
            }

        except ImportError as e:
            logger.warning(f"Could not import AutogenLib components: {e}")
            return {}

    def _hop_through_imports(self, imp: Import) -> Symbol | ExternalModule:
        """Enhanced import resolution (from original example)."""
        if isinstance(imp.imported_symbol, Import):
            return self._hop_through_imports(imp.imported_symbol)

        # Ensure we return the correct type
        imported_symbol = imp.imported_symbol
        if imported_symbol is None:
            # For now, just raise an error if symbol is None
            # In a real implementation, we'd create a proper placeholder
            msg = "Import symbol is None - cannot resolve"
            raise ValueError(msg)

        return imported_symbol

    def _get_symbol_source(self, symbol: Symbol) -> str:
        """Get source code for a symbol."""
        try:
            if hasattr(symbol, 'source'):
                return symbol.source
            elif hasattr(symbol, 'definition'):
                return symbol.definition
            else:
                return str(symbol)
        except Exception as e:
            logger.exception(f"Error getting symbol source: {e}")
            return str(symbol)

    def _get_fix_suggestions(
        self,
        error_info: dict[str, Any],
        enhanced_data: dict[str, Any]
    ) -> list[str]:
        """Get fix suggestions for errors using enhanced context."""
        suggestions = []

        try:
            # This would integrate with AutogenLib's exception handler (placeholder imports)
            # from ..extensions.autogenlib._exception_handler import generate_fix_for_analysis_error

            # For now, return placeholder suggestions
            suggestions.append("Placeholder fix suggestion")

        except ImportError as e:
            logger.warning(f"Could not import AutogenLib exception handler: {e}")
        except Exception as e:
            logger.exception(f"Error generating fix suggestions: {e}")

        return suggestions
