"""
Base class for analysis rules.

This module provides the BaseRule class, which is the base class for all
analysis rules in the PR analysis system.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, ClassVar

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext


logger = logging.getLogger(__name__)


class BaseRule(ABC):
    """
    Base class for analysis rules.
    
    This class defines the interface for analysis rules and provides common
    functionality for rule configuration and execution.
    
    Attributes:
        rule_id: Rule ID
        name: Rule name
        description: Rule description
        context: Analysis context
        config: Rule configuration
    """
    
    rule_id: ClassVar[str]
    name: ClassVar[str]
    description: ClassVar[str]
    
    def __init__(self, context: AnalysisContext):
        """
        Initialize the rule.
        
        Args:
            context: Analysis context
        """
        self.context = context
        self.config = {}
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the rule.
        
        Args:
            config: Rule configuration
        """
        self.config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Run the rule.
        
        Returns:
            Rule results
        """
        pass
    
    def get_severity(self) -> str:
        """
        Get the rule severity.
        
        Returns:
            Rule severity (high, medium, low, info)
        """
        return self.get_config('severity', 'medium')
    
    def create_result(self, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a rule result.
        
        Args:
            status: Result status (success, warning, error)
            message: Result message
            details: Result details (optional)
            
        Returns:
            Rule result
        """
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'severity': self.get_severity(),
            'status': status,
            'message': message,
            'details': details or {}
        }
    
    def success(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a success result.
        
        Args:
            message: Result message
            details: Result details (optional)
            
        Returns:
            Success result
        """
        return self.create_result('success', message, details)
    
    def warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a warning result.
        
        Args:
            message: Result message
            details: Result details (optional)
            
        Returns:
            Warning result
        """
        return self.create_result('warning', message, details)
    
    def error(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an error result.
        
        Args:
            message: Result message
            details: Result details (optional)
            
        Returns:
            Error result
        """
        return self.create_result('error', message, details)

