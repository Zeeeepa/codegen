"""
Rule for detecting syntax errors in code.

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
    Rule for detecting syntax errors in Python code.
    
    This rule parses Python files to detect syntax errors.
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
        return "Detects syntax errors in Python code by attempting to parse the files."
    
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
                # Create a result for the syntax error
                results.append(
                    RuleResult(
                        rule_id=self.id,
                        severity=self.severity,
                        message=f"Syntax error: {str(e)}",
                        filepath=filepath,
                        line=e.lineno,
                        column=e.offset,
                        code_snippet=e.text,
                        fix_suggestions=[
                            "Check for missing parentheses, brackets, or quotes",
                            "Ensure proper indentation",
                            "Verify that all keywords are spelled correctly",
                        ],
                    )
                )
        
        return results

