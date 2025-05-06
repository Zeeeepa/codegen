"""
Implementation validation rules for PR static analysis.

This module defines rules for detecting implementation validation issues such as
feature completeness, test coverage, performance implications, and security considerations.
"""

import ast
import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple

from .base_rule import BaseRule, AnalysisResult


class FeatureCompletenessRule(BaseRule):
    """Rule for detecting incomplete feature implementations."""
    
    def __init__(self):
        """Initialize the feature completeness rule."""
        super().__init__(
            rule_id="IV001",
            name="Feature Completeness Check",
            description="Checks if a feature is completely implemented."
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
        
        # Check for TODO, FIXME, and similar markers in the code
        for file_path, change_type in context.get_file_changes().items():
            if change_type in ["added", "modified"]:
                file_content = context.head_context.get_file_content(file_path)
                incomplete_features = self._check_incomplete_features(file_path, file_content)
                results.extend(incomplete_features)
        
        return results
        
    def _check_incomplete_features(self, file_path: str, content: str) -> List[AnalysisResult]:
        """
        Check for incomplete features in code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Look for TODO, FIXME, and similar markers
        todo_pattern = re.compile(r'(TODO|FIXME|XXX|HACK|BUG)[\s:](.*)', re.IGNORECASE)
        
        for i, line in enumerate(content.splitlines(), 1):
            match = todo_pattern.search(line)
            if match:
                marker = match.group(1)
                message = match.group(2).strip()
                
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Incomplete feature: {marker} - {message}",
                    file=file_path,
                    line=i,
                    details={
                        "error_type": "incomplete_feature",
                        "marker": marker,
                        "message": message
                    }
                ))
        
        # Look for NotImplementedError and pass statements in function bodies
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = IncompleteFeatureVisitor()
            visitor.visit(tree)
            
            for node, issue_type, message in visitor.incomplete_features:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Incomplete feature: {message}",
                    file=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    details={
                        "error_type": "incomplete_feature",
                        "issue_type": issue_type,
                        "message": message
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class IncompleteFeatureVisitor(ast.NodeVisitor):
    """AST visitor for finding incomplete features."""
    
    def __init__(self):
        """Initialize the visitor."""
        self.incomplete_features = []
        
    def visit_FunctionDef(self, node):
        """Visit a FunctionDef node."""
        # Check if the function body contains only 'pass'
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.incomplete_features.append(
                (node, "empty_function", f"Function '{node.name}' contains only 'pass'")
            )
        
        # Check if the function body raises NotImplementedError
        for stmt in node.body:
            if isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Name) and stmt.exc.id == "NotImplementedError":
                    self.incomplete_features.append(
                        (node, "not_implemented", f"Function '{node.name}' raises NotImplementedError")
                    )
                elif isinstance(stmt.exc, ast.Call) and isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                    self.incomplete_features.append(
                        (node, "not_implemented", f"Function '{node.name}' raises NotImplementedError")
                    )
        
        self.generic_visit(node)


class TestCoverageRule(BaseRule):
    """Rule for detecting insufficient test coverage."""
    
    def __init__(self):
        """Initialize the test coverage rule."""
        super().__init__(
            rule_id="IV002",
            name="Test Coverage Check",
            description="Checks if the code has sufficient test coverage."
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
        
        # Get all added or modified Python files
        python_files = [
            file_path for file_path, change_type in context.get_file_changes().items()
            if change_type in ["added", "modified"] and file_path.endswith(".py")
            and not file_path.startswith("tests/") and not file_path.endswith("_test.py")
            and not file_path.endswith("test_.py")
        ]
        
        # Check if there are corresponding test files
        for file_path in python_files:
            test_files = self._find_test_files(file_path, context)
            
            if not test_files:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"No test file found for {file_path}",
                    file=file_path,
                    details={
                        "error_type": "missing_tests",
                        "file": file_path
                    }
                ))
            else:
                # Check if all public functions are tested
                file_content = context.head_context.get_file_content(file_path)
                public_functions = self._extract_public_functions(file_path, file_content)
                
                for test_file in test_files:
                    test_content = context.head_context.get_file_content(test_file)
                    tested_functions = self._extract_tested_functions(test_file, test_content, file_path)
                    
                    for func_name in public_functions:
                        if func_name not in tested_functions:
                            results.append(AnalysisResult(
                                rule_id=self.rule_id,
                                severity="info",
                                message=f"Function '{func_name}' in {file_path} may not be tested",
                                file=file_path,
                                details={
                                    "error_type": "untested_function",
                                    "file": file_path,
                                    "function": func_name
                                }
                            ))
        
        return results
        
    def _find_test_files(self, file_path: str, context) -> List[str]:
        """
        Find test files for a given file.
        
        Args:
            file_path: Path to the file
            context: Analysis context
            
        Returns:
            List of test file paths
        """
        # Extract the module name from the file path
        module_name = os.path.basename(file_path)
        if module_name.endswith(".py"):
            module_name = module_name[:-3]
        
        # Look for test files in the tests directory
        test_files = []
        
        # Pattern 1: tests/test_<module>.py
        test_file_1 = f"tests/test_{module_name}.py"
        if test_file_1 in context.head_context.get_files():
            test_files.append(test_file_1)
        
        # Pattern 2: tests/<module>_test.py
        test_file_2 = f"tests/{module_name}_test.py"
        if test_file_2 in context.head_context.get_files():
            test_files.append(test_file_2)
        
        # Pattern 3: <directory>/tests/test_<module>.py
        directory = os.path.dirname(file_path)
        test_file_3 = f"{directory}/tests/test_{module_name}.py"
        if test_file_3 in context.head_context.get_files():
            test_files.append(test_file_3)
        
        return test_files
        
    def _extract_public_functions(self, file_path: str, content: str) -> Set[str]:
        """
        Extract public functions from a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            
        Returns:
            Set of public function names
        """
        public_functions = set()
        
        try:
            tree = ast.parse(content, filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    public_functions.add(node.name)
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return public_functions
        
    def _extract_tested_functions(self, test_file: str, content: str, source_file: str) -> Set[str]:
        """
        Extract tested functions from a test file.
        
        Args:
            test_file: Path to the test file
            content: Content of the test file
            source_file: Path to the source file being tested
            
        Returns:
            Set of tested function names
        """
        tested_functions = set()
        
        # Extract the module name from the source file path
        module_name = os.path.basename(source_file)
        if module_name.endswith(".py"):
            module_name = module_name[:-3]
        
        try:
            tree = ast.parse(content, filename=test_file)
            
            # Look for function calls that might be testing functions in the source file
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == module_name:
                            tested_functions.add(node.func.attr)
                    elif isinstance(node.func, ast.Name):
                        tested_functions.add(node.func.id)
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return tested_functions


class PerformanceImplicationRule(BaseRule):
    """Rule for detecting performance implications in code changes."""
    
    def __init__(self):
        """Initialize the performance implication rule."""
        super().__init__(
            rule_id="IV003",
            name="Performance Implication Check",
            description="Checks for performance implications in code changes."
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
                performance_issues = self._check_performance_issues(file_path, file_content)
                results.extend(performance_issues)
        
        return results
        
    def _check_performance_issues(self, file_path: str, content: str) -> List[AnalysisResult]:
        """
        Check for performance issues in code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            
        Returns:
            List of analysis results
        """
        results = []
        
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = PerformanceIssueVisitor()
            visitor.visit(tree)
            
            for node, issue_type, message in visitor.performance_issues:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="info",
                    message=f"Performance issue: {message}",
                    file=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    details={
                        "error_type": "performance_issue",
                        "issue_type": issue_type,
                        "message": message
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class PerformanceIssueVisitor(ast.NodeVisitor):
    """AST visitor for finding performance issues."""
    
    def __init__(self):
        """Initialize the visitor."""
        self.performance_issues = []
        
    def visit_For(self, node):
        """Visit a For node."""
        # Check for inefficient list comprehensions
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            # Check if the loop body contains only a single append to a list
            if len(node.body) == 1 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Call):
                call = node.body[0].value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    self.performance_issues.append(
                        (node, "inefficient_loop", "Consider using a list comprehension instead of a for loop with append")
                    )
        
        self.generic_visit(node)
        
    def visit_BinOp(self, node):
        """Visit a BinOp node."""
        # Check for string concatenation in a loop
        if isinstance(node.op, ast.Add) and isinstance(node.left, ast.Name) and isinstance(node.right, ast.Str):
            # This is a simplification; in a real implementation, we would need
            # to check if this is inside a loop
            self.performance_issues.append(
                (node, "string_concat", "String concatenation with '+' can be inefficient; consider using join() or f-strings")
            )
        
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Visit a Call node."""
        # Check for inefficient list operations
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "keys" and len(node.args) == 0:
                # Check if this is used in a membership test
                parent = self.get_parent(node)
                if isinstance(parent, ast.Compare) and isinstance(parent.ops[0], (ast.In, ast.NotIn)):
                    self.performance_issues.append(
                        (node, "inefficient_dict_lookup", "Use 'key in dict' instead of 'key in dict.keys()' for better performance")
                    )
        
        self.generic_visit(node)
        
    def get_parent(self, node):
        """Get the parent node of a node (simplified)."""
        # This is a placeholder; in a real implementation, we would need
        # to track parent nodes during traversal
        return None


class SecurityConsiderationRule(BaseRule):
    """Rule for detecting security considerations in code changes."""
    
    def __init__(self):
        """Initialize the security consideration rule."""
        super().__init__(
            rule_id="IV004",
            name="Security Consideration Check",
            description="Checks for security considerations in code changes."
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
                security_issues = self._check_security_issues(file_path, file_content)
                results.extend(security_issues)
        
        return results
        
    def _check_security_issues(self, file_path: str, content: str) -> List[AnalysisResult]:
        """
        Check for security issues in code.
        
        Args:
            file_path: Path to the file being checked
            content: Content of the file
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Check for hardcoded secrets
        secret_pattern = re.compile(
            r'(password|secret|key|token|credential)s?\s*=\s*[\'"]((?!dummy|example|placeholder|changeme).{8,})[\'"]',
            re.IGNORECASE
        )
        
        for i, line in enumerate(content.splitlines(), 1):
            match = secret_pattern.search(line)
            if match:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="error",
                    message=f"Potential hardcoded secret: {match.group(1)}",
                    file=file_path,
                    line=i,
                    details={
                        "error_type": "hardcoded_secret",
                        "secret_type": match.group(1)
                    }
                ))
        
        # Check for other security issues using AST
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = SecurityIssueVisitor()
            visitor.visit(tree)
            
            for node, issue_type, message in visitor.security_issues:
                results.append(AnalysisResult(
                    rule_id=self.rule_id,
                    severity="warning",
                    message=f"Security issue: {message}",
                    file=file_path,
                    line=node.lineno,
                    column=node.col_offset,
                    details={
                        "error_type": "security_issue",
                        "issue_type": issue_type,
                        "message": message
                    }
                ))
        except SyntaxError:
            # Syntax errors will be caught by the SyntaxErrorRule
            pass
        
        return results


class SecurityIssueVisitor(ast.NodeVisitor):
    """AST visitor for finding security issues."""
    
    def __init__(self):
        """Initialize the visitor."""
        self.security_issues = []
        
    def visit_Call(self, node):
        """Visit a Call node."""
        # Check for dangerous functions
        if isinstance(node.func, ast.Name):
            # Check for eval, exec, etc.
            if node.func.id in ["eval", "exec", "compile"]:
                self.security_issues.append(
                    (node, "dangerous_function", f"Use of potentially dangerous function '{node.func.id}'")
                )
            
            # Check for os.system, subprocess.call, etc.
            if node.func.id in ["system", "popen", "call", "Popen"]:
                self.security_issues.append(
                    (node, "command_injection", f"Potential command injection vulnerability with '{node.func.id}'")
                )
        
        # Check for SQL injection
        if isinstance(node.func, ast.Attribute) and node.func.attr in ["execute", "executemany", "raw"]:
            # Check if any of the arguments is a formatted string or string concatenation
            for arg in node.args:
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add) and (isinstance(arg.left, ast.Str) or isinstance(arg.right, ast.Str)):
                    self.security_issues.append(
                        (node, "sql_injection", "Potential SQL injection vulnerability with string concatenation")
                    )
                elif isinstance(arg, ast.JoinedStr):
                    self.security_issues.append(
                        (node, "sql_injection", "Potential SQL injection vulnerability with f-string")
                    )
        
        self.generic_visit(node)

