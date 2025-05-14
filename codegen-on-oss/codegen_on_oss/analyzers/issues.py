#!/usr/bin/env python3
"""
Issues Module

This module defines issue models, categories, and severities for code analysis.
It provides a standardized way to represent and manage issues across different analyzers.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""

    CODEBASE = "codebase"
    PR = "pr"
    COMPARISON = "comparison"
    CODE_QUALITY = "code_quality"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TYPE_CHECKING = "type_checking"


class IssueSeverity(str, Enum):
    """Severity levels for issues."""

    CRITICAL = "critical"  # Must be fixed immediately, blocks functionality
    ERROR = "error"  # Must be fixed, causes errors or undefined behavior
    WARNING = "warning"  # Should be fixed, may cause problems in future
    INFO = "info"  # Informational, could be improved but not critical


class IssueCategory(str, Enum):
    """Categories of issues that can be detected."""

    # Code Quality Issues
    DEAD_CODE = "dead_code"  # Unused variables, functions, etc.
    COMPLEXITY = "complexity"  # Code too complex, needs refactoring
    STYLE_ISSUE = "style_issue"  # Code style issues (line length, etc.)
    DOCUMENTATION = "documentation"  # Missing or incomplete documentation

    # Type and Parameter Issues
    TYPE_ERROR = "type_error"  # Type errors or inconsistencies
    PARAMETER_MISMATCH = "parameter_mismatch"  # Parameter type or count mismatch
    RETURN_TYPE_ERROR = "return_type_error"  # Return type error or mismatch

    # Implementation Issues
    IMPLEMENTATION_ERROR = "implementation_error"  # Incorrect implementation
    MISSING_IMPLEMENTATION = "missing_implementation"  # Missing implementation

    # Dependency Issues
    IMPORT_ERROR = "import_error"  # Import errors or issues
    DEPENDENCY_CYCLE = "dependency_cycle"  # Circular dependency
    MODULE_COUPLING = "module_coupling"  # High coupling between modules

    # API Issues
    API_CHANGE = "api_change"  # API has changed in a breaking way
    API_USAGE_ERROR = "api_usage_error"  # Incorrect API usage

    # Security Issues
    SECURITY_VULNERABILITY = "security_vulnerability"  # Security vulnerability

    # Performance Issues
    PERFORMANCE_ISSUE = "performance_issue"  # Performance issue


class IssueStatus(str, Enum):
    """Status of an issue."""

    OPEN = "open"  # Issue is open and needs to be fixed
    FIXED = "fixed"  # Issue has been fixed
    WONTFIX = "wontfix"  # Issue will not be fixed
    INVALID = "invalid"  # Issue is invalid or not applicable
    DUPLICATE = "duplicate"  # Issue is a duplicate of another


@dataclass
class CodeLocation:
    """Location of an issue in code."""

    file: str
    line: int | None = None
    column: int | None = None
    end_line: int | None = None
    end_column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CodeLocation":
        """Create from dictionary representation."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def __str__(self) -> str:
        """Convert to string representation."""
        if self.line is not None:
            if self.column is not None:
                return f"{self.file}:{self.line}:{self.column}"
            return f"{self.file}:{self.line}"
        return self.file


@dataclass
class Issue:
    """Represents an issue found during analysis."""

    # Core fields
    message: str
    severity: IssueSeverity
    location: CodeLocation

    # Classification fields
    category: IssueCategory | None = None
    analysis_type: AnalysisType | None = None
    status: IssueStatus = IssueStatus.OPEN

    # Context fields
    symbol: str | None = None
    code: str | None = None
    suggestion: str | None = None
    related_symbols: list[str] = field(default_factory=list)
    related_locations: list[CodeLocation] = field(default_factory=list)

    # Metadata fields
    id: str | None = None
    hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize derived fields."""
        # Generate an ID if not provided
        if self.id is None:
            import hashlib

            # Create a hash based on location and message
            hash_input = f"{self.location.file}:{self.location.line}:{self.message}"
            self.id = hashlib.md5(hash_input.encode()).hexdigest()[:12]

    @property
    def file(self) -> str:
        """Get the file path."""
        return self.location.file

    @property
    def line(self) -> int | None:
        """Get the line number."""
        return self.location.line

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "id": self.id,
            "message": self.message,
            "severity": self.severity.value,
            "location": self.location.to_dict(),
            "status": self.status.value,
        }

        # Add optional fields if present
        if self.category:
            result["category"] = self.category.value

        if self.analysis_type:
            result["analysis_type"] = self.analysis_type.value

        if self.symbol:
            result["symbol"] = self.symbol

        if self.code:
            result["code"] = self.code

        if self.suggestion:
            result["suggestion"] = self.suggestion

        if self.related_symbols:
            result["related_symbols"] = self.related_symbols  # type: ignore

        if self.related_locations:
            result["related_locations"] = [  # type: ignore
                loc.to_dict() for loc in self.related_locations
            ]

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create from dictionary representation."""
        # Convert string enums to actual enum values
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = IssueSeverity(data["severity"])

        if "category" in data and isinstance(data["category"], str):
            data["category"] = IssueCategory(data["category"])

        if "analysis_type" in data and isinstance(data["analysis_type"], str):
            data["analysis_type"] = AnalysisType(data["analysis_type"])

        if "status" in data and isinstance(data["status"], str):
            data["status"] = IssueStatus(data["status"])

        # Convert location dict to CodeLocation
        if "location" in data and isinstance(data["location"], dict):
            data["location"] = CodeLocation.from_dict(data["location"])

        # Convert related_locations dicts to CodeLocation objects
        if "related_locations" in data and isinstance(data["related_locations"], list):
            data["related_locations"] = [
                CodeLocation.from_dict(loc) if isinstance(loc, dict) else loc
                for loc in data["related_locations"]
            ]

        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class IssueCollection:
    """Collection of issues with filtering and grouping capabilities."""

    def __init__(self, issues: list[Issue] | None = None):
        """
        Initialize the issue collection.

        Args:
            issues: Initial list of issues
        """
        self.issues = issues or []
        self._filters: list[tuple[Callable[[Issue], bool], str]] = []

    def add_issue(self, issue: Issue):
        """
        Add an issue to the collection.

        Args:
            issue: Issue to add
        """
        self.issues.append(issue)

    def add_issues(self, issues: list[Issue]):
        """
        Add multiple issues to the collection.

        Args:
            issues: Issues to add
        """
        self.issues.extend(issues)

    def add_filter(self, filter_func: Callable[[Issue], bool], description: str = ""):
        """
        Add a filter function.

        Args:
            filter_func: Function that returns True if issue should be included
            description: Description of the filter
        """
        self._filters.append((filter_func, description))

    def get_issues(
        self,
        severity: IssueSeverity | None = None,
        category: IssueCategory | None = None,
        status: IssueStatus | None = None,
        file_path: str | None = None,
        symbol: str | None = None,
    ) -> list[Issue]:
        """
        Get issues matching the specified criteria.

        Args:
            severity: Severity to filter by
            category: Category to filter by
            status: Status to filter by
            file_path: File path to filter by
            symbol: Symbol name to filter by

        Returns:
            List of matching issues
        """
        filtered_issues = self.issues

        # Apply custom filters
        for filter_func, _ in self._filters:
            filtered_issues = [i for i in filtered_issues if filter_func(i)]

        # Apply standard filters
        if severity:
            filtered_issues = [i for i in filtered_issues if i.severity == severity]

        if category:
            filtered_issues = [i for i in filtered_issues if i.category == category]

        if status:
            filtered_issues = [i for i in filtered_issues if i.status == status]

        if file_path:
            filtered_issues = [
                i for i in filtered_issues if i.location.file == file_path
            ]

        if symbol:
            filtered_issues = [
                i
                for i in filtered_issues
                if (
                    i.symbol == symbol
                    or (i.related_symbols and symbol in i.related_symbols)
                )
            ]

        return filtered_issues

    def group_by_severity(self) -> dict[IssueSeverity, list[Issue]]:
        """
        Group issues by severity.

        Returns:
            Dictionary mapping severities to lists of issues
        """
        result: dict[IssueSeverity, list[Issue]] = {severity: [] for severity in IssueSeverity}

        for issue in self.issues:
            result[issue.severity].append(issue)

        return result

    def group_by_category(self) -> dict[IssueCategory, list[Issue]]:
        """
        Group issues by category.

        Returns:
            Dictionary mapping categories to lists of issues
        """
        result: dict[IssueCategory, list[Issue]] = {category: [] for category in IssueCategory}

        for issue in self.issues:
            if issue.category:
                result[issue.category].append(issue)

        return result

    def group_by_file(self) -> dict[str, list[Issue]]:
        """
        Group issues by file.

        Returns:
            Dictionary mapping file paths to lists of issues
        """
        result: dict[str, list[Issue]] = {}

        for issue in self.issues:
            if issue.location.file not in result:
                result[issue.location.file] = []

            result[issue.location.file].append(issue)

        return result

    def statistics(self) -> dict[str, Any]:
        """
        Get statistics about the issues.

        Returns:
            Dictionary with issue statistics
        """
        by_severity = self.group_by_severity()
        by_category = self.group_by_category()
        by_status: dict[IssueStatus, list[Issue]] = {status: [] for status in IssueStatus}
        for issue in self.issues:
            by_status[issue.status].append(issue)

        return {
            "total": len(self.issues),
            "by_severity": {
                severity.value: len(issues) for severity, issues in by_severity.items()
            },
            "by_category": {
                category.value: len(issues)
                for category, issues in by_category.items()
                if len(issues) > 0  # Only include non-empty categories
            },
            "by_status": {
                status.value: len(issues) for status, issues in by_status.items()
            },
            "file_count": len(self.group_by_file()),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary representation of the issue collection
        """
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "statistics": self.statistics(),
            "filters": [desc for _, desc in self._filters if desc],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueCollection":
        """
        Create from dictionary representation.

        Args:
            data: Dictionary representation

        Returns:
            Issue collection
        """
        collection = cls()

        if "issues" in data and isinstance(data["issues"], list):
            collection.add_issues([
                Issue.from_dict(issue) if isinstance(issue, dict) else issue
                for issue in data["issues"]
            ])

        return collection

    def save_to_file(self, file_path: str, format: str = "json"):
        """
        Save to file.

        Args:
            file_path: Path to save to
            format: Format to save in
        """
        if format == "json":
            with open(file_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    @classmethod
    def load_from_file(cls, file_path: str) -> "IssueCollection":
        """
        Load from file.

        Args:
            file_path: Path to load from

        Returns:
            Issue collection
        """
        with open(file_path) as f:
            data = json.load(f)

        return cls.from_dict(data)


def create_issue(
    message: str,
    severity: str | IssueSeverity,
    file: str,
    line: int | None = None,
    category: str | IssueCategory | None = None,
    symbol: str | None = None,
    suggestion: str | None = None,
) -> Issue:
    """
    Create an issue with simplified parameters.

    Args:
        message: Issue message
        severity: Issue severity
        file: File path
        line: Line number
        category: Issue category
        symbol: Symbol name
        suggestion: Suggested fix

    Returns:
        Issue object
    """
    # Convert string severity to enum
    if isinstance(severity, str):
        severity = IssueSeverity(severity)

    # Convert string category to enum
    if isinstance(category, str) and category:
        category = IssueCategory(category)

    # Create location
    location = CodeLocation(file=file, line=line)

    # Create issue
    return Issue(
        message=message,
        severity=severity,
        location=location,
        category=category if category != "" else None,  # type: ignore
        symbol=symbol,
        suggestion=suggestion,
    )
