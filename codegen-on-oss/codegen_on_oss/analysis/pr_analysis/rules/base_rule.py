"""
Base rule for PR analysis.

This module provides the BaseRule class, which is the base class for all analysis rules.
"""

import logging
from typing import Dict, List, Any, Optional

from codegen_on_oss.analysis.pr_analysis.core.analysis_context import AnalysisContext

logger = logging.getLogger(__name__)


class BaseRule:
    """
    Base class for all analysis rules.

    This class defines the interface for analysis rules and provides common functionality.

    Attributes:
        rule_id: Unique identifier for the rule
        name: Human-readable name for the rule
        description: Description of the rule
        context: Analysis context
        config: Rule configuration
    """

    rule_id = "base_rule"
    name = "Base Rule"
    description = "Base class for all analysis rules"

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

    def run(self) -> Dict[str, Any]:
        """
        Run the rule.

        This method should be overridden by subclasses.

        Returns:
            Rule result dictionary
        """
        return self.success("Rule not implemented")

    def success(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a success result.

        Args:
            message: Success message
            details: Additional details

        Returns:
            Success result dictionary
        """
        return self._create_result("success", message, details)

    def warning(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a warning result.

        Args:
            message: Warning message
            details: Additional details

        Returns:
            Warning result dictionary
        """
        return self._create_result("warning", message, details)

    def error(self, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an error result.

        Args:
            message: Error message
            details: Additional details

        Returns:
            Error result dictionary
        """
        return self._create_result("error", message, details)

    def _create_result(
        self, status: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a rule result.

        Args:
            status: Result status
            message: Result message
            details: Additional details

        Returns:
            Rule result dictionary
        """
        result = {
            "status": status,
            "message": message,
            "rule_id": self.rule_id,
            "rule_name": self.name,
        }

        if details:
            result["details"] = details

        return result

