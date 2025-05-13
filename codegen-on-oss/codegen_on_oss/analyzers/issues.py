"""Issue tracking and management for code analysis."""

import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IssueCategory(str, Enum):
    """Categories for code issues."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    USABILITY = "usability"
    COMPATIBILITY = "compatibility"
    ACCESSIBILITY = "accessibility"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    OTHER = "other"


class IssueSeverity(str, Enum):
    """Severity levels for code issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueStatus(str, Enum):
    """Status of an issue."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"
    INVALID = "invalid"


@dataclass
class Location:
    """Location of an issue in the code.

    Attributes:
        file: Path to the file
        line_start: Starting line number
        line_end: Ending line number
        column_start: Starting column number
        column_end: Ending column number
    """

    file: str
    line_start: int = 0
    line_end: int = 0
    column_start: int = 0
    column_end: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert the location to a dictionary.

        Returns:
            Dictionary representation of the location
        """
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "column_start": self.column_start,
            "column_end": self.column_end,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Location":
        """Create a Location instance from a dictionary.

        Args:
            data: Dictionary containing location data

        Returns:
            A Location instance
        """
        return cls(
            file=data.get("file", ""),
            line_start=data.get("line_start", 0),
            line_end=data.get("line_end", 0),
            column_start=data.get("column_start", 0),
            column_end=data.get("column_end", 0),
        )


@dataclass
class Issue:
    """Representation of a code issue.

    Attributes:
        id: Unique identifier for the issue
        message: Description of the issue
        severity: Severity level of the issue
        location: Location of the issue in the code
        category: Category of the issue
        status: Status of the issue
        symbol: Symbol associated with the issue
        suggestion: Suggested fix for the issue
        related_symbols: List of related symbols
        related_locations: List of related locations
    """

    message: str
    severity: IssueSeverity
    location: Location
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: Optional[IssueCategory] = None
    status: IssueStatus = IssueStatus.OPEN
    symbol: Optional[str] = None
    suggestion: Optional[str] = None
    related_symbols: Optional[list[str]] = None
    related_locations: Optional[list[Location]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the issue to a dictionary.

        Returns:
            Dictionary representation of the issue
        """
        result = {
            "id": self.id,
            "message": self.message,
            "severity": self.severity,
            "location": self.location.to_dict(),
            "status": self.status,
        }

        if self.category:
            result["category"] = self.category

        if self.symbol:
            result["symbol"] = self.symbol

        if self.suggestion:
            result["suggestion"] = self.suggestion

        if self.related_symbols:
            result["related_symbols"] = self.related_symbols  # type: ignore

        if self.related_locations:
            result["related_locations"] = [  # type: ignore
                loc.to_dict() for loc in self.related_locations
            ]

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create an Issue instance from a dictionary.

        Args:
            data: Dictionary containing issue data

        Returns:
            An Issue instance
        """
        location_data = data.get("location", {})
        location = Location.from_dict(location_data)

        related_locations = None
        if "related_locations" in data:
            related_locations = [
                Location.from_dict(loc) for loc in data["related_locations"]
            ]

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            message=data.get("message", ""),
            severity=data.get("severity", IssueSeverity.MEDIUM),
            location=location,
            category=data.get("category"),
            status=data.get("status", IssueStatus.OPEN),
            symbol=data.get("symbol"),
            suggestion=data.get("suggestion"),
            related_symbols=data.get("related_symbols"),
            related_locations=related_locations,
        )


class IssueCollection:
    """Collection of code issues with filtering and grouping capabilities.

    Attributes:
        issues: List of issues in the collection
    """

    def __init__(self, issues: Optional[list[Issue]] = None):
        """Initialize an issue collection.

        Args:
            issues: Initial list of issues
        """
        self.issues = issues or []
        self._filters: list[tuple[Callable[[Issue], bool], str]] = []

    def add_issue(self, issue: Issue):
        """Add an issue to the collection.

        Args:
            issue: The issue to add
        """
        self.issues.append(issue)

    def add_issues(self, issues: list[Issue]):
        """Add multiple issues to the collection.

        Args:
            issues: List of issues to add
        """
        self.issues.extend(issues)

    def add_filter(self, filter_func: Callable[[Issue], bool], name: str = ""):
        """Add a filter function to the collection.

        Args:
            filter_func: Function that takes an issue and returns True if it should be included
            name: Name of the filter for reference
        """
        self._filters.append((filter_func, name))

    def filter_by_severity(self, severity: IssueSeverity):
        """Add a filter to include only issues with the specified severity.

        Args:
            severity: The severity level to filter by
        """
        self.add_filter(
            lambda issue: issue.severity == severity, f"severity={severity}"
        )

    def filter_by_category(self, category: IssueCategory):
        """Add a filter to include only issues with the specified category.

        Args:
            category: The category to filter by
        """
        self.add_filter(
            lambda issue: issue.category == category, f"category={category}"
        )

    def filter_by_status(self, status: IssueStatus):
        """Add a filter to include only issues with the specified status.

        Args:
            status: The status to filter by
        """
        self.add_filter(lambda issue: issue.status == status, f"status={status}")

    def filter_by_file(self, file_path: str):
        """Add a filter to include only issues in the specified file.

        Args:
            file_path: The file path to filter by
        """
        self.add_filter(
            lambda issue: issue.location.file == file_path, f"file={file_path}"
        )

    def filter_by_symbol(self, symbol: str):
        """Add a filter to include only issues related to the specified symbol.

        Args:
            symbol: The symbol to filter by
        """
        self.add_filter(lambda issue: issue.symbol == symbol, f"symbol={symbol}")

    def clear_filters(self):
        """Clear all filters from the collection."""
        self._filters = []

    def get_filtered_issues(self) -> list[Issue]:
        """Get issues that pass all filters.

        Returns:
            List of filtered issues
        """
        if not self._filters:
            return self.issues

        filtered_issues = self.issues
        for filter_func, _ in self._filters:
            filtered_issues = [issue for issue in filtered_issues if filter_func(issue)]

        return filtered_issues

    def group_by_severity(self) -> dict[IssueSeverity, list[Issue]]:
        """Group issues by severity.

        Returns:
            Dictionary mapping severities to lists of issues
        """
        result: dict[IssueSeverity, list[Issue]] = {severity: [] for severity in IssueSeverity}

        for issue in self.issues:
            result[issue.severity].append(issue)

        return result

    def group_by_category(self) -> dict[IssueCategory, list[Issue]]:
        """Group issues by category.

        Returns:
            Dictionary mapping categories to lists of issues
        """
        result: dict[IssueCategory, list[Issue]] = {category: [] for category in IssueCategory}

        for issue in self.issues:
            if issue.category:
                result[issue.category].append(issue)

        return result

    def group_by_file(self) -> dict[str, list[Issue]]:
        """Group issues by file.

        Returns:
            Dictionary mapping file paths to lists of issues
        """
        result: dict[str, list[Issue]] = {}

        for issue in self.issues:
            if issue.location.file not in result:
                result[issue.location.file] = []
            result[issue.location.file].append(issue)

        return result

    def group_by_status(self) -> dict[IssueStatus, list[Issue]]:
        """Group issues by status.

        Returns:
            Dictionary mapping statuses to lists of issues
        """
        by_severity = self.group_by_severity()
        by_category = self.group_by_category()
        by_status: dict[IssueStatus, list[Issue]] = {status: [] for status in IssueStatus}
        for issue in self.issues:
            by_status[issue.status].append(issue)

        return by_status

    def to_dict(self) -> dict[str, Any]:
        """Convert the issue collection to a dictionary.

        Returns:
            Dictionary representation of the issue collection
        """
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "filters": [name for _, name in self._filters if name],
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert the issue collection to a JSON string.

        Args:
            indent: Number of spaces for indentation in the JSON output

        Returns:
            JSON string representation of the issue collection
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IssueCollection":
        """Create an IssueCollection instance from a dictionary.

        Args:
            data: Dictionary containing issue collection data

        Returns:
            An IssueCollection instance
        """
        issues_data = data.get("issues", [])
        issues = [Issue.from_dict(issue_data) for issue_data in issues_data]
        return cls(issues)

    @classmethod
    def from_json(cls, json_str: str) -> "IssueCollection":
        """Create an IssueCollection instance from a JSON string.

        Args:
            json_str: JSON string containing issue collection data

        Returns:
            An IssueCollection instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


def create_issue(
    message: str,
    file: str,
    line_start: int = 0,
    line_end: int = 0,
    column_start: int = 0,
    column_end: int = 0,
    severity: IssueSeverity = IssueSeverity.MEDIUM,
    category: Optional[IssueCategory] = None,
    symbol: Optional[str] = None,
    suggestion: Optional[str] = None,
) -> Issue:
    """Create a new issue with the specified parameters.

    Args:
        message: Description of the issue
        file: Path to the file containing the issue
        line_start: Starting line number
        line_end: Ending line number
        column_start: Starting column number
        column_end: Ending column number
        severity: Severity level of the issue
        category: Category of the issue
        symbol: Symbol associated with the issue
        suggestion: Suggested fix for the issue

    Returns:
        A new Issue instance
    """
    location = Location(
        file=file,
        line_start=line_start,
        line_end=line_end,
        column_start=column_start,
        column_end=column_end,
    )

    # Create issue
    return Issue(
        message=message,
        severity=severity,
        location=location,
        category=category if category != "" else None,
        symbol=symbol,
        suggestion=suggestion,
    )

