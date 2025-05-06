"""
Rule for detecting syntax errors.

This module provides a rule for detecting syntax errors in code.
"""

import ast
import logging
from typing import Any, Dict, List

from pr_static_analysis.rules.base import RuleResult, RuleSeverity
from pr_static_analysis.rules.code_integrity import BaseCodeIntegrityRule

logger = logging.getLogger(__name__)


class SyntaxErrorRule(BaseCodeIntegrityRule):
    """
    Rule for detecting syntax errors in code.
    
    This rule checks for syntax errors in Python files.
    """
    
    @property
    def id(self) -> str:
        """Get the unique identifier for the rule."""
        return "syntax-error"
    
    @property
    def name(self) -> str:
        """Get the human-readable name for the rule."""
        return "Syntax Error Detection"
    
    @property
    def description(self) -> str:
        """Get the detailed description of what the rule checks for."""
        return "Detects syntax errors in Python files."
    
    @property
    def severity(self) -> RuleSeverity:
        """Get the default severity level for issues found by this rule."""
        return RuleSeverity.ERROR
    
    def analyze(self, context: Dict[str, Any]) -> List[RuleResult]:
        """
        Analyze the PR for syntax errors.
        
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
            
            # Try to parse the file
            try:
                ast.parse(content)
            except SyntaxError as e:
                # Get the line with the syntax error
                lines = content.split("\n")
                line_index = e.lineno - 1
                line = lines[line_index] if 0 <= line_index < len(lines) else ""
                
                # Create a code snippet with context
                start_line = max(0, line_index - 2)
                end_line = min(len(lines), line_index + 3)
                code_snippet = "\n".join(lines[start_line:end_line])
                
                # Add a result for the syntax error
                results.append(
                    RuleResult(
                        rule_id=self.id,
                        severity=self.severity,
                        message=f"Syntax error: {e.msg}",
                        filepath=filepath,
                        line=e.lineno,
                        column=e.offset,
                        code_snippet=code_snippet,
                        fix_suggestions=[
                            "Fix the syntax error according to Python syntax rules",
                            "Check for missing or extra parentheses, brackets, or braces",
                            "Check for indentation issues",
                            "Check for missing colons in control flow statements",
                        ],
                    )
                )
        
        return results

