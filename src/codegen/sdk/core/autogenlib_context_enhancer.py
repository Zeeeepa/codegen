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
AutogenLib Context Enhancement

This module integrates AutogenLib capabilities to provide enhanced context
for error resolution, including comprehensive type information, variable
definitions, and impact radius analysis.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
import threading
import time
from dataclasses import dataclass, field

from .integration_interfaces import (
    IContextEnhancer, UnifiedDiagnostic, UnifiedSymbol, UnifiedLocation,
    UnifiedRange, UnifiedPosition, DiagnosticSeverity, SymbolKind
)
from .unified_config import UnifiedConfiguration

# AutogenLib imports
try:
    from autogenlib import AutogenLib
    from autogenlib.context import ContextAnalyzer, ContextScope
    from autogenlib.types import TypeInferencer, TypeDefinition
    from autogenlib.impact import ImpactAnalyzer, ImpactRadius
    from autogenlib.symbols import SymbolResolver, SymbolDefinition
    AUTOGENLIB_AVAILABLE = True
except ImportError:
    AUTOGENLIB_AVAILABLE = False
    AutogenLib = None
    ContextAnalyzer = None
    ContextScope = None
    TypeInferencer = None
    TypeDefinition = None
    ImpactAnalyzer = None
    ImpactRadius = None
    SymbolResolver = None
    SymbolDefinition = None

logger = logging.getLogger(__name__)


@dataclass
class EnhancedContext:
    """Enhanced context information for error resolution"""
    diagnostic: UnifiedDiagnostic
    symbol_definitions: List[Dict[str, Any]] = field(default_factory=list)
    type_information: Dict[str, Any] = field(default_factory=dict)
    variable_definitions: List[Dict[str, Any]] = field(default_factory=list)
    function_signatures: List[Dict[str, Any]] = field(default_factory=list)
    import_dependencies: List[Dict[str, Any]] = field(default_factory=list)
    impact_radius: Dict[str, Any] = field(default_factory=dict)
    related_errors: List[UnifiedDiagnostic] = field(default_factory=list)
    suggested_fixes: List[Dict[str, Any]] = field(default_factory=list)
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextScope:
    """Represents a scope for context analysis"""
    file_path: str
    start_line: int
    end_line: int
    scope_type: str  # 'function', 'class', 'module', 'block'
    parent_scope: Optional['ContextScope'] = None
    symbols: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


class AutogenLibContextEnhancer(IContextEnhancer):
    """
    Context enhancer that uses AutogenLib to provide comprehensive context
    information for error resolution and code analysis.
    
    This enhancer provides:
    - Type information and inference
    - Variable and function definitions
    - Import dependency analysis
    - Impact radius calculation
    - Related error detection
    - Automated fix suggestions
    """
    
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # AutogenLib components
        self._autogenlib: Optional[AutogenLib] = None
        self._context_analyzer: Optional[ContextAnalyzer] = None
        self._type_inferencer: Optional[TypeInferencer] = None
        self._impact_analyzer: Optional[ImpactAnalyzer] = None
        self._symbol_resolver: Optional[SymbolResolver] = None
        
        # Component dependencies (injected)
        self._language_server = None
        self._project_manager = None
        self._diagnostic_collector = None
        
        # Context cache
        self._context_cache: Dict[str, EnhancedContext] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 60.0  # Cache TTL in seconds
        
        # State management
        self._lock = threading.RLock()
        self._initialized = False
        
        # Performance tracking
        self._enhancement_metrics: Dict[str, Any] = {}
        
        if not AUTOGENLIB_AVAILABLE:
            logger.warning("AutogenLib is not available - enhanced context will be limited")
        
        logger.info("AutogenLib context enhancer initialized")
    
    def set_language_server(self, language_server):
        """Inject language server dependency"""
        self._language_server = language_server
    
    def set_project_manager(self, project_manager):
        """Inject project manager dependency"""
        self._project_manager = project_manager
    
    def set_diagnostic_collector(self, diagnostic_collector):
        """Inject diagnostic collector dependency"""
        self._diagnostic_collector = diagnostic_collector
    
    def initialize(self, project_root: str) -> bool:
        """Initialize the context enhancer"""
        try:
            with self._lock:
                if self._initialized:
                    logger.debug("Context enhancer already initialized")
                    return True
                
                logger.info(f"Initializing AutogenLib context enhancer for {project_root}")
                
                self.project_root = project_root
                
                if not AUTOGENLIB_AVAILABLE:
                    logger.warning("AutogenLib not available - using fallback implementation")
                    self._initialized = True
                    return True
                
                # Initialize AutogenLib
                try:
                    self._autogenlib = AutogenLib(project_root=project_root)
                    
                    # Initialize components
                    self._context_analyzer = ContextAnalyzer(self._autogenlib)
                    self._type_inferencer = TypeInferencer(self._autogenlib)
                    self._impact_analyzer = ImpactAnalyzer(self._autogenlib)
                    self._symbol_resolver = SymbolResolver(self._autogenlib)
                    
                    self._initialized = True
                    logger.info("AutogenLib context enhancer initialized successfully")
                    return True
                    
                except Exception as e:
                    logger.error(f"Failed to initialize AutogenLib: {e}")
                    self._initialized = True  # Use fallback
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to initialize context enhancer: {e}")
            return False
    
    async def enhance_context(self, diagnostic: UnifiedDiagnostic, file_path: str) -> EnhancedContext:
        """Enhance context for a diagnostic"""
        try:
            start_time = time.time()
            
            # Check cache first
            cache_key = self._get_cache_key(diagnostic, file_path)
            if self._is_cache_valid(cache_key):
                logger.debug(f"Using cached enhanced context for {cache_key}")
                return self._context_cache[cache_key]
            
            logger.debug(f"Enhancing context for diagnostic in {file_path}")
            
            # Create enhanced context
            enhanced_context = EnhancedContext(diagnostic=diagnostic)
            
            if not self._initialized:
                logger.warning("Context enhancer not initialized")
                return enhanced_context
            
            # Enhance context using AutogenLib
            if AUTOGENLIB_AVAILABLE and self._autogenlib:
                await self._enhance_with_autogenlib(enhanced_context, file_path)
            else:
                await self._enhance_with_fallback(enhanced_context, file_path)
            
            # Calculate confidence score
            enhanced_context.confidence_score = self._calculate_confidence_score(enhanced_context)
            
            # Update cache
            self._context_cache[cache_key] = enhanced_context
            self._cache_timestamps[cache_key] = time.time()
            
            # Update metrics
            enhancement_time = time.time() - start_time
            self._enhancement_metrics[cache_key] = {
                'enhancement_time': enhancement_time,
                'symbol_definitions_count': len(enhanced_context.symbol_definitions),
                'type_information_count': len(enhanced_context.type_information),
                'impact_radius_size': len(enhanced_context.impact_radius.get('affected_files', [])),
                'suggested_fixes_count': len(enhanced_context.suggested_fixes),
                'confidence_score': enhanced_context.confidence_score,
                'timestamp': time.time()
            }
            
            logger.debug(f"Enhanced context in {enhancement_time:.3f}s with confidence {enhanced_context.confidence_score:.2f}")
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Failed to enhance context for diagnostic: {e}")
            return EnhancedContext(diagnostic=diagnostic)
    
    async def get_impact_radius(self, file_path: str, position: UnifiedPosition) -> Dict[str, Any]:
        """Get impact radius for a change at a specific position"""
        try:
            if not self._initialized or not AUTOGENLIB_AVAILABLE or not self._impact_analyzer:
                return self._get_fallback_impact_radius(file_path, position)
            
            # Use AutogenLib impact analysis
            impact_result = await self._impact_analyzer.analyze_impact(
                file_path=file_path,
                line=position.line,
                column=position.character
            )
            
            return {
                'affected_files': impact_result.affected_files,
                'affected_symbols': impact_result.affected_symbols,
                'impact_score': impact_result.impact_score,
                'change_type': impact_result.change_type,
                'propagation_depth': impact_result.propagation_depth
            }
            
        except Exception as e:
            logger.error(f"Failed to get impact radius: {e}")
            return self._get_fallback_impact_radius(file_path, position)
    
    async def get_symbol_context(self, symbol: UnifiedSymbol) -> Dict[str, Any]:
        """Get comprehensive context for a symbol"""
        try:
            if not self._initialized or not AUTOGENLIB_AVAILABLE or not self._symbol_resolver:
                return self._get_fallback_symbol_context(symbol)
            
            # Use AutogenLib symbol resolution
            symbol_definition = await self._symbol_resolver.resolve_symbol(
                name=symbol.name,
                file_path=symbol.location.absolute_path if symbol.location else None,
                line=symbol.location.range.start.line if symbol.location else None
            )
            
            return {
                'definition': {
                    'file_path': symbol_definition.file_path,
                    'line': symbol_definition.line,
                    'column': symbol_definition.column,
                    'signature': symbol_definition.signature,
                    'docstring': symbol_definition.docstring
                },
                'type_information': {
                    'type_name': symbol_definition.type_name,
                    'type_parameters': symbol_definition.type_parameters,
                    'return_type': symbol_definition.return_type,
                    'parameter_types': symbol_definition.parameter_types
                },
                'references': [
                    {
                        'file_path': ref.file_path,
                        'line': ref.line,
                        'column': ref.column,
                        'context': ref.context
                    }
                    for ref in symbol_definition.references
                ],
                'scope': {
                    'scope_type': symbol_definition.scope.scope_type,
                    'parent_scope': symbol_definition.scope.parent_scope,
                    'local_variables': symbol_definition.scope.local_variables
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get symbol context: {e}")
            return self._get_fallback_symbol_context(symbol)
    
    async def suggest_fixes(self, diagnostic: UnifiedDiagnostic, enhanced_context: EnhancedContext) -> List[Dict[str, Any]]:
        """Suggest fixes for a diagnostic based on enhanced context"""
        try:
            fixes = []
            
            # Use AutogenLib for fix suggestions if available
            if AUTOGENLIB_AVAILABLE and self._autogenlib:
                fixes.extend(await self._suggest_fixes_with_autogenlib(diagnostic, enhanced_context))
            
            # Add fallback fix suggestions
            fixes.extend(self._suggest_fixes_fallback(diagnostic, enhanced_context))
            
            # Sort by confidence score
            fixes.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
            
            return fixes[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest fixes: {e}")
            return []
    
    # Private methods
    
    async def _enhance_with_autogenlib(self, enhanced_context: EnhancedContext, file_path: str) -> None:
        """Enhance context using AutogenLib"""
        try:
            diagnostic = enhanced_context.diagnostic
            
            # Get context scope
            if diagnostic.range:
                scope = await self._context_analyzer.analyze_scope(
                    file_path=file_path,
                    line=diagnostic.range.start.line,
                    column=diagnostic.range.start.character
                )
                
                # Get symbol definitions in scope
                enhanced_context.symbol_definitions = [
                    {
                        'name': symbol.name,
                        'type': symbol.type,
                        'definition_location': {
                            'file_path': symbol.file_path,
                            'line': symbol.line,
                            'column': symbol.column
                        },
                        'signature': symbol.signature,
                        'docstring': symbol.docstring
                    }
                    for symbol in scope.symbols
                ]
                
                # Get type information
                if self._type_inferencer:
                    type_info = await self._type_inferencer.infer_types_at_position(
                        file_path=file_path,
                        line=diagnostic.range.start.line,
                        column=diagnostic.range.start.character
                    )
                    
                    enhanced_context.type_information = {
                        'inferred_types': type_info.inferred_types,
                        'type_constraints': type_info.type_constraints,
                        'type_errors': type_info.type_errors
                    }
                
                # Get impact radius
                if self._impact_analyzer:
                    impact = await self._impact_analyzer.analyze_impact(
                        file_path=file_path,
                        line=diagnostic.range.start.line,
                        column=diagnostic.range.start.character
                    )
                    
                    enhanced_context.impact_radius = {
                        'affected_files': impact.affected_files,
                        'affected_symbols': impact.affected_symbols,
                        'impact_score': impact.impact_score,
                        'propagation_depth': impact.propagation_depth
                    }
            
        except Exception as e:
            logger.error(f"Failed to enhance context with AutogenLib: {e}")
    
    async def _enhance_with_fallback(self, enhanced_context: EnhancedContext, file_path: str) -> None:
        """Enhance context using fallback implementation"""
        try:
            # Basic context enhancement without AutogenLib
            diagnostic = enhanced_context.diagnostic
            
            # Read file content for basic analysis
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                if diagnostic.range:
                    line_num = diagnostic.range.start.line
                    if 0 <= line_num < len(lines):
                        error_line = lines[line_num]
                        
                        # Basic symbol extraction
                        enhanced_context.symbol_definitions = self._extract_symbols_from_line(error_line, line_num)
                        
                        # Basic type information
                        enhanced_context.type_information = self._extract_type_info_from_line(error_line)
                        
                        # Basic impact analysis
                        enhanced_context.impact_radius = {
                            'affected_files': [file_path],
                            'impact_score': 0.5,
                            'propagation_depth': 1
                        }
                        
            except Exception as e:
                logger.debug(f"Failed to read file for fallback enhancement: {e}")
            
        except Exception as e:
            logger.error(f"Failed to enhance context with fallback: {e}")
    
    async def _suggest_fixes_with_autogenlib(self, diagnostic: UnifiedDiagnostic, enhanced_context: EnhancedContext) -> List[Dict[str, Any]]:
        """Suggest fixes using AutogenLib"""
        try:
            # This would use AutogenLib's fix suggestion capabilities
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Failed to suggest fixes with AutogenLib: {e}")
            return []
    
    def _suggest_fixes_fallback(self, diagnostic: UnifiedDiagnostic, enhanced_context: EnhancedContext) -> List[Dict[str, Any]]:
        """Suggest fixes using fallback implementation"""
        try:
            fixes = []
            
            # Basic fix suggestions based on diagnostic message
            message = diagnostic.message.lower()
            
            if "undefined" in message or "not defined" in message:
                fixes.append({
                    'title': 'Add import statement',
                    'description': 'Import the undefined symbol',
                    'confidence': 0.7,
                    'fix_type': 'import',
                    'suggested_code': '# Add appropriate import statement'
                })
            
            if "type" in message and "error" in message:
                fixes.append({
                    'title': 'Fix type annotation',
                    'description': 'Correct the type annotation',
                    'confidence': 0.6,
                    'fix_type': 'type_annotation',
                    'suggested_code': '# Fix type annotation'
                })
            
            if "syntax" in message:
                fixes.append({
                    'title': 'Fix syntax error',
                    'description': 'Correct the syntax error',
                    'confidence': 0.8,
                    'fix_type': 'syntax',
                    'suggested_code': '# Fix syntax error'
                })
            
            return fixes
            
        except Exception as e:
            logger.error(f"Failed to suggest fallback fixes: {e}")
            return []
    
    def _extract_symbols_from_line(self, line: str, line_num: int) -> List[Dict[str, Any]]:
        """Extract symbols from a line of code (fallback implementation)"""
        try:
            symbols = []
            
            # Basic symbol extraction using simple patterns
            import re
            
            # Function definitions
            func_match = re.search(r'def\s+(\w+)\s*\(', line)
            if func_match:
                symbols.append({
                    'name': func_match.group(1),
                    'type': 'function',
                    'line': line_num,
                    'signature': line.strip()
                })
            
            # Class definitions
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                symbols.append({
                    'name': class_match.group(1),
                    'type': 'class',
                    'line': line_num,
                    'signature': line.strip()
                })
            
            # Variable assignments
            var_matches = re.findall(r'(\w+)\s*=', line)
            for var_name in var_matches:
                symbols.append({
                    'name': var_name,
                    'type': 'variable',
                    'line': line_num,
                    'signature': line.strip()
                })
            
            return symbols
            
        except Exception as e:
            logger.debug(f"Failed to extract symbols from line: {e}")
            return []
    
    def _extract_type_info_from_line(self, line: str) -> Dict[str, Any]:
        """Extract type information from a line (fallback implementation)"""
        try:
            type_info = {}
            
            # Look for type annotations
            import re
            
            # Function type annotations
            func_annotation = re.search(r'def\s+\w+\([^)]*\)\s*->\s*([^:]+):', line)
            if func_annotation:
                type_info['return_type'] = func_annotation.group(1).strip()
            
            # Variable type annotations
            var_annotation = re.search(r'(\w+)\s*:\s*([^=]+)', line)
            if var_annotation:
                type_info['variable_types'] = {
                    var_annotation.group(1): var_annotation.group(2).strip()
                }
            
            return type_info
            
        except Exception as e:
            logger.debug(f"Failed to extract type info from line: {e}")
            return {}
    
    def _get_fallback_impact_radius(self, file_path: str, position: UnifiedPosition) -> Dict[str, Any]:
        """Get fallback impact radius"""
        return {
            'affected_files': [file_path],
            'affected_symbols': [],
            'impact_score': 0.3,
            'change_type': 'unknown',
            'propagation_depth': 1
        }
    
    def _get_fallback_symbol_context(self, symbol: UnifiedSymbol) -> Dict[str, Any]:
        """Get fallback symbol context"""
        return {
            'definition': {
                'file_path': symbol.location.absolute_path if symbol.location else None,
                'line': symbol.location.range.start.line if symbol.location else None,
                'signature': symbol.name
            },
            'type_information': {
                'type_name': symbol.kind.value
            },
            'references': [],
            'scope': {
                'scope_type': 'unknown'
            }
        }
    
    def _calculate_confidence_score(self, enhanced_context: EnhancedContext) -> float:
        """Calculate confidence score for enhanced context"""
        try:
            score = 0.0
            
            # Base score
            score += 0.2
            
            # Symbol definitions boost confidence
            if enhanced_context.symbol_definitions:
                score += min(0.3, len(enhanced_context.symbol_definitions) * 0.1)
            
            # Type information boosts confidence
            if enhanced_context.type_information:
                score += 0.2
            
            # Impact radius boosts confidence
            if enhanced_context.impact_radius:
                score += 0.2
            
            # Suggested fixes boost confidence
            if enhanced_context.suggested_fixes:
                score += min(0.1, len(enhanced_context.suggested_fixes) * 0.02)
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {e}")
            return 0.0
    
    def _get_cache_key(self, diagnostic: UnifiedDiagnostic, file_path: str) -> str:
        """Generate cache key for diagnostic"""
        return f"{file_path}:{diagnostic.range.start.line if diagnostic.range else 0}:{diagnostic.message[:50]}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached context is still valid"""
        try:
            if cache_key not in self._cache_timestamps:
                return False
            
            cache_age = time.time() - self._cache_timestamps[cache_key]
            return cache_age < self._cache_ttl and cache_key in self._context_cache
            
        except Exception as e:
            logger.error(f"Failed to check cache validity: {e}")
            return False
    
    def clear_cache(self, file_path: Optional[str] = None) -> None:
        """Clear context cache"""
        try:
            with self._lock:
                if file_path:
                    # Clear cache for specific file
                    keys_to_remove = [k for k in self._context_cache.keys() if k.startswith(file_path)]
                    for key in keys_to_remove:
                        self._context_cache.pop(key, None)
                        self._cache_timestamps.pop(key, None)
                    logger.debug(f"Cleared cache for {file_path}")
                else:
                    # Clear all cache
                    self._context_cache.clear()
                    self._cache_timestamps.clear()
                    logger.debug("Cleared all context cache")
                    
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_enhancement_metrics(self) -> Dict[str, Any]:
        """Get context enhancement metrics"""
        try:
            with self._lock:
                return {
                    'initialized': self._initialized,
                    'autogenlib_available': AUTOGENLIB_AVAILABLE,
                    'cached_contexts': len(self._context_cache),
                    'cache_ttl': self._cache_ttl,
                    'enhancement_metrics': dict(self._enhancement_metrics)
                }
                
        except Exception as e:
            logger.error(f"Failed to get enhancement metrics: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get enhancer status"""
        return {
            'initialized': self._initialized,
            'project_root': self.project_root,
            'autogenlib_available': AUTOGENLIB_AVAILABLE,
            'autogenlib_initialized': self._autogenlib is not None,
            'cached_contexts': len(self._context_cache),
            'config': {
                'enhancedcontext': self.config.enhancedcontext,
                'cache_ttl': self._cache_ttl
            }
        }
