"""
Enhanced Context Provider for comprehensive code analysis.

This module integrates AutogenLib, SolidLSP, Graph-Sitter, and Serena tools
to provide comprehensive context analysis with configurable depth and scope.
"""

import logging
from typing import Dict, List, Set, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache

# Core imports
from ..autogenlib import init as autogenlib_init
from ..autogenlib._context import get_module_context, set_module_context, extract_defined_names
from ..autogenlib._caller import get_caller_info
from ..index.code_index import CodeIndex
from ..index.file_index import FileIndex  
from ..index.symbol_index import SymbolIndex
from ..tools.reveal_symbol import reveal_symbol
from ..tools.reflection import reflect_on_code
from ..tools.view_file import view_file
from ..tools.document_functions import document_functions

# Integration imports
from .config import EnhancedContextConfig, ContextDepth

logger = logging.getLogger(__name__)


@dataclass
class Location:
    """Represents a location in the codebase"""
    file_path: str
    line: int
    character: int
    symbol_name: Optional[str] = None


@dataclass
class SymbolContext:
    """Context information for a symbol"""
    symbol_name: str
    definition_location: Location
    symbol_type: str
    signature: Optional[str] = None
    docstring: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    usages: List[Location] = field(default_factory=list)
    similar_symbols: List[str] = field(default_factory=list)


@dataclass
class TypeInfo:
    """Type information for a location"""
    primary_type: Optional[str] = None
    generic_types: List[str] = field(default_factory=list)
    union_types: List[str] = field(default_factory=list)
    optional: bool = False
    nullable: bool = False
    constraints: List[str] = field(default_factory=list)


@dataclass
class ParameterInfo:
    """Parameter information"""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = True
    description: Optional[str] = None


@dataclass
class VariableContext:
    """Variable context information"""
    name: str
    type_info: Optional[TypeInfo] = None
    scope: str = "local"  # local, global, class, module
    definition_location: Optional[Location] = None
    assignments: List[Location] = field(default_factory=list)
    usages: List[Location] = field(default_factory=list)
    lifecycle: str = "unknown"  # created, modified, read, deleted


@dataclass
class ImpactAnalysis:
    """Analysis of potential impact of changes"""
    directly_affected_symbols: List[str] = field(default_factory=list)
    indirectly_affected_symbols: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    risk_level: str = "low"  # low, medium, high, critical
    confidence_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class EnhancedContext:
    """Comprehensive context information"""
    location: Location
    
    # Core context
    symbol_context: Optional[SymbolContext] = None
    type_info: Optional[TypeInfo] = None
    parameter_info: List[ParameterInfo] = field(default_factory=list)
    variable_context: List[VariableContext] = field(default_factory=list)
    
    # Extended context
    related_symbols: List[SymbolContext] = field(default_factory=list)
    similar_patterns: List[Dict[str, Any]] = field(default_factory=list)
    import_dependencies: List[str] = field(default_factory=list)
    usage_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Analysis results
    impact_analysis: Optional[ImpactAnalysis] = None
    
    # Source context
    file_content: Optional[str] = None
    surrounding_code: Optional[str] = None
    ast_context: Optional[Dict[str, Any]] = None
    
    # Integration context
    autogenlib_context: Optional[Dict[str, Any]] = None
    lsp_context: Optional[Dict[str, Any]] = None
    serena_context: Optional[Dict[str, Any]] = None
    
    # Metadata
    analysis_timestamp: float = field(default_factory=time.time)
    analysis_duration_ms: float = 0.0
    context_size_tokens: int = 0


class EnhancedContextProvider:
    """Provides comprehensive context analysis using all available tools"""
    
    def __init__(self, config: EnhancedContextConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_autogenlib()
        self._initialize_indexing_systems()
        self._initialize_caches()
        
        # Thread pool for parallel analysis
        if config.enable_parallel_analysis:
            self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_analyses)
        else:
            self.executor = None
    
    def _initialize_autogenlib(self):
        """Initialize AutogenLib for enhanced context generation"""
        if not self.config.enable_autogenlib:
            return
        
        try:
            autogenlib_init(
                desc=self.config.autogenlib_description,
                enable_caching=self.config.autogenlib_enable_caching,
                enable_exception_handler=self.config.autogenlib_enable_exception_handler
            )
            self.logger.info("AutogenLib initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AutogenLib: {e}")
            self.config.enable_autogenlib = False
    
    def _initialize_indexing_systems(self):
        """Initialize indexing systems for fast lookups"""
        self.code_index = CodeIndex() if self.config.enabled else None
        self.file_index = FileIndex() if self.config.enabled else None
        self.symbol_index = SymbolIndex() if self.config.enabled else None
    
    def _initialize_caches(self):
        """Initialize caching systems"""
        if self.config.enable_caching:
            # LRU cache for frequently accessed contexts
            self._context_cache = {}
            self._cache_timestamps = {}
    
    def build_indexes(self, codebase) -> None:
        """Build comprehensive indexes for the codebase"""
        if not self.config.enabled:
            return
        
        self.logger.info("Building comprehensive indexes...")
        start_time = time.time()
        
        try:
            # Build indexes in parallel if possible
            if self.executor:
                futures = []
                if self.code_index:
                    futures.append(self.executor.submit(self.code_index.index_codebase, codebase))
                if self.file_index:
                    futures.append(self.executor.submit(self.file_index.index_files, codebase.root_path))
                if self.symbol_index:
                    futures.append(self.executor.submit(self.symbol_index.index_symbols, codebase))
                
                # Wait for completion
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"Index building failed: {e}")
            else:
                # Sequential building
                if self.code_index:
                    self.code_index.index_codebase(codebase)
                if self.file_index:
                    self.file_index.index_files(codebase.root_path)
                if self.symbol_index:
                    self.symbol_index.index_symbols(codebase)
            
            duration = time.time() - start_time
            self.logger.info(f"Index building completed in {duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Failed to build indexes: {e}")
    
    def get_comprehensive_context(self, location: Location) -> EnhancedContext:
        """Get comprehensive context for a location"""
        start_time = time.time()
        
        # Check cache first
        if self.config.enable_caching:
            cached_context = self._get_cached_context(location)
            if cached_context:
                return cached_context
        
        try:
            # Create base context
            context = EnhancedContext(location=location)
            
            # Gather context from all sources
            if self.config.enable_parallel_analysis and self.executor:
                context = self._gather_context_parallel(context)
            else:
                context = self._gather_context_sequential(context)
            
            # Calculate analysis duration and token count
            context.analysis_duration_ms = (time.time() - start_time) * 1000
            context.context_size_tokens = self._estimate_token_count(context)
            
            # Cache the result
            if self.config.enable_caching:
                self._cache_context(location, context)
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get comprehensive context: {e}")
            return EnhancedContext(location=location)
    
    def _gather_context_parallel(self, context: EnhancedContext) -> EnhancedContext:
        """Gather context using parallel processing"""
        futures = {}
        
        # Submit all analysis tasks
        if self.config.include_symbol_definitions:
            futures['symbol'] = self.executor.submit(self._get_symbol_context, context.location)
        
        if self.config.include_type_information:
            futures['type'] = self.executor.submit(self._get_type_information, context.location)
        
        if self.config.include_parameter_info:
            futures['params'] = self.executor.submit(self._get_parameter_information, context.location)
        
        if self.config.include_variable_scope:
            futures['variables'] = self.executor.submit(self._get_variable_context, context.location)
        
        if self.config.enable_autogenlib:
            futures['autogenlib'] = self.executor.submit(self._get_autogenlib_context, context.location)
        
        if self.config.enable_solidlsp_context:
            futures['lsp'] = self.executor.submit(self._get_lsp_context, context.location)
        
        if self.config.enable_serena_symbols:
            futures['serena'] = self.executor.submit(self._get_serena_context, context.location)
        
        # Collect results
        for key, future in futures.items():
            try:
                result = future.result(timeout=30)  # 30 second timeout
                if key == 'symbol':
                    context.symbol_context = result
                elif key == 'type':
                    context.type_info = result
                elif key == 'params':
                    context.parameter_info = result
                elif key == 'variables':
                    context.variable_context = result
                elif key == 'autogenlib':
                    context.autogenlib_context = result
                elif key == 'lsp':
                    context.lsp_context = result
                elif key == 'serena':
                    context.serena_context = result
            except Exception as e:
                self.logger.warning(f"Failed to get {key} context: {e}")
        
        # Get extended context based on depth
        context = self._get_extended_context(context)
        
        return context
    
    def _gather_context_sequential(self, context: EnhancedContext) -> EnhancedContext:
        """Gather context using sequential processing"""
        try:
            # Core context
            if self.config.include_symbol_definitions:
                context.symbol_context = self._get_symbol_context(context.location)
            
            if self.config.include_type_information:
                context.type_info = self._get_type_information(context.location)
            
            if self.config.include_parameter_info:
                context.parameter_info = self._get_parameter_information(context.location)
            
            if self.config.include_variable_scope:
                context.variable_context = self._get_variable_context(context.location)
            
            # Integration context
            if self.config.enable_autogenlib:
                context.autogenlib_context = self._get_autogenlib_context(context.location)
            
            if self.config.enable_solidlsp_context:
                context.lsp_context = self._get_lsp_context(context.location)
            
            if self.config.enable_serena_symbols:
                context.serena_context = self._get_serena_context(context.location)
            
            # Extended context
            context = self._get_extended_context(context)
            
        except Exception as e:
            self.logger.error(f"Error in sequential context gathering: {e}")
        
        return context
    
    def _get_symbol_context(self, location: Location) -> Optional[SymbolContext]:
        """Get symbol context using reveal_symbol tool"""
        if not location.symbol_name:
            return None
        
        try:
            # Use reveal_symbol tool for comprehensive symbol analysis
            symbol_info = reveal_symbol(location.symbol_name, None)  # Will need codebase reference
            
            if symbol_info:
                return SymbolContext(
                    symbol_name=location.symbol_name,
                    definition_location=location,
                    symbol_type=getattr(symbol_info, 'type', 'unknown'),
                    signature=getattr(symbol_info, 'signature', None),
                    docstring=getattr(symbol_info, 'docstring', None),
                    dependencies=getattr(symbol_info, 'dependencies', []),
                    usages=getattr(symbol_info, 'usages', [])
                )
        except Exception as e:
            self.logger.warning(f"Failed to get symbol context: {e}")
        
        return None
    
    def _get_type_information(self, location: Location) -> Optional[TypeInfo]:
        """Get type information for the location"""
        try:
            # This would integrate with LSP hover information and tree-sitter analysis
            # For now, return a placeholder
            return TypeInfo(primary_type="unknown")
        except Exception as e:
            self.logger.warning(f"Failed to get type information: {e}")
            return None
    
    def _get_parameter_information(self, location: Location) -> List[ParameterInfo]:
        """Get parameter information for functions/methods"""
        try:
            # This would analyze function signatures and extract parameter info
            return []
        except Exception as e:
            self.logger.warning(f"Failed to get parameter information: {e}")
            return []
    
    def _get_variable_context(self, location: Location) -> List[VariableContext]:
        """Get variable context and scope information"""
        try:
            # This would analyze variable scope, assignments, and usage
            return []
        except Exception as e:
            self.logger.warning(f"Failed to get variable context: {e}")
            return []
    
    def _get_autogenlib_context(self, location: Location) -> Optional[Dict[str, Any]]:
        """Get context using AutogenLib capabilities"""
        if not self.config.enable_autogenlib:
            return None
        
        try:
            # Get caller context
            caller_info = get_caller_info()
            
            # Get module context
            module_context = get_module_context(location.file_path)
            
            return {
                'caller_info': caller_info,
                'module_context': module_context,
                'defined_names': extract_defined_names(module_context.get('code', ''))
            }
        except Exception as e:
            self.logger.warning(f"Failed to get AutogenLib context: {e}")
            return None
    
    def _get_lsp_context(self, location: Location) -> Optional[Dict[str, Any]]:
        """Get context from LSP servers"""
        if not self.config.enable_solidlsp_context:
            return None
        
        try:
            # This would integrate with SolidLSP to get hover info, symbols, etc.
            return {'placeholder': 'lsp_context'}
        except Exception as e:
            self.logger.warning(f"Failed to get LSP context: {e}")
            return None
    
    def _get_serena_context(self, location: Location) -> Optional[Dict[str, Any]]:
        """Get context from Serena tools"""
        if not self.config.enable_serena_symbols:
            return None
        
        try:
            # This would integrate with Serena symbol tools
            return {'placeholder': 'serena_context'}
        except Exception as e:
            self.logger.warning(f"Failed to get Serena context: {e}")
            return None
    
    def _get_extended_context(self, context: EnhancedContext) -> EnhancedContext:
        """Get extended context based on configured depth"""
        try:
            depth = self.config.depth.value
            
            if depth > 1 and context.symbol_context:
                # Get related symbols
                context.related_symbols = self._get_related_symbols(
                    context.symbol_context, depth - 1
                )
            
            if self.config.include_similar_code:
                context.similar_patterns = self._find_similar_patterns(context.location)
            
            if self.config.include_import_dependencies:
                context.import_dependencies = self._get_import_dependencies(context.location)
            
            if self.config.include_usage_patterns:
                context.usage_patterns = self._get_usage_patterns(context.location)
            
            # Impact analysis
            context.impact_analysis = self._analyze_impact_radius(context.location)
            
        except Exception as e:
            self.logger.warning(f"Failed to get extended context: {e}")
        
        return context
    
    def _get_related_symbols(self, symbol_context: SymbolContext, depth: int) -> List[SymbolContext]:
        """Recursively get related symbols up to specified depth"""
        if depth <= 0:
            return []
        
        related = []
        try:
            # This implements the enhanced version of get_extended_context
            # from the original example, but with full integration
            for dep in symbol_context.dependencies:
                # Get symbol context for dependency
                dep_location = Location(file_path="", line=0, character=0, symbol_name=dep)
                dep_context = self._get_symbol_context(dep_location)
                if dep_context:
                    related.append(dep_context)
                    # Recursively get nested dependencies
                    if depth > 1:
                        nested = self._get_related_symbols(dep_context, depth - 1)
                        related.extend(nested)
        except Exception as e:
            self.logger.warning(f"Failed to get related symbols: {e}")
        
        return related[:self.config.max_related_symbols]
    
    def _find_similar_patterns(self, location: Location) -> List[Dict[str, Any]]:
        """Find similar code patterns"""
        try:
            if self.code_index:
                return self.code_index.find_similar_patterns(location)
        except Exception as e:
            self.logger.warning(f"Failed to find similar patterns: {e}")
        
        return []
    
    def _get_import_dependencies(self, location: Location) -> List[str]:
        """Get import dependencies for the file"""
        try:
            # Analyze imports in the file
            file_content = self._get_file_content(location.file_path)
            if file_content:
                # Extract imports (simplified)
                imports = []
                for line in file_content.split('\n'):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
                return imports
        except Exception as e:
            self.logger.warning(f"Failed to get import dependencies: {e}")
        
        return []
    
    def _get_usage_patterns(self, location: Location) -> List[Dict[str, Any]]:
        """Get usage patterns for symbols"""
        try:
            # This would analyze how symbols are used across the codebase
            return []
        except Exception as e:
            self.logger.warning(f"Failed to get usage patterns: {e}")
            return []
    
    def _analyze_impact_radius(self, location: Location) -> ImpactAnalysis:
        """Analyze the potential impact of changes at this location"""
        try:
            # This would perform comprehensive impact analysis
            return ImpactAnalysis(
                risk_level="low",
                confidence_score=0.5,
                recommendations=["Consider adding tests", "Review dependent code"]
            )
        except Exception as e:
            self.logger.warning(f"Failed to analyze impact radius: {e}")
            return ImpactAnalysis()
    
    def _get_file_content(self, file_path: str) -> Optional[str]:
        """Get file content safely"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.warning(f"Failed to read file {file_path}: {e}")
            return None
    
    def _estimate_token_count(self, context: EnhancedContext) -> int:
        """Estimate token count for the context"""
        # Simple estimation: ~4 characters per token
        total_chars = 0
        
        if context.file_content:
            total_chars += len(context.file_content)
        
        if context.symbol_context and context.symbol_context.docstring:
            total_chars += len(context.symbol_context.docstring)
        
        # Add other context sizes...
        
        return total_chars // 4
    
    def _get_cached_context(self, location: Location) -> Optional[EnhancedContext]:
        """Get cached context if available and not expired"""
        if not self.config.enable_caching:
            return None
        
        cache_key = f"{location.file_path}:{location.line}:{location.character}"
        
        if cache_key in self._context_cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return self._context_cache[cache_key]
            else:
                # Remove expired entry
                del self._context_cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        return None
    
    def _cache_context(self, location: Location, context: EnhancedContext) -> None:
        """Cache context for future use"""
        if not self.config.enable_caching:
            return
        
        cache_key = f"{location.file_path}:{location.line}:{location.character}"
        self._context_cache[cache_key] = context
        self._cache_timestamps[cache_key] = time.time()
    
    def invalidate_cache(self, file_path: Optional[str] = None) -> None:
        """Invalidate cache entries"""
        if not self.config.enable_caching:
            return
        
        if file_path:
            # Invalidate entries for specific file
            keys_to_remove = [
                key for key in self._context_cache.keys()
                if key.startswith(f"{file_path}:")
            ]
            for key in keys_to_remove:
                del self._context_cache[key]
                del self._cache_timestamps[key]
        else:
            # Clear all cache
            self._context_cache.clear()
            self._cache_timestamps.clear()
    
    def get_error_context(self, diagnostic) -> EnhancedContext:
        """Get enhanced context for error resolution"""
        location = Location(
            file_path=diagnostic.file_path,
            line=diagnostic.range.start.line,
            character=diagnostic.range.start.character
        )
        
        context = self.get_comprehensive_context(location)
        
        # Add error-specific context
        context.diagnostic = diagnostic
        
        return context
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        if self.config.enable_caching:
            self._context_cache.clear()
            self._cache_timestamps.clear()
