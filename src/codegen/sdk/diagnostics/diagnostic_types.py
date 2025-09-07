"""Common diagnostic types for unified diagnostics system."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class DiagnosticSeverity(Enum):
    """Severity levels for diagnostics."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


class DiagnosticSource(Enum):
    """Source of diagnostic information."""
    SOLIDLSP = "solidlsp"
    SERENA = "serena"
    GRAPH_SITTER = "graph_sitter"
    TOOLS = "tools"
    AUTOGENLIB = "autogenlib"


@dataclass
class DiagnosticPosition:
    """Position in a file (line and character)."""
    line: int
    character: int

    def __str__(self) -> str:
        return f"{self.line}:{self.character}"


@dataclass
class DiagnosticRange:
    """Range in a file (start and end positions)."""
    start: DiagnosticPosition
    end: DiagnosticPosition

    def __str__(self) -> str:
        return f"{self.start}-{self.end}"


@dataclass
class Diagnostic:
    """A diagnostic message (error, warning, info, or hint)."""

    # Core diagnostic information
    message: str
    severity: DiagnosticSeverity
    source: DiagnosticSource
    file_path: Path
    range: DiagnosticRange

    # Optional additional information
    code: str | None = None
    """Diagnostic code (e.g., 'E501' for ruff, 'unused-import' for mypy)."""

    tool_name: str | None = None
    """Name of the tool that generated this diagnostic."""

    category: str | None = None
    """Category of the diagnostic (e.g., 'syntax', 'type', 'style')."""

    fix_suggestion: str | None = None
    """Suggested fix for the diagnostic."""

    related_information: list[dict[str, Any]] | None = None
    """Related diagnostic information."""

    tags: list[str] | None = None
    """Tags for categorizing diagnostics."""

    def __str__(self) -> str:
        """String representation of diagnostic."""
        parts = [
            str(self.file_path),
            str(self.range),
            self.severity.value,
            self.message
        ]

        if self.code:
            parts.insert(-1, f"[{self.code}]")

        return ": ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert diagnostic to dictionary."""
        return {
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source.value,
            "file_path": str(self.file_path),
            "range": {
                "start": {"line": self.range.start.line, "character": self.range.start.character},
                "end": {"line": self.range.end.line, "character": self.range.end.character}
            },
            "code": self.code,
            "tool_name": self.tool_name,
            "category": self.category,
            "fix_suggestion": self.fix_suggestion,
            "related_information": self.related_information,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Diagnostic":
        """Create diagnostic from dictionary."""
        range_data = data["range"]
        diagnostic_range = DiagnosticRange(
            start=DiagnosticPosition(
                line=range_data["start"]["line"],
                character=range_data["start"]["character"]
            ),
            end=DiagnosticPosition(
                line=range_data["end"]["line"],
                character=range_data["end"]["character"]
            )
        )

        return cls(
            message=data["message"],
            severity=DiagnosticSeverity(data["severity"]),
            source=DiagnosticSource(data["source"]),
            file_path=Path(data["file_path"]),
            range=diagnostic_range,
            code=data.get("code"),
            tool_name=data.get("tool_name"),
            category=data.get("category"),
            fix_suggestion=data.get("fix_suggestion"),
            related_information=data.get("related_information"),
            tags=data.get("tags"),
        )

    def is_error(self) -> bool:
        """Check if diagnostic is an error."""
        return self.severity == DiagnosticSeverity.ERROR

    def is_warning(self) -> bool:
        """Check if diagnostic is a warning."""
        return self.severity == DiagnosticSeverity.WARNING

    def is_fixable(self) -> bool:
        """Check if diagnostic has a fix suggestion."""
        return self.fix_suggestion is not None
