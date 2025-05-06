"""
Base Rule Module

This module provides the base class for all analysis rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisResult:
    """
    Represents a result from an analysis rule.
    
    Attributes:
        rule_id: ID of the rule that produced this result
        severity: Severity level of the result (error, warning, info)
        message: Human-readable message describing the result
        file_path: Optional path to the file related to the result
        line_number: Optional line number in the file
        code_snippet: Optional code snippet related to the result
        metadata: Optional additional metadata about the result
    """
    rule_id: str
    severity: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseRule(ABC):
    """
    Base class for all analysis rules.
    
    All rules should inherit from this class and implement the apply method.
    """
    
    def __init__(self, rule_id: str, name: str, description: str, category: str):
        """
        Initialize a new rule.
        
        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name for the rule
            description: Description of what the rule checks for
            category: Category of the rule (e.g., "security", "performance")
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.category = category
    
    @abstractmethod
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the given context and return results.
        
        Args:
            context: Context to apply the rule to
            
        Returns:
            List of analysis results
        """
        pass
    
    def get_documentation(self) -> Dict[str, str]:
        """
        Get documentation for this rule.
        
        Returns:
            Dictionary with rule documentation
        """
        return {
            "id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
        }

