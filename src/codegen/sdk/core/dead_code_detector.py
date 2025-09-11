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
Dead Code Detection System

This module provides comprehensive dead code detection with reachability analysis,
unused symbol identification, and safe removal suggestions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union, Tuple
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

from .integration_interfaces import (
    IDeadCodeDetector, UnifiedSymbol, UnifiedLocation, UnifiedRange, 
    UnifiedPosition, SymbolKind
)
from .unified_config import UnifiedConfiguration

logger = logging.getLogger(__name__)


class DeadCodeType(Enum):
    """Types of dead code"""
    UNUSED_FUNCTION = "unused_function"
    UNUSED_CLASS = "unused_class"
    UNUSED_VARIABLE = "unused_variable"
    UNUSED_IMPORT = "unused_import"
    UNREACHABLE_CODE = "unreachable_code"
    DUPLICATE_CODE = "duplicate_code"
    EMPTY_FUNCTION = "empty_function"
    COMMENTED_CODE = "commented_code"


@dataclass
class DeadCodeItem:
    """Represents a piece of dead code"""
    code_type: DeadCodeType
    symbol_name: str
    file_path: str
    location: UnifiedLocation
    confidence: float
    reason: str
    impact_score: float = 0.0
    safe_to_remove: bool = False
    references: List[UnifiedLocation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReachabilityGraph:
    """Graph representing code reachability"""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    entry_points: Set[str] = field(default_factory=set)
    reachable_nodes: Set[str] = field(default_factory=set)


class DeadCodeDetector(IDeadCodeDetector):
    """
    Comprehensive dead code detector that identifies unused code through
    reachability analysis and symbol usage tracking.
    """
    
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # Component dependencies
        self._language_server = None
        self._project_manager = None
        self._graph_builder = None
        
        # Detection state
        self._reachability_graph: Optional[ReachabilityGraph] = None
        self._symbol_usage: Dict[str, Set[str]] = {}
        self._entry_points: Set[str] = set()
        
        # State management
        self._lock = threading.RLock()
        self._initialized = False
        
        # Performance tracking
        self._detection_metrics: Dict[str, Any] = {}
        
        logger.info("Dead code detector initialized")
    
    def set_language_server(self, language_server):
        """Inject language server dependency"""
        self._language_server = language_server
    
    def set_project_manager(self, project_manager):
        """Inject project manager dependency"""
        self._project_manager = project_manager
    
    def set_graph_builder(self, graph_builder):
        """Inject graph builder dependency"""
        self._graph_builder = graph_builder
    
    def initialize(self, project_root: str) -> bool:
        """Initialize the dead code detector"""
        try:
            with self._lock:
                if self._initialized:
                    return True
                
                self.project_root = project_root
                self._initialized = True
                
                # Initialize entry points
                self._initialize_entry_points()
                
                logger.info(f"Dead code detector initialized for {project_root}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize dead code detector: {e}")
            return False
    
    async def detect_dead_code(self, file_paths: Optional[List[str]] = None) -> List[DeadCodeItem]:
        """Detect dead code in the project or specific files"""
        try:
            start_time = time.time()
            
            if not self._initialized:
                logger.warning("Dead code detector not initialized")
                return []
            
            # Get files to analyze
            if file_paths is None:
                if not self._project_manager:
                    return []
                file_paths = self._project_manager.get_project_files()
            
            logger.info(f"Analyzing {len(file_paths)} files for dead code")
            
            # Build reachability graph
            await self._build_reachability_graph(file_paths)
            
            # Detect different types of dead code
            dead_code_items = []
            
            # Detect unused symbols
            unused_symbols = await self._detect_unused_symbols(file_paths)
            dead_code_items.extend(unused_symbols)
            
            # Detect unreachable code
            unreachable_code = await self._detect_unreachable_code(file_paths)
            dead_code_items.extend(unreachable_code)
            
            # Detect unused imports
            unused_imports = await self._detect_unused_imports(file_paths)
            dead_code_items.extend(unused_imports)
            
            # Detect empty functions
            empty_functions = await self._detect_empty_functions(file_paths)
            dead_code_items.extend(empty_functions)
            
            # Detect commented code
            commented_code = await self._detect_commented_code(file_paths)
            dead_code_items.extend(commented_code)
            
            # Sort by confidence and impact
            dead_code_items.sort(key=lambda x: (x.confidence, x.impact_score), reverse=True)
            
            # Update metrics
            detection_time = time.time() - start_time
            self._update_detection_metrics(dead_code_items, detection_time)
            
            logger.info(f"Found {len(dead_code_items)} dead code items in {detection_time:.2f}s")
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect dead code: {e}")
            return []
    
    async def analyze_symbol_usage(self, symbol: UnifiedSymbol) -> Dict[str, Any]:
        """Analyze usage of a specific symbol"""
        try:
            if not self._language_server:
                return {}
            
            # Get references to the symbol
            references = await self._language_server.get_references(
                symbol.location.absolute_path,
                symbol.location.range.start
            )
            
            # Analyze usage patterns
            usage_analysis = {
                'symbol_name': symbol.name,
                'symbol_kind': symbol.kind.value,
                'total_references': len(references),
                'reference_locations': [
                    {
                        'file_path': ref.absolute_path,
                        'line': ref.range.start.line,
                        'column': ref.range.start.character
                    }
                    for ref in references
                ],
                'is_used': len(references) > 1,  # More than just the definition
                'usage_files': list(set(ref.absolute_path for ref in references)),
                'is_public': not symbol.name.startswith('_'),
                'is_entry_point': self._is_entry_point(symbol)
            }
            
            return usage_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze symbol usage: {e}")
            return {}
    
    def get_reachability_info(self, symbol_name: str) -> Dict[str, Any]:
        """Get reachability information for a symbol"""
        try:
            if not self._reachability_graph:
                return {}
            
            return {
                'is_reachable': symbol_name in self._reachability_graph.reachable_nodes,
                'is_entry_point': symbol_name in self._reachability_graph.entry_points,
                'dependencies': self._reachability_graph.edges.get(symbol_name, []),
                'dependents': [
                    node for node, deps in self._reachability_graph.edges.items()
                    if symbol_name in deps
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get reachability info: {e}")
            return {}
    
    # Private methods
    
    def _initialize_entry_points(self) -> None:
        """Initialize entry points for reachability analysis"""
        try:
            # Common entry point patterns
            self._entry_points = {
                'main',
                '__main__',
                'if __name__ == "__main__"',
                'app',
                'run',
                'start',
                'init',
                '__init__',
                'setup',
                'test_',
                'Test'
            }
            
            logger.debug(f"Initialized {len(self._entry_points)} entry point patterns")
            
        except Exception as e:
            logger.error(f"Failed to initialize entry points: {e}")
    
    async def _build_reachability_graph(self, file_paths: List[str]) -> None:
        """Build reachability graph for the codebase"""
        try:
            self._reachability_graph = ReachabilityGraph()
            
            # Get all symbols
            all_symbols = []
            if self._language_server:
                for file_path in file_paths:
                    try:
                        symbols = await self._language_server.get_symbols(file_path)
                        all_symbols.extend(symbols)
                    except Exception as e:
                        logger.debug(f"Failed to get symbols for {file_path}: {e}")
            
            # Build nodes
            for symbol in all_symbols:
                node_id = f"{symbol.location.absolute_path}:{symbol.name}"
                self._reachability_graph.nodes[node_id] = {
                    'symbol': symbol,
                    'file_path': symbol.location.absolute_path,
                    'name': symbol.name,
                    'kind': symbol.kind.value
                }
                
                # Check if it's an entry point
                if self._is_entry_point(symbol):
                    self._reachability_graph.entry_points.add(node_id)
            
            # Build edges (simplified - would need more sophisticated analysis)
            await self._build_dependency_edges(all_symbols)
            
            # Calculate reachability
            self._calculate_reachability()
            
            logger.debug(f"Built reachability graph with {len(self._reachability_graph.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Failed to build reachability graph: {e}")
    
    async def _build_dependency_edges(self, symbols: List[UnifiedSymbol]) -> None:
        """Build dependency edges between symbols"""
        try:
            if not self._language_server:
                return
            
            for symbol in symbols:
                node_id = f"{symbol.location.absolute_path}:{symbol.name}"
                self._reachability_graph.edges[node_id] = []
                
                try:
                    # Get references to find dependencies
                    references = await self._language_server.get_references(
                        symbol.location.absolute_path,
                        symbol.location.range.start
                    )
                    
                    for ref in references:
                        # Find symbol at reference location
                        ref_symbols = await self._language_server.get_symbols(ref.absolute_path)
                        for ref_symbol in ref_symbols:
                            if (ref_symbol.location.range.start.line <= ref.range.start.line <= 
                                ref_symbol.location.range.end.line):
                                ref_node_id = f"{ref.absolute_path}:{ref_symbol.name}"
                                if ref_node_id != node_id and ref_node_id in self._reachability_graph.nodes:
                                    self._reachability_graph.edges[node_id].append(ref_node_id)
                                break
                                
                except Exception as e:
                    logger.debug(f"Failed to build edges for {symbol.name}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to build dependency edges: {e}")
    
    def _calculate_reachability(self) -> None:
        """Calculate reachable nodes from entry points"""
        try:
            if not self._reachability_graph:
                return
            
            # DFS from entry points
            visited = set()
            
            def dfs(node_id: str):
                if node_id in visited or node_id not in self._reachability_graph.nodes:
                    return
                
                visited.add(node_id)
                self._reachability_graph.reachable_nodes.add(node_id)
                
                for dependency in self._reachability_graph.edges.get(node_id, []):
                    dfs(dependency)
            
            # Start DFS from all entry points
            for entry_point in self._reachability_graph.entry_points:
                dfs(entry_point)
            
            logger.debug(f"Found {len(self._reachability_graph.reachable_nodes)} reachable nodes")
            
        except Exception as e:
            logger.error(f"Failed to calculate reachability: {e}")
    
    async def _detect_unused_symbols(self, file_paths: List[str]) -> List[DeadCodeItem]:
        """Detect unused symbols"""
        try:
            dead_code_items = []
            
            if not self._reachability_graph:
                return dead_code_items
            
            for node_id, node_info in self._reachability_graph.nodes.items():
                if node_id not in self._reachability_graph.reachable_nodes:
                    symbol = node_info['symbol']
                    
                    # Skip if it's a public API or test
                    if (symbol.name.startswith('test_') or 
                        symbol.name.startswith('Test') or
                        (not symbol.name.startswith('_') and symbol.kind in [SymbolKind.CLASS, SymbolKind.FUNCTION])):
                        continue
                    
                    # Determine dead code type
                    if symbol.kind == SymbolKind.FUNCTION:
                        code_type = DeadCodeType.UNUSED_FUNCTION
                    elif symbol.kind == SymbolKind.CLASS:
                        code_type = DeadCodeType.UNUSED_CLASS
                    elif symbol.kind == SymbolKind.VARIABLE:
                        code_type = DeadCodeType.UNUSED_VARIABLE
                    else:
                        continue
                    
                    dead_code_item = DeadCodeItem(
                        code_type=code_type,
                        symbol_name=symbol.name,
                        file_path=symbol.location.absolute_path,
                        location=symbol.location,
                        confidence=0.8,
                        reason=f"Symbol '{symbol.name}' is not reachable from any entry point",
                        safe_to_remove=True
                    )
                    
                    dead_code_items.append(dead_code_item)
            
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect unused symbols: {e}")
            return []
    
    async def _detect_unreachable_code(self, file_paths: List[str]) -> List[DeadCodeItem]:
        """Detect unreachable code blocks"""
        try:
            dead_code_items = []
            
            for file_path in file_paths:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Look for unreachable code patterns
                    for i, line in enumerate(lines):
                        line_stripped = line.strip()
                        
                        # Code after return/raise/break/continue
                        if (line_stripped.startswith(('return', 'raise', 'break', 'continue')) and
                            i + 1 < len(lines)):
                            next_line = lines[i + 1].strip()
                            if (next_line and 
                                not next_line.startswith(('#', 'def ', 'class ', 'if ', 'elif ', 'else:', 'except', 'finally'))):
                                
                                location = UnifiedLocation(
                                    uri=f"file://{file_path}",
                                    range=UnifiedRange(
                                        start=UnifiedPosition(line=i + 1, character=0),
                                        end=UnifiedPosition(line=i + 1, character=len(next_line))
                                    ),
                                    absolute_path=file_path
                                )
                                
                                dead_code_item = DeadCodeItem(
                                    code_type=DeadCodeType.UNREACHABLE_CODE,
                                    symbol_name=f"line_{i + 2}",
                                    file_path=file_path,
                                    location=location,
                                    confidence=0.9,
                                    reason="Code after return/raise/break/continue statement",
                                    safe_to_remove=True
                                )
                                
                                dead_code_items.append(dead_code_item)
                                
                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path} for unreachable code: {e}")
            
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect unreachable code: {e}")
            return []
    
    async def _detect_unused_imports(self, file_paths: List[str]) -> List[DeadCodeItem]:
        """Detect unused imports"""
        try:
            dead_code_items = []
            
            for file_path in file_paths:
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    # Find import statements
                    import_lines = []
                    for i, line in enumerate(lines):
                        line_stripped = line.strip()
                        if (line_stripped.startswith(('import ', 'from ')) and 
                            not line_stripped.startswith('#')):
                            import_lines.append((i, line_stripped))
                    
                    # Check if imports are used
                    for line_num, import_line in import_lines:
                        imported_names = self._extract_imported_names(import_line)
                        
                        for name in imported_names:
                            # Simple check - look for usage in the rest of the file
                            if not self._is_name_used_in_content(name, content, import_line):
                                location = UnifiedLocation(
                                    uri=f"file://{file_path}",
                                    range=UnifiedRange(
                                        start=UnifiedPosition(line=line_num, character=0),
                                        end=UnifiedPosition(line=line_num, character=len(import_line))
                                    ),
                                    absolute_path=file_path
                                )
                                
                                dead_code_item = DeadCodeItem(
                                    code_type=DeadCodeType.UNUSED_IMPORT,
                                    symbol_name=name,
                                    file_path=file_path,
                                    location=location,
                                    confidence=0.85,
                                    reason=f"Import '{name}' is not used in the file",
                                    safe_to_remove=True
                                )
                                
                                dead_code_items.append(dead_code_item)
                                
                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path} for unused imports: {e}")
            
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect unused imports: {e}")
            return []
    
    async def _detect_empty_functions(self, file_paths: List[str]) -> List[DeadCodeItem]:
        """Detect empty functions"""
        try:
            dead_code_items = []
            
            if not self._language_server:
                return dead_code_items
            
            for file_path in file_paths:
                try:
                    symbols = await self._language_server.get_symbols(file_path)
                    
                    for symbol in symbols:
                        if symbol.kind == SymbolKind.FUNCTION:
                            # Check if function is empty
                            if await self._is_function_empty(file_path, symbol):
                                dead_code_item = DeadCodeItem(
                                    code_type=DeadCodeType.EMPTY_FUNCTION,
                                    symbol_name=symbol.name,
                                    file_path=file_path,
                                    location=symbol.location,
                                    confidence=0.7,
                                    reason=f"Function '{symbol.name}' is empty or only contains pass/comments",
                                    safe_to_remove=False  # Might be intentional
                                )
                                
                                dead_code_items.append(dead_code_item)
                                
                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path} for empty functions: {e}")
            
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect empty functions: {e}")
            return []
    
    async def _detect_commented_code(self, file_paths: List[str]) -> List[DeadCodeItem]:
        """Detect commented out code"""
        try:
            dead_code_items = []
            
            for file_path in file_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Look for commented code patterns
                    for i, line in enumerate(lines):
                        line_stripped = line.strip()
                        
                        # Check if it looks like commented code
                        if (line_stripped.startswith('#') and 
                            self._looks_like_commented_code(line_stripped[1:].strip())):
                            
                            location = UnifiedLocation(
                                uri=f"file://{file_path}",
                                range=UnifiedRange(
                                    start=UnifiedPosition(line=i, character=0),
                                    end=UnifiedPosition(line=i, character=len(line.rstrip()))
                                ),
                                absolute_path=file_path
                            )
                            
                            dead_code_item = DeadCodeItem(
                                code_type=DeadCodeType.COMMENTED_CODE,
                                symbol_name=f"commented_line_{i + 1}",
                                file_path=file_path,
                                location=location,
                                confidence=0.6,
                                reason="Line appears to be commented out code",
                                safe_to_remove=False  # Might be intentional
                            )
                            
                            dead_code_items.append(dead_code_item)
                            
                except Exception as e:
                    logger.debug(f"Failed to analyze {file_path} for commented code: {e}")
            
            return dead_code_items
            
        except Exception as e:
            logger.error(f"Failed to detect commented code: {e}")
            return []
    
    def _is_entry_point(self, symbol: UnifiedSymbol) -> bool:
        """Check if a symbol is an entry point"""
        try:
            name = symbol.name.lower()
            
            # Check against entry point patterns
            for pattern in self._entry_points:
                if pattern.lower() in name:
                    return True
            
            # Check if it's a public API
            if (not name.startswith('_') and 
                symbol.kind in [SymbolKind.FUNCTION, SymbolKind.CLASS]):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check entry point: {e}")
            return False
    
    def _extract_imported_names(self, import_line: str) -> List[str]:
        """Extract imported names from import statement"""
        try:
            names = []
            
            if import_line.startswith('import '):
                # import module, module2
                modules = import_line[7:].split(',')
                for module in modules:
                    module = module.strip()
                    if ' as ' in module:
                        names.append(module.split(' as ')[1].strip())
                    else:
                        names.append(module.split('.')[0])
            
            elif import_line.startswith('from '):
                # from module import name1, name2
                parts = import_line.split(' import ')
                if len(parts) == 2:
                    imported = parts[1].split(',')
                    for item in imported:
                        item = item.strip()
                        if ' as ' in item:
                            names.append(item.split(' as ')[1].strip())
                        else:
                            names.append(item)
            
            return names
            
        except Exception as e:
            logger.error(f"Failed to extract imported names: {e}")
            return []
    
    def _is_name_used_in_content(self, name: str, content: str, import_line: str) -> bool:
        """Check if a name is used in the file content"""
        try:
            # Remove the import line from content
            content_without_import = content.replace(import_line, '')
            
            # Simple check - look for the name as a word boundary
            import re
            pattern = r'\b' + re.escape(name) + r'\b'
            return bool(re.search(pattern, content_without_import))
            
        except Exception as e:
            logger.error(f"Failed to check name usage: {e}")
            return True  # Default to used to be safe
    
    async def _is_function_empty(self, file_path: str, symbol: UnifiedSymbol) -> bool:
        """Check if a function is empty"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = symbol.location.range.start.line
            end_line = symbol.location.range.end.line
            
            # Get function body
            function_lines = lines[start_line:end_line + 1]
            
            # Check if only contains pass, comments, or docstrings
            has_content = False
            in_docstring = False
            
            for line in function_lines[1:]:  # Skip function definition line
                line_stripped = line.strip()
                
                if not line_stripped:
                    continue
                
                if line_stripped.startswith('#'):
                    continue
                
                if line_stripped in ['pass', '...']:
                    continue
                
                # Check for docstrings
                if line_stripped.startswith(('"""', "'''")):
                    if line_stripped.count('"""') == 2 or line_stripped.count("'''") == 2:
                        continue  # Single line docstring
                    in_docstring = not in_docstring
                    continue
                
                if in_docstring:
                    continue
                
                has_content = True
                break
            
            return not has_content
            
        except Exception as e:
            logger.error(f"Failed to check if function is empty: {e}")
            return False
    
    def _looks_like_commented_code(self, line: str) -> bool:
        """Check if a line looks like commented out code"""
        try:
            # Patterns that suggest commented code
            code_patterns = [
                r'^\s*(def|class|if|for|while|try|except|with|import|from)\s',
                r'^\s*\w+\s*=',  # Assignment
                r'^\s*\w+\(',    # Function call
                r'^\s*return\s',
                r'^\s*print\s*\(',
                r'^\s*\w+\.\w+',  # Method call
            ]
            
            import re
            for pattern in code_patterns:
                if re.match(pattern, line):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check commented code pattern: {e}")
            return False
    
    def _update_detection_metrics(self, dead_code_items: List[DeadCodeItem], detection_time: float) -> None:
        """Update detection metrics"""
        try:
            self._detection_metrics = {
                'last_detection_time': time.time(),
                'detection_duration': detection_time,
                'total_items_found': len(dead_code_items),
                'items_by_type': {},
                'high_confidence_items': len([item for item in dead_code_items if item.confidence > 0.8]),
                'safe_to_remove_items': len([item for item in dead_code_items if item.safe_to_remove])
            }
            
            # Count by type
            for item in dead_code_items:
                type_name = item.code_type.value
                self._detection_metrics['items_by_type'][type_name] = (
                    self._detection_metrics['items_by_type'].get(type_name, 0) + 1
                )
                
        except Exception as e:
            logger.error(f"Failed to update detection metrics: {e}")
    
    def get_detection_metrics(self) -> Dict[str, Any]:
        """Get detection metrics"""
        try:
            return {
                'initialized': self._initialized,
                'project_root': self.project_root,
                'reachability_graph_size': len(self._reachability_graph.nodes) if self._reachability_graph else 0,
                'entry_points_count': len(self._entry_points),
                'detection_metrics': self._detection_metrics.copy()
            }
            
        except Exception as e:
            logger.error(f"Failed to get detection metrics: {e}")
            return {}
    
    def get_status(self) -> Dict[str, Any]:
        """Get detector status"""
        return {
            'initialized': self._initialized,
            'project_root': self.project_root,
            'reachability_graph_built': self._reachability_graph is not None,
            'entry_points_count': len(self._entry_points)
        }
