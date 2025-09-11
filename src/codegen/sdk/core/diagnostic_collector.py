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
Diagnostic Collection System

This module provides comprehensive diagnostic collection from all sources
including LSP servers, tree-sitter parsing errors, and static analysis tools.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
import threading
import time
from dataclasses import dataclass
from collections import defaultdict

from .integration_interfaces import (
    IDiagnosticCollector, ILanguageServer, IProjectManager,
    UnifiedDiagnostic, UnifiedLocation, UnifiedRange, UnifiedPosition,
    DiagnosticSeverity
)
from .unified_config import DiagnosticsConfiguration

# Tree-sitter imports for parsing errors
try:
    from ..tree_sitter_parser import parse_file, print_errors
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    parse_file = None
    print_errors = None

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticSource:
    """Represents a source of diagnostics"""
    name: str
    collector: Callable[[], List[UnifiedDiagnostic]]
    enabled: bool = True
    priority: int = 1  # Higher priority sources are processed first
    last_run: Optional[float] = None
    error_count: int = 0


class DiagnosticCollector(IDiagnosticCollector):
    """
    Comprehensive diagnostic collector that aggregates diagnostics from multiple sources.
    
    This collector integrates:
    - LSP server diagnostics
    - Tree-sitter parsing errors
    - Static analysis tools
    - Custom diagnostic sources
    """
    
    def __init__(self, config: DiagnosticsConfiguration):
        self.config = config
        
        # Component dependencies (injected)
        self._language_server: Optional[ILanguageServer] = None
        self._project_manager: Optional[IProjectManager] = None
        
        # Diagnostic sources
        self._sources: Dict[str, DiagnosticSource] = {}
        self._builtin_sources_registered = False
        
        # Diagnostic cache
        self._diagnostic_cache: Dict[str, List[UnifiedDiagnostic]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 30.0  # Cache TTL in seconds
        
        # State management
        self._lock = threading.RLock()
        self._collecting = False
        self._last_collection_time: Optional[float] = None
        
        # Performance tracking
        self._collection_metrics: Dict[str, Any] = {}
        self._source_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        logger.info("Diagnostic collector initialized")
    
    def set_language_server(self, language_server: ILanguageServer):
        """Inject language server dependency"""
        self._language_server = language_server
        self._register_builtin_sources()
    
    def set_project_manager(self, project_manager: IProjectManager):
        """Inject project manager dependency"""
        self._project_manager = project_manager
        self._register_builtin_sources()
    
    async def collect_diagnostics(self, file_path: Optional[str] = None) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from all sources"""
        try:
            with self._lock:
                if self._collecting:
                    logger.debug("Diagnostic collection already in progress")
                    return self._get_cached_diagnostics(file_path)
                
                self._collecting = True
            
            start_time = time.time()
            logger.debug(f"Collecting diagnostics{f' for {file_path}' if file_path else ''}")
            
            # Check cache first
            if file_path and self._is_cache_valid(file_path):
                logger.debug(f"Using cached diagnostics for {file_path}")
                return self._diagnostic_cache.get(file_path, [])
            
            # Collect from all sources
            all_diagnostics = []
            source_results = {}
            
            # Sort sources by priority
            sorted_sources = sorted(
                self._sources.items(),
                key=lambda x: x[1].priority,
                reverse=True
            )
            
            for source_name, source in sorted_sources:
                if not source.enabled:
                    continue
                
                try:
                    source_start = time.time()
                    
                    if file_path:
                        # Collect diagnostics for specific file
                        diagnostics = await self._collect_from_source_for_file(source, file_path)
                    else:
                        # Collect all diagnostics
                        diagnostics = await self._collect_from_source(source)
                    
                    source_time = time.time() - source_start
                    
                    # Filter diagnostics
                    filtered_diagnostics = self._filter_diagnostics(diagnostics)
                    
                    all_diagnostics.extend(filtered_diagnostics)
                    source_results[source_name] = {
                        'count': len(filtered_diagnostics),
                        'time': source_time,
                        'success': True
                    }
                    
                    source.last_run = time.time()
                    
                    logger.debug(f"Collected {len(filtered_diagnostics)} diagnostics from {source_name} in {source_time:.3f}s")
                    
                except Exception as e:
                    logger.error(f"Failed to collect diagnostics from {source_name}: {e}")
                    source.error_count += 1
                    source_results[source_name] = {
                        'count': 0,
                        'time': 0,
                        'success': False,
                        'error': str(e)
                    }
            
            # Deduplicate diagnostics
            deduplicated_diagnostics = self._deduplicate_diagnostics(all_diagnostics)
            
            # Update cache
            if file_path:
                self._diagnostic_cache[file_path] = deduplicated_diagnostics
                self._cache_timestamps[file_path] = time.time()
            
            # Update metrics
            collection_time = time.time() - start_time
            self._collection_metrics = {
                'last_collection_time': time.time(),
                'collection_duration': collection_time,
                'total_diagnostics': len(deduplicated_diagnostics),
                'source_results': source_results,
                'file_path': file_path
            }
            
            self._last_collection_time = time.time()
            
            logger.info(f"Collected {len(deduplicated_diagnostics)} diagnostics from {len(source_results)} sources in {collection_time:.3f}s")
            
            return deduplicated_diagnostics
            
        finally:
            with self._lock:
                self._collecting = False
    
    def add_diagnostic_source(self, source_name: str, collector: Callable[[], List[UnifiedDiagnostic]]) -> None:
        """Add a diagnostic source"""
        try:
            with self._lock:
                if source_name in self._sources:
                    logger.warning(f"Diagnostic source '{source_name}' already exists, replacing")
                
                self._sources[source_name] = DiagnosticSource(
                    name=source_name,
                    collector=collector,
                    enabled=True,
                    priority=1
                )
                
                logger.info(f"Added diagnostic source: {source_name}")
                
        except Exception as e:
            logger.error(f"Failed to add diagnostic source {source_name}: {e}")
    
    def remove_diagnostic_source(self, source_name: str) -> None:
        """Remove a diagnostic source"""
        try:
            with self._lock:
                if source_name in self._sources:
                    del self._sources[source_name]
                    logger.info(f"Removed diagnostic source: {source_name}")
                else:
                    logger.warning(f"Diagnostic source '{source_name}' not found")
                    
        except Exception as e:
            logger.error(f"Failed to remove diagnostic source {source_name}: {e}")
    
    def filter_diagnostics(self, diagnostics: List[UnifiedDiagnostic], severity: Optional[DiagnosticSeverity] = None) -> List[UnifiedDiagnostic]:
        """Filter diagnostics by criteria"""
        try:
            filtered = []
            
            for diagnostic in diagnostics:
                # Filter by severity
                if severity and diagnostic.severity != severity:
                    continue
                
                # Filter by configuration
                if not self.config.should_include_severity(diagnostic.severity.value):
                    continue
                
                filtered.append(diagnostic)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to filter diagnostics: {e}")
            return diagnostics
    
    def group_diagnostics(self, diagnostics: List[UnifiedDiagnostic]) -> Dict[str, List[UnifiedDiagnostic]]:
        """Group diagnostics by file or other criteria"""
        try:
            grouped = defaultdict(list)
            
            for diagnostic in diagnostics:
                # Group by file URI
                file_uri = getattr(diagnostic, 'file_uri', 'unknown')
                if hasattr(diagnostic, 'range') and hasattr(diagnostic.range, 'start'):
                    # Extract file from location if available
                    # This would need to be implemented based on how location is stored
                    pass
                
                grouped[file_uri].append(diagnostic)
            
            return dict(grouped)
            
        except Exception as e:
            logger.error(f"Failed to group diagnostics: {e}")
            return {'all': diagnostics}
    
    # Private methods
    
    def _register_builtin_sources(self) -> None:
        """Register built-in diagnostic sources"""
        try:
            if self._builtin_sources_registered:
                return
            
            # LSP diagnostics source
            if self._language_server:
                self.add_diagnostic_source("lsp", self._collect_lsp_diagnostics)
                self._sources["lsp"].priority = 10  # High priority
            
            # Tree-sitter parsing errors
            if TREE_SITTER_AVAILABLE:
                self.add_diagnostic_source("tree_sitter", self._collect_tree_sitter_diagnostics)
                self._sources["tree_sitter"].priority = 8
            
            # Static analysis (placeholder for future tools)
            self.add_diagnostic_source("static_analysis", self._collect_static_analysis_diagnostics)
            self._sources["static_analysis"].priority = 5
            
            self._builtin_sources_registered = True
            logger.info("Built-in diagnostic sources registered")
            
        except Exception as e:
            logger.error(f"Failed to register built-in sources: {e}")
    
    async def _collect_from_source(self, source: DiagnosticSource) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from a source"""
        try:
            if asyncio.iscoroutinefunction(source.collector):
                return await source.collector()
            else:
                # Run synchronous collector in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, source.collector)
                
        except Exception as e:
            logger.error(f"Failed to collect from source {source.name}: {e}")
            return []
    
    async def _collect_from_source_for_file(self, source: DiagnosticSource, file_path: str) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from a source for a specific file"""
        try:
            # For now, collect all and filter
            # In the future, sources could support file-specific collection
            all_diagnostics = await self._collect_from_source(source)
            
            # Filter diagnostics for the specific file
            file_diagnostics = []
            for diagnostic in all_diagnostics:
                # This would need to check if diagnostic is for the specific file
                # Implementation depends on how file information is stored in diagnostics
                file_diagnostics.append(diagnostic)
            
            return file_diagnostics
            
        except Exception as e:
            logger.error(f"Failed to collect from source {source.name} for file {file_path}: {e}")
            return []
    
    def _collect_lsp_diagnostics(self) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from LSP servers"""
        try:
            if not self._language_server or not self._project_manager:
                return []
            
            diagnostics = []
            project_files = self._project_manager.get_project_files()
            
            # Limit files for performance
            files_to_check = project_files[:100]  # Limit to first 100 files
            
            for file_path in files_to_check:
                try:
                    # This would need to be made async in a real implementation
                    # For now, return empty list
                    pass
                except Exception as e:
                    logger.debug(f"Failed to get LSP diagnostics for {file_path}: {e}")
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Failed to collect LSP diagnostics: {e}")
            return []
    
    def _collect_tree_sitter_diagnostics(self) -> List[UnifiedDiagnostic]:
        """Collect parsing errors from tree-sitter"""
        try:
            if not TREE_SITTER_AVAILABLE or not self._project_manager:
                return []
            
            diagnostics = []
            project_files = self._project_manager.get_project_files()
            
            for file_path in project_files:
                try:
                    # Check if file has parsing errors
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    ast_root = parse_file(file_path, content)
                    
                    if ast_root.has_error:
                        # Create diagnostic for parsing error
                        diagnostic = self._create_parsing_error_diagnostic(file_path, ast_root, content)
                        if diagnostic:
                            diagnostics.append(diagnostic)
                            
                except Exception as e:
                    logger.debug(f"Failed to check tree-sitter errors for {file_path}: {e}")
            
            return diagnostics
            
        except Exception as e:
            logger.error(f"Failed to collect tree-sitter diagnostics: {e}")
            return []
    
    def _collect_static_analysis_diagnostics(self) -> List[UnifiedDiagnostic]:
        """Collect diagnostics from static analysis tools"""
        try:
            # Placeholder for future static analysis integration
            # Could integrate tools like:
            # - Ruff for Python
            # - ESLint for JavaScript/TypeScript
            # - Clippy for Rust
            # - etc.
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to collect static analysis diagnostics: {e}")
            return []
    
    def _create_parsing_error_diagnostic(self, file_path: str, ast_root, content: str) -> Optional[UnifiedDiagnostic]:
        """Create a diagnostic for parsing errors"""
        try:
            # Find the first error node
            def find_error_node(node):
                if node.is_error or node.is_missing:
                    return node
                for child in node.children:
                    error_node = find_error_node(child)
                    if error_node:
                        return error_node
                return None
            
            error_node = find_error_node(ast_root)
            if not error_node:
                return None
            
            # Create location
            start_pos = UnifiedPosition(line=error_node.start_point[0], character=error_node.start_point[1])
            end_pos = UnifiedPosition(line=error_node.end_point[0], character=error_node.end_point[1])
            range_obj = UnifiedRange(start=start_pos, end=end_pos)
            
            location = UnifiedLocation(
                uri=f"file://{file_path}",
                range=range_obj,
                absolute_path=file_path
            )
            
            # Create diagnostic
            diagnostic = UnifiedDiagnostic(
                range=range_obj,
                severity=DiagnosticSeverity.ERROR,
                code="parse_error",
                source="tree_sitter",
                message=f"Parsing error: {error_node.type}"
            )
            
            return diagnostic
            
        except Exception as e:
            logger.error(f"Failed to create parsing error diagnostic: {e}")
            return None
    
    def _filter_diagnostics(self, diagnostics: List[UnifiedDiagnostic]) -> List[UnifiedDiagnostic]:
        """Apply configuration-based filtering to diagnostics"""
        try:
            filtered = []
            
            for diagnostic in diagnostics:
                # Check severity filter
                if not self.config.should_include_severity(diagnostic.severity.value):
                    continue
                
                # Check max diagnostics limit
                if len(filtered) >= self.config.max_diagnostics:
                    logger.warning(f"Reached max diagnostics limit ({self.config.max_diagnostics})")
                    break
                
                filtered.append(diagnostic)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to filter diagnostics: {e}")
            return diagnostics
    
    def _deduplicate_diagnostics(self, diagnostics: List[UnifiedDiagnostic]) -> List[UnifiedDiagnostic]:
        """Remove duplicate diagnostics"""
        try:
            seen = set()
            deduplicated = []
            
            for diagnostic in diagnostics:
                # Create a key for deduplication
                key = (
                    diagnostic.message,
                    diagnostic.severity.value,
                    diagnostic.code,
                    diagnostic.source,
                    diagnostic.range.start.line if diagnostic.range else None,
                    diagnostic.range.start.character if diagnostic.range else None
                )
                
                if key not in seen:
                    seen.add(key)
                    deduplicated.append(diagnostic)
            
            if len(diagnostics) != len(deduplicated):
                logger.debug(f"Deduplicated {len(diagnostics) - len(deduplicated)} duplicate diagnostics")
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"Failed to deduplicate diagnostics: {e}")
            return diagnostics
    
    def _is_cache_valid(self, file_path: str) -> bool:
        """Check if cached diagnostics are still valid"""
        try:
            if file_path not in self._cache_timestamps:
                return False
            
            cache_age = time.time() - self._cache_timestamps[file_path]
            return cache_age < self._cache_ttl
            
        except Exception as e:
            logger.error(f"Failed to check cache validity: {e}")
            return False
    
    def _get_cached_diagnostics(self, file_path: Optional[str]) -> List[UnifiedDiagnostic]:
        """Get cached diagnostics"""
        try:
            if file_path and file_path in self._diagnostic_cache:
                return self._diagnostic_cache[file_path]
            
            # Return all cached diagnostics if no specific file requested
            all_cached = []
            for diagnostics in self._diagnostic_cache.values():
                all_cached.extend(diagnostics)
            
            return all_cached
            
        except Exception as e:
            logger.error(f"Failed to get cached diagnostics: {e}")
            return []
    
    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """Clear diagnostic cache"""
        try:
            with self._lock:
                if file_path:
                    self._diagnostic_cache.pop(file_path, None)
                    self._cache_timestamps.pop(file_path, None)
                    logger.debug(f"Cleared cache for {file_path}")
                else:
                    self._diagnostic_cache.clear()
                    self._cache_timestamps.clear()
                    logger.debug("Cleared all diagnostic cache")
                    
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_collection_metrics(self) -> Dict[str, Any]:
        """Get diagnostic collection metrics"""
        try:
            with self._lock:
                return {
                    'collection_metrics': self._collection_metrics.copy(),
                    'source_metrics': dict(self._source_metrics),
                    'cache_stats': {
                        'cached_files': len(self._diagnostic_cache),
                        'cache_ttl': self._cache_ttl
                    },
                    'sources': {
                        name: {
                            'enabled': source.enabled,
                            'priority': source.priority,
                            'last_run': source.last_run,
                            'error_count': source.error_count
                        }
                        for name, source in self._sources.items()
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get collection metrics: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status"""
        return {
            'collecting': self._collecting,
            'last_collection_time': self._last_collection_time,
            'sources_count': len(self._sources),
            'enabled_sources': len([s for s in self._sources.values() if s.enabled]),
            'cached_files': len(self._diagnostic_cache),
            'config': {
                'enabled': self.config.enabled,
                'real_time': self.config.real_time,
                'max_diagnostics': self.config.max_diagnostics,
                'severity_filter': self.config.severity_filter
            }
        }
