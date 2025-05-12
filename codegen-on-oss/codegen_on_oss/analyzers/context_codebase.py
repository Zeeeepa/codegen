#!/usr/bin/env python3
"""
CodebaseContext Module

This module provides context for codebase analysis, including graph manipulation
and codebase comparison capabilities. It's particularly useful for PR analysis
and codebase vs. PR comparisons.
"""

import os
import sys
import tempfile
import shutil
import re
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional, Union, TypeVar, cast, Callable
from enum import Enum
import networkx as nx

try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.codebase.codebase_context import CodebaseContext as SDKCodebaseContext
    from codegen.configs.models.codebase import CodebaseConfig
    from codegen.configs.models.secrets import SecretsConfig
    from codegen.sdk.codebase.config import ProjectConfig
    from codegen.git.schemas.repo_config import RepoConfig
    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.shared.enums.programming_language import ProgrammingLanguage
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.directory import Directory
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.enums import EdgeType, SymbolType
    from codegen.sdk.codebase.transactions import Transaction
    from codegen.sdk.codebase.transaction_manager import TransactionManager
except ImportError:
    print("Codegen SDK not found. Please install it first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global ignore list for files that should be excluded from analysis
GLOBAL_FILE_IGNORE_LIST = [
    "__pycache__",
    ".git",
    ".github",
    ".vscode",
    ".idea",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".env",
    "env",
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.zip",
    "*.gz",
    "*.tar",
    "*.log",
]

def get_node_classes():
    """Return a tuple of classes that represent nodes in the codebase graph."""
    return (Symbol, Function, Class, Directory, SourceFile)

class CodebaseContext:
    """
    Enhanced context for codebase analysis, providing graph manipulation
    and codebase comparison capabilities.
    
    This class extends the functionality of the SDK's CodebaseContext
    with additional methods for PR analysis and codebase comparison.
    """
    
    def __init__(
        self,
        codebase: Codebase,
        base_path: Optional[str] = None,
        pr_branch: Optional[str] = None,
        base_branch: str = "main",
    ):
        """
        Initialize the CodebaseContext.
        
        Args:
            codebase: Codebase instance to analyze
            base_path: Base path of the codebase
            pr_branch: PR branch name (if applicable)
            base_branch: Base branch name
        """
        self.codebase = codebase
        self.base_path = base_path or ""
        self.pr_branch = pr_branch
        self.base_branch = base_branch
        
        # Graph for storing codebase structure
        self._graph = nx.DiGraph()
        
        # Transaction management
        self.transaction_manager = TransactionManager()
        
        # Cache for nodes and files
        self._node_cache = {}
        self._file_cache = {}
        self._directory_cache = {}
        
        # Initialize the graph
        self.build_graph()
    
    def __repr__(self) -> str:
        """String representation of the CodebaseContext."""
        return f"CodebaseContext(nodes={len(self.nodes)}, edges={len(self.edges)}, files={len(self._file_cache)})"
    
    @property
    def _graph(self) -> nx.DiGraph:
        """Get the graph."""
        return self.__graph
    
    @_graph.setter
    def _graph(self, graph: nx.DiGraph) -> None:
        """Set the graph."""
        self.__graph = graph
    
    def build_graph(self) -> None:
        """Build the codebase graph."""
        # Clear existing graph and caches
        self._graph = nx.DiGraph()
        self._node_cache = {}
        self._file_cache = {}
        self._directory_cache = {}
        
        # Add files to the graph
        for file in self.codebase.files:
            if any(re.match(pattern, file.path) for pattern in GLOBAL_FILE_IGNORE_LIST):
                continue
                
            self.add_node(file)
            
            # Cache file for faster access
            self._file_cache[str(file.path)] = file
        
        # Add symbols to the graph
        for symbol in self.codebase.symbols:
            self.add_node(symbol)
            
            # Connect symbol to its file
            if hasattr(symbol, 'file') and symbol.file:
                self.add_edge(symbol.file, symbol, EdgeType.CONTAINS)
                
            # Connect class members to their class
            if hasattr(symbol, 'parent') and symbol.parent:
                self.add_edge(symbol.parent, symbol, EdgeType.CONTAINS)
        
        # Build directory tree
        self.build_directory_tree()
        
        # Compute dependencies
        self._compute_dependencies()
    
    def apply_diffs(self, diffs: Dict[str, Any]) -> None:
        """
        Apply diffs to the codebase.
        
        Args:
            diffs: Dictionary of file paths to diff content
        """
        for file_path, diff in diffs.items():
            # Process each file's diff
            self._process_diff_files({file_path: diff})
        
        # Rebuild the graph with the applied diffs
        self.build_graph()
    
    def _reset_files(self) -> None:
        """Reset any modified files to their original state."""
        # Clear file cache
        self._file_cache = {}
        
        # Re-populate cache from codebase
        for file in self.codebase.files:
            self._file_cache[str(file.path)] = file
    
    def reset_codebase(self) -> None:
        """Reset the codebase to its original state."""
        # Reset files
        self._reset_files()
        
        # Rebuild the graph
        self.build_graph()
    
    def undo_applied_diffs(self) -> None:
        """Undo all applied diffs."""
        self._revert_diffs()
        self.build_graph()
    
    def _revert_diffs(self) -> None:
        """Revert any applied diffs."""
        # Use transaction manager to revert all transactions
        self.transaction_manager.revert_all()
        
        # Reset files
        self._reset_files()
    
    def save_commit(self, message: str) -> str:
        """
        Save changes as a commit.
        
        Args:
            message: Commit message
            
        Returns:
            Commit hash
        """
        # Use repo operator to commit changes
        if hasattr(self.codebase, 'repo_operator'):
            return self.codebase.repo_operator.commit(message)
        return ""
    
    def prune_graph(self) -> None:
        """Remove any nodes that no longer exist in the codebase."""
        nodes_to_remove = []
        
        for node in self.nodes:
            if hasattr(node, 'path'):
                path = str(node.path)
                
                # Check if file still exists
                if isinstance(node, SourceFile) and path not in self._file_cache:
                    nodes_to_remove.append(node)
                    
                # Check if directory still exists
                elif isinstance(node, Directory) and path not in self._directory_cache:
                    nodes_to_remove.append(node)
            
            # Check if symbol's file still exists
            elif hasattr(node, 'file') and node.file:
                file_path = str(node.file.path)
                if file_path not in self._file_cache:
                    nodes_to_remove.append(node)
        
        # Remove nodes
        for node in nodes_to_remove:
            self.remove_node(node)
    
    def build_directory_tree(self) -> None:
        """Build the directory tree from the files."""
        directories = {}
        
        for file in self._file_cache.values():
            path = file.path
            parent_dir = path.parent
            
            # Create directory nodes
            current_dir = parent_dir
            while str(current_dir) != ".":
                dir_path = str(current_dir)
                
                if dir_path not in directories:
                    dir_node = Directory(current_dir)
                    directories[dir_path] = dir_node
                    self.add_node(dir_node)
                    self._directory_cache[dir_path] = dir_node
                    
                    # Connect to parent directory
                    parent_path = str(current_dir.parent)
                    if parent_path != "." and parent_path in directories:
                        parent_node = directories[parent_path]
                        self.add_edge(parent_node, dir_node, EdgeType.CONTAINS)
                
                # Connect file to directory
                if str(current_dir) == str(parent_dir):
                    self.add_edge(directories[dir_path], file, EdgeType.CONTAINS)
                
                current_dir = current_dir.parent
                if str(current_dir) == ".":
                    break
    
    def get_directory(self, path: Union[str, Path]) -> Optional[Directory]:
        """
        Get a directory node from the graph.
        
        Args:
            path: Directory path
            
        Returns:
            Directory node or None if not found
        """
        path_str = str(path)
        
        # Check cache first
        if path_str in self._directory_cache:
            return self._directory_cache[path_str]
        
        # Search for the directory in the graph
        for node in self.nodes:
            if isinstance(node, Directory) and str(node.path) == path_str:
                self._directory_cache[path_str] = node
                return node
        
        return None
    
    def _process_diff_files(self, diff_files: Dict[str, Any]) -> None:
        """
        Process diff files and apply changes to the codebase.
        
        Args:
            diff_files: Dictionary mapping file paths to diff content
        """
        for file_path, diff_content in diff_files.items():
            file = self.get_file(file_path)
            
            if file:
                # Create a transaction for this change
                transaction = Transaction(file, diff_content)
                
                # Apply the transaction
                self.transaction_manager.apply(transaction)
            else:
                # Handle new file creation
                if isinstance(diff_content, str):
                    # Create new file
                    new_file = self.add_single_file(file_path, diff_content)
                    
                    if new_file:
                        # Add to cache
                        self._file_cache[file_path] = new_file
    
    def _compute_dependencies(self) -> None:
        """Compute dependencies between symbols."""
        # Process imports to create dependency edges
        for file in self._file_cache.values():
            if hasattr(file, 'imports'):
                for import_item in file.imports:
                    imported_symbol = None
                    
                    # Try to resolve the import
                    if hasattr(import_item, 'resolved_symbol') and import_item.resolved_symbol:
                        imported_symbol = import_item.resolved_symbol
                    elif hasattr(import_item, 'name'):
                        # Try to find the symbol by name
                        for symbol in self.codebase.symbols:
                            if hasattr(symbol, 'name') and symbol.name == import_item.name:
                                imported_symbol = symbol
                                break
                    
                    if imported_symbol:
                        # Create dependency edge
                        self.add_edge(file, imported_symbol, EdgeType.IMPORTS)
        
        # Process function calls to create call edges
        for func in self.codebase.functions:
            if hasattr(func, 'calls'):
                for call in func.calls:
                    called_func = None
                    
                    # Try to resolve the call
                    if hasattr(call, 'resolved_symbol') and call.resolved_symbol:
                        called_func = call.resolved_symbol
                    elif hasattr(call, 'name'):
                        # Try to find the function by name
                        for other_func in self.codebase.functions:
                            if hasattr(other_func, 'name') and other_func.name == call.name:
                                called_func = other_func
                                break
                    
                    if called_func:
                        # Create call edge
                        self.add_edge(func, called_func, EdgeType.CALLS)
    
    def build_subgraph(self, nodes: List[Any]) -> nx.DiGraph:
        """
        Build a subgraph containing only the specified nodes.
        
        Args:
            nodes: List of nodes to include in the subgraph
            
        Returns:
            Subgraph as a new DiGraph
        """
        subgraph = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            if self.has_node(node):
                subgraph.add_node(node)
        
        # Add edges
        for u, v, data in self.edges(data=True):
            if subgraph.has_node(u) and subgraph.has_node(v):
                subgraph.add_edge(u, v, **data)
        
        return subgraph
    
    def get_node(self, id_or_obj: Any) -> Optional[Any]:
        """
        Get a node from the graph by ID or object.
        
        Args:
            id_or_obj: Node ID or object
            
        Returns:
            Node or None if not found
        """
        if self.has_node(id_or_obj):
            return id_or_obj
        
        # Check if it's a string path
        if isinstance(id_or_obj, str):
            # Try to find file or directory
            if id_or_obj in self._file_cache:
                return self._file_cache[id_or_obj]
            
            if id_or_obj in self._directory_cache:
                return self._directory_cache[id_or_obj]
            
            # Try to find by name
            for node in self.nodes:
                if hasattr(node, 'name') and node.name == id_or_obj:
                    return node
                    
                if hasattr(node, 'path') and str(node.path) == id_or_obj:
                    return node
        
        return None
    
    def get_nodes(self, node_type: Optional[Any] = None) -> List[Any]:
        """
        Get all nodes of a specific type.
        
        Args:
            node_type: Type of nodes to return
            
        Returns:
            List of nodes
        """
        if node_type is None:
            return list(self.nodes)
        
        return [node for node in self.nodes if isinstance(node, node_type)]
    
    def get_edges(self, edge_type: Optional[Any] = None) -> List[Tuple[Any, Any, Dict[str, Any]]]:
        """
        Get all edges of a specific type.
        
        Args:
            edge_type: Type of edges to return
            
        Returns:
            List of edges as (u, v, data) tuples
        """
        edges = list(self.edges(data=True))
        
        if edge_type is None:
            return edges
        
        return [
            (u, v, data) for u, v, data in edges
            if 'type' in data and data['type'] == edge_type
        ]
    
    def get_file(self, path: Union[str, Path]) -> Optional[SourceFile]:
        """
        Get a file from the codebase.
        
        Args:
            path: File path
            
        Returns:
            SourceFile or None if not found
        """
        path_str = str(path)
        
        # Check cache first
        if path_str in self._file_cache:
            return self._file_cache[path_str]
        
        # Try to get raw file
        file = self._get_raw_file_from_path(path_str)
        
        if file:
            self._file_cache[path_str] = file
        
        return file
    
    def _get_raw_file_from_path(self, path: str) -> Optional[SourceFile]:
        """
        Get a file from the codebase by its path.
        
        Args:
            path: File path
            
        Returns:
            SourceFile or None if not found
        """
        # Try to get file from codebase
        if hasattr(self.codebase, 'get_file'):
            return self.codebase.get_file(path)
            
        # Fallback to searching in files
        for file in self.codebase.files:
            if str(file.path) == path:
                return file
        
        return None
    
    def get_external_module(self, name: str) -> Optional[Any]:
        """
        Get an external module from the codebase.
        
        Args:
            name: Module name
            
        Returns:
            External module or None if not found
        """
        if hasattr(self.codebase, 'get_external_module'):
            return self.codebase.get_external_module(name)
        
        # Fallback: search through external modules
        if hasattr(self.codebase, 'external_modules'):
            for module in self.codebase.external_modules:
                if hasattr(module, 'name') and module.name == name:
                    return module
        
        return None
    
    def add_node(self, node: Any) -> None:
        """
        Add a node to the graph.
        
        Args:
            node: Node to add
        """
        if not self.has_node(node):
            self._graph.add_node(node)
            
            # Add to cache if applicable
            if hasattr(node, 'path'):
                path_str = str(node.path)
                
                if isinstance(node, SourceFile):
                    self._file_cache[path_str] = node
                elif isinstance(node, Directory):
                    self._directory_cache[path_str] = node
    
    def add_child(self, parent: Any, child: Any, edge_type: Optional[Any] = None) -> None:
        """
        Add a child node to a parent node.
        
        Args:
            parent: Parent node
            child: Child node
            edge_type: Type of edge
        """
        self.add_node(parent)
        self.add_node(child)
        
        edge_data = {}
        if edge_type is not None:
            edge_data['type'] = edge_type
        
        self.add_edge(parent, child, edge_type)
    
    def has_node(self, node: Any) -> bool:
        """
        Check if a node exists in the graph.
        
        Args:
            node: Node to check
            
        Returns:
            True if the node exists, False otherwise
        """
        return self._graph.has_node(node)
    
    def has_edge(self, u: Any, v: Any) -> bool:
        """
        Check if an edge exists in the graph.
        
        Args:
            u: Source node
            v: Target node
            
        Returns:
            True if the edge exists, False otherwise
        """
        return self._graph.has_edge(u, v)
    
    def add_edge(self, u: Any, v: Any, edge_type: Optional[Any] = None) -> None:
        """
        Add an edge to the graph.
        
        Args:
            u: Source node
            v: Target node
            edge_type: Type of edge
        """
        if not self.has_node(u):
            self.add_node(u)
        
        if not self.has_node(v):
            self.add_node(v)
        
        edge_data = {}
        if edge_type is not None:
            edge_data['type'] = edge_type
        
        self._graph.add_edge(u, v, **edge_data)
    
    def add_edges(self, edge_list: List[Tuple[Any, Any, Dict[str, Any]]]) -> None:
        """
        Add multiple edges to the graph.
        
        Args:
            edge_list: List of (u, v, data) tuples
        """
        for u, v, data in edge_list:
            if not self.has_node(u):
                self.add_node(u)
            
            if not self.has_node(v):
                self.add_node(v)
            
            self._graph.add_edge(u, v, **data)
    
    @property
    def nodes(self) -> List[Any]:
        """Get all nodes in the graph."""
        return list(self._graph.nodes())
    
    @property
    def edges(self) -> Callable:
        """Get all edges in the graph."""
        return self._graph.edges
    
    def predecessor(self, node: Any) -> Optional[Any]:
        """
        Get the predecessor of a node.
        
        Args:
            node: Node to get predecessor for
            
        Returns:
            Predecessor node or None if not found
        """
        preds = list(self.predecessors(node))
        return preds[0] if preds else None
    
    def predecessors(self, node: Any) -> List[Any]:
        """
        Get all predecessors of a node.
        
        Args:
            node: Node to get predecessors for
            
        Returns:
            List of predecessor nodes
        """
        if not self.has_node(node):
            return []
        
        return list(self._graph.predecessors(node))
    
    def successors(self, node: Any) -> List[Any]:
        """
        Get all successors of a node.
        
        Args:
            node: Node to get successors for
            
        Returns:
            List of successor nodes
        """
        if not self.has_node(node):
            return []
        
        return list(self._graph.successors(node))
    
    def get_edge_data(self, u: Any, v: Any) -> Dict[str, Any]:
        """
        Get the data for an edge.
        
        Args:
            u: Source node
            v: Target node
            
        Returns:
            Edge data dictionary
        """
        if not self.has_edge(u, v):
            return {}
        
        return self._graph.get_edge_data(u, v)
    
    def in_edges(self, node: Any, data: bool = False) -> List[Any]:
        """
        Get all incoming edges for a node.
        
        Args:
            node: Node to get incoming edges for
            data: Whether to include edge data
            
        Returns:
            List of incoming edges
        """
        if not self.has_node(node):
            return []
        
        return list(self._graph.in_edges(node, data=data))
    
    def out_edges(self, node: Any, data: bool = False) -> List[Any]:
        """
        Get all outgoing edges for a node.
        
        Args:
            node: Node to get outgoing edges for
            data: Whether to include edge data
            
        Returns:
            List of outgoing edges
        """
        if not self.has_node(node):
            return []
        
        return list(self._graph.out_edges(node, data=data))
    
    def remove_node(self, node: Any) -> None:
        """
        Remove a node from the graph.
        
        Args:
            node: Node to remove
        """
        if self.has_node(node):
            self._graph.remove_node(node)
            
            # Remove from cache if applicable
            if hasattr(node, 'path'):
                path_str = str(node.path)
                
                if isinstance(node, SourceFile) and path_str in self._file_cache:
                    del self._file_cache[path_str]
                elif isinstance(node, Directory) and path_str in self._directory_cache:
                    del self._directory_cache[path_str]
    
    def remove_edge(self, u: Any, v: Any) -> None:
        """
        Remove an edge from the graph.
        
        Args:
            u: Source node
            v: Target node
        """
        if self.has_edge(u, v):
            self._graph.remove_edge(u, v)
    
    def to_absolute(self, path: Union[str, Path]) -> str:
        """
        Convert a relative path to an absolute path.
        
        Args:
            path: Relative path
            
        Returns:
            Absolute path
        """
        path_str = str(path)
        
        if os.path.isabs(path_str):
            return path_str
        
        return os.path.join(self.base_path, path_str)
    
    def to_relative(self, path: Union[str, Path]) -> str:
        """
        Convert an absolute path to a relative path.
        
        Args:
            path: Absolute path
            
        Returns:
            Relative path
        """
        path_str = str(path)
        
        if not os.path.isabs(path_str):
            return path_str
        
        return os.path.relpath(path_str, self.base_path)
    
    def is_subdir(self, parent: Union[str, Path], child: Union[str, Path]) -> bool:
        """
        Check if a directory is a subdirectory of another.
        
        Args:
            parent: Parent directory
            child: Child directory
            
        Returns:
            True if child is a subdirectory of parent, False otherwise
        """
        parent_str = str(parent)
        child_str = str(child)
        
        parent_abs = os.path.abspath(parent_str)
        child_abs = os.path.abspath(child_str)
        
        return child_abs.startswith(parent_abs)
    
    def commit_transactions(self, message: str) -> str:
        """
        Commit all pending transactions.
        
        Args:
            message: Commit message
            
        Returns:
            Commit hash
        """
        # Apply all transactions and commit
        self.transaction_manager.apply_all()
        
        return self.save_commit(message)
    
    def add_single_file(self, path: str, content: str) -> Optional[SourceFile]:
        """
        Add a single file to the codebase.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            SourceFile or None if creation failed
        """
        # Add file to the transaction manager
        transaction = Transaction.create_new_file(path, content)
        self.transaction_manager.add(transaction)
        
        # Initialize file in codebase
        if hasattr(self.codebase, 'add_file'):
            return self.codebase.add_file(path, content)
        
        return None
    
    @property
    def session(self) -> Any:
        """Get the transaction session."""
        return self.transaction_manager.session
    
    def remove_directory(self, path: Union[str, Path]) -> None:
        """
        Remove a directory and all its contents from the codebase.
        
        Args:
            path: Directory path
        """
        path_str = str(path)
        dir_node = self.get_directory(path_str)
        
        if not dir_node:
            return
        
        # Get all files in the directory
        files_to_remove = []
        for file in self._file_cache.values():
            if self.is_subdir(path_str, file.path):
                files_to_remove.append(file)
        
        # Remove files
        for file in files_to_remove:
            file_path = str(file.path)
            
            # Create transaction for removal
            transaction = Transaction.delete_file(file_path)
            self.transaction_manager.add(transaction)
            
            # Remove from cache
            if file_path in self._file_cache:
                del self._file_cache[file_path]
            
            # Remove from graph
            if self.has_node(file):
                self.remove_node(file)
        
        # Remove directory from cache
        if path_str in self._directory_cache:
            del self._directory_cache[path_str]
        
        # Remove directory node from graph
        if self.has_node(dir_node):
            self.remove_node(dir_node)
    
    @property
    def ts_declassify(self) -> Optional[Callable]:
        """Get TypeScript declassify function if available."""
        if hasattr(self.codebase, 'ts_declassify'):
            return self.codebase.ts_declassify
        return None