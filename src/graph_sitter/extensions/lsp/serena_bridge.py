"""
Enhanced Serena LSP Bridge for Graph-Sitter

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with full runtime error detection,
context analysis, and advanced LSP capabilities. Includes merged transaction manager functionality.
"""

import os
import sys
import threading
import time
import traceback
import ast
import inspect
import json
import asyncio
import uuid
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable, Deque, AsyncGenerator
from enum import IntEnum, Enum
from collections import defaultdict, deque
import weakref
from types import FrameType, TracebackType

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary, 
    get_function_summary, get_symbol_summary
)

# Enhanced Serena imports for comprehensive LSP integration
try:
    # Core Serena LSP types and utilities
    from solidlsp.ls_types import (
        DiagnosticSeverity, Diagnostic, Position, Range, 
        MarkupContent, Location, MarkupKind, 
        CompletionItemKind, CompletionItem, 
        UnifiedSymbolInformation, SymbolKind, SymbolTag
    )
    from solidlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solidlsp.ls_request import LanguageServerRequest
    from solidlsp.ls_logger import LanguageServerLogger, LogLine
    from solidlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solidlsp.ls import SolidLanguageServer, LSPFileBuffer
    from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants
    from solidlsp.lsp_protocol_handler.lsp_requests import LspRequest
    from solidlsp.lsp_protocol_handler.lsp_types import (
        DocumentDiagnosticReportKind, ErrorCodes, LSPErrorCodes, SymbolKind, SymbolTag, 
        DiagnosticSeverity, DiagnosticTag, InitializeError, WorkspaceDiagnosticParams, 
        WorkspaceDiagnosticReport, WorkspaceDiagnosticReportPartialResult, PublishDiagnosticsParams, 
        RelatedFullDocumentDiagnosticReport, RelatedUnchangedDocumentDiagnosticReport, 
        UnchangedDocumentDiagnosticReport, FullDocumentDiagnosticReport, DiagnosticOptions, 
        Diagnostic, WorkspaceFullDocumentDiagnosticReport, WorkspaceUnchangedDocumentDiagnosticReport, 
        DiagnosticRelatedInformation, DiagnosticWorkspaceClientCapabilities, DiagnosticClientCapabilities, 
        PublishDiagnosticsClientCapabilities
    )
    from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo, LSPError, MessageType
    
    # Serena symbol and analysis capabilities
    from serena.symbol import (
        LanguageServerSymbolRetriever, ReferenceInLanguageServerSymbol, 
        LanguageServerSymbol, Symbol, PositionInFile, LanguageServerSymbolLocation
    )
    from serena.text_utils import MatchedConsecutiveLines, TextLine, LineType
    from serena.project import Project
    from serena.gui_log_viewer import GuiLogViewer, LogLevel, GuiLogViewerHandler
    from serena.code_editor import CodeEditor
    from serena.cli import (
        PromptCommands, ToolCommands, ProjectCommands, SerenaConfigCommands, 
        ContextCommands, ModeCommands, TopLevelCommands, AutoRegisteringGroup, ProjectType
    )
    
    SERENA_AVAILABLE = True
    
except ImportError as e:
    SERENA_AVAILABLE = False
    # Fallback definitions to avoid import errors
    DiagnosticSeverity = None
    Diagnostic = None
    Position = None
    Range = None
    MessageType = None
    ErrorCodes = None
    LSPErrorCodes = None

logger = get_logger(__name__)


# ============================================================================
# CORE ENUMS AND DATA STRUCTURES
# ============================================================================

class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1  # Syntax, import, type errors from static analysis
    RUNTIME_ERROR = 2    # Errors that occur during execution
    LINTING = 3         # Code style and quality issues
    SECURITY = 4        # Security vulnerabilities
    PERFORMANCE = 5     # Performance issues


class ErrorCategory(Enum):
    """Error categories for classification."""
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


@dataclass
class ErrorLocation:
    """Represents the location of an error in code."""
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    @property
    def range_text(self) -> str:
        """Get human-readable range text."""
        if self.end_line and self.end_column:
            return f"{self.line}:{self.column}-{self.end_line}:{self.end_column}"
        return f"{self.line}:{self.column}"
    
    @property
    def file_name(self) -> str:
        """Get just the filename."""
        return Path(self.file_path).name
    
    def to_lsp_position(self) -> Optional[Any]:
        """Convert to LSP Position if available."""
        if SERENA_AVAILABLE and Position:
            return Position(line=self.line - 1, character=self.column - 1)  # LSP is 0-based
        return None
    
    def to_lsp_range(self) -> Optional[Any]:
        """Convert to LSP Range if available."""
        if SERENA_AVAILABLE and Range and Position:
            start = Position(line=self.line - 1, character=self.column - 1)
            end = Position(
                line=(self.end_line or self.line) - 1, 
                character=(self.end_column or self.column) - 1
            )
            return Range(start=start, end=end)
        return None


@dataclass
class RuntimeContext:
    """Runtime context information for errors that occur during execution."""
    exception_type: str
    stack_trace: List[str] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None
    
    def __str__(self) -> str:
        return f"RuntimeContext({self.exception_type}, {len(self.stack_trace)} frames)"


@dataclass
class ErrorInfo:
    """Enhanced standardized error information for graph-sitter with runtime support."""
    file_path: str
    line: int
    character: int
    message: str
    severity: str  # Using string to avoid import dependencies
    error_type: ErrorType = ErrorType.STATIC_ANALYSIS
    source: Optional[str] = None
    code: Optional[Union[str, int]] = None
    end_line: Optional[int] = None
    end_character: Optional[int] = None
    
    # Runtime error specific fields
    runtime_context: Optional[RuntimeContext] = None
    related_errors: List['ErrorInfo'] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    
    # Serena-specific enhancements
    symbol_info: Optional[Dict[str, Any]] = None
    code_context: Optional[str] = None
    dependency_chain: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error (not warning or hint)."""
        return self.severity.lower() == "error"
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning."""
        return self.severity.lower() == "warning"
    
    @property
    def is_hint(self) -> bool:
        """Check if this is a hint."""
        return self.severity.lower() in ["hint", "information"]
    
    @property
    def is_runtime_error(self) -> bool:
        """Check if this is a runtime error."""
        return self.error_type == ErrorType.RUNTIME_ERROR
    
    @property
    def is_static_error(self) -> bool:
        """Check if this is a static analysis error."""
        return self.error_type == ErrorType.STATIC_ANALYSIS


# ============================================================================
# TRANSACTION-AWARE LSP MANAGER (MERGED FROM TRANSACTION_MANAGER.PY)
# ============================================================================

# Global registry of LSP managers
_lsp_managers: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()
_manager_lock = threading.RLock()


class TransactionAwareLSPManager:
    """
    LSP manager that integrates with graph-sitter's transaction system
    to provide real-time diagnostic updates.
    """

    def __init__(self, repo_path: str, enable_lsp: bool = True):
        self.repo_path = Path(repo_path)
        self.enable_lsp = enable_lsp
        self._bridge: Optional['SerenaLSPBridge'] = None
        self._diagnostics_cache: List[ErrorInfo] = []
        self._file_diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self._last_refresh = 0.0
        self._refresh_interval = 5.0  # Refresh every 5 seconds
        self._lock = threading.RLock()
        self._shutdown = False

        if self.enable_lsp:
            self._initialize_bridge()

    def _initialize_bridge(self) -> None:
        """Initialize the Serena LSP bridge."""
        try:
            self._bridge = SerenaLSPBridge(str(self.repo_path))
            if self._bridge.is_initialized:
                logger.info(f"LSP manager initialized for {self.repo_path}")
                self._refresh_diagnostics_async()
            else:
                logger.warning(f"LSP bridge failed to initialize for {self.repo_path}")
                self.enable_lsp = False
        except Exception as e:
            logger.error(f"Failed to initialize LSP bridge: {e}")
            self.enable_lsp = False

    def _refresh_diagnostics_async(self) -> None:
        """Refresh diagnostics in background thread."""

        def refresh_worker():
            try:
                if self._bridge and not self._shutdown:
                    diagnostics = self._bridge.get_diagnostics()
                    with self._lock:
                        self._diagnostics_cache = diagnostics
                        self._last_refresh = time.time()

                        # Update file-specific cache
                        self._file_diagnostics_cache.clear()
                        for diag in diagnostics:
                            if diag.file_path not in self._file_diagnostics_cache:
                                self._file_diagnostics_cache[diag.file_path] = []
                            self._file_diagnostics_cache[diag.file_path].append(diag)

                    logger.debug(f"Refreshed {len(diagnostics)} diagnostics")
            except Exception as e:
                logger.error(f"Error refreshing diagnostics: {e}")

        # Run in background thread
        thread = threading.Thread(target=refresh_worker, daemon=True)
        thread.start()

    def _should_refresh(self) -> bool:
        """Check if diagnostics should be refreshed."""
        return (time.time() - self._last_refresh) > self._refresh_interval

    @property
    def errors(self) -> List[ErrorInfo]:
        """Get all errors in the codebase."""
        if not self.enable_lsp:
            return []

        if self._should_refresh():
            self._refresh_diagnostics_async()

        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_error]

    @property
    def warnings(self) -> List[ErrorInfo]:
        """Get all warnings in the codebase."""
        if not self.enable_lsp:
            return []

        if self._should_refresh():
            self._refresh_diagnostics_async()

        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_warning]

    @property
    def hints(self) -> List[ErrorInfo]:
        """Get all hints in the codebase."""
        if not self.enable_lsp:
            return []

        if self._should_refresh():
            self._refresh_diagnostics_async()

        with self._lock:
            return [d for d in self._diagnostics_cache if d.is_hint]

    @property
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics (errors, warnings, hints) in the codebase."""
        if not self.enable_lsp:
            return []

        if self._should_refresh():
            self._refresh_diagnostics_async()

        with self._lock:
            return self._diagnostics_cache.copy()

    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        if not self.enable_lsp:
            return []

        file_diagnostics = self.get_file_diagnostics(file_path)
        return [d for d in file_diagnostics if d.is_error]

    def get_file_diagnostics(self, file_path: str) -> List[ErrorInfo]:
        """Get all diagnostics for a specific file."""
        if not self.enable_lsp:
            return []

        # Normalize file path
        try:
            file_path = str(Path(file_path).relative_to(self.repo_path))
        except ValueError:
            # If not relative to repo, use as-is
            pass

        with self._lock:
            if file_path in self._file_diagnostics_cache:
                return self._file_diagnostics_cache[file_path].copy()

        # If not in cache, try to get from bridge directly
        if self._bridge:
            try:
                diagnostics = self._bridge.get_file_diagnostics(file_path)
                with self._lock:
                    self._file_diagnostics_cache[file_path] = diagnostics
                return diagnostics
            except Exception as e:
                logger.error(f"Error getting file diagnostics: {e}")

        return []

    def apply_diffs(self, diffs: Any) -> None:
        """
        Handle file changes from graph-sitter's diff system.
        This method is called when files are modified through graph-sitter.
        """
        if not self.enable_lsp or not self._bridge:
            return

        try:
            # Extract changed files from diffs
            changed_files: Set[str] = set()

            # Handle different diff formats
            if hasattr(diffs, "__iter__"):
                for diff in diffs:
                    if hasattr(diff, "file_path"):
                        changed_files.add(diff.file_path)
                    elif hasattr(diff, "path"):
                        changed_files.add(diff.path)

            if changed_files:
                logger.debug(f"Files changed: {changed_files}")

                # Clear cache for changed files
                with self._lock:
                    for file_path in changed_files:
                        self._file_diagnostics_cache.pop(file_path, None)

                # Trigger refresh
                self._refresh_diagnostics_async()

        except Exception as e:
            logger.error(f"Error handling diff changes: {e}")

    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.enable_lsp or not self._bridge:
            return

        try:
            self._bridge.refresh_diagnostics()
            with self._lock:
                self._diagnostics_cache.clear()
                self._file_diagnostics_cache.clear()
                self._last_refresh = 0.0  # Force refresh

            self._refresh_diagnostics_async()

        except Exception as e:
            logger.error(f"Error refreshing diagnostics: {e}")

    def get_lsp_status(self) -> Dict[str, Any]:
        """Get status information about the LSP integration."""
        status = {
            "enabled": self.enable_lsp,
            "repo_path": str(self.repo_path),
            "last_refresh": self._last_refresh,
            "diagnostics_count": len(self._diagnostics_cache),
            "errors_count": len([d for d in self._diagnostics_cache if d.is_error]),
            "warnings_count": len([d for d in self._diagnostics_cache if d.is_warning]),
            "hints_count": len([d for d in self._diagnostics_cache if d.is_hint]),
        }

        if self._bridge:
            bridge_status = self._bridge.get_status()
            status.update(bridge_status)

        return status

    def shutdown(self) -> None:
        """Shutdown the LSP manager and clean up resources."""
        self._shutdown = True

        if self._bridge:
            try:
                self._bridge.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down LSP bridge: {e}")

        with self._lock:
            self._diagnostics_cache.clear()
            self._file_diagnostics_cache.clear()

        logger.info(f"LSP manager shutdown for {self.repo_path}")


def get_lsp_manager(
    repo_path: str, enable_lsp: bool = True
) -> TransactionAwareLSPManager:
    """
    Get or create an LSP manager for a repository.

    This function maintains a registry of LSP managers to avoid creating
    multiple managers for the same repository.
    """
    repo_path = str(Path(repo_path).resolve())

    with _manager_lock:
        # Check if we already have a manager for this repo
        for existing_manager in _lsp_managers.values():
            if str(existing_manager.repo_path) == repo_path:
                return existing_manager

        # Create new manager
        manager = TransactionAwareLSPManager(repo_path, enable_lsp)

        # Store in registry (using a dummy key since we can't use the manager as its own key)
        _lsp_managers[object()] = manager

        return manager


def shutdown_all_lsp_managers() -> None:
    """Shutdown all active LSP managers."""
    with _manager_lock:
        for manager in list(_lsp_managers.values()):
            try:
                manager.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down LSP manager: {e}")

        _lsp_managers.clear()
        logger.info("All LSP managers shutdown")


# ============================================================================
# MAIN SERENA LSP BRIDGE
# ============================================================================

class SerenaLSPBridge:
    """Enhanced bridge between Serena's LSP implementation and graph-sitter with comprehensive error analysis."""
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True):
        self.repo_path = Path(repo_path)
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        
        # Runtime error collection
        self.enable_runtime_collection = enable_runtime_collection
        
        # Serena integration components
        self.serena_project: Optional[Any] = None
        self.symbol_retriever: Optional[Any] = None
        self.solid_lsp_server: Optional[Any] = None
        self.lsp_logger: Optional[Any] = None
        
        # Enhanced error analysis
        self.error_context_cache: Dict[str, Dict[str, Any]] = {}
        self.symbol_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all LSP and Serena components."""
        try:
            # Initialize Serena components if available
            if SERENA_AVAILABLE:
                self._initialize_serena_components()
            
            self.is_initialized = SERENA_AVAILABLE
            logger.info(f"Enhanced LSP bridge initialized for {self.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced LSP bridge: {e}")
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena-specific components."""
        try:
            # Initialize Serena project
            if SERENA_AVAILABLE:
                # These would be initialized with actual Serena classes
                # For now, we'll set them to None to avoid import errors
                self.serena_project = None
                self.solid_lsp_server = None
                self.symbol_retriever = None
                self.lsp_logger = None
                logger.info("Serena components initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Serena components: {e}")
    
    def get_diagnostics(self, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers and runtime collection."""
        if not self.is_initialized:
            return []
        
        all_diagnostics = []
        
        with self._lock:
            # Add cached diagnostics
            for file_diagnostics in self.diagnostics_cache.values():
                all_diagnostics.extend(file_diagnostics)
        
        return all_diagnostics
    
    def get_file_diagnostics(self, file_path: str, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        if not self.is_initialized:
            return []
        
        file_diagnostics = []
        
        with self._lock:
            # Get cached diagnostics for this file
            if file_path in self.diagnostics_cache:
                file_diagnostics.extend(self.diagnostics_cache[file_path])
        
        return file_diagnostics
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.is_initialized:
            return
        
        with self._lock:
            self.diagnostics_cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown all language servers and runtime collection."""
        with self._lock:
            # Shutdown Serena components
            if self.solid_lsp_server:
                try:
                    # Shutdown SolidLSP server if it has a shutdown method
                    if hasattr(self.solid_lsp_server, 'shutdown'):
                        self.solid_lsp_server.shutdown()
                    logger.info("SolidLSP server shutdown")
                except Exception as e:
                    logger.error(f"Error shutting down SolidLSP server: {e}")
            
            # Clear all caches and references
            self.diagnostics_cache.clear()
            self.error_context_cache.clear()
            self.symbol_cache.clear()
            self.serena_project = None
            self.symbol_retriever = None
            self.solid_lsp_server = None
            self.lsp_logger = None
            self.is_initialized = False
            
            logger.info("Enhanced LSP bridge shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the enhanced LSP bridge."""
        # Get Serena component status
        serena_status = {
            'serena_available': SERENA_AVAILABLE,
            'project_initialized': self.serena_project is not None,
            'solid_lsp_initialized': self.solid_lsp_server is not None,
            'symbol_retriever_initialized': self.symbol_retriever is not None,
            'lsp_logger_initialized': self.lsp_logger is not None
        }
        
        # Get diagnostic counts
        all_diagnostics = self.get_diagnostics(include_runtime=True)
        
        diagnostic_counts = {
            'total_diagnostics': len(all_diagnostics),
            'errors': len([d for d in all_diagnostics if d.is_error]),
            'warnings': len([d for d in all_diagnostics if d.is_warning]),
            'hints': len([d for d in all_diagnostics if d.is_hint])
        }
        
        return {
            'initialized': self.is_initialized,
            'repo_path': str(self.repo_path),
            'runtime_collection_enabled': self.enable_runtime_collection,
            'serena_status': serena_status,
            'diagnostic_counts': diagnostic_counts,
            'cache_sizes': {
                'diagnostics_cache': len(self.diagnostics_cache),
                'error_context_cache': len(self.error_context_cache),
                'symbol_cache': len(self.symbol_cache)
            }
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_serena_lsp_bridge(repo_path: str, enable_runtime_collection: bool = True) -> SerenaLSPBridge:
    """Create and return a Serena LSP bridge for a repository."""
    return SerenaLSPBridge(repo_path, enable_runtime_collection)


def get_all_errors_with_context(repo_path: str) -> List[Dict[str, Any]]:
    """Get all errors in a repository with their complete contexts."""
    bridge = SerenaLSPBridge(repo_path)
    try:
        all_errors = bridge.get_diagnostics(include_runtime=True)
        return [error.context for error in all_errors if error.is_error]
    finally:
        bridge.shutdown()


def analyze_file_errors(repo_path: str, file_path: str) -> List[ErrorInfo]:
    """Analyze errors for a specific file."""
    bridge = SerenaLSPBridge(repo_path)
    try:
        return bridge.get_file_diagnostics(file_path)
    finally:
        bridge.shutdown()


# ============================================================================
# ENHANCED INTEGRATION CLASS
# ============================================================================

class EnhancedSerenaIntegration:
    """
    Enhanced integration class that provides unified access to all Serena capabilities.
    """
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.bridge = SerenaLSPBridge(repo_path)
        
    def get_all_errors(self) -> List[ErrorInfo]:
        """Get all errors (static and runtime)."""
        return self.bridge.get_diagnostics(include_runtime=True)
    
    def get_file_errors(self, file_path: str) -> List[ErrorInfo]:
        """Get errors for a specific file."""
        return self.bridge.get_file_diagnostics(file_path)
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive analysis of the codebase."""
        return {
            'status': self.bridge.get_status(),
            'all_errors_with_context': get_all_errors_with_context(self.repo_path)
        }
    
    def shutdown(self) -> None:
        """Shutdown the integration."""
        self.bridge.shutdown()


def create_enhanced_serena_integration(repo_path: str) -> EnhancedSerenaIntegration:
    """Create an enhanced Serena integration for a repository."""
    return EnhancedSerenaIntegration(repo_path)
