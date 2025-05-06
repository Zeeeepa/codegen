"""
Base Rule

Base class for all analysis rules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext


class BaseRule(ABC):
    """
    Base class for all analysis rules.
    
    Analysis rules examine a pull request and identify potential issues.
    Each rule should focus on a specific aspect of code quality or correctness.
    """
    
    rule_id: str = "base_rule"
    """Unique identifier for the rule."""
    
    rule_name: str = "Base Rule"
    """Human-readable name for the rule."""
    
    rule_description: str = "Base class for all analysis rules."
    """Description of what the rule checks for."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the rule with optional configuration.
        
        Args:
            config: Configuration options for the rule
        """
        self.config = config or {}
    
    @abstractmethod
    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Analyze the PR and return the results.
        
        Args:
            context: The analysis context containing PR and codebase information
            
        Returns:
            A dictionary containing the analysis results
        """
        pass
    
    def create_issue(
        self,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        message: str = "",
        severity: str = "warning",
        code: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an issue object for reporting.
        
        Args:
            file_path: The path of the file where the issue was found
            line_number: The line number where the issue was found
            message: A description of the issue
            severity: The severity of the issue ("info", "warning", or "error")
            code: The code snippet related to the issue
            suggestion: A suggested fix for the issue
            
        Returns:
            A dictionary representing the issue
        """
        return {
            "file_path": file_path,
            "line_number": line_number,
            "message": message,
            "severity": severity,
            "code": code,
            "suggestion": suggestion,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name
        }

