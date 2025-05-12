#!/usr/bin/env python3
"""
Issue Types Module

This module defines the common issue types and enumerations used across
all analyzers in the system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""

    CODEBASE = "codebase"
    PR = "pr"
    COMPARISON = "comparison"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DEPENDENCY = "dependency"
    TYPE_CHECKING = "type_checking"


class IssueSeverity(str, Enum):
    """Severity levels for issues."""

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCategory(str, Enum):
    """Categories of issues that can be detected."""

    DEAD_CODE = "dead_code"
    COMPLEXITY = "complexity"
    TYPE_ERROR = "type_error"
    PARAMETER_MISMATCH = "parameter_mismatch"
    IMPORT_ERROR = "import_error"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_ISSUE = "performance_issue"
    DEPENDENCY_CYCLE = "dependency_cycle"
    API_CHANGE = "api_change"
    STYLE_ISSUE = "style_issue"
    DOCUMENTATION = "documentation"


@dataclass
class Issue:
    """Represents an issue found during analysis."""

    file: str
    line: int | None
    message: str
    severity: IssueSeverity
    category: IssueCategory | None = None
    symbol: str | None = None
    code: str | None = None
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary representation."""
        return {
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "symbol": self.symbol,
            "code": self.code,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Issue":
        """Create an issue from a dictionary representation."""
        return cls(
            file=data["file"],
            line=data.get("line"),
            message=data["message"],
            severity=IssueSeverity(data["severity"]),
            category=IssueCategory(data["category"]) if "category" in data else None,
            symbol=data.get("symbol"),
            code=data.get("code"),
            suggestion=data.get("suggestion"),
        )
