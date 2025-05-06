"""
Rule for detecting missing edge cases.

This module provides a rule for detecting potential missing edge cases.
"""

import ast
import logging
from typing import Any, Dict, List, Set

from pr_static_analysis.rules.base import RuleResult, RuleSeverity
from pr_static_analysis.rules.implementation_validation import BaseImplementationValidationRule

logger = logging.getLogger(__name__)


class MissingEdgeCaseRule(BaseImplementationValidationRule):
    """
    Rule for detecting potential missing edge cases.
    
    This rule checks for various edge cases that might be missing, such as:
    - Division by zero
    - Array bounds checking
    - File operation error handling
    - Null/None reference checks
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
            "Detects potential missing edge cases, such as division by zero, "
            "array bounds checking, file operation error handling, and null/None reference checks."
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
                    results.extend(self._check_division_by_zero(tree, filepath, content))
                
                # Check for array bounds
                if self.config.get("check_array_bounds", True):
                    results.extend(self._check_array_bounds(tree, filepath, content))
                
                # Check for file operations
                if self.config.get("check_file_operations", True):
                    results.extend(self._check_file_operations(tree, filepath, content))
                
                # Check for null references
                if self.config.get("check_null_references", True):
                    results.extend(self._check_null_references(tree, filepath, content))
            
            except SyntaxError:
                # Skip files with syntax errors (they will be caught by the syntax error rule)
                continue
        
        return results
    
    def _check_division_by_zero(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for potential division by zero.
        
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
                self.potential_divisions_by_zero = []
            
            def visit_BinOp(self, node):
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    # Check if the divisor is a constant zero
                    if (
                        isinstance(node.right, ast.Constant)
                        and node.right.value == 0
                    ):
                        self.potential_divisions_by_zero.append(node)
                    # Check if the divisor is a variable without a check
                    elif isinstance(node.right, ast.Name):
                        # This is a simplistic check; in a real implementation,
                        # we would do data flow analysis to see if the variable
                        # is checked for zero before the division
                        self.potential_divisions_by_zero.append(node)
                
                self.generic_visit(node)
        
        visitor = DivisionVisitor()
        visitor.visit(tree)
        
        for node in visitor.potential_divisions_by_zero:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="Potential division by zero",
                    filepath=filepath,
                    line=node.lineno,
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
        Check for potential array bounds issues.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class ArrayBoundsVisitor(ast.NodeVisitor):
            def __init__(self):
                self.potential_bounds_issues = []
            
            def visit_Subscript(self, node):
                # Check if the index is a variable without a bounds check
                if isinstance(node.slice, ast.Name):
                    # This is a simplistic check; in a real implementation,
                    # we would do data flow analysis to see if the variable
                    # is checked for bounds before the subscript
                    self.potential_bounds_issues.append(node)
                
                self.generic_visit(node)
        
        visitor = ArrayBoundsVisitor()
        visitor.visit(tree)
        
        for node in visitor.potential_bounds_issues:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="Potential array bounds issue",
                    filepath=filepath,
                    line=node.lineno,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Add a check to ensure the index is within bounds",
                        "Use a try-except block to catch IndexError",
                        "Use the `get` method for dictionaries with a default value",
                    ],
                )
            )
        
        return results
    
    def _check_file_operations(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for potential file operation issues.
        
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
                self.potential_file_issues = []
                self.in_try_except = False
            
            def visit_Try(self, node):
                old_in_try_except = self.in_try_except
                self.in_try_except = True
                self.generic_visit(node)
                self.in_try_except = old_in_try_except
            
            def visit_Call(self, node):
                # Check for file operations without error handling
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "open"
                    and not self.in_try_except
                ):
                    self.potential_file_issues.append(node)
                
                self.generic_visit(node)
        
        visitor = FileOperationVisitor()
        visitor.visit(tree)
        
        for node in visitor.potential_file_issues:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="File operation without error handling",
                    filepath=filepath,
                    line=node.lineno,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Use a try-except block to catch file operation errors",
                        "Check if the file exists before opening it",
                        "Use a context manager (with statement) for file operations",
                    ],
                )
            )
        
        return results
    
    def _check_null_references(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for potential null reference issues.
        
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
                self.potential_null_issues = []
                self.checked_vars: Set[str] = set()
            
            def visit_If(self, node):
                # Track variables that are checked for None
                if (
                    isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and any(
                        isinstance(op, (ast.Is, ast.IsNot, ast.Eq, ast.NotEq))
                        for op in node.test.ops
                    )
                    and any(
                        isinstance(comp, ast.Constant) and comp.value is None
                        for comp in node.test.comparators
                    )
                ):
                    self.checked_vars.add(node.test.left.id)
                
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Check for attribute access on a variable that might be None
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id not in self.checked_vars
                ):
                    self.potential_null_issues.append(node)
                
                self.generic_visit(node)
        
        visitor = NullReferenceVisitor()
        visitor.visit(tree)
        
        for node in visitor.potential_null_issues:
            results.append(
                RuleResult(
                    rule_id=self.id,
                    severity=self.severity,
                    message="Potential null reference issue",
                    filepath=filepath,
                    line=node.lineno,
                    code_snippet=ast.get_source_segment(content, node),
                    fix_suggestions=[
                        "Add a check to ensure the variable is not None",
                        "Use the `getattr` function with a default value",
                        "Use a try-except block to catch AttributeError",
                    ],
                )
            )
        
        return results

