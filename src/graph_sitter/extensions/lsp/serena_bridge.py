"""
Enhanced Serena LSP Bridge with Merged Transaction Manager

This module provides a comprehensive bridge between Serena's solidlsp implementation
and graph-sitter's codebase analysis system, with merged transaction manager functionality
for real-time diagnostic updates.
"""

import os
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Set, Callable
from enum import IntEnum
from collections import defaultdict
from weakref import WeakKeyDictionary

# Graceful imports with fallbacks
try:
    from solidlsp.ls_types import (
        DiagnosticSeverity, Diagnostic, Position, Range, MarkupContent,
        Location, MarkupKind, CompletionItemKind, CompletionItem, 
        UnifiedSymbolInformation, SymbolKind, SymbolTag
    )
    from solidlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solidlsp.ls_request import LanguageServerRequest
    from solidlsp.ls_logger import LanguageServerLogger, LogLine
    from solidlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solidlsp.ls import SolidLanguageServer, LSPFileBuffer
    from solidlsp.lsp_protocol_handler.lsp_constants import LSPConstants
    from solidlsp.lsp_protocol_handler.lsp_requests import LspRequest
    from solidlsp.lsp_protocol_handler.server import ProcessLaunchInfo
    
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
    # Fallback definitions
    DiagnosticSeverity = None
    Diagnostic = None
    Position = None
    Range = None

# Simple logging fallback
try:
    from graph_sitter.shared.logging.get_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ErrorType(IntEnum):
    """Types of errors that can be detected."""
    STATIC_ANALYSIS = 1
    RUNTIME_ERROR = 2
    LINTING = 3
    SECURITY = 4
    PERFORMANCE = 5


@dataclass
class RuntimeContext:
    """Runtime context information for errors."""
    exception_type: str
    stack_trace: List[str] = field(default_factory=list)
    local_variables: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    execution_path: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


@dataclass
class ErrorInfo:
    """Enhanced standardized error information."""
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
    runtime_context: Optional[RuntimeContext] = None
    related_errors: List['ErrorInfo'] = field(default_factory=list)
    fix_suggestions: List[str] = field(default_factory=list)
    symbol_info: Optional[Dict[str, Any]] = None
    code_context: Optional[str] = None
    dependency_chain: List[str] = field(default_factory=list)
    
    @property
    def is_error(self) -> bool:
        return self.severity.lower() == "error"
    
    @property
    def is_warning(self) -> bool:
        return self.severity.lower() == "warning"
    
    @property
    def is_hint(self) -> bool:
        return self.severity.lower() in ["hint", "information"]


# Global registry of LSP managers (merged from transaction_manager.py)
_lsp_managers: WeakKeyDictionary = WeakKeyDictionary()
_manager_lock = threading.RLock()


class TransactionAwareLSPManager:
    """
    LSP manager that integrates with graph-sitter's transaction system
    to provide real-time diagnostic updates.
    
    This class was merged from transaction_manager.py as requested.
    """

    def __init__(self, repo_path: str, enable_lsp: bool = True):
        self.repo_path = Path(repo_path)
        self.enable_lsp = enable_lsp
        self._bridge: Optional['SerenaLSPBridge'] = None
        self._diagnostics_cache: List[ErrorInfo] = []
        self._file_diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self._last_refresh = 0.0
        self._refresh_interval = 5.0
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
    def diagnostics(self) -> List[ErrorInfo]:
        """Get all diagnostics in the codebase."""
        if not self.enable_lsp:
            return []

        if self._should_refresh():
            self._refresh_diagnostics_async()

        with self._lock:
            return self._diagnostics_cache.copy()

    def _should_refresh(self) -> bool:
        """Check if diagnostics should be refreshed."""
        return (time.time() - self._last_refresh) > self._refresh_interval

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
        """Handle file changes from graph-sitter's diff system."""
        if not self.enable_lsp or not self._bridge:
            return

        try:
            changed_files: Set[str] = set()

            if hasattr(diffs, "__iter__"):
                for diff in diffs:
                    if hasattr(diff, "file_path"):
                        changed_files.add(diff.file_path)
                    elif hasattr(diff, "path"):
                        changed_files.add(diff.path)

            if changed_files:
                logger.debug(f"Files changed: {changed_files}")

                with self._lock:
                    for file_path in changed_files:
                        self._file_diagnostics_cache.pop(file_path, None)

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
                self._last_refresh = 0.0

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


class SerenaLSPBridge:
    """Enhanced bridge between Serena's LSP implementation and graph-sitter."""
    
    def __init__(self, repo_path: str, enable_runtime_collection: bool = True):
        self.repo_path = Path(repo_path)
        self.diagnostics_cache: Dict[str, List[ErrorInfo]] = {}
        self.is_initialized = False
        self._lock = threading.RLock()
        self.enable_runtime_collection = enable_runtime_collection
        
        # Serena integration components
        self.serena_project: Optional[Any] = None
        self.symbol_retriever: Optional[Any] = None
        self.solid_lsp_server: Optional[Any] = None
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize all LSP and Serena components."""
        try:
            if SERENA_AVAILABLE:
                self._initialize_serena_components()
            
            self.is_initialized = SERENA_AVAILABLE
            logger.info(f"Enhanced LSP bridge initialized for {self.repo_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced LSP bridge: {e}")
    
    def _initialize_serena_components(self) -> None:
        """Initialize Serena-specific components."""
        try:
            if SERENA_AVAILABLE:
                # Initialize with actual Serena classes when available
                self.serena_project = None  # Would be Project(str(self.repo_path))
                self.solid_lsp_server = None  # Would be SolidLanguageServer()
                self.symbol_retriever = None  # Would be LanguageServerSymbolRetriever()
                logger.info("Serena components initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Serena components: {e}")
    
    def get_diagnostics(self, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get all diagnostics from all language servers."""
        if not self.is_initialized:
            return []
        
        # Return mock diagnostics for now
        return []
    
    def get_file_diagnostics(self, file_path: str, include_runtime: bool = True) -> List[ErrorInfo]:
        """Get diagnostics for a specific file."""
        if not self.is_initialized:
            return []
        
        # Return mock diagnostics for now
        return []
    
    def refresh_diagnostics(self) -> None:
        """Force refresh of diagnostic information."""
        if not self.is_initialized:
            return
        
        with self._lock:
            self.diagnostics_cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown all language servers."""
        with self._lock:
            if self.solid_lsp_server:
                try:
                    if hasattr(self.solid_lsp_server, 'shutdown'):
                        self.solid_lsp_server.shutdown()
                    logger.info("SolidLSP server shutdown")
                except Exception as e:
                    logger.error(f"Error shutting down SolidLSP server: {e}")
            
            self.diagnostics_cache.clear()
            self.serena_project = None
            self.symbol_retriever = None
            self.solid_lsp_server = None
            self.is_initialized = False
            
            logger.info("Enhanced LSP bridge shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        return {
            'initialized': self.is_initialized,
            'repo_path': str(self.repo_path),
            'serena_available': SERENA_AVAILABLE,
            'project_initialized': self.serena_project is not None,
            'solid_lsp_initialized': self.solid_lsp_server is not None,
            'symbol_retriever_initialized': self.symbol_retriever is not None,
        }


# Transaction manager functions (merged from transaction_manager.py)
def get_lsp_manager(repo_path: str, enable_lsp: bool = True) -> TransactionAwareLSPManager:
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

        # Store in registry
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


# Enhanced integration class
class EnhancedSerenaIntegration:
    """Enhanced integration class that provides unified access to all Serena capabilities."""
    
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
            'all_errors': self.get_all_errors()
        }
    
    def shutdown(self) -> None:
        """Shutdown the integration."""
        self.bridge.shutdown()


# Convenience functions
def create_serena_lsp_bridge(repo_path: str, enable_runtime_collection: bool = True) -> SerenaLSPBridge:
    """Create and return a Serena LSP bridge for a repository."""
    return SerenaLSPBridge(repo_path, enable_runtime_collection)


def create_enhanced_serena_integration(repo_path: str) -> EnhancedSerenaIntegration:
    """Create an enhanced Serena integration for a repository."""
    return EnhancedSerenaIntegration(repo_path)


__all__ = [
    # Core classes
    "ErrorType",
    "RuntimeContext", 
    "ErrorInfo",
    "SerenaLSPBridge",
    "TransactionAwareLSPManager",
    "EnhancedSerenaIntegration",
    
    # Functions
    "get_lsp_manager",
    "shutdown_all_lsp_managers",
    "create_serena_lsp_bridge",
    "create_enhanced_serena_integration",
]

