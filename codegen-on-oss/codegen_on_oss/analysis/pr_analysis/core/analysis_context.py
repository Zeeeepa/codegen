"""
Analysis Context Module

This module provides the context for PR analysis.
"""

from typing import Dict, List, Any, Optional, Set
from graph_sitter.codebase.codebase_context import CodebaseContext
from ..github.models import PRPartContext


class AnalysisContext:
    """Context for PR analysis, providing data and utilities for rules."""
    
    def __init__(self, codebase: CodebaseContext, pr_data: PRPartContext):
        """
        Initialize a new analysis context.
        
        Args:
            codebase: Codebase to analyze
            pr_data: PR data to analyze
        """
        self.codebase = codebase
        self.pr_data = pr_data
        self._file_changes = None
        self._symbol_changes = None
    
    def get_changed_files(self) -> Dict[str, str]:
        """
        Get files changed in the PR.
        
        Returns:
            Dictionary mapping file paths to change types
        """
        if self._file_changes is None:
            self._compute_file_changes()
        return self._file_changes
        
    def get_symbol_changes(self) -> Dict[str, Any]:
        """
        Get symbols changed in the PR.
        
        Returns:
            Dictionary mapping symbol names to change information
        """
        if self._symbol_changes is None:
            self._compute_symbol_changes()
        return self._symbol_changes
    
    def _compute_file_changes(self) -> None:
        """Compute file changes."""
        self._file_changes = {}
        
        # Get all files in the codebase
        for file in self.codebase.get_all_files():
            self._file_changes[file.filepath] = "unchanged"
    
    def _compute_symbol_changes(self) -> None:
        """Compute symbol changes."""
        self._symbol_changes = {}
        
        # Get all symbols in the codebase
        for symbol in self.codebase.get_all_symbols():
            self._symbol_changes[symbol.name] = {
                "type": symbol.symbol_type.name if hasattr(symbol, "symbol_type") else "unknown",
                "file": symbol.filepath if hasattr(symbol, "filepath") else "unknown",
                "line": symbol.line_range[0] if hasattr(symbol, "line_range") else 0,
                "column": symbol.column_range[0] if hasattr(symbol, "column_range") else 0,
            }
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Content of the file, or None if not found
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return None
        return file.content
    
    def get_file_symbols(self, file_path: str) -> List[Any]:
        """
        Get symbols defined in a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of symbols defined in the file
        """
        file = self.codebase.get_file(file_path)
        if file is None:
            return []
        return file.symbols


class DiffContext:
    """Context representing differences between base and head branches."""
    
    def __init__(self, base_context: AnalysisContext, head_context: AnalysisContext):
        """
        Initialize a new diff context.
        
        Args:
            base_context: Context for the base branch
            head_context: Context for the head branch
        """
        self.base_context = base_context
        self.head_context = head_context
        self._file_changes = None
        self._function_changes = None
        self._class_changes = None
        
    def get_file_changes(self) -> Dict[str, str]:
        """
        Get files changed between base and head.
        
        Returns:
            Dictionary mapping file paths to change types
        """
        if self._file_changes is None:
            self._compute_file_changes()
        return self._file_changes
        
    def get_function_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get functions changed between base and head.
        
        Returns:
            Dictionary mapping function names to change information
        """
        if self._function_changes is None:
            self._compute_function_changes()
        return self._function_changes
    
    def get_class_changes(self) -> Dict[str, Dict[str, Any]]:
        """
        Get classes changed between base and head.
        
        Returns:
            Dictionary mapping class names to change information
        """
        if self._class_changes is None:
            self._compute_class_changes()
        return self._class_changes
    
    def _compute_file_changes(self) -> None:
        """Compute file changes between base and head."""
        self._file_changes = {}
        
        # Get files in base and head
        base_files = {file.filepath: file for file in self.base_context.codebase.get_all_files()}
        head_files = {file.filepath: file for file in self.head_context.codebase.get_all_files()}
        
        # Find added files
        for path in head_files:
            if path not in base_files:
                self._file_changes[path] = "added"
        
        # Find deleted files
        for path in base_files:
            if path not in head_files:
                self._file_changes[path] = "deleted"
        
        # Find modified files
        for path in base_files:
            if path in head_files:
                base_content = self.base_context.get_file_content(path)
                head_content = self.head_context.get_file_content(path)
                if base_content != head_content:
                    self._file_changes[path] = "modified"
                else:
                    self._file_changes[path] = "unchanged"
    
    def _compute_function_changes(self) -> None:
        """Compute function changes between base and head."""
        self._function_changes = {}
        
        # Get functions in base and head
        base_functions = {}
        head_functions = {}
        
        for symbol in self.base_context.codebase.get_all_symbols():
            if hasattr(symbol, "symbol_type") and symbol.symbol_type.name == "Function":
                base_functions[symbol.name] = symbol
        
        for symbol in self.head_context.codebase.get_all_symbols():
            if hasattr(symbol, "symbol_type") and symbol.symbol_type.name == "Function":
                head_functions[symbol.name] = symbol
        
        # Find added functions
        for name in head_functions:
            if name not in base_functions:
                self._function_changes[name] = {
                    "change_type": "added",
                    "function": head_functions[name],
                }
        
        # Find deleted functions
        for name in base_functions:
            if name not in head_functions:
                self._function_changes[name] = {
                    "change_type": "deleted",
                    "function": base_functions[name],
                }
        
        # Find modified functions
        for name in base_functions:
            if name in head_functions:
                base_func = base_functions[name]
                head_func = head_functions[name]
                
                # Compare function bodies
                if hasattr(base_func, "body") and hasattr(head_func, "body"):
                    if base_func.body != head_func.body:
                        self._function_changes[name] = {
                            "change_type": "modified",
                            "base_function": base_func,
                            "head_function": head_func,
                        }
    
    def _compute_class_changes(self) -> None:
        """Compute class changes between base and head."""
        self._class_changes = {}
        
        # Get classes in base and head
        base_classes = {}
        head_classes = {}
        
        for symbol in self.base_context.codebase.get_all_symbols():
            if hasattr(symbol, "symbol_type") and symbol.symbol_type.name == "Class":
                base_classes[symbol.name] = symbol
        
        for symbol in self.head_context.codebase.get_all_symbols():
            if hasattr(symbol, "symbol_type") and symbol.symbol_type.name == "Class":
                head_classes[symbol.name] = symbol
        
        # Find added classes
        for name in head_classes:
            if name not in base_classes:
                self._class_changes[name] = {
                    "change_type": "added",
                    "class": head_classes[name],
                }
        
        # Find deleted classes
        for name in base_classes:
            if name not in head_classes:
                self._class_changes[name] = {
                    "change_type": "deleted",
                    "class": base_classes[name],
                }
        
        # Find modified classes
        for name in base_classes:
            if name in head_classes:
                base_cls = base_classes[name]
                head_cls = head_classes[name]
                
                # Compare class bodies
                if hasattr(base_cls, "body") and hasattr(head_cls, "body"):
                    if base_cls.body != head_cls.body:
                        self._class_changes[name] = {
                            "change_type": "modified",
                            "base_class": base_cls,
                            "head_class": head_cls,
                        }
    
    def get_all_changes(self) -> Dict[str, Any]:
        """
        Get all changes between base and head.
        
        Returns:
            Dictionary with all changes
        """
        return {
            "file_changes": self.get_file_changes(),
            "function_changes": self.get_function_changes(),
            "class_changes": self.get_class_changes(),
        }
    
    def get_changed_symbols(self) -> Set[str]:
        """
        Get all symbols that have changed.
        
        Returns:
            Set of changed symbol names
        """
        changed_symbols = set()
        
        # Add changed functions
        function_changes = self.get_function_changes()
        for name, change in function_changes.items():
            changed_symbols.add(name)
        
        # Add changed classes
        class_changes = self.get_class_changes()
        for name, change in class_changes.items():
            changed_symbols.add(name)
        
        return changed_symbols

