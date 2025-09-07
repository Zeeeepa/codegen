"""Unified diagnostics system aggregating solidlsp + serena + graph-sitter."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING

from ..config.graph_sitter_config import GraphSitterConfig
from .diagnostic_types import Diagnostic, DiagnosticSeverity, DiagnosticSource

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class UnifiedDiagnostics:
    """Unified diagnostics system that aggregates diagnostics from multiple sources."""

    def __init__(self, config: GraphSitterConfig):
        """Initialize unified diagnostics system."""
        self.config = config
        self._collectors: dict[DiagnosticSource, Callable] = {}
        self._cache: dict[str, list[Diagnostic]] = {}
        self._cache_enabled = config.cache_enabled

        # Initialize collectors based on configuration
        self._initialize_collectors()

    def _initialize_collectors(self):
        """Initialize diagnostic collectors based on configuration."""
        if self.config.lsp_server:
            self._collectors[DiagnosticSource.SOLIDLSP] = self._collect_solidlsp_diagnostics
            self._collectors[DiagnosticSource.SERENA] = self._collect_serena_diagnostics

        if self.config.enhanced_context or self.config.doc_gen:
            self._collectors[DiagnosticSource.TOOLS] = self._collect_tools_diagnostics
            self._collectors[DiagnosticSource.GRAPH_SITTER] = self._collect_graph_sitter_diagnostics

        if self.config.error_auto_resolve:
            self._collectors[DiagnosticSource.AUTOGENLIB] = self._collect_autogenlib_diagnostics

    async def collect_all_diagnostics(
        self,
        file_paths: list[Path] | None = None,
        force_refresh: bool = False
    ) -> list[Diagnostic]:
        """Collect diagnostics from all enabled sources.

        Args:
            file_paths: Specific files to analyze (None for all files)
            force_refresh: Force refresh of cached diagnostics

        Returns:
            List of all diagnostics sorted by severity and file path
        """
        cache_key = self._get_cache_key(file_paths)

        # Check cache first
        if not force_refresh and self._cache_enabled and cache_key in self._cache:
            if self.config.debug_mode:
                logger.debug(f"Returning cached diagnostics for {cache_key}")
            return self._cache[cache_key]

        all_diagnostics = []

        # Collect diagnostics from all sources concurrently
        with ThreadPoolExecutor(max_workers=len(self._collectors)) as executor:
            future_to_source = {
                executor.submit(collector, file_paths): source
                for source, collector in self._collectors.items()
            }

            for future in as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    diagnostics = future.result()
                    all_diagnostics.extend(diagnostics)
                    if self.config.debug_mode:
                        logger.debug(f"Collected {len(diagnostics)} diagnostics from {source.value}")
                except Exception as e:
                    logger.exception(f"Error collecting diagnostics from {source.value}: {e}")

        # Sort diagnostics by severity and file path
        sorted_diagnostics = self._sort_diagnostics(all_diagnostics)

        # Cache results
        if self._cache_enabled:
            self._cache[cache_key] = sorted_diagnostics

        return sorted_diagnostics

    def _collect_solidlsp_diagnostics(self, file_paths: list[Path] | None) -> list[Diagnostic]:
        """Collect diagnostics from SolidLSP language server."""
        diagnostics: list[Diagnostic] = []

        try:
            # Import SolidLSP components (placeholder imports)
            # from ..extensions.lsp.solidlsp.ls import SolidLanguageServer
            # from ..extensions.lsp.solidlsp.ls_types import UnifiedSymbolInformation

            # Initialize language server if not already done
            # This is a simplified implementation - in practice, you'd want to
            # maintain a persistent language server instance

            # For now, return empty list - full implementation would:
            # 1. Start/connect to language server
            # 2. Request diagnostics for specified files
            # 3. Convert LSP diagnostics to our unified format

            if self.config.debug_mode:
                logger.debug("SolidLSP diagnostics collection not yet implemented")

        except ImportError as e:
            logger.warning(f"Could not import SolidLSP components: {e}")
        except Exception as e:
            logger.exception(f"Error collecting SolidLSP diagnostics: {e}")

        return diagnostics

    def _collect_serena_diagnostics(self, file_paths: list[Path] | None) -> list[Diagnostic]:
        """Collect diagnostics from Serena file analysis tools."""
        diagnostics: list[Diagnostic] = []

        try:
            # Import Serena components (placeholder imports)
            # from ..extensions.lsp.serena.file_tools import FileTools

            # For now, return empty list - full implementation would:
            # 1. Use Serena's file analysis capabilities
            # 2. Check for file system issues, symbol problems
            # 3. Convert to unified diagnostic format

            if self.config.debug_mode:
                logger.debug("Serena diagnostics collection not yet implemented")

        except ImportError as e:
            logger.warning(f"Could not import Serena components: {e}")
        except Exception as e:
            logger.exception(f"Error collecting Serena diagnostics: {e}")

        return diagnostics

    def _collect_tools_diagnostics(self, file_paths: list[Path] | None) -> list[Diagnostic]:
        """Collect diagnostics from tools directory analysis."""
        diagnostics: list[Diagnostic] = []

        try:
            # Import tools components (placeholder imports)
            # from ..extensions.tools.generate_docs_json import generate_docs_json
            # from ..extensions.tools.reveal_symbol import reveal_symbol

            # For now, return empty list - full implementation would:
            # 1. Run static analysis tools on specified files
            # 2. Extract issues from analysis results
            # 3. Convert to unified diagnostic format

            if self.config.debug_mode:
                logger.debug("Tools diagnostics collection not yet implemented")

        except ImportError as e:
            logger.warning(f"Could not import tools components: {e}")
        except Exception as e:
            logger.exception(f"Error collecting tools diagnostics: {e}")

        return diagnostics

    def _collect_graph_sitter_diagnostics(self, file_paths: list[Path] | None) -> list[Diagnostic]:
        """Collect diagnostics from graph-sitter parsing."""
        diagnostics: list[Diagnostic] = []

        try:
            # For now, return empty list - full implementation would:
            # 1. Parse files with tree-sitter
            # 2. Check for syntax errors, parsing issues
            # 3. Convert to unified diagnostic format

            if self.config.debug_mode:
                logger.debug("Graph-sitter diagnostics collection not yet implemented")

        except Exception as e:
            logger.exception(f"Error collecting graph-sitter diagnostics: {e}")

        return diagnostics

    def _collect_autogenlib_diagnostics(self, file_paths: list[Path] | None) -> list[Diagnostic]:
        """Collect diagnostics from AutogenLib analysis."""
        diagnostics: list[Diagnostic] = []

        try:
            # Import AutogenLib components (placeholder imports)
            # from ..extensions.autogenlib._exception_handler import generate_fix_for_analysis_error

            # For now, return empty list - full implementation would:
            # 1. Use AutogenLib's analysis capabilities
            # 2. Check for potential runtime issues
            # 3. Convert to unified diagnostic format

            if self.config.debug_mode:
                logger.debug("AutogenLib diagnostics collection not yet implemented")

        except ImportError as e:
            logger.warning(f"Could not import AutogenLib components: {e}")
        except Exception as e:
            logger.exception(f"Error collecting AutogenLib diagnostics: {e}")

        return diagnostics

    def _sort_diagnostics(self, diagnostics: list[Diagnostic]) -> list[Diagnostic]:
        """Sort diagnostics by severity and file path."""
        severity_order = {
            DiagnosticSeverity.ERROR: 0,
            DiagnosticSeverity.WARNING: 1,
            DiagnosticSeverity.INFO: 2,
            DiagnosticSeverity.HINT: 3,
        }

        return sorted(
            diagnostics,
            key=lambda d: (
                severity_order[d.severity],
                str(d.file_path),
                d.range.start.line,
                d.range.start.character
            )
        )

    def _get_cache_key(self, file_paths: list[Path] | None) -> str:
        """Generate cache key for diagnostics."""
        if file_paths is None:
            return "all_files"
        return "|".join(str(p) for p in sorted(file_paths))

    def get_diagnostics_by_severity(
        self,
        diagnostics: list[Diagnostic],
        severity: DiagnosticSeverity
    ) -> list[Diagnostic]:
        """Filter diagnostics by severity."""
        return [d for d in diagnostics if d.severity == severity]

    def get_diagnostics_by_file(
        self,
        diagnostics: list[Diagnostic],
        file_path: Path
    ) -> list[Diagnostic]:
        """Filter diagnostics by file path."""
        return [d for d in diagnostics if d.file_path == file_path]

    def get_diagnostics_by_source(
        self,
        diagnostics: list[Diagnostic],
        source: DiagnosticSource
    ) -> list[Diagnostic]:
        """Filter diagnostics by source."""
        return [d for d in diagnostics if d.source == source]

    def get_fixable_diagnostics(self, diagnostics: list[Diagnostic]) -> list[Diagnostic]:
        """Get diagnostics that have fix suggestions."""
        return [d for d in diagnostics if d.is_fixable()]

    def clear_cache(self):
        """Clear diagnostic cache."""
        self._cache.clear()
        if self.config.debug_mode:
            logger.debug("Diagnostic cache cleared")

    def get_summary(self, diagnostics: list[Diagnostic]) -> dict[str, int]:
        """Get summary of diagnostics by severity."""
        summary = {
            "errors": len(self.get_diagnostics_by_severity(diagnostics, DiagnosticSeverity.ERROR)),
            "warnings": len(self.get_diagnostics_by_severity(diagnostics, DiagnosticSeverity.WARNING)),
            "info": len(self.get_diagnostics_by_severity(diagnostics, DiagnosticSeverity.INFO)),
            "hints": len(self.get_diagnostics_by_severity(diagnostics, DiagnosticSeverity.HINT)),
            "total": len(diagnostics),
            "fixable": len(self.get_fixable_diagnostics(diagnostics)),
        }
        return summary
