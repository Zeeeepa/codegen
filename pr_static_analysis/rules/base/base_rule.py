"""Base rule class for PR static analysis.

This module defines the BaseRule abstract class that all rules will inherit from,
as well as supporting classes and enums for rule configuration and management.
"""

import abc
from enum import Enum
from typing import Any, Optional


class RuleSeverity(str, Enum):
    """Enum for rule severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class RuleCategory(str, Enum):
    """Enum for rule categories."""

    CODE_INTEGRITY = "code_integrity"
    PARAMETER_VALIDATION = "parameter_validation"
    IMPLEMENTATION_VALIDATION = "implementation_validation"
    CUSTOM = "custom"


class RuleResult:
    """Class representing the result of a rule analysis.

    Attributes:
        rule_id (str): The ID of the rule that produced this result
        severity (RuleSeverity): The severity level of the issue
        message (str): A descriptive message about the issue
        filepath (str): The path to the file where the issue was found
        line (Optional[int]): The line number where the issue was found
        column (Optional[int]): The column number where the issue was found
        code_snippet (Optional[str]): A snippet of the code where the issue was found
        fix_suggestions (Optional[List[str]]): Suggestions for fixing the issue
        metadata (Optional[Dict[str, Any]]): Additional metadata about the issue
    """

    def __init__(
        self,
        rule_id: str,
        severity: RuleSeverity,
        message: str,
        filepath: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        code_snippet: Optional[str] = None,
        fix_suggestions: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        self.rule_id = rule_id
        self.severity = severity
        self.message = message
        self.filepath = filepath
        self.line = line
        self.column = column
        self.code_snippet = code_snippet
        self.fix_suggestions = fix_suggestions or []
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "filepath": self.filepath,
            "line": self.line,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "fix_suggestions": self.fix_suggestions,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuleResult":
        """Create a RuleResult from a dictionary."""
        return cls(
            rule_id=data["rule_id"],
            severity=RuleSeverity(data["severity"]),
            message=data["message"],
            filepath=data["filepath"],
            line=data.get("line"),
            column=data.get("column"),
            code_snippet=data.get("code_snippet"),
            fix_suggestions=data.get("fix_suggestions", []),
            metadata=data.get("metadata", {}),
        )


class BaseRule(abc.ABC):
    """Abstract base class for all PR static analysis rules.

    All rules must inherit from this class and implement the required methods.

    Attributes:
        id (str): Unique identifier for the rule
        name (str): Human-readable name for the rule
        description (str): Detailed description of what the rule checks for
        category (RuleCategory): Category of the rule
        severity (RuleSeverity): Default severity level for issues found by this rule
        enabled (bool): Whether the rule is enabled by default
        dependencies (Set[str]): IDs of rules that this rule depends on
        config (Dict[str, Any]): Configuration options for the rule
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the rule.

        Args:
            config: Optional configuration options to override defaults
        """
        self.config = self.get_default_config()
        if config:
            self.config.update(config)

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Get the unique identifier for the rule."""
        pass

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Get the human-readable name for the rule."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Get the detailed description of what the rule checks for."""
        pass

    @property
    @abc.abstractmethod
    def category(self) -> RuleCategory:
        """Get the category of the rule."""
        pass

    @property
    def severity(self) -> RuleSeverity:
        """Get the default severity level for issues found by this rule."""
        return RuleSeverity.WARNING

    @property
    def enabled(self) -> bool:
        """Get whether the rule is enabled by default."""
        return True

    @property
    def dependencies(self) -> set[str]:
        """Get the IDs of rules that this rule depends on."""
        return set()

    def get_default_config(self) -> dict[str, Any]:
        """Get the default configuration options for the rule.

        Returns:
            A dictionary of configuration options
        """
        return {}

    @abc.abstractmethod
    def analyze(self, context: dict[str, Any]) -> list[RuleResult]:
        """Analyze the PR for issues.

        Args:
            context: Context information for the analysis, including:
                - codebase: The codebase object
                - pr: The PR object
                - files: List of files in the PR
                - diff: The diff of the PR
                - config: Global configuration options
                - results: Results from dependent rules

        Returns:
            A list of RuleResult objects representing issues found
        """
        pass

    def is_applicable(self, context: dict[str, Any]) -> bool:
        """Check if the rule is applicable to the given context.

        Args:
            context: Context information for the analysis

        Returns:
            True if the rule is applicable, False otherwise
        """
        return True
