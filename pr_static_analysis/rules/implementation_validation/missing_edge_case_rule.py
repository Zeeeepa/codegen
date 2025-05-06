"""
Rule for detecting missing edge cases.

This module provides a rule for detecting potential missing edge cases in code.
"""

import ast
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pr_static_analysis.rules.base import RuleResult, RuleSeverity
from pr_static_analysis.rules.implementation_validation import (
    BaseImplementationValidationRule,
)

logger = logging.getLogger(__name__)


class MissingEdgeCaseRule(BaseImplementationValidationRule):
    """
    Rule for detecting potential missing edge cases in code.
    
    This rule checks for common patterns where edge cases might be missing, such as:
    - Division without checking for zero
    - Array access without bounds checking
    - File operations without error handling
    - Null/None checks
    """
    
    @property
    def id(self) -> str:
        """Get the unique identifier for the rule."""
        return "missing-edge-case"
    
    @property
    def name(self) -> str:
        """Get the human-readable name for the rule."""
        return "Missing Edge Case Detection"
    
    @property
    def description(self) -> str:
        """Get the detailed description of what the rule checks for."""
        return (
            "Detects potential missing edge cases in code, such as division without "
            "checking for zero, array access without bounds checking, file operations "
            "without error handling, and missing null/None checks."
        )
    
    @property
    def severity(self) -> RuleSeverity:
        """Get the default severity level for issues found by this rule."""
        return RuleSeverity.WARNING
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get the default configuration options for the rule.
        
        Returns:
            A dictionary of configuration options
        """
        return {
            "check_division_by_zero": True,
            "check_array_bounds": True,
            "check_file_operations": True,
            "check_null_references": True,
        }
    
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        """
        Analyze the PR for missing edge cases.
        
        Args:
            context: Context information for the analysis
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        # Get the files from the context
        files = context.get("files", [])
        
        for file_info in files:
            filepath = file_info.get("filepath")
            content = file_info.get("content")
            
            # Skip non-Python files
            if not filepath.endswith(".py"):
                continue
            
            # Skip empty files
            if not content:
                continue
            
            # Parse the file
            try:
                tree = ast.parse(content)
                
                # Check for division by zero
                if self.config.get("check_division_by_zero", True):
                    results.extend(
                        self._check_division_by_zero(tree, filepath, content)
                    )
                
                # Check for array bounds
                if self.config.get("check_array_bounds", True):
                    results.extend(self._check_array_bounds(tree, filepath, content))
                
                # Check for file operations
                if self.config.get("check_file_operations", True):
                    results.extend(
                        self._check_file_operations(tree, filepath, content)
                    )
                
                # Check for null references
                if self.config.get("check_null_references", True):
                    results.extend(
                        self._check_null_references(tree, filepath, content)
                    )
            
            except SyntaxError:
                # Skip files with syntax errors (they will be caught by the syntax error rule)
                continue
        
        return results
    
    def _check_division_by_zero(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for division operations without checking for zero.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class DivisionVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unsafe_divisions = []
                self.checked_names = set()
            
            def visit_If(self, node):
                # Look for zero checks in if conditions
                if isinstance(node.test, ast.Compare):
                    # Check for patterns like "if x != 0:" or "if x > 0:"
                    if isinstance(node.test.left, ast.Name):
                        name = node.test.left.id
                        for op, comparator in zip(node.test.ops, node.test.comparators):
                            if (
                                isinstance(op, (ast.Eq, ast.NotEq, ast.Gt, ast.Lt, ast.GtE, ast.LtE))
                                and isinstance(comparator, ast.Constant)
                                and comparator.value == 0
                            ):
                                self.checked_names.add(name)
                
                self.generic_visit(node)
            
            def visit_BinOp(self, node):
                # Check for division operations
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Name) and node.right.id not in self.checked_names:
                        self.unsafe_divisions.append(node)
                    elif isinstance(node.right, ast.Constant) and node.right.value == 0:
                        # Division by literal 0 is a definite error
                        self.unsafe_divisions.append(node)
                    elif not isinstance(node.right, ast.Constant):
                        # Any non-constant divisor that isn't a checked name is potentially unsafe
                        self.unsafe_divisions.append(node)
                
                self.generic_visit(node)
        
        visitor = DivisionVisitor()
        visitor.visit(tree)
        
        for node in visitor.unsafe_divisions:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="Potential division by zero",
                    filepath=filepath,
                    line=node.lineno if hasattr(node, "lineno") else None,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Add a check to ensure the divisor is not zero",
                        "Use a try-except block to catch ZeroDivisionError",
                        "Provide a default value or alternative behavior for the zero case",
                    ],
                )
            )
        
        return results
    
    def _check_array_bounds(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for array access without bounds checking.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class ArrayAccessVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unsafe_accesses = []
                self.checked_indices = set()
                self.length_checks = {}  # Map from array name to checked length
            
            def visit_If(self, node):
                # Look for bounds checks in if conditions
                if isinstance(node.test, ast.Compare):
                    # Check for patterns like "if i < len(arr):" or "if 0 <= i < len(arr):"
                    if isinstance(node.test.left, ast.Name):
                        index_name = node.test.left.id
                        for op, comparator in zip(node.test.ops, node.test.comparators):
                            if isinstance(op, (ast.Lt, ast.LtE)) and isinstance(comparator, ast.Call):
                                if (
                                    isinstance(comparator.func, ast.Name)
                                    and comparator.func.id == "len"
                                    and len(comparator.args) == 1
                                    and isinstance(comparator.args[0], ast.Name)
                                ):
                                    array_name = comparator.args[0].id
                                    self.length_checks[array_name] = index_name
                                    self.checked_indices.add(index_name)
                
                self.generic_visit(node)
            
            def visit_Subscript(self, node):
                # Check for array access operations
                if isinstance(node.value, ast.Name) and isinstance(node.slice, ast.Index):
                    array_name = node.value.id
                    if isinstance(node.slice.value, ast.Name):
                        index_name = node.slice.value.id
                        if (
                            index_name not in self.checked_indices
                            and array_name not in self.length_checks
                        ):
                            self.unsafe_accesses.append(node)
                    elif not isinstance(node.slice.value, ast.Constant):
                        # Any non-constant index that isn't checked is potentially unsafe
                        self.unsafe_accesses.append(node)
                
                self.generic_visit(node)
        
        visitor = ArrayAccessVisitor()
        visitor.visit(tree)
        
        for node in visitor.unsafe_accesses:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="Potential array index out of bounds",
                    filepath=filepath,
                    line=node.lineno if hasattr(node, "lineno") else None,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Add a check to ensure the index is within bounds",
                        "Use a try-except block to catch IndexError",
                        "Use the .get() method for dictionaries with a default value",
                        "Use list comprehension or other higher-level constructs to avoid explicit indexing",
                    ],
                )
            )
        
        return results
    
    def _check_file_operations(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for file operations without error handling.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class FileOperationVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unsafe_operations = []
                self.in_try_block = False
            
            def visit_Try(self, node):
                old_in_try = self.in_try_block
                self.in_try_block = True
                self.generic_visit(node)
                self.in_try_block = old_in_try
            
            def visit_Call(self, node):
                # Check for file operations
                if isinstance(node.func, ast.Name) and node.func.id == "open":
                    if not self.in_try_block:
                        self.unsafe_operations.append(node)
                
                self.generic_visit(node)
        
        visitor = FileOperationVisitor()
        visitor.visit(tree)
        
        for node in visitor.unsafe_operations:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="File operation without error handling",
                    filepath=filepath,
                    line=node.lineno if hasattr(node, "lineno") else None,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Wrap the file operation in a try-except block",
                        "Use a context manager (with statement) for file operations",
                        "Check if the file exists before opening it",
                    ],
                )
            )
        
        return results
    
    def _check_null_references(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for potential null/None references.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class NullReferenceVisitor(ast.NodeVisitor):
            def __init__(self):
                self.unsafe_references = []
                self.checked_names = set()
            
            def visit_If(self, node):
                # Look for None checks in if conditions
                if isinstance(node.test, ast.Compare):
                    # Check for patterns like "if x is not None:" or "if x is None:"
                    if isinstance(node.test.left, ast.Name):
                        name = node.test.left.id
                        for op, comparator in zip(node.test.ops, node.test.comparators):
                            if (
                                isinstance(op, (ast.Is, ast.IsNot))
                                and isinstance(comparator, ast.Constant)
                                and comparator.value is None
                            ):
                                self.checked_names.add(name)
                
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Check for attribute access on potentially None objects
                if isinstance(node.value, ast.Name) and node.value.id not in self.checked_names:
                    self.unsafe_references.append(node)
                
                self.generic_visit(node)
        
        visitor = NullReferenceVisitor()
        visitor.visit(tree)
        
        for node in visitor.unsafe_references:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message=f"Potential null reference when accessing attribute '{node.attr}'",
                    filepath=filepath,
                    line=node.lineno if hasattr(node, "lineno") else None,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        f"Add a check to ensure '{node.value.id}' is not None before accessing '{node.attr}'",
                        "Use the getattr() function with a default value",
                        "Use a try-except block to catch AttributeError",
                    ],
                )
            )
        
        return results

