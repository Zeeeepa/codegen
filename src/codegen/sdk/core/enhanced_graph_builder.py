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
Enhanced Graph Construction Pipeline

This module extends the existing graph construction capabilities to incorporate
LSP diagnostics, symbol information, and Serena's project analysis into a
unified graph representation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
import threading
import time
import json
from dataclasses import dataclass, asdict

from .integration_interfaces import (
    IGraphBuilder, ILanguageServer, IProjectManager, IDiagnosticCollector,
    UnifiedDiagnostic, UnifiedSymbol, UnifiedLocation, DiagnosticSeverity, SymbolKind
)
from .unified_config import UnifiedConfiguration

# Import existing graph utilities
try:
    from ..extensions.graph.create_graph import create_codebase_graph
    from ..extensions.graph.utils import Node, NodeLabel, Relation, RelationLabel, SimpleGraph
    GRAPH_UTILS_AVAILABLE = True
except ImportError:
    GRAPH_UTILS_AVAILABLE = False
    create_codebase_graph = None
    Node = None
    NodeLabel = None
    Relation = None
    RelationLabel = None
    SimpleGraph = None

# Tree-sitter imports
try:
    from ..tree_sitter_parser import parse_file, get_parser_by_filepath_or_extension
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    parse_file = None
    get_parser_by_filepath_or_extension = None

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Enhanced graph node with LSP and diagnostic information"""
    id: str
    name: str
    node_type: str  # 'file', 'class', 'function', 'variable', 'diagnostic', etc.
    location: Optional[UnifiedLocation] = None
    properties: Dict[str, Any] = None
    diagnostics: List[UnifiedDiagnostic] = None
    symbols: List[UnifiedSymbol] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.diagnostics is None:
            self.diagnostics = []
        if self.symbols is None:
            self.symbols = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class GraphEdge:
    """Enhanced graph edge with relationship metadata"""
    id: str
    source_id: str
    target_id: str
    edge_type: str  # 'calls', 'imports', 'defines', 'references', 'diagnoses', etc.
    properties: Dict[str, Any] = None
    weight: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.metadata is None:
            self.metadata = {}


class EnhancedGraphBuilder(IGraphBuilder):
    """
    Enhanced graph builder that incorporates LSP diagnostics, symbol information,
    and Serena's project analysis into a unified graph representation.
    
    This builder extends the existing graph construction capabilities with:
    - LSP diagnostic information as graph nodes
    - Symbol relationships from language servers
    - Cross-file dependency analysis
    - Error context and resolution metadata
    """
    
    def __init__(self, config: UnifiedConfiguration):
        self.config = config
        self.project_root: Optional[str] = None
        
        # Component dependencies (injected)
        self._language_server: Optional[ILanguageServer] = None
        self._project_manager: Optional[IProjectManager] = None
        self._diagnostic_collector: Optional[IDiagnosticCollector] = None
        
        # Graph state
        self._graph_nodes: Dict[str, GraphNode] = {}
        self._graph_edges: Dict[str, GraphEdge] = {}
        self._node_counter = 0
        self._edge_counter = 0
        
        # State management
        self._lock = threading.RLock()
        self._graph_built = False
        self._last_build_time: Optional[float] = None
        
        # Performance tracking
        self._build_metrics: Dict[str, Any] = {}
        
        logger.info("Enhanced graph builder initialized")
    
    def set_language_server(self, language_server: ILanguageServer):
        """Inject language server dependency"""
        self._language_server = language_server
    
    def set_project_manager(self, project_manager: IProjectManager):
        """Inject project manager dependency"""
        self._project_manager = project_manager
    
    def set_diagnostic_collector(self, diagnostic_collector: IDiagnosticCollector):
        """Inject diagnostic collector dependency"""
        self._diagnostic_collector = diagnostic_collector
    
    def build_graph(self, project_root: str) -> Dict[str, Any]:
        """Build a comprehensive graph representation of the codebase"""
        try:
            with self._lock:
                start_time = time.time()
                logger.info(f"Building enhanced graph for {project_root}")
                
                self.project_root = project_root
                
                # Clear existing graph
                self._graph_nodes.clear()
                self._graph_edges.clear()
                self._node_counter = 0
                self._edge_counter = 0
                
                # Build graph in phases
                self._build_file_structure()
                self._build_ast_nodes()
                self._build_symbol_nodes()
                self._build_diagnostic_nodes()
                self._build_relationships()
                
                # Calculate metrics
                build_time = time.time() - start_time
                self._build_metrics = {
                    'build_time': build_time,
                    'node_count': len(self._graph_nodes),
                    'edge_count': len(self._graph_edges),
                    'file_count': len([n for n in self._graph_nodes.values() if n.node_type == 'file']),
                    'diagnostic_count': len([n for n in self._graph_nodes.values() if n.node_type == 'diagnostic']),
                    'symbol_count': len([n for n in self._graph_nodes.values() if n.node_type in ['class', 'function', 'variable']]),
                    'timestamp': time.time()
                }
                
                self._graph_built = True
                self._last_build_time = time.time()
                
                logger.info(f"Graph built successfully: {self._build_metrics['node_count']} nodes, {self._build_metrics['edge_count']} edges in {build_time:.2f}s")
                
                return self._export_graph_dict()
                
        except Exception as e:
            logger.error(f"Failed to build graph: {e}")
            return {}
    
    def update_graph(self, file_path: str, content: str) -> None:
        """Update graph with changes to a file"""
        try:
            with self._lock:
                if not self._graph_built:
                    logger.warning("Graph not built yet, cannot update")
                    return
                
                logger.debug(f"Updating graph for file: {file_path}")
                
                # Remove existing nodes for this file
                self._remove_file_nodes(file_path)
                
                # Rebuild nodes for this file
                self._build_file_nodes(file_path, content)
                
                # Update relationships
                self._update_file_relationships(file_path)
                
                logger.debug(f"Graph updated for {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to update graph for {file_path}: {e}")
    
    def get_graph_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get nodes from the graph"""
        try:
            with self._lock:
                nodes = []
                for node in self._graph_nodes.values():
                    if node_type is None or node.node_type == node_type:
                        nodes.append(self._node_to_dict(node))
                return nodes
                
        except Exception as e:
            logger.error(f"Failed to get graph nodes: {e}")
            return []
    
    def get_graph_edges(self, edge_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get edges from the graph"""
        try:
            with self._lock:
                edges = []
                for edge in self._graph_edges.values():
                    if edge_type is None or edge.edge_type == edge_type:
                        edges.append(self._edge_to_dict(edge))
                return edges
                
        except Exception as e:
            logger.error(f"Failed to get graph edges: {e}")
            return []
    
    def find_related_nodes(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Find nodes related to a given node"""
        try:
            with self._lock:
                if node_id not in self._graph_nodes:
                    return []
                
                related_nodes = set()
                visited = set()
                queue = [(node_id, 0)]
                
                while queue:
                    current_id, depth = queue.pop(0)
                    
                    if current_id in visited or depth > max_depth:
                        continue
                    
                    visited.add(current_id)
                    if depth > 0:  # Don't include the starting node
                        related_nodes.add(current_id)
                    
                    # Find connected nodes
                    for edge in self._graph_edges.values():
                        next_node_id = None
                        if edge.source_id == current_id:
                            next_node_id = edge.target_id
                        elif edge.target_id == current_id:
                            next_node_id = edge.source_id
                        
                        if next_node_id and next_node_id not in visited:
                            queue.append((next_node_id, depth + 1))
                
                # Convert to dictionaries
                result = []
                for node_id in related_nodes:
                    if node_id in self._graph_nodes:
                        result.append(self._node_to_dict(self._graph_nodes[node_id]))
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to find related nodes: {e}")
            return []
    
    def export_graph(self, format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export graph in specified format"""
        try:
            with self._lock:
                if format.lower() == "json":
                    return json.dumps(self._export_graph_dict(), indent=2)
                elif format.lower() == "dict":
                    return self._export_graph_dict()
                elif format.lower() == "neo4j" and GRAPH_UTILS_AVAILABLE:
                    return self._export_neo4j_format()
                else:
                    logger.warning(f"Unsupported export format: {format}")
                    return self._export_graph_dict()
                    
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return {}
    
    # Private graph building methods
    
    def _build_file_structure(self) -> None:
        """Build file structure nodes"""
        try:
            if not self._project_manager:
                logger.warning("No project manager available for file structure")
                return
            
            project_files = self._project_manager.get_project_files()
            
            for file_path in project_files:
                self._create_file_node(file_path)
            
            logger.debug(f"Built file structure: {len(project_files)} files")
            
        except Exception as e:
            logger.error(f"Failed to build file structure: {e}")
    
    def _build_ast_nodes(self) -> None:
        """Build AST nodes using tree-sitter"""
        try:
            if not TREE_SITTER_AVAILABLE:
                logger.warning("Tree-sitter not available for AST parsing")
                return
            
            if not self._project_manager:
                return
            
            project_files = self._project_manager.get_project_files()
            
            for file_path in project_files:
                try:
                    self._build_file_ast_nodes(file_path)
                except Exception as e:
                    logger.debug(f"Failed to build AST for {file_path}: {e}")
            
            logger.debug("Built AST nodes")
            
        except Exception as e:
            logger.error(f"Failed to build AST nodes: {e}")
    
    def _build_file_ast_nodes(self, file_path: str) -> None:
        """Build AST nodes for a specific file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse with tree-sitter
            ast_root = parse_file(file_path, content)
            
            # Extract symbols from AST
            self._extract_ast_symbols(file_path, ast_root, content)
            
        except Exception as e:
            logger.debug(f"Failed to build AST nodes for {file_path}: {e}")
    
    def _extract_ast_symbols(self, file_path: str, node, content: str, parent_id: Optional[str] = None) -> None:
        """Extract symbols from AST nodes"""
        try:
            # Define symbol types we're interested in
            symbol_types = {
                'function_definition': 'function',
                'class_definition': 'class',
                'method_definition': 'method',
                'variable_declaration': 'variable',
                'import_statement': 'import',
                'import_from_statement': 'import'
            }
            
            if node.type in symbol_types:
                symbol_node = self._create_ast_symbol_node(file_path, node, content, symbol_types[node.type])
                
                # Create relationship to parent
                if parent_id:
                    self._create_edge(parent_id, symbol_node.id, "contains")
            
            # Recursively process children
            for child in node.children:
                self._extract_ast_symbols(file_path, child, content, parent_id)
                
        except Exception as e:
            logger.debug(f"Failed to extract AST symbols: {e}")
    
    def _build_symbol_nodes(self) -> None:
        """Build symbol nodes using LSP information"""
        try:
            if not self._language_server:
                logger.warning("No language server available for symbol information")
                return
            
            if not self._project_manager:
                return
            
            project_files = self._project_manager.get_project_files()
            
            for file_path in project_files:
                try:
                    asyncio.create_task(self._build_file_symbol_nodes(file_path))
                except Exception as e:
                    logger.debug(f"Failed to build symbols for {file_path}: {e}")
            
            logger.debug("Built symbol nodes")
            
        except Exception as e:
            logger.error(f"Failed to build symbol nodes: {e}")
    
    async def _build_file_symbol_nodes(self, file_path: str) -> None:
        """Build symbol nodes for a specific file"""
        try:
            symbols = await self._language_server.get_symbols(file_path)
            
            for symbol in symbols:
                self._create_symbol_node(file_path, symbol)
            
        except Exception as e:
            logger.debug(f"Failed to build symbol nodes for {file_path}: {e}")
    
    def _build_diagnostic_nodes(self) -> None:
        """Build diagnostic nodes"""
        try:
            if not self._diagnostic_collector:
                logger.warning("No diagnostic collector available")
                return
            
            asyncio.create_task(self._build_diagnostic_nodes_async())
            
        except Exception as e:
            logger.error(f"Failed to build diagnostic nodes: {e}")
    
    async def _build_diagnostic_nodes_async(self) -> None:
        """Build diagnostic nodes asynchronously"""
        try:
            diagnostics = await self._diagnostic_collector.collect_diagnostics()
            
            for diagnostic in diagnostics:
                self._create_diagnostic_node(diagnostic)
            
            logger.debug(f"Built {len(diagnostics)} diagnostic nodes")
            
        except Exception as e:
            logger.error(f"Failed to build diagnostic nodes: {e}")
    
    def _build_relationships(self) -> None:
        """Build relationships between nodes"""
        try:
            # Build file-to-symbol relationships
            self._build_file_symbol_relationships()
            
            # Build symbol-to-symbol relationships
            self._build_symbol_relationships()
            
            # Build diagnostic relationships
            self._build_diagnostic_relationships()
            
            logger.debug("Built node relationships")
            
        except Exception as e:
            logger.error(f"Failed to build relationships: {e}")
    
    def _build_file_symbol_relationships(self) -> None:
        """Build relationships between files and symbols"""
        try:
            for node in self._graph_nodes.values():
                if node.node_type in ['class', 'function', 'method', 'variable'] and node.location:
                    # Find the file node
                    file_path = node.location.absolute_path or node.location.uri.replace('file://', '')
                    file_node_id = self._get_file_node_id(file_path)
                    
                    if file_node_id:
                        self._create_edge(file_node_id, node.id, "defines")
            
        except Exception as e:
            logger.error(f"Failed to build file-symbol relationships: {e}")
    
    def _build_symbol_relationships(self) -> None:
        """Build relationships between symbols"""
        try:
            # This would analyze call graphs, inheritance, etc.
            # For now, implement basic relationships
            
            for node in self._graph_nodes.values():
                if node.node_type == 'class':
                    # Find methods in this class
                    for other_node in self._graph_nodes.values():
                        if (other_node.node_type == 'method' and 
                            other_node.location and node.location and
                            other_node.location.uri == node.location.uri):
                            self._create_edge(node.id, other_node.id, "contains")
            
        except Exception as e:
            logger.error(f"Failed to build symbol relationships: {e}")
    
    def _build_diagnostic_relationships(self) -> None:
        """Build relationships between diagnostics and code elements"""
        try:
            for node in self._graph_nodes.values():
                if node.node_type == 'diagnostic' and node.location:
                    # Find symbols at the same location
                    for other_node in self._graph_nodes.values():
                        if (other_node.node_type in ['class', 'function', 'method', 'variable'] and
                            other_node.location and
                            self._locations_overlap(node.location, other_node.location)):
                            self._create_edge(node.id, other_node.id, "diagnoses")
            
        except Exception as e:
            logger.error(f"Failed to build diagnostic relationships: {e}")
    
    # Node and edge creation methods
    
    def _create_file_node(self, file_path: str) -> GraphNode:
        """Create a file node"""
        node_id = self._generate_node_id()
        
        node = GraphNode(
            id=node_id,
            name=Path(file_path).name,
            node_type='file',
            properties={
                'file_path': file_path,
                'extension': Path(file_path).suffix,
                'size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
            },
            metadata={
                'absolute_path': str(Path(file_path).resolve()),
                'relative_path': str(Path(file_path).relative_to(self.project_root)) if self.project_root else file_path
            }
        )
        
        self._graph_nodes[node_id] = node
        return node
    
    def _create_ast_symbol_node(self, file_path: str, ast_node, content: str, symbol_type: str) -> GraphNode:
        """Create a symbol node from AST"""
        node_id = self._generate_node_id()
        
        # Extract symbol name
        name = "unknown"
        if hasattr(ast_node, 'child_by_field_name'):
            name_node = ast_node.child_by_field_name('name')
            if name_node:
                name = content[name_node.start_byte:name_node.end_byte]
        
        # Create location
        location = UnifiedLocation(
            uri=f"file://{file_path}",
            range=self._ast_node_to_range(ast_node),
            absolute_path=file_path
        )
        
        node = GraphNode(
            id=node_id,
            name=name,
            node_type=symbol_type,
            location=location,
            properties={
                'file_path': file_path,
                'ast_type': ast_node.type,
                'start_line': ast_node.start_point[0],
                'end_line': ast_node.end_point[0]
            }
        )
        
        self._graph_nodes[node_id] = node
        return node
    
    def _create_symbol_node(self, file_path: str, symbol: UnifiedSymbol) -> GraphNode:
        """Create a symbol node from LSP symbol"""
        node_id = self._generate_node_id()
        
        node = GraphNode(
            id=node_id,
            name=symbol.name,
            node_type=symbol.kind.value,
            location=symbol.location,
            properties={
                'file_path': file_path,
                'symbol_kind': symbol.kind.value,
                'container_name': symbol.container_name,
                'detail': symbol.detail,
                'deprecated': symbol.deprecated
            },
            symbols=[symbol]
        )
        
        self._graph_nodes[node_id] = node
        return node
    
    def _create_diagnostic_node(self, diagnostic: UnifiedDiagnostic) -> GraphNode:
        """Create a diagnostic node"""
        node_id = self._generate_node_id()
        
        node = GraphNode(
            id=node_id,
            name=f"Diagnostic: {diagnostic.message[:50]}...",
            node_type='diagnostic',
            properties={
                'severity': diagnostic.severity.value,
                'code': diagnostic.code,
                'source': diagnostic.source,
                'message': diagnostic.message
            },
            diagnostics=[diagnostic]
        )
        
        self._graph_nodes[node_id] = node
        return node
    
    def _create_edge(self, source_id: str, target_id: str, edge_type: str, properties: Optional[Dict[str, Any]] = None) -> GraphEdge:
        """Create an edge between two nodes"""
        edge_id = self._generate_edge_id()
        
        edge = GraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {}
        )
        
        self._graph_edges[edge_id] = edge
        return edge
    
    # Helper methods
    
    def _generate_node_id(self) -> str:
        """Generate a unique node ID"""
        self._node_counter += 1
        return f"node_{self._node_counter}"
    
    def _generate_edge_id(self) -> str:
        """Generate a unique edge ID"""
        self._edge_counter += 1
        return f"edge_{self._edge_counter}"
    
    def _get_file_node_id(self, file_path: str) -> Optional[str]:
        """Get the node ID for a file"""
        for node_id, node in self._graph_nodes.items():
            if node.node_type == 'file' and node.properties.get('file_path') == file_path:
                return node_id
        return None
    
    def _ast_node_to_range(self, ast_node) -> 'UnifiedRange':
        """Convert AST node to unified range"""
        from .integration_interfaces import UnifiedPosition, UnifiedRange
        
        start = UnifiedPosition(line=ast_node.start_point[0], character=ast_node.start_point[1])
        end = UnifiedPosition(line=ast_node.end_point[0], character=ast_node.end_point[1])
        return UnifiedRange(start=start, end=end)
    
    def _locations_overlap(self, loc1: UnifiedLocation, loc2: UnifiedLocation) -> bool:
        """Check if two locations overlap"""
        if loc1.uri != loc2.uri:
            return False
        
        # Simple overlap check
        return (loc1.range.start.line <= loc2.range.end.line and
                loc1.range.end.line >= loc2.range.start.line)
    
    def _node_to_dict(self, node: GraphNode) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            'id': node.id,
            'name': node.name,
            'type': node.node_type,
            'location': asdict(node.location) if node.location else None,
            'properties': node.properties,
            'diagnostics_count': len(node.diagnostics),
            'symbols_count': len(node.symbols),
            'metadata': node.metadata
        }
    
    def _edge_to_dict(self, edge: GraphEdge) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            'id': edge.id,
            'source': edge.source_id,
            'target': edge.target_id,
            'type': edge.edge_type,
            'properties': edge.properties,
            'weight': edge.weight,
            'metadata': edge.metadata
        }
    
    def _export_graph_dict(self) -> Dict[str, Any]:
        """Export graph as dictionary"""
        return {
            'nodes': [self._node_to_dict(node) for node in self._graph_nodes.values()],
            'edges': [self._edge_to_dict(edge) for edge in self._graph_edges.values()],
            'metadata': {
                'project_root': self.project_root,
                'build_metrics': self._build_metrics,
                'node_count': len(self._graph_nodes),
                'edge_count': len(self._graph_edges),
                'last_build_time': self._last_build_time
            }
        }
    
    def _export_neo4j_format(self) -> Dict[str, Any]:
        """Export graph in Neo4j compatible format"""
        # This would format the graph for Neo4j import
        # For now, return the standard format
        return self._export_graph_dict()
    
    def _remove_file_nodes(self, file_path: str) -> None:
        """Remove all nodes associated with a file"""
        nodes_to_remove = []
        edges_to_remove = []
        
        for node_id, node in self._graph_nodes.items():
            if (node.properties.get('file_path') == file_path or
                (node.location and node.location.absolute_path == file_path)):
                nodes_to_remove.append(node_id)
        
        # Remove associated edges
        for edge_id, edge in self._graph_edges.items():
            if edge.source_id in nodes_to_remove or edge.target_id in nodes_to_remove:
                edges_to_remove.append(edge_id)
        
        # Remove nodes and edges
        for node_id in nodes_to_remove:
            del self._graph_nodes[node_id]
        
        for edge_id in edges_to_remove:
            del self._graph_edges[edge_id]
    
    def _build_file_nodes(self, file_path: str, content: str) -> None:
        """Build nodes for a specific file"""
        # Create file node
        self._create_file_node(file_path)
        
        # Build AST nodes
        if TREE_SITTER_AVAILABLE:
            try:
                ast_root = parse_file(file_path, content)
                self._extract_ast_symbols(file_path, ast_root, content)
            except Exception as e:
                logger.debug(f"Failed to build AST for {file_path}: {e}")
    
    def _update_file_relationships(self, file_path: str) -> None:
        """Update relationships for a specific file"""
        # This would rebuild relationships for the updated file
        # For now, rebuild all relationships (could be optimized)
        self._build_relationships()
    
    def get_build_metrics(self) -> Dict[str, Any]:
        """Get graph build metrics"""
        return self._build_metrics.copy()
    
    def is_graph_built(self) -> bool:
        """Check if graph has been built"""
        return self._graph_built
