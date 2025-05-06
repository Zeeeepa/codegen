"""
Docstring Rule Module

This module provides a rule for checking docstrings.
"""

from typing import List, Dict, Any
from .base_rule import BaseRule, AnalysisResult


class DocstringRule(BaseRule):
    """
    Rule for checking docstrings.
    
    This rule checks if functions and classes have docstrings.
    """
    
    def __init__(self):
        """Initialize a new docstring rule."""
        super().__init__(
            rule_id="docstring",
            name="Docstring Check",
            description="Checks if functions and classes have docstrings",
            category="documentation"
        )
    
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the given context and return results.
        
        Args:
            context: Context to apply the rule to
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Check functions
        function_changes = context.get_function_changes()
        for func_name, change_info in function_changes.items():
            if change_info["change_type"] in ["added", "modified"]:
                # Get the function
                func = change_info.get("function") or change_info.get("head_function")
                
                # Check if the function has a docstring
                if not self._has_docstring(func):
                    results.append(
                        AnalysisResult(
                            rule_id=self.rule_id,
                            severity="warning",
                            message=f"Function '{func_name}' is missing a docstring",
                            file_path=func.filepath if hasattr(func, "filepath") else None,
                            line_number=func.line_range[0] if hasattr(func, "line_range") else None,
                        )
                    )
        
        # Check classes
        class_changes = context.get_class_changes()
        for class_name, change_info in class_changes.items():
            if change_info["change_type"] in ["added", "modified"]:
                # Get the class
                cls = change_info.get("class") or change_info.get("head_class")
                
                # Check if the class has a docstring
                if not self._has_docstring(cls):
                    results.append(
                        AnalysisResult(
                            rule_id=self.rule_id,
                            severity="warning",
                            message=f"Class '{class_name}' is missing a docstring",
                            file_path=cls.filepath if hasattr(cls, "filepath") else None,
                            line_number=cls.line_range[0] if hasattr(cls, "line_range") else None,
                        )
                    )
        
        return results
    
    def _has_docstring(self, symbol) -> bool:
        """
        Check if a symbol has a docstring.
        
        Args:
            symbol: Symbol to check
            
        Returns:
            True if the symbol has a docstring, False otherwise
        """
        # Check if the symbol has a docstring attribute
        if hasattr(symbol, "docstring"):
            return bool(symbol.docstring)
        
        # Check if the symbol has a body attribute that might contain a docstring
        if hasattr(symbol, "body") and symbol.body:
            # Check if the first line of the body is a docstring
            body = symbol.body
            if isinstance(body, list) and body:
                first_line = body[0].strip() if isinstance(body[0], str) else str(body[0]).strip()
                return first_line.startswith('"""') or first_line.startswith("'''")
            elif isinstance(body, str) and body.strip():
                first_line = body.strip().split('\n')[0]
                return first_line.startswith('"""') or first_line.startswith("'''")
        
        return False

