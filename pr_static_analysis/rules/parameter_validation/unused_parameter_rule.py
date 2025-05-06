"""
Rule for detecting unused parameters.

This module provides a rule for detecting unused parameters in functions.
"""

import ast
import logging
from typing import Any, Dict, List, Set

from pr_static_analysis.rules.base import RuleResult, RuleSeverity
from pr_static_analysis.rules.parameter_validation import BaseParameterValidationRule

logger = logging.getLogger(__name__)


class UnusedParameterRule(BaseParameterValidationRule):
    """
    Rule for detecting unused parameters in functions.
    
    This rule checks for parameters that are defined but never used within a function.
    """
    
    @property
    def id(self) -> str:
        """Get the unique identifier for the rule."""
        return "unused-parameter"
    
    @property
    def name(self) -> str:
        """Get the human-readable name for the rule."""
        return "Unused Parameter Detection"
    
    @property
    def description(self) -> str:
        """Get the detailed description of what the rule checks for."""
        return "Detects parameters that are defined but never used within a function."
    
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
            "ignore_self": True,
            "ignore_cls": True,
            "ignore_unused_args": True,
            "ignore_unused_kwargs": True,
            "ignore_private_methods": False,
            "ignore_special_methods": True,
        }
    
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        """
        Analyze the PR for unused parameters.
        
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
                
                # Check for unused parameters
                results.extend(self._check_unused_parameters(tree, filepath, content))
            
            except SyntaxError:
                # Skip files with syntax errors (they will be caught by the syntax error rule)
                continue
        
        return results
    
    def _check_unused_parameters(
        self, tree: ast.AST, filepath: str, content: str
    ) -> List[RuleResult]:
        """
        Check for unused parameters in functions.
        
        Args:
            tree: AST of the file
            filepath: Path to the file
            content: Content of the file
        
        Returns:
            A list of RuleResult objects representing issues found
        """
        results = []
        
        class FunctionVisitor(ast.NodeVisitor):
            def __init__(self, rule_config):
                self.functions_with_unused_params = []
                self.rule_config = rule_config
            
            def visit_FunctionDef(self, node):
                self._check_function(node)
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                self._check_function(node)
                self.generic_visit(node)
            
            def _check_function(self, node):
                # Skip special methods if configured to do so
                if (
                    self.rule_config.get("ignore_special_methods", True)
                    and node.name.startswith("__")
                    and node.name.endswith("__")
                ):
                    return
                
                # Skip private methods if configured to do so
                if (
                    self.rule_config.get("ignore_private_methods", False)
                    and node.name.startswith("_")
                    and not node.name.startswith("__")
                ):
                    return
                
                # Get all parameter names
                param_names = set()
                for arg in node.args.args:
                    # Skip 'self' and 'cls' if configured to do so
                    if (
                        arg.arg == "self"
                        and self.rule_config.get("ignore_self", True)
                    ) or (
                        arg.arg == "cls"
                        and self.rule_config.get("ignore_cls", True)
                    ):
                        continue
                    
                    param_names.add(arg.arg)
                
                # Skip *args and **kwargs if configured to do so
                if not self.rule_config.get("ignore_unused_args", True) and node.args.vararg:
                    param_names.add(node.args.vararg.arg)
                
                if not self.rule_config.get("ignore_unused_kwargs", True) and node.args.kwarg:
                    param_names.add(node.args.kwarg.arg)
                
                # Find all used names in the function body
                used_names = set()
                
                class NameVisitor(ast.NodeVisitor):
                    def visit_Name(self, node):
                        if isinstance(node.ctx, ast.Load):
                            used_names.add(node.id)
                        self.generic_visit(node)
                
                for stmt in node.body:
                    NameVisitor().visit(stmt)
                
                # Find unused parameters
                unused_params = param_names - used_names
                
                if unused_params:
                    self.functions_with_unused_params.append((node, unused_params))
        
        visitor = FunctionVisitor(self.config)
        visitor.visit(tree)
        
        for node, unused_params in visitor.functions_with_unused_params:
            for param in unused_params:
                results.append(
                    RuleResult(
                        rule_id=self.id,
                        severity=self.severity,
                        message=f"Unused parameter '{param}' in function '{node.name}'",
                        filepath=filepath,
                        line=node.lineno,
                        code_snippet=ast.get_source_segment(content, node),
                        fix_suggestions=[
                            f"Remove the unused parameter '{param}'",
                            f"Rename the parameter to '_{param}' to indicate it's unused",
                            "Use the parameter in the function body",
                        ],
                    )
                )
        
        return results

