# Copyright 2025 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unified API Implementation

This module provides the main unified API that brings together all components
of the SolidLSP + Serena + Graph-Sitter integration system.

The main entry point is the `codebase.from_repo()` function that initializes
the entire system and provides a unified interface for all capabilities.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import threading
import time
from dataclasses import dataclass

from .unified_config import UnifiedConfiguration, ConfigurationManager
from .project_context import ProjectContext
from .adapters.solidlsp_adapter import SolidLSPAdapter
from .adapters.serena_adapter import SerenaAdapter
from .enhanced_graph_builder import EnhancedGraphBuilder
from .diagnostic_collector import DiagnosticCollector
from .autogenlib_context_enhancer import AutogenLibContextEnhancer
from .integration_interfaces import (
    UnifiedDiagnostic, UnifiedSymbol, UnifiedLocation,
    DiagnosticSeverity, SymbolKind
)

logger = logging.getLogger(__name__)


@dataclass
class CodebaseAnalysisResult:
    """Result of codebase analysis"""
    diagnostics: List[UnifiedDiagnostic]
    symbols: List[UnifiedSymbol]
    graph: Dict[str, Any]
    resolved_errors: List[Dict[str, Any]]
    error_contexts: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    timestamp: float


class UnifiedCodebaseAPI:
    """
    Unified API for the integrated SolidLSP + Serena + Graph-Sitter system.
    
    This class provides the main interface for all codebase analysis capabilities:
    - LSP diagnostics and symbol information
    - Serena project management and workspace analysis
    - Enhanced graph construction with cross-system integration
    - Automatic error resolution with enhanced context
    - Performance tracking and metrics
    """
    
    def __init__(self, project_root: str, config: Optional[UnifiedConfiguration] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or UnifiedConfiguration()
        
        # Core components
        self._project_context: Optional[ProjectContext] = None
        self._solidlsp_adapter: Optional[SolidLSPAdapter] = None
        self._serena_adapter: Optional[SerenaAdapter] = None
        self._graph_builder: Optional[EnhancedGraphBuilder] = None
        self._diagnostic_collector: Optional[DiagnosticCollector] = None
        self._context_enhancer: Optional[AutogenLibContextEnhancer] = None
        
        # State management
        self._lock = threading.RLock()
        self._initialized = False
        self._initialization_error: Optional[str] = None
        
        # Performance tracking
        self._api_metrics: Dict[str, Any] = {}
        
        logger.info(f"Unified codebase API created for {self.project_root}")
    
    async def initialize(self) -> bool:
        """Initialize the unified system"""
        try:
            with self._lock:
                if self._initialized:
                    logger.debug("Unified API already initialized")
                    return True
                
                logger.info(f"Initializing unified codebase API for {self.project_root}")
                start_time = time.time()
                
                # Validate project root
                if not self.project_root.exists():
                    self._initialization_error = f"Project root does not exist: {self.project_root}"
                    logger.error(self._initialization_error)
                    return False
                
                # Initialize core components
                success = await self._initialize_components()
                if not success:
                    return False
                
                # Wire up dependencies
                self._wire_dependencies()
                
                # Initialize project context
                self._project_context = ProjectContext(str(self.project_root), self.config)
                context_success = await self._project_context.initialize()
                if not context_success:
                    self._initialization_error = "Failed to initialize project context"
                    logger.error(self._initialization_error)
                    return False
                
                # Set up file watching if enabled
                if (self.config.diagnostics and 
                    self.config.diagnostics_config.real_time):
                    self._setup_file_watching()
                
                initialization_time = time.time() - start_time
                self._api_metrics['initialization_time'] = initialization_time
                self._api_metrics['initialized_at'] = time.time()
                
                self._initialized = True
                logger.info(f"Unified codebase API initialized successfully in {initialization_time:.2f}s")
                return True
                
        except Exception as e:
            self._initialization_error = f"Failed to initialize unified API: {e}"
            logger.error(self._initialization_error)
            import traceback
            traceback.print_exc()
            return False
    
    async def analyze(self, include_graph: bool = True, include_context: bool = True) -> CodebaseAnalysisResult:
        """Perform comprehensive codebase analysis"""
        try:
            if not self._initialized:
                raise RuntimeError("Unified API not initialized")
            
            start_time = time.time()
            logger.info("Starting comprehensive codebase analysis")
            
            # Collect diagnostics
            diagnostics = []
            if self.config.diagnostics and self._diagnostic_collector:
                diagnostics = await self._diagnostic_collector.collect_diagnostics()
                logger.debug(f"Collected {len(diagnostics)} diagnostics")
            
            # Get symbols
            symbols = []
            if self.config.lspserver and self._solidlsp_adapter:
                symbols = await self._get_all_symbols()
                logger.debug(f"Collected {len(symbols)} symbols")
            
            # Build graph
            graph = {}
            if include_graph and self._graph_builder:
                graph = self._graph_builder.build_graph(str(self.project_root))
                logger.debug(f"Built graph with {graph.get('metadata', {}).get('node_count', 0)} nodes")
            
            # Resolve errors
            resolved_errors = []
            error_contexts = []
            if self.config.errorautoresolve and diagnostics:
                resolved_errors, error_contexts = await self._resolve_errors(diagnostics, include_context)
                logger.debug(f"Resolved {len(resolved_errors)} errors with context")
            
            # Collect metrics
            metrics = self._collect_analysis_metrics()
            
            analysis_time = time.time() - start_time
            metrics['analysis_time'] = analysis_time
            
            result = CodebaseAnalysisResult(
                diagnostics=diagnostics,
                symbols=symbols,
                graph=graph,
                resolved_errors=resolved_errors,
                error_contexts=error_contexts,
                metrics=metrics,
                timestamp=time.time()
            )
            
            logger.info(f"Codebase analysis completed in {analysis_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze codebase: {e}")
            return CodebaseAnalysisResult(
                diagnostics=[],
                symbols=[],
                graph={},
                resolved_errors=[],
                error_contexts=[],
                metrics={'error': str(e)},
                timestamp=time.time()
            )
    
    async def get_diagnostics(self, file_path: Optional[str] = None) -> List[UnifiedDiagnostic]:
        """Get diagnostics for the codebase or specific file"""
        try:
            if not self._initialized or not self._diagnostic_collector:
                return []
            
            return await self._diagnostic_collector.collect_diagnostics(file_path)
            
        except Exception as e:
            logger.error(f"Failed to get diagnostics: {e}")
            return []
    
    async def get_symbols(self, file_path: Optional[str] = None) -> List[UnifiedSymbol]:
        """Get symbols for the codebase or specific file"""
        try:
            if not self._initialized or not self._solidlsp_adapter:
                return []
            
            if file_path:
                return await self._solidlsp_adapter.get_symbols(file_path)
            else:
                return await self._get_all_symbols()
                
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            return []
    
    async def resolve_errors(self, diagnostics: Optional[List[UnifiedDiagnostic]] = None) -> List[Dict[str, Any]]:
        """Resolve errors with automatic fixes"""
        try:
            if not self._initialized:
                return []
            
            if diagnostics is None:
                diagnostics = await self.get_diagnostics()
            
            if not diagnostics:
                return []
            
            resolved_errors, _ = await self._resolve_errors(diagnostics, include_context=False)
            return resolved_errors
            
        except Exception as e:
            logger.error(f"Failed to resolve errors: {e}")
            return []
    
    async def get_enhanced_context(self, diagnostic: UnifiedDiagnostic, file_path: str) -> Dict[str, Any]:
        """Get enhanced context for a diagnostic"""
        try:
            if not self._initialized or not self._context_enhancer:
                return {}
            
            enhanced_context = await self._context_enhancer.enhance_context(diagnostic, file_path)
            return {
                'symbol_definitions': enhanced_context.symbol_definitions,
                'type_information': enhanced_context.type_information,
                'variable_definitions': enhanced_context.variable_definitions,
                'function_signatures': enhanced_context.function_signatures,
                'import_dependencies': enhanced_context.import_dependencies,
                'impact_radius': enhanced_context.impact_radius,
                'related_errors': [
                    {
                        'message': err.message,
                        'severity': err.severity.value,
                        'source': err.source
                    }
                    for err in enhanced_context.related_errors
                ],
                'suggested_fixes': enhanced_context.suggested_fixes,
                'confidence_score': enhanced_context.confidence_score,
                'metadata': enhanced_context.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get enhanced context: {e}")
            return {}
    
    def get_graph(self, format: str = "dict") -> Union[str, Dict[str, Any]]:
        """Get the codebase graph"""
        try:
            if not self._initialized or not self._graph_builder:
                return {} if format == "dict" else "{}"
            
            return self._graph_builder.export_graph(format)
            
        except Exception as e:
            logger.error(f"Failed to get graph: {e}")
            return {} if format == "dict" else "{}"
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information"""
        try:
            info = {
                'project_root': str(self.project_root),
                'initialized': self._initialized,
                'initialization_error': self._initialization_error,
                'config': self.config.to_dict(),
                'components': {
                    'solidlsp_adapter': self._solidlsp_adapter is not None,
                    'serena_adapter': self._serena_adapter is not None,
                    'graph_builder': self._graph_builder is not None,
                    'diagnostic_collector': self._diagnostic_collector is not None,
                    'context_enhancer': self._context_enhancer is not None
                }
            }
            
            # Add component status if available
            if self._serena_adapter:
                info['serena_status'] = self._serena_adapter.get_status()
            
            if self._diagnostic_collector:
                info['diagnostic_status'] = self._diagnostic_collector.get_status()
            
            if self._context_enhancer:
                info['context_enhancer_status'] = self._context_enhancer.get_status()
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return {'error': str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            metrics = {
                'api_metrics': self._api_metrics.copy(),
                'components': {}
            }
            
            if self._graph_builder:
                metrics['components']['graph_builder'] = self._graph_builder.get_build_metrics()
            
            if self._diagnostic_collector:
                metrics['components']['diagnostic_collector'] = self._diagnostic_collector.get_collection_metrics()
            
            if self._context_enhancer:
                metrics['components']['context_enhancer'] = self._context_enhancer.get_enhancement_metrics()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {'error': str(e)}
    
    async def shutdown(self) -> None:
        """Shutdown the unified system"""
        try:
            logger.info("Shutting down unified codebase API")
            
            # Shutdown components
            if self._solidlsp_adapter:
                await self._solidlsp_adapter.shutdown()
            
            if self._serena_adapter:
                self._serena_adapter.stop_watching()
            
            if self._project_context:
                await self._project_context.shutdown()
            
            self._initialized = False
            logger.info("Unified codebase API shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Private methods
    
    async def _initialize_components(self) -> bool:
        """Initialize all components"""
        try:
            # Initialize SolidLSP adapter
            if self.config.lspserver:
                self._solidlsp_adapter = SolidLSPAdapter(self.config.lsp_config)
                logger.debug("SolidLSP adapter created")
            
            # Initialize Serena adapter
            self._serena_adapter = SerenaAdapter(self.config)
            serena_success = self._serena_adapter.initialize_project(str(self.project_root))
            if not serena_success:
                logger.warning("Serena adapter initialization failed, continuing with limited functionality")
            
            # Initialize graph builder
            self._graph_builder = EnhancedGraphBuilder(self.config)
            
            # Initialize diagnostic collector
            if self.config.diagnostics:
                self._diagnostic_collector = DiagnosticCollector(self.config.diagnostics_config)
            
            # Initialize context enhancer
            if self.config.enhancedcontext:
                self._context_enhancer = AutogenLibContextEnhancer(self.config)
                context_success = self._context_enhancer.initialize(str(self.project_root))
                if not context_success:
                    logger.warning("Context enhancer initialization failed, continuing with limited functionality")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _wire_dependencies(self) -> None:
        """Wire up dependencies between components"""
        try:
            # Wire graph builder dependencies
            if self._graph_builder:
                if self._solidlsp_adapter:
                    self._graph_builder.set_language_server(self._solidlsp_adapter)
                if self._serena_adapter:
                    self._graph_builder.set_project_manager(self._serena_adapter)
                if self._diagnostic_collector:
                    self._graph_builder.set_diagnostic_collector(self._diagnostic_collector)
            
            # Wire diagnostic collector dependencies
            if self._diagnostic_collector:
                if self._solidlsp_adapter:
                    self._diagnostic_collector.set_language_server(self._solidlsp_adapter)
                if self._serena_adapter:
                    self._diagnostic_collector.set_project_manager(self._serena_adapter)
            
            # Wire context enhancer dependencies
            if self._context_enhancer:
                if self._solidlsp_adapter:
                    self._context_enhancer.set_language_server(self._solidlsp_adapter)
                if self._serena_adapter:
                    self._context_enhancer.set_project_manager(self._serena_adapter)
                if self._diagnostic_collector:
                    self._context_enhancer.set_diagnostic_collector(self._diagnostic_collector)
            
            logger.debug("Component dependencies wired successfully")
            
        except Exception as e:
            logger.error(f"Failed to wire dependencies: {e}")
    
    def _setup_file_watching(self) -> None:
        """Set up file watching for real-time updates"""
        try:
            if self._serena_adapter:
                def on_file_change(file_path: str, change_type: str):
                    """Handle file change events"""
                    try:
                        logger.debug(f"File {change_type}: {file_path}")
                        
                        # Clear caches
                        if self._diagnostic_collector:
                            self._diagnostic_collector.clear_cache(file_path)
                        
                        if self._context_enhancer:
                            self._context_enhancer.clear_cache(file_path)
                        
                        # Update graph if needed
                        if self._graph_builder and change_type in ['modified', 'created']:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                self._graph_builder.update_graph(file_path, content)
                            except Exception as e:
                                logger.debug(f"Failed to update graph for {file_path}: {e}")
                                
                    except Exception as e:
                        logger.error(f"Error handling file change: {e}")
                
                self._serena_adapter.watch_files(on_file_change)
                logger.debug("File watching set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up file watching: {e}")
    
    async def _get_all_symbols(self) -> List[UnifiedSymbol]:
        """Get all symbols from all files"""
        try:
            if not self._serena_adapter or not self._solidlsp_adapter:
                return []
            
            all_symbols = []
            project_files = self._serena_adapter.get_project_files()
            
            # Limit files for performance
            files_to_process = project_files[:50]  # Process first 50 files
            
            for file_path in files_to_process:
                try:
                    file_symbols = await self._solidlsp_adapter.get_symbols(file_path)
                    all_symbols.extend(file_symbols)
                except Exception as e:
                    logger.debug(f"Failed to get symbols for {file_path}: {e}")
            
            return all_symbols
            
        except Exception as e:
            logger.error(f"Failed to get all symbols: {e}")
            return []
    
    async def _resolve_errors(self, diagnostics: List[UnifiedDiagnostic], include_context: bool = True) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Resolve errors with automatic fixes"""
        try:
            resolved_errors = []
            error_contexts = []
            
            for diagnostic in diagnostics:
                try:
                    # Skip non-error diagnostics for auto-resolution
                    if diagnostic.severity not in [DiagnosticSeverity.ERROR, DiagnosticSeverity.WARNING]:
                        continue
                    
                    # Get enhanced context if available
                    enhanced_context = None
                    if include_context and self._context_enhancer:
                        # We need to determine the file path from the diagnostic
                        # This is a simplified approach - in practice, you'd extract this from the diagnostic
                        file_path = "unknown"  # This would need to be extracted from diagnostic location
                        enhanced_context = await self._context_enhancer.enhance_context(diagnostic, file_path)
                        
                        error_contexts.append({
                            'diagnostic': {
                                'message': diagnostic.message,
                                'severity': diagnostic.severity.value,
                                'source': diagnostic.source
                            },
                            'context': await self.get_enhanced_context(diagnostic, file_path)
                        })
                    
                    # Generate fix suggestions
                    fixes = []
                    if enhanced_context and self._context_enhancer:
                        fixes = await self._context_enhancer.suggest_fixes(diagnostic, enhanced_context)
                    
                    if fixes:
                        resolved_errors.append({
                            'diagnostic': {
                                'message': diagnostic.message,
                                'severity': diagnostic.severity.value,
                                'code': diagnostic.code,
                                'source': diagnostic.source
                            },
                            'fixes': fixes,
                            'resolution_confidence': max(fix.get('confidence', 0.0) for fix in fixes),
                            'auto_resolvable': any(fix.get('confidence', 0.0) > 0.8 for fix in fixes)
                        })
                        
                except Exception as e:
                    logger.debug(f"Failed to resolve error: {diagnostic.message}: {e}")
            
            return resolved_errors, error_contexts
            
        except Exception as e:
            logger.error(f"Failed to resolve errors: {e}")
            return [], []
    
    def _collect_analysis_metrics(self) -> Dict[str, Any]:
        """Collect metrics from all components"""
        try:
            metrics = {
                'timestamp': time.time(),
                'project_root': str(self.project_root),
                'config': self.config.to_dict()
            }
            
            # Add component metrics
            if self._graph_builder:
                metrics['graph_metrics'] = self._graph_builder.get_build_metrics()
            
            if self._diagnostic_collector:
                metrics['diagnostic_metrics'] = self._diagnostic_collector.get_collection_metrics()
            
            if self._context_enhancer:
                metrics['context_metrics'] = self._context_enhancer.get_enhancement_metrics()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect analysis metrics: {e}")
            return {'error': str(e)}


# Global instance management
_active_codebase: Optional[UnifiedCodebaseAPI] = None
_codebase_lock = threading.Lock()


async def from_repo(repo_path: str, config: Optional[UnifiedConfiguration] = None) -> UnifiedCodebaseAPI:
    """
    Main entry point for the unified codebase API.
    
    This function initializes the complete SolidLSP + Serena + Graph-Sitter
    integration system for a given repository.
    
    Args:
        repo_path: Path to the repository root
        config: Optional configuration (uses defaults if not provided)
    
    Returns:
        UnifiedCodebaseAPI instance ready for analysis
    
    Example:
        ```python
        # Initialize the unified system
        codebase = await from_repo("/path/to/project")
        
        # Perform comprehensive analysis
        result = await codebase.analyze()
        
        # Get diagnostics
        diagnostics = await codebase.get_diagnostics()
        
        # Resolve errors automatically
        resolved = await codebase.resolve_errors()
        
        # Get enhanced context for an error
        context = await codebase.get_enhanced_context(diagnostics[0], "file.py")
        ```
    """
    global _active_codebase
    
    try:
        with _codebase_lock:
            # Shutdown existing codebase if different
            if _active_codebase and str(_active_codebase.project_root) != str(Path(repo_path).resolve()):
                await _active_codebase.shutdown()
                _active_codebase = None
            
            # Create new codebase if needed
            if _active_codebase is None:
                logger.info(f"Creating unified codebase API for {repo_path}")
                
                # Use provided config or load from configuration manager
                if config is None:
                    config_manager = ConfigurationManager()
                    config = config_manager.get_config()
                
                _active_codebase = UnifiedCodebaseAPI(repo_path, config)
                
                # Initialize the system
                success = await _active_codebase.initialize()
                if not success:
                    error_msg = _active_codebase._initialization_error or "Unknown initialization error"
                    logger.error(f"Failed to initialize codebase API: {error_msg}")
                    _active_codebase = None
                    raise RuntimeError(f"Failed to initialize codebase API: {error_msg}")
            
            return _active_codebase
            
    except Exception as e:
        logger.error(f"Failed to create codebase API: {e}")
        raise


def get_active_codebase() -> Optional[UnifiedCodebaseAPI]:
    """Get the currently active codebase API instance"""
    return _active_codebase


async def shutdown_active_codebase() -> None:
    """Shutdown the currently active codebase API"""
    global _active_codebase
    
    with _codebase_lock:
        if _active_codebase:
            await _active_codebase.shutdown()
            _active_codebase = None
