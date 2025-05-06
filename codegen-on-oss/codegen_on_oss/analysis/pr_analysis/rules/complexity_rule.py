"""
Complexity Rule Module

This module provides a rule for checking code complexity.
"""

from typing import List, Dict, Any
from .base_rule import BaseRule, AnalysisResult


class ComplexityRule(BaseRule):
    """
    Rule for checking code complexity.
    
    This rule checks for functions with high cyclomatic complexity.
    """
    
    def __init__(self, max_complexity: int = 10):
        """
        Initialize a new complexity rule.
        
        Args:
            max_complexity: Maximum allowed cyclomatic complexity
        """
        super().__init__(
            rule_id="complexity",
            name="Function Complexity Check",
            description=f"Checks for functions with cyclomatic complexity greater than {max_complexity}",
            category="code_quality"
        )
        self.max_complexity = max_complexity
    
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the given context and return results.
        
        Args:
            context: Context to apply the rule to
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Get function changes
        function_changes = context.get_function_changes()
        
        # Check added and modified functions
        for func_name, change_info in function_changes.items():
            if change_info["change_type"] in ["added", "modified"]:
                # Get the function
                func = change_info.get("function") or change_info.get("head_function")
                
                # Check if the function has a complexity attribute
                if hasattr(func, "cyclomatic_complexity"):
                    complexity = func.cyclomatic_complexity
                    
                    # Check if complexity exceeds the threshold
                    if complexity > self.max_complexity:
                        results.append(
                            AnalysisResult(
                                rule_id=self.rule_id,
                                severity="warning",
                                message=f"Function '{func_name}' has high cyclomatic complexity ({complexity})",
                                file_path=func.filepath if hasattr(func, "filepath") else None,
                                line_number=func.line_range[0] if hasattr(func, "line_range") else None,
                                metadata={
                                    "complexity": complexity,
                                    "max_complexity": self.max_complexity,
                                    "function_name": func_name,
                                }
                            )
                        )
        
        return results

