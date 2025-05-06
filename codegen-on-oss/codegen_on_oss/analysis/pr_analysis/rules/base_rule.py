"""
Base rule class for PR static analysis.

This module defines the base rule class and analysis result class that all analysis rules
should inherit from. It provides the interface for rule implementation and result representation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class AnalysisResult:
    """Represents a result from an analysis rule."""
    
    def __init__(
        self,
        rule_id: str,
        severity: str,
        message: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an analysis result.
        
        Args:
            rule_id: Unique identifier for the rule that produced this result
            severity: Severity level ("error", "warning", or "info")
            message: Human-readable message describing the issue
            file: Path to the file where the issue was found (optional)
            line: Line number where the issue was found (optional)
            column: Column number where the issue was found (optional)
            details: Additional details about the issue (optional)
        """
        self.rule_id = rule_id
        self.severity = severity  # "error", "warning", or "info"
        self.message = message
        self.file = file
        self.line = line
        self.column = column
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "details": self.details,
        }
    
    def __str__(self) -> str:
        """Return a string representation of the result."""
        location = ""
        if self.file:
            location += f"File: {self.file}"
            if self.line:
                location += f", Line: {self.line}"
                if self.column:
                    location += f", Column: {self.column}"
        
        return f"[{self.severity.upper()}] {self.rule_id}: {self.message} {location}"


class BaseRule(ABC):
    """Base class for all analysis rules."""
    
    def __init__(self, rule_id: str, name: str, description: str):
        """
        Initialize a rule.
        
        Args:
            rule_id: Unique identifier for the rule
            name: Human-readable name for the rule
            description: Description of what the rule checks for
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        
    @abstractmethod
    def apply(self, context) -> List[AnalysisResult]:
        """
        Apply the rule to the context and return results.
        
        Args:
            context: Analysis context containing PR data and utilities
            
        Returns:
            List of analysis results
        """
        pass
    
    def __str__(self) -> str:
        """Return a string representation of the rule."""
        return f"{self.rule_id}: {self.name} - {self.description}"

