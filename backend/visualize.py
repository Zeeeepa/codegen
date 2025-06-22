"""
Interactive Codebase Visualization Engine

This module provides interactive web-based visualization for codebases including:
- Interactive graph visualization with symbol selection
- Context viewing panels for selected symbols
- Function and class hierarchy browsing
- Issue highlighting and context display
- Search and filtering capabilities
- Export capabilities for different formats

Replaces Neo4j-only approach with modern web-based visualization.
"""

import json
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import networkx as nx
from collections import defaultdict

from backend.analysis import ComprehensiveAnalyzer, EntryPoint, ImportantFunction, CodeIssue, SymbolContext


@dataclass
class VisualizationNode:
    """Node for visualization graph"""
    id: str
    label: str
    type: str  # 'function', 'class', 'file', 'module'
    size: float
    color: str
    position: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = None


@dataclass
class VisualizationEdge:
    """Edge for visualization graph"""
    source: str
    target: str
    type: str  # 'calls', 'imports', 'inherits', 'contains'
    weight: float
    color: str
    metadata: Dict[str, Any] = None


@dataclass
class VisualizationGraph:
    """Complete visualization graph"""
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    metadata: Dict[str, Any]


@dataclass
class FilterOptions:
    """Options for filtering the visualization"""
    node_types: List[str] = None
    min_importance: float = 0.0
    max_complexity: int = 100
    show_entry_points_only: bool = False
    show_issues_only: bool = False
    file_patterns: List[str] = None


@dataclass
class LayoutOptions:
    """Options for graph layout"""
    algorithm: str = "force_directed"  # 'force_directed', 'hierarchical', 'circular', 'tree'
    spacing: float = 1.0
    iterations: int = 50
    cluster_by: str = "file"  # 'file', 'type', 'importance'


class InteractiveVisualizer:
    """
    Interactive codebase visualizer that creates web-based visualizations.
    
    Provides:
    - Interactive graph with zoom/pan/filter
    - Symbol selection with context panels
    - Hierarchical browsing
    - Issue highlighting
    - Search and filtering
    - Export capabilities
    """
    
    def __init__(self, analyzer: ComprehensiveAnalyzer):
        """Initialize visualizer with analyzer"""
        self.analyzer = analyzer
        self._graph_cache: Optional[VisualizationGraph] = None
        
        # Color schemes
        self.node_colors = {
            'function': '#4CAF50',
            'class': '#2196F3',
            'file': '#FF9800',
            'module': '#9C27B0',
            'entry_point': '#F44336',
            'important': '#FFD700',
            'issue': '#FF5722'
        }
        
        self.edge_colors = {
            'calls': '#666666',
            'imports': '#999999',
            'inherits': '#3F51B5',
            'contains': '#795548'
        }
    
    def create_interactive_graph(self, 
                                filter_options: FilterOptions = None,
                                layout_options: LayoutOptions = None) -> VisualizationGraph:
        """
        Create an interactive visualization graph.
        
        Args:
            filter_options: Options for filtering nodes and edges
            layout_options: Options for graph layout
            
        Returns:
            VisualizationGraph ready for web rendering
        """
        if filter_options is None:
            filter_options = FilterOptions()
        if layout_options is None:
            layout_options = LayoutOptions()
        
        # Get analysis data
        important_functions = self.analyzer.get_all_important_functions()
        entry_points = self.analyzer.get_all_entry_points()
        issues = self.analyzer.detect_issues()
        
        # Create nodes and edges
        nodes = self._create_nodes(important_functions, entry_points, issues, filter_options)
        edges = self._create_edges(important_functions, filter_options)
        
        # Apply layout
        nodes = self._apply_layout(nodes, edges, layout_options)
        
        # Create metadata
        metadata = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "filter_options": asdict(filter_options),
            "layout_options": asdict(layout_options),
            "node_types": list(set(node.type for node in nodes)),
            "edge_types": list(set(edge.type for edge in edges))
        }
        
        graph = VisualizationGraph(nodes=nodes, edges=edges, metadata=metadata)
        self._graph_cache = graph
        return graph
    
    def _create_nodes(self, 
                     important_functions: List[ImportantFunction],
                     entry_points: List[EntryPoint],
                     issues: List[CodeIssue],
                     filter_options: FilterOptions) -> List[VisualizationNode]:
        """Create visualization nodes"""
        nodes = []
        node_id_counter = 0
        
        # Create function nodes
        for func in important_functions:
            if self._should_include_function(func, filter_options):
                node_type = 'entry_point' if func.is_entry_point else 'function'
                if func.importance_score > 0.7:
                    node_type = 'important'
                
                nodes.append(VisualizationNode(
                    id=f"func_{node_id_counter}",
                    label=func.name,
                    type=node_type,
                    size=max(10, func.importance_score * 50),
                    color=self.node_colors.get(node_type, '#666666'),
                    metadata={
                        'full_name': func.full_name,
                        'filepath': func.filepath,
                        'line_number': func.line_number,
                        'importance_score': func.importance_score,
                        'usage_count': func.usage_count,
                        'dependency_count': func.dependency_count,
                        'is_public_api': func.is_public_api,
                        'is_entry_point': func.is_entry_point,
                        'source_preview': func.source_code[:200] + '...' if len(func.source_code) > 200 else func.source_code,
                        'context': func.context
                    }
                ))
                node_id_counter += 1
        
        # Create class nodes
        for cls in self.analyzer.codebase.classes:
            if self._should_include_class(cls, filter_options):
                nodes.append(VisualizationNode(
                    id=f"class_{node_id_counter}",
                    label=cls.name,
                    type='class',
                    size=max(15, len(cls.methods) * 3),
                    color=self.node_colors['class'],
                    metadata={
                        'filepath': getattr(cls, 'filepath', ''),
                        'methods_count': len(cls.methods),
                        'attributes_count': len(cls.attributes),
                        'parent_classes': [p.name for p in cls.parent_classes] if cls.parent_classes else [],
                        'source_preview': getattr(cls, 'source', '')[:200] + '...' if len(getattr(cls, 'source', '')) > 200 else getattr(cls, 'source', '')
                    }
                ))
                node_id_counter += 1
        
        # Create file nodes (if requested)
        if not filter_options.node_types or 'file' in filter_options.node_types:
            file_function_count = defaultdict(int)
            for func in important_functions:
                file_function_count[func.filepath] += 1
            
            for file in self.analyzer.codebase.files:
                if file_function_count[file.filepath] > 0:
                    nodes.append(VisualizationNode(
                        id=f"file_{node_id_counter}",
                        label=Path(file.filepath).name,
                        type='file',
                        size=max(20, file_function_count[file.filepath] * 5),
                        color=self.node_colors['file'],
                        metadata={
                            'filepath': file.filepath,
                            'functions_count': len(file.functions),
                            'classes_count': len(file.classes),
                            'imports_count': len(file.imports),
                            'lines_of_code': len(getattr(file, 'source', '').split('\n')) if hasattr(file, 'source') else 0
                        }
                    ))
                    node_id_counter += 1
        
        # Add issue markers
        issue_nodes = self._create_issue_nodes(issues, filter_options)
        nodes.extend(issue_nodes)
        
        return nodes
    
    def _create_edges(self, 
                     important_functions: List[ImportantFunction],
                     filter_options: FilterOptions) -> List[VisualizationEdge]:
        """Create visualization edges"""
        edges = []
        
        # Function call relationships
        for func in important_functions:
            if self._should_include_function(func, filter_options):
                # Get function calls from the analyzer
                codebase_func = self._find_codebase_function(func.name, func.filepath)
                if codebase_func:
                    for call in codebase_func.function_calls:
                        target_func = self._find_function_by_call(call, important_functions)
                        if target_func and self._should_include_function(target_func, filter_options):
                            edges.append(VisualizationEdge(
                                source=self._get_node_id(func),
                                target=self._get_node_id(target_func),
                                type='calls',
                                weight=1.0,
                                color=self.edge_colors['calls'],
                                metadata={
                                    'call_type': 'function_call',
                                    'source_function': func.name,
                                    'target_function': target_func.name
                                }
                            ))
        
        # Class inheritance relationships
        for cls in self.analyzer.codebase.classes:
            if cls.parent_classes:
                for parent in cls.parent_classes:
                    if hasattr(parent, 'name'):
                        edges.append(VisualizationEdge(
                            source=f"class_{cls.name}",
                            target=f"class_{parent.name}",
                            type='inherits',
                            weight=2.0,
                            color=self.edge_colors['inherits'],
                            metadata={
                                'relationship': 'inheritance',
                                'child_class': cls.name,
                                'parent_class': parent.name
                            }
                        ))
        
        # File containment relationships
        if not filter_options.node_types or 'file' in filter_options.node_types:
            for func in important_functions:
                if self._should_include_function(func, filter_options):
                    file_node_id = f"file_{Path(func.filepath).name}"
                    func_node_id = self._get_node_id(func)
                    
                    edges.append(VisualizationEdge(
                        source=file_node_id,
                        target=func_node_id,
                        type='contains',
                        weight=0.5,
                        color=self.edge_colors['contains'],
                        metadata={
                            'relationship': 'containment',
                            'file': func.filepath,
                            'function': func.name
                        }
                    ))
        
        return edges
    
    def _create_issue_nodes(self, issues: List[CodeIssue], filter_options: FilterOptions) -> List[VisualizationNode]:
        """Create nodes for code issues"""
        if filter_options.show_issues_only or not filter_options.node_types or 'issue' in filter_options.node_types:
            issue_nodes = []
            for i, issue in enumerate(issues):
                severity_size = {'low': 8, 'medium': 12, 'high': 16, 'critical': 20}
                
                issue_nodes.append(VisualizationNode(
                    id=f"issue_{i}",
                    label=f"{issue.type}: {issue.message[:30]}...",
                    type='issue',
                    size=severity_size.get(issue.severity, 10),
                    color=self.node_colors['issue'],
                    metadata={
                        'issue_type': issue.type,
                        'severity': issue.severity,
                        'message': issue.message,
                        'filepath': issue.filepath,
                        'line_number': issue.line_number,
                        'context': issue.context
                    }
                ))
            return issue_nodes
        return []
    
    def _should_include_function(self, func: ImportantFunction, filter_options: FilterOptions) -> bool:
        """Check if function should be included based on filters"""
        if filter_options.node_types and 'function' not in filter_options.node_types:
            return False
        
        if func.importance_score < filter_options.min_importance:
            return False
        
        if filter_options.show_entry_points_only and not func.is_entry_point:
            return False
        
        if filter_options.file_patterns:
            if not any(pattern in func.filepath for pattern in filter_options.file_patterns):
                return False
        
        return True
    
    def _should_include_class(self, cls, filter_options: FilterOptions) -> bool:
        """Check if class should be included based on filters"""
        if filter_options.node_types and 'class' not in filter_options.node_types:
            return False
        
        return True
    
    def _find_codebase_function(self, func_name: str, filepath: str):
        """Find function in codebase by name and filepath"""
        for file in self.analyzer.codebase.files:
            if file.filepath == filepath:
                for func in file.functions:
                    if func.name == func_name:
                        return func
        return None
    
    def _find_function_by_call(self, call, important_functions: List[ImportantFunction]):
        """Find function in important_functions list by call"""
        if hasattr(call, 'function_definition') and call.function_definition:
            func_def = call.function_definition
            if hasattr(func_def, 'name'):
                for func in important_functions:
                    if func.name == func_def.name:
                        return func
        return None
    
    def _get_node_id(self, func: ImportantFunction) -> str:
        """Get node ID for a function"""
        return f"func_{func.name}_{hash(func.filepath) % 1000}"
    
    def _apply_layout(self, 
                     nodes: List[VisualizationNode], 
                     edges: List[VisualizationEdge],
                     layout_options: LayoutOptions) -> List[VisualizationNode]:
        """Apply layout algorithm to position nodes"""
        if not nodes:
            return nodes
        
        # Create NetworkX graph for layout calculation
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node.id, **asdict(node))
        
        # Add edges
        for edge in edges:
            if edge.source in G.nodes and edge.target in G.nodes:
                G.add_edge(edge.source, edge.target, weight=edge.weight)
        
        # Calculate positions based on layout algorithm
        if layout_options.algorithm == "force_directed":
            pos = nx.spring_layout(G, k=layout_options.spacing, iterations=layout_options.iterations)
        elif layout_options.algorithm == "circular":
            pos = nx.circular_layout(G)
        elif layout_options.algorithm == "hierarchical":
            pos = nx.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
        else:
            pos = nx.spring_layout(G)
        
        # Apply positions to nodes
        for node in nodes:
            if node.id in pos:
                node.position = {
                    'x': float(pos[node.id][0]) * 100,  # Scale for web display
                    'y': float(pos[node.id][1]) * 100
                }
            else:
                node.position = {'x': 0.0, 'y': 0.0}
        
        return nodes
    
    def get_symbol_details(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a selected symbol"""
        # Extract symbol name from ID
        if symbol_id.startswith('func_'):
            func_name = symbol_id.replace('func_', '').split('_')[0]
            
            # Find the function
            important_functions = self.analyzer.get_all_important_functions()
            for func in important_functions:
                if func.name == func_name:
                    return {
                        'type': 'function',
                        'name': func.name,
                        'full_name': func.full_name,
                        'filepath': func.filepath,
                        'line_number': func.line_number,
                        'source_code': func.source_code,
                        'importance_score': func.importance_score,
                        'usage_count': func.usage_count,
                        'dependency_count': func.dependency_count,
                        'is_public_api': func.is_public_api,
                        'is_entry_point': func.is_entry_point,
                        'call_graph_centrality': func.call_graph_centrality,
                        'context': func.context
                    }
        
        elif symbol_id.startswith('class_'):
            class_name = symbol_id.replace('class_', '')
            
            # Find the class
            for cls in self.analyzer.codebase.classes:
                if cls.name == class_name:
                    return {
                        'type': 'class',
                        'name': cls.name,
                        'filepath': getattr(cls, 'filepath', ''),
                        'methods': [method.name for method in cls.methods],
                        'attributes': [attr.name for attr in cls.attributes] if hasattr(cls, 'attributes') else [],
                        'parent_classes': [p.name for p in cls.parent_classes] if cls.parent_classes else [],
                        'source_code': getattr(cls, 'source', ''),
                        'docstring': getattr(cls, 'docstring', '')
                    }
        
        return None
    
    def search_symbols(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for symbols matching query"""
        results = []
        query_lower = query.lower()
        
        # Search functions
        important_functions = self.analyzer.get_all_important_functions()
        for func in important_functions:
            if query_lower in func.name.lower() or query_lower in func.full_name.lower():
                results.append({
                    'type': 'function',
                    'name': func.name,
                    'full_name': func.full_name,
                    'filepath': func.filepath,
                    'importance_score': func.importance_score,
                    'match_type': 'name'
                })
        
        # Search classes
        for cls in self.analyzer.codebase.classes:
            if query_lower in cls.name.lower():
                results.append({
                    'type': 'class',
                    'name': cls.name,
                    'filepath': getattr(cls, 'filepath', ''),
                    'methods_count': len(cls.methods),
                    'match_type': 'name'
                })
        
        # Search in source code (limited)
        for func in important_functions[:50]:  # Limit for performance
            if query_lower in func.source_code.lower():
                results.append({
                    'type': 'function',
                    'name': func.name,
                    'full_name': func.full_name,
                    'filepath': func.filepath,
                    'importance_score': func.importance_score,
                    'match_type': 'source'
                })
        
        # Sort by relevance (importance score for functions)
        results.sort(key=lambda x: x.get('importance_score', 0), reverse=True)
        
        return results[:limit]
    
    def get_hierarchy_view(self, root_type: str = 'file') -> Dict[str, Any]:
        """Get hierarchical view of codebase"""
        if root_type == 'file':
            return self._get_file_hierarchy()
        elif root_type == 'class':
            return self._get_class_hierarchy()
        else:
            return self._get_function_hierarchy()
    
    def _get_file_hierarchy(self) -> Dict[str, Any]:
        """Get file-based hierarchy"""
        hierarchy = {}
        
        for file in self.analyzer.codebase.files:
            file_path = Path(file.filepath)
            parts = file_path.parts
            
            current = hierarchy
            for part in parts[:-1]:  # Directory parts
                if part not in current:
                    current[part] = {'type': 'directory', 'children': {}}
                current = current[part]['children']
            
            # File part
            file_name = parts[-1]
            current[file_name] = {
                'type': 'file',
                'filepath': file.filepath,
                'functions': [func.name for func in file.functions],
                'classes': [cls.name for cls in file.classes],
                'children': {}
            }
        
        return hierarchy
    
    def _get_class_hierarchy(self) -> Dict[str, Any]:
        """Get class inheritance hierarchy"""
        hierarchy = {}
        
        for cls in self.analyzer.codebase.classes:
            if not cls.parent_classes:  # Root classes
                hierarchy[cls.name] = {
                    'type': 'class',
                    'filepath': getattr(cls, 'filepath', ''),
                    'methods': [method.name for method in cls.methods],
                    'children': self._get_class_children(cls.name)
                }
        
        return hierarchy
    
    def _get_class_children(self, class_name: str) -> Dict[str, Any]:
        """Get children of a class"""
        children = {}
        
        for cls in self.analyzer.codebase.classes:
            if cls.parent_classes:
                for parent in cls.parent_classes:
                    if hasattr(parent, 'name') and parent.name == class_name:
                        children[cls.name] = {
                            'type': 'class',
                            'filepath': getattr(cls, 'filepath', ''),
                            'methods': [method.name for method in cls.methods],
                            'children': self._get_class_children(cls.name)
                        }
        
        return children
    
    def _get_function_hierarchy(self) -> Dict[str, Any]:
        """Get function call hierarchy"""
        hierarchy = {}
        important_functions = self.analyzer.get_all_important_functions()
        entry_points = self.analyzer.get_all_entry_points()
        
        # Start with entry points as roots
        for ep in entry_points:
            func = next((f for f in important_functions if f.name == ep.name), None)
            if func:
                hierarchy[func.name] = {
                    'type': 'function',
                    'filepath': func.filepath,
                    'importance_score': func.importance_score,
                    'is_entry_point': True,
                    'children': self._get_function_calls(func.name, func.filepath, set())
                }
        
        return hierarchy
    
    def _get_function_calls(self, func_name: str, filepath: str, visited: Set[str]) -> Dict[str, Any]:
        """Get functions called by a function"""
        if func_name in visited:
            return {}
        
        visited.add(func_name)
        children = {}
        
        codebase_func = self._find_codebase_function(func_name, filepath)
        if codebase_func:
            for call in codebase_func.function_calls:
                if hasattr(call, 'function_definition') and call.function_definition:
                    called_func = call.function_definition
                    if hasattr(called_func, 'name'):
                        children[called_func.name] = {
                            'type': 'function',
                            'filepath': getattr(called_func, 'filepath', ''),
                            'children': self._get_function_calls(called_func.name, getattr(called_func, 'filepath', ''), visited.copy())
                        }
        
        return children
    
    def export_graph(self, format_type: str = 'json') -> str:
        """Export visualization graph in specified format"""
        if not self._graph_cache:
            self.create_interactive_graph()
        
        if format_type == 'json':
            return json.dumps({
                'nodes': [asdict(node) for node in self._graph_cache.nodes],
                'edges': [asdict(edge) for edge in self._graph_cache.edges],
                'metadata': self._graph_cache.metadata
            }, indent=2)
        
        elif format_type == 'cytoscape':
            # Cytoscape.js format
            elements = []
            
            # Add nodes
            for node in self._graph_cache.nodes:
                elements.append({
                    'data': {
                        'id': node.id,
                        'label': node.label,
                        'type': node.type,
                        **node.metadata
                    },
                    'position': node.position or {'x': 0, 'y': 0},
                    'style': {
                        'background-color': node.color,
                        'width': node.size,
                        'height': node.size
                    }
                })
            
            # Add edges
            for edge in self._graph_cache.edges:
                elements.append({
                    'data': {
                        'id': f"{edge.source}_{edge.target}",
                        'source': edge.source,
                        'target': edge.target,
                        'type': edge.type,
                        **edge.metadata
                    },
                    'style': {
                        'line-color': edge.color,
                        'width': edge.weight
                    }
                })
            
            return json.dumps({'elements': elements}, indent=2)
        
        elif format_type == 'd3':
            # D3.js format
            return json.dumps({
                'nodes': [
                    {
                        'id': node.id,
                        'label': node.label,
                        'type': node.type,
                        'size': node.size,
                        'color': node.color,
                        'x': node.position['x'] if node.position else 0,
                        'y': node.position['y'] if node.position else 0,
                        **node.metadata
                    }
                    for node in self._graph_cache.nodes
                ],
                'links': [
                    {
                        'source': edge.source,
                        'target': edge.target,
                        'type': edge.type,
                        'weight': edge.weight,
                        'color': edge.color,
                        **edge.metadata
                    }
                    for edge in self._graph_cache.edges
                ]
            }, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


def create_visualizer(analyzer: ComprehensiveAnalyzer) -> InteractiveVisualizer:
    """Factory function to create an interactive visualizer"""
    return InteractiveVisualizer(analyzer)

