"""
Style Rule Module

This module provides a rule for checking code style.
"""

import re
from typing import List, Dict, Any
from .base_rule import BaseRule, AnalysisResult


class StyleRule(BaseRule):
    """
    Rule for checking code style.
    
    This rule checks for style issues like line length, indentation, etc.
    """
    
    def __init__(self, max_line_length: int = 100):
        """
        Initialize a new style rule.
        
        Args:
            max_line_length: Maximum allowed line length
        """
        super().__init__(
            rule_id="style",
            name="Code Style Check",
            description=f"Checks for code style issues like lines longer than {max_line_length} characters",
            category="code_quality"
        )
        self.max_line_length = max_line_length
    
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the given context and return results.
        
        Args:
            context: Context to apply the rule to
            
        Returns:
            List of analysis results
        """
        results = []
        
        # Get file changes
        file_changes = context.get_file_changes()
        
        # Check added and modified files
        for file_path, change_type in file_changes.items():
            if change_type in ["added", "modified"]:
                # Get the file content
                content = context.head_context.get_file_content(file_path)
                
                # Skip if content is None
                if content is None:
                    continue
                
                # Check each line
                for i, line in enumerate(content.splitlines(), 1):
                    # Check line length
                    if len(line) > self.max_line_length:
                        results.append(
                            AnalysisResult(
                                rule_id=self.rule_id,
                                severity="info",
                                message=f"Line {i} is too long ({len(line)} > {self.max_line_length})",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line,
                                metadata={
                                    "line_length": len(line),
                                    "max_line_length": self.max_line_length,
                                }
                            )
                        )
                    
                    # Check trailing whitespace
                    if line.rstrip() != line:
                        results.append(
                            AnalysisResult(
                                rule_id=self.rule_id,
                                severity="info",
                                message=f"Line {i} has trailing whitespace",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line,
                            )
                        )
                    
                    # Check mixed tabs and spaces
                    if "\t" in line and " " in line:
                        results.append(
                            AnalysisResult(
                                rule_id=self.rule_id,
                                severity="info",
                                message=f"Line {i} has mixed tabs and spaces",
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line,
                            )
                        )
        
        return results

