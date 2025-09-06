"""
Project Context Manager for Unified Graph-Sitter Integration

This module provides the core ProjectContext class that manages workspace state
across SolidLSP, Serena, and graph-sitter systems, serving as the foundation
for the codebase.from_repo() API.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from .unified_config import UnifiedConfiguration, ConfigurationManager
from .integration_interfaces import (
    ILanguageServer, IProjectManager, IGraphBuilder, IDiagnosticCollector,
    ISymbolResolver, IErrorResolver, IContextEnhancer, IUnifiedSystem,
    UnifiedDiagnostic, UnifiedSymbol, ErrorResolutionResult
)

logger = logging.getLogger(__name__)


@dataclass
class ProjectState:
    """Represents the current state of a project"""
    initialized: bool = False
    languages_detected: List[str] = field(default_factory=list)
    files_tracked: Set[str] = field(default_factory=set)
    last_analysis: Optional[float] = None
    diagnostics_count: int = 0
    symbols_count: int = 0
    errors_resolved: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "initialized": self.initialized,
            "languages_detected": self.languages_detected,
            "files_tracked": list(self.files_tracked),
            "last_analysis": self.last_analysis,
            "diagnostics_count": self.diagnostics_count,
            "symbols_count": self.symbols_count,
            "errors_resolved": self.errors_resolved
        }


class ProjectContext:
    """
    Centralized project context manager that coordinates workspace state
    across SolidLSP, Serena, and graph-sitter systems.
    
    This class serves as the foundation for the unified codebase.from_repo() API
    and manages all aspects of project initialization, file tracking, and
    cross-system coordination.
    """
    
    def __init__(self, project_root: str, config: Optional[UnifiedConfiguration] = None):
        self.project_root = Path(project_root).resolve()
        self.project_name = self.project_root.name
        
        # Configuration management
        self.config_manager = ConfigurationManager(str(self.project_root))
        self.config = config or self.config_manager.load_or_create_config()
        
        # Project state
        self.state = ProjectState()
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        
        # Component interfaces (will be injected)
        self._language_server: Optional[ILanguageServer] = None
        self._project_manager: Optional[IProjectManager] = None
        self._graph_builder: Optional[IGraphBuilder] = None
        self._diagnostic_collector: Optional[IDiagnosticCollector] = None
        self._symbol_resolver: Optional[ISymbolResolver] = None
        self._error_resolver: Optional[IErrorResolver] = None
        self._context_enhancer: Optional[IContextEnhancer] = None
        
        # Event system
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._file_watchers: List[Callable] = []
        
        # Performance tracking
        self._performance_metrics: Dict[str, Any] = {}
        self._executor = ThreadPoolExecutor(max_workers=self.config.performance_config.get_worker_count())
        
        logger.info(f"ProjectContext initialized for {self.project_root}")
    
    # Component injection methods
    def set_language_server(self, language_server: ILanguageServer):
        """Inject language server implementation"""
        self._language_server = language_server
        logger.debug("Language server injected")
    
    def set_project_manager(self, project_manager: IProjectManager):
        """Inject project manager implementation"""
        self._project_manager = project_manager
        logger.debug("Project manager injected")
    
    def set_graph_builder(self, graph_builder: IGraphBuilder):
        """Inject graph builder implementation"""
        self._graph_builder = graph_builder
        logger.debug("Graph builder injected")
    
    def set_diagnostic_collector(self, diagnostic_collector: IDiagnosticCollector):
        """Inject diagnostic collector implementation"""
        self._diagnostic_collector = diagnostic_collector
        logger.debug("Diagnostic collector injected")
    
    def set_symbol_resolver(self, symbol_resolver: ISymbolResolver):
        """Inject symbol resolver implementation"""
        self._symbol_resolver = symbol_resolver
        logger.debug("Symbol resolver injected")
    
    def set_error_resolver(self, error_resolver: IErrorResolver):
        """Inject error resolver implementation"""
        self._error_resolver = error_resolver
        logger.debug("Error resolver injected")
    
    def set_context_enhancer(self, context_enhancer: IContextEnhancer):
        """Inject context enhancer implementation"""
        self._context_enhancer = context_enhancer
        logger.debug("Context enhancer injected")
    
    # Core initialization methods
    async def initialize(self) -> bool:
        """
        Initialize the project context and all integrated systems.
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            with self._lock:
                if self.state.initialized:
                    logger.warning("Project context already initialized")
                    return True
                
                logger.info(f"Initializing project context for {self.project_root}")
                
                # Validate project directory
                if not self.project_root.exists():
                    raise FileNotFoundError(f"Project directory not found: {self.project_root}")
                
                # Initialize project manager first
                if self._project_manager:
                    success = self._project_manager.initialize_project(str(self.project_root))
                    if not success:
                        logger.error("Failed to initialize project manager")
                        return False
                
                # Detect languages
                await self._detect_languages()
                
                # Initialize language servers for detected languages
                if self.config.lspserver and self._language_server:
                    await self._initialize_language_servers()
                
                # Initialize graph builder
                if self._graph_builder:
                    await self._initialize_graph_builder()
                
                # Set up file watching
                await self._setup_file_watching()
                
                # Perform initial analysis
                await self._perform_initial_analysis()
                
                self.state.initialized = True
                self.state.last_analysis = time.time()
                
                # Emit initialization event
                await self._emit_event("project_initialized", {"project_root": str(self.project_root)})
                
                logger.info(f"Project context initialized successfully for {self.project_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize project context: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the project context and cleanup resources"""
        try:
            logger.info(f"Shutting down project context for {self.project_name}")
            
            # Set shutdown event
            self._shutdown_event.set()
            
            # Stop file watching
            if self._project_manager:
                self._project_manager.stop_watching()
            
            # Shutdown language server
            if self._language_server:
                await self._language_server.shutdown()
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            
            # Clear state
            with self._lock:
                self.state.initialized = False
            
            logger.info("Project context shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Language detection and setup
    async def _detect_languages(self):
        """Detect programming languages in the project"""
        try:
            if self._project_manager:
                detected_languages = self._project_manager.get_project_languages()
            else:
                # Fallback to config-based detection
                detected_languages = self.config.languages or []
            
            with self._lock:
                self.state.languages_detected = detected_languages
            
            logger.info(f"Detected languages: {detected_languages}")
            
        except Exception as e:
            logger.error(f"Failed to detect languages: {e}")
    
    async def _initialize_language_servers(self):
        """Initialize language servers for detected languages"""
        try:
            if not self._language_server:
                return
            
            for language in self.state.languages_detected:
                success = await self._language_server.initialize(str(self.project_root), language)
                if success:
                    logger.info(f"Language server initialized for {language}")
                else:
                    logger.warning(f"Failed to initialize language server for {language}")
            
        except Exception as e:
            logger.error(f"Failed to initialize language servers: {e}")
    
    async def _initialize_graph_builder(self):
        """Initialize the graph builder"""
        try:
            if not self._graph_builder:
                return
            
            # Build initial graph
            graph = self._graph_builder.build_graph(str(self.project_root))
            logger.info(f"Initial graph built with {len(graph.get('nodes', []))} nodes")
            
        except Exception as e:
            logger.error(f"Failed to initialize graph builder: {e}")
    
    # File watching and event handling
    async def _setup_file_watching(self):
        """Set up file system monitoring"""
        try:
            if not self._project_manager:
                return
            
            def on_file_change(file_path: str, change_type: str):
                """Handle file change events"""
                asyncio.create_task(self._handle_file_change(file_path, change_type))
            
            self._project_manager.watch_files(on_file_change)
            logger.info("File watching enabled")
            
        except Exception as e:
            logger.error(f"Failed to setup file watching: {e}")
    
    async def _handle_file_change(self, file_path: str, change_type: str):
        """Handle file change events"""
        try:
            logger.debug(f"File change detected: {file_path} ({change_type})")
            
            # Update graph if graph builder is available
            if self._graph_builder and change_type in ["modified", "created"]:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self._graph_builder.update_graph(file_path, content)
            
            # Emit file change event
            await self._emit_event("file_changed", {
                "file_path": file_path,
                "change_type": change_type
            })
            
        except Exception as e:
            logger.error(f"Error handling file change: {e}")
    
    # Analysis methods
    async def _perform_initial_analysis(self):
        """Perform initial project analysis"""
        try:
            logger.info("Performing initial project analysis")
            
            # Collect initial diagnostics
            if self.config.diagnostics and self._diagnostic_collector:
                diagnostics = await self._diagnostic_collector.collect_diagnostics()
                with self._lock:
                    self.state.diagnostics_count = len(diagnostics)
                logger.info(f"Found {len(diagnostics)} diagnostics")
            
            # Count symbols if available
            if self._symbol_resolver and self._project_manager:
                project_files = self._project_manager.get_project_files()
                symbol_count = 0
                for file_path in project_files[:10]:  # Limit for initial analysis
                    try:
                        if self._language_server:
                            symbols = await self._language_server.get_symbols(file_path)
                            symbol_count += len(symbols)
                    except Exception as e:
                        logger.debug(f"Failed to get symbols for {file_path}: {e}")
                
                with self._lock:
                    self.state.symbols_count = symbol_count
                logger.info(f"Found {symbol_count} symbols")
            
        except Exception as e:
            logger.error(f"Failed to perform initial analysis: {e}")
    
    # Event system
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable):
        """Remove an event handler"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all registered handlers"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    # Public API methods
    async def get_diagnostics(self, file_path: Optional[str] = None) -> List[UnifiedDiagnostic]:
        """Get diagnostics for the project or a specific file"""
        if not self.config.diagnostics or not self._diagnostic_collector:
            return []
        
        try:
            return await self._diagnostic_collector.collect_diagnostics(file_path)
        except Exception as e:
            logger.error(f"Failed to get diagnostics: {e}")
            return []
    
    async def get_symbols(self, file_path: Optional[str] = None) -> List[UnifiedSymbol]:
        """Get symbols for the project or a specific file"""
        if not self.config.lspserver or not self._language_server:
            return []
        
        try:
            if file_path:
                return await self._language_server.get_symbols(file_path)
            else:
                # Get symbols for all project files
                symbols = []
                if self._project_manager:
                    project_files = self._project_manager.get_project_files()
                    for file in project_files[:50]:  # Limit for performance
                        try:
                            file_symbols = await self._language_server.get_symbols(file)
                            symbols.extend(file_symbols)
                        except Exception as e:
                            logger.debug(f"Failed to get symbols for {file}: {e}")
                return symbols
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    async def auto_resolve_errors(self, max_errors: int = 10) -> List[ErrorResolutionResult]:
        """Automatically resolve errors in the project"""
        if not self.config.errorautoresolve or not self._error_resolver:
            return []
        
        try:
            # Get diagnostics
            diagnostics = await self.get_diagnostics()
            
            # Filter to errors only
            errors = [d for d in diagnostics if d.severity.value == "error"]
            
            # Limit the number of errors to resolve
            errors_to_resolve = errors[:max_errors]
            
            # Resolve errors
            results = await self._error_resolver.resolve_errors(errors_to_resolve)
            
            # Update state
            successful_resolutions = sum(1 for r in results if r.success)
            with self._lock:
                self.state.errors_resolved += successful_resolutions
            
            logger.info(f"Resolved {successful_resolutions}/{len(errors_to_resolve)} errors")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to auto-resolve errors: {e}")
            return []
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get comprehensive project information"""
        with self._lock:
            return {
                "project_root": str(self.project_root),
                "project_name": self.project_name,
                "config": self.config.to_dict(),
                "state": self.state.to_dict(),
                "integration_level": self.config.get_integration_level(),
                "components_available": {
                    "language_server": self._language_server is not None,
                    "project_manager": self._project_manager is not None,
                    "graph_builder": self._graph_builder is not None,
                    "diagnostic_collector": self._diagnostic_collector is not None,
                    "symbol_resolver": self._symbol_resolver is not None,
                    "error_resolver": self._error_resolver is not None,
                    "context_enhancer": self._context_enhancer is not None
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the status of all system components"""
        status = {
            "project_context": {
                "initialized": self.state.initialized,
                "project_root": str(self.project_root),
                "languages": self.state.languages_detected
            }
        }
        
        # Check language server status
        if self._language_server:
            status["language_server"] = {
                "available": True,
                "running": self._language_server.is_running()
            }
        else:
            status["language_server"] = {"available": False}
        
        # Add other component statuses
        status["components"] = {
            "project_manager": self._project_manager is not None,
            "graph_builder": self._graph_builder is not None,
            "diagnostic_collector": self._diagnostic_collector is not None,
            "symbol_resolver": self._symbol_resolver is not None,
            "error_resolver": self._error_resolver is not None,
            "context_enhancer": self._context_enhancer is not None
        }
        
        return status
    
    # Configuration management
    def update_config(self, **kwargs) -> UnifiedConfiguration:
        """Update project configuration"""
        return self.config_manager.update_config(**kwargs)
    
    def save_config(self):
        """Save current configuration to file"""
        self.config_manager.save_config()
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.shutdown()
    
    def __enter__(self):
        """Sync context manager entry (not recommended)"""
        # For sync usage, but async initialization is preferred
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        # Cleanup what we can synchronously
        self._shutdown_event.set()
        self._executor.shutdown(wait=False)
