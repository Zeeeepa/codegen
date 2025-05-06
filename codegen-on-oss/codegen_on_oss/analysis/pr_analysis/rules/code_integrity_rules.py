"""
Code integrity rules for PR static analysis.

This module defines rules for detecting code integrity issues such as syntax errors,
undefined references, unused imports, and circular dependencies.
"""

import ast
import builtins
import importlib
import os
import sys
from typing import List, Dict, Any, Optional, Set, Tuple

from .base_rule import BaseRule, AnalysisResult


class SyntaxErrorRule(BaseRule):
    """Rule for detecting syntax errors in Python files."""
    
    def __init__(self):
        """Initialize the syntax error rule."""
        super().__init__(
            rule_id="CI001",
            name="Syntax Error Check",
            description="Checks for syntax errors in the code."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                syntax_errors = self._check_syntax(file_path, file_content)
                results.extend(syntax_errors)
        return results
        
    def _check_syntax(self, file_path: str, content: str) -> List[AnalysisResult]:
        """
        Check for syntax errors in Python code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            ast.parse(content, filename=file_path)
        except SyntaxError as e:
            results.append(AnalysisResult(
                rule_id=self.rule_id,
                severity="error",
                message=f"Syntax error: {str(e)}",
                file=file_path,
                line=e.lineno,
                column=e.offset,
                details={"error_type": "syntax_error"}
            ))
        return results


class UndefinedReferenceRule(BaseRule):
    """Rule for detecting undefined references in Python files."""
    
    def __init__(self):
        """Initialize the undefined reference rule."""
        super().__init__(
            rule_id="CI002",
            name="Undefined Reference Check",
            description="Checks for undefined references in the code."
        )
        # Add built-in names to defined names
        self.defined_names: Set[str] = set(dir(builtins))
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                undefined_refs = self._check_undefined_references(file_path, file_content, context)
                results.extend(undefined_refs)
        return results
        
    def _check_undefined_references(self, file_path: str, content: str, context) -> List[AnalysisResult]:
        """
        Check for undefined references in Python code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            context: Analysis context
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = UndefinedReferenceVisitor(self.defined_names)
            visitor.visit(tree)
            
            for ref in visitor.undefined_references:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="error",
                    message=f"Undefined reference: {ref.id}",
                    file=file_path,
                    line=ref.lineno,
                    column=ref.col_offset,
                    details={"error_type": "undefined_reference", "name": ref.id}
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class UndefinedReferenceVisitor(ast.NodeVisitor):
    """AST visitor to find undefined references in Python code."""

    def __init__(self, defined_names: Set[str]):
        """
        Initialize the visitor with a set of defined names.

        Args:
            defined_names: Set of names that are defined in the current scope
        """
        self.defined_names: Set[str] = defined_names
        self.undefined_references: List[ast.Name] = []

    def visit_Name(self, node: ast.Name) -> None:
        """Visit a Name node."""
        if isinstance(node.ctx, ast.Load) and node.id not in self.defined_names:
            # Add the node to undefined references
            self.undefined_references.append(node)
        self.generic_visit(node)


class UnusedImportRule(BaseRule):
    """Rule for detecting unused imports in Python files."""
    
    def __init__(self):
        """Initialize the unused import rule."""
        super().__init__(
            rule_id="CI003",
            name="Unused Import Check",
            description="Checks for unused imports in the code."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                unused_imports = self._check_unused_imports(file_path, file_content)
                results.extend(unused_imports)
        return results
        
    def _check_unused_imports(self, file_path: str, content: str) -> List[AnalysisResult]:
        """
        Check for unused imports in Python code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            
        Returns:
            List of analysis results
        """
        results = []
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = UnusedImportVisitor()
            visitor.visit(tree)
            visitor.finalize()
            
            for import_node, name in visitor.unused_imports:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Unused import: {name}",
                    file=file_path,
                    line=import_node.lineno,
                    column=import_node.col_offset,
                    details={"error_type": "unused_import", "name": name}
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class UnusedImportVisitor(ast.NodeVisitor):
    """AST visitor for finding unused imports."""
    
    def __init__(self):
        """Initialize the visitor."""
        self.imports = {}  # name -> node
        self.used_names = set()
        self.unused_imports = []
        
    def visit_Import(self, node):
        """Visit an Import node."""
        for name in node.names:
            alias = name.asname or name.name
            self.imports[alias] = (node, name.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Visit an ImportFrom node."""
        for name in node.names:
            alias = name.asname or name.name
            if name.name != '*':
                self.imports[alias] = (node, name.name)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Visit a Name node."""
        if isinstance(node.ctx, ast.Load) and node.id in self.imports:
            self.used_names.add(node.id)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        """Visit an Attribute node."""
        if isinstance(node.value, ast.Name) and node.value.id in self.imports:
            self.used_names.add(node.value.id)
        self.generic_visit(node)
        
    def finalize(self):
        """Finalize the analysis."""
        for name, (node, import_name) in self.imports.items():
            if name not in self.used_names:
                self.unused_imports.append((node, import_name))


class CircularDependencyRule(BaseRule):
    """Rule for detecting circular dependencies in Python files."""
    
    def __init__(self):
        """Initialize the circular dependency rule."""
        super().__init__(
            rule_id="CI004",
            name="Circular Dependency Check",
            description="Checks for circular dependencies in the code."
        )
        
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        results = []
        # Build a dependency graph
        dependency_graph = self._build_dependency_graph(context)
        
        # Check for cycles in the graph
        cycles = self._find_cycles(dependency_graph)
        
        # Create results for each cycle
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            results.append(AnalysisResult(
                rule_id=self.rule_id,
                severity="warning",
                message=f"Circular dependency detected: {cycle_str}",
                details={"error_type": "circular_dependency", "cycle": cycle}
            ))
        
        return results
        
    def _build_dependency_graph(self, context) -> Dict[str, Set[str]]:
        """
        Build a dependency graph from the files in the PR.
        
        Args:
            context: Analysis context
            
        Returns:
            Dictionary mapping module names to sets of imported module names
        """
        graph: Dict[str, Set[str]] = {}
        
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"] and file_path.endswith(".py"):
                file_content = context.head_context.get_file_content(file_path)
                module_name = self._file_path_to_module_name(file_path)
                
                if module_name not in graph:
                    graph[module_name] = set()
                
                try:
                    tree = ast.parse(file_content, filename=file_path)
                    imports = self._extract_imports(tree)
                    
                    for imported_module in imports:
                        graph[module_name].add(imported_module)
                except SyntaxError:
                    # Syntax errors will be caught by the SyntaxErrorRule
                    pass
        
        return graph
        
    def _file_path_to_module_name(self, file_path: str) -> str:
        """
        Convert a file path to a module name.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Module name
        """
        # Remove .py extension
        if file_path.endswith(".py"):
            file_path = file_path[:-3]
        
        # Replace / with .
        module_name = file_path.replace("/", ".")
        
        return module_name
        
    def _extract_imports(self, tree: ast.AST) -> Set[str]:
        """
        Extract imported module names from an AST.
        
        Args:
            tree: AST of a Python file
            
        Returns:
            Set of imported module names
        """
        imports = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
        
        return imports
        
    def _find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Find cycles in a dependency graph.
        
        Args:
            graph: Dependency graph
            
        Returns:
            List of cycles, where each cycle is a list of module names
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        path: List[str] = []
        
        def dfs(node: str) -> None:
            if node in path:
                cycle = path[path.index(node):] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph:  # Only consider nodes that are in our graph
                    dfs(neighbor)
            
            path.pop()
        
        for node in graph:
            dfs(node)
        
        return cycles

