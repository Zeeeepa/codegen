"""
Data models for versioned test tracking system.

Provides strongly-typed dataclasses for snapshots, diffs, and change tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ChangeType(StrEnum):
    """Type of change detected between versions."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"
    UNCHANGED = "unchanged"


class ChangeSeverity(StrEnum):
    """Severity level of detected changes."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Bounding box coordinates for element positioning."""

    x: int
    y: int
    width: int
    height: int

    def overlaps(self, other: BoundingBox) -> bool:
        """Check if this box overlaps with another."""
        return not (
            self.x + self.width < other.x
            or other.x + other.width < self.x
            or self.y + self.height < other.y
            or other.y + other.height < self.y
        )

    def distance_to(self, other: BoundingBox) -> float:
        """Calculate center-to-center distance to another box."""
        self_center_x = self.x + self.width / 2
        self_center_y = self.y + self.height / 2
        other_center_x = other.x + other.width / 2
        other_center_y = other.y + other.height / 2
        return ((self_center_x - other_center_x) ** 2 + (self_center_y - other_center_y) ** 2) ** 0.5


@dataclass(frozen=True, slots=True)
class ElementState:
    """State of a DOM element at a point in time."""

    selector: str
    tag_name: str
    text_content: str | None
    attributes: dict[str, str]
    bounding_box: BoundingBox | None
    is_visible: bool
    is_enabled: bool
    computed_styles: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "selector": self.selector,
            "tag_name": self.tag_name,
            "text_content": self.text_content,
            "attributes": dict(self.attributes),
            "bounding_box": {
                "x": self.bounding_box.x,
                "y": self.bounding_box.y,
                "width": self.bounding_box.width,
                "height": self.bounding_box.height,
            } if self.bounding_box else None,
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled,
            "computed_styles": dict(self.computed_styles),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ElementState:
        """Create from dictionary."""
        bbox_data = data.get("bounding_box")
        bbox = BoundingBox(
            x=bbox_data["x"],
            y=bbox_data["y"],
            width=bbox_data["width"],
            height=bbox_data["height"],
        ) if bbox_data else None

        return cls(
            selector=data["selector"],
            tag_name=data["tag_name"],
            text_content=data.get("text_content"),
            attributes=data.get("attributes", {}),
            bounding_box=bbox,
            is_visible=data.get("is_visible", True),
            is_enabled=data.get("is_enabled", True),
            computed_styles=data.get("computed_styles", {}),
        )


@dataclass(frozen=True, slots=True)
class NetworkRequest:
    """Captured network request."""

    url: str
    method: str
    status_code: int | None
    response_time_ms: int | None
    request_headers: dict[str, str]
    response_headers: dict[str, str]
    content_type: str | None
    content_length: int | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "url": self.url,
            "method": self.method,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "request_headers": dict(self.request_headers),
            "response_headers": dict(self.response_headers),
            "content_type": self.content_type,
            "content_length": self.content_length,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkRequest:
        """Create from dictionary."""
        return cls(
            url=data["url"],
            method=data["method"],
            status_code=data.get("status_code"),
            response_time_ms=data.get("response_time_ms"),
            request_headers=data.get("request_headers", {}),
            response_headers=data.get("response_headers", {}),
            content_type=data.get("content_type"),
            content_length=data.get("content_length"),
        )


@dataclass(slots=True)
class TestSnapshot:
    """
    Complete snapshot of test state at a point in time.

    Captures all observable state: screenshots, texts, elements, network.
    """

    test_name: str
    timestamp: datetime
    version_id: str

    # Screenshot data
    screenshot_path: str | None = None
    screenshot_hash: str | None = None

    # Extracted content
    extracted_texts: dict[str, str] = field(default_factory=dict)
    page_title: str | None = None
    page_url: str | None = None

    # DOM state
    element_states: list[ElementState] = field(default_factory=list)
    dom_structure_hash: str | None = None

    # Network activity
    network_requests: list[NetworkRequest] = field(default_factory=list)

    # Test execution metadata
    test_status: str | None = None
    duration_ms: int = 0
    error_message: str | None = None

    # Environment metadata
    browser_name: str | None = None
    browser_version: str | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    user_agent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_name": self.test_name,
            "timestamp": self.timestamp.isoformat(),
            "version_id": self.version_id,
            "screenshot_path": self.screenshot_path,
            "screenshot_hash": self.screenshot_hash,
            "extracted_texts": self.extracted_texts,
            "page_title": self.page_title,
            "page_url": self.page_url,
            "element_states": [e.to_dict() for e in self.element_states],
            "dom_structure_hash": self.dom_structure_hash,
            "network_requests": [r.to_dict() for r in self.network_requests],
            "test_status": self.test_status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "browser_name": self.browser_name,
            "browser_version": self.browser_version,
            "viewport_width": self.viewport_width,
            "viewport_height": self.viewport_height,
            "user_agent": self.user_agent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TestSnapshot:
        """Create from dictionary."""
        return cls(
            test_name=data["test_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version_id=data["version_id"],
            screenshot_path=data.get("screenshot_path"),
            screenshot_hash=data.get("screenshot_hash"),
            extracted_texts=data.get("extracted_texts", {}),
            page_title=data.get("page_title"),
            page_url=data.get("page_url"),
            element_states=[
                ElementState.from_dict(e) for e in data.get("element_states", [])
            ],
            dom_structure_hash=data.get("dom_structure_hash"),
            network_requests=[
                NetworkRequest.from_dict(r) for r in data.get("network_requests", [])
            ],
            test_status=data.get("test_status"),
            duration_ms=data.get("duration_ms", 0),
            error_message=data.get("error_message"),
            browser_name=data.get("browser_name"),
            browser_version=data.get("browser_version"),
            viewport_width=data.get("viewport_width"),
            viewport_height=data.get("viewport_height"),
            user_agent=data.get("user_agent"),
        )


@dataclass(slots=True)
class TextChange:
    """Detected change in text content."""

    change_type: ChangeType
    selector: str | None
    key: str | None
    old_value: str | None
    new_value: str | None
    severity: ChangeSeverity = ChangeSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "selector": self.selector,
            "key": self.key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity,
        }


@dataclass(slots=True)
class ElementChange:
    """Detected change in element state."""

    change_type: ChangeType
    selector: str
    old_state: ElementState | None
    new_state: ElementState | None
    changed_attributes: list[str] = field(default_factory=list)
    changed_styles: list[str] = field(default_factory=list)
    severity: ChangeSeverity = ChangeSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "selector": self.selector,
            "old_state": self.old_state.to_dict() if self.old_state else None,
            "new_state": self.new_state.to_dict() if self.new_state else None,
            "changed_attributes": self.changed_attributes,
            "changed_styles": self.changed_styles,
            "severity": self.severity,
        }


@dataclass(slots=True)
class LayoutChange:
    """Detected layout shift or position change."""

    selector: str
    old_position: BoundingBox | None
    new_position: BoundingBox | None
    shift_x: int
    shift_y: int
    shift_distance: float
    severity: ChangeSeverity = ChangeSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector": self.selector,
            "old_position": {
                "x": self.old_position.x,
                "y": self.old_position.y,
                "width": self.old_position.width,
                "height": self.old_position.height,
            } if self.old_position else None,
            "new_position": {
                "x": self.new_position.x,
                "y": self.new_position.y,
                "width": self.new_position.width,
                "height": self.new_position.height,
            } if self.new_position else None,
            "shift_x": self.shift_x,
            "shift_y": self.shift_y,
            "shift_distance": self.shift_distance,
            "severity": self.severity,
        }


@dataclass(slots=True)
class VisualChange:
    """Detected visual difference between screenshots."""

    diff_percentage: float
    diff_image_path: str | None
    changed_regions: list[BoundingBox] = field(default_factory=list)
    severity: ChangeSeverity = ChangeSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diff_percentage": self.diff_percentage,
            "diff_image_path": self.diff_image_path,
            "changed_regions": [
                {"x": r.x, "y": r.y, "width": r.width, "height": r.height}
                for r in self.changed_regions
            ],
            "severity": self.severity,
        }


@dataclass(slots=True)
class NetworkChange:
    """Detected change in network requests."""

    change_type: ChangeType
    url_pattern: str
    old_request: NetworkRequest | None
    new_request: NetworkRequest | None
    status_code_changed: bool = False
    response_time_changed: bool = False
    severity: ChangeSeverity = ChangeSeverity.MEDIUM

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "change_type": self.change_type,
            "url_pattern": self.url_pattern,
            "old_request": self.old_request.to_dict() if self.old_request else None,
            "new_request": self.new_request.to_dict() if self.new_request else None,
            "status_code_changed": self.status_code_changed,
            "response_time_changed": self.response_time_changed,
            "severity": self.severity,
        }


@dataclass(slots=True)
class VersionDiff:
    """
    Complete diff result between two test snapshots.

    Contains all detected changes across visual, text, element, layout, and network.
    """

    snapshot_a: TestSnapshot
    snapshot_b: TestSnapshot

    # Changes by category
    visual_changes: VisualChange | None = None
    text_changes: list[TextChange] = field(default_factory=list)
    element_changes: list[ElementChange] = field(default_factory=list)
    layout_changes: list[LayoutChange] = field(default_factory=list)
    network_changes: list[NetworkChange] = field(default_factory=list)

    # Summary metrics
    total_changes: int = 0
    critical_changes: int = 0
    high_changes: int = 0
    medium_changes: int = 0
    low_changes: int = 0

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    comparison_duration_ms: int = 0

    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return self.total_changes > 0

    def get_severity_summary(self) -> dict[str, int]:
        """Get count of changes by severity."""
        return {
            "critical": self.critical_changes,
            "high": self.high_changes,
            "medium": self.medium_changes,
            "low": self.low_changes,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "snapshot_a_id": self.snapshot_a.version_id,
            "snapshot_a_timestamp": self.snapshot_a.timestamp.isoformat(),
            "snapshot_b_id": self.snapshot_b.version_id,
            "snapshot_b_timestamp": self.snapshot_b.timestamp.isoformat(),
            "visual_changes": self.visual_changes.to_dict() if self.visual_changes else None,
            "text_changes": [c.to_dict() for c in self.text_changes],
            "element_changes": [c.to_dict() for c in self.element_changes],
            "layout_changes": [c.to_dict() for c in self.layout_changes],
            "network_changes": [c.to_dict() for c in self.network_changes],
            "total_changes": self.total_changes,
            "critical_changes": self.critical_changes,
            "high_changes": self.high_changes,
            "medium_changes": self.medium_changes,
            "low_changes": self.low_changes,
            "generated_at": self.generated_at.isoformat(),
            "comparison_duration_ms": self.comparison_duration_ms,
        }


@dataclass(slots=True)
class VersioningConfig:
    """Configuration for versioned test tracking."""

    enabled: bool = False
    storage_path: str = ".autoqa/history"
    retention_days: int = 90
    capture_screenshots: bool = True
    capture_network: bool = True
    capture_elements: bool = True
    element_selectors: list[str] = field(default_factory=list)
    auto_compare_previous: bool = False
    diff_threshold: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "storage_path": self.storage_path,
            "retention_days": self.retention_days,
            "capture_screenshots": self.capture_screenshots,
            "capture_network": self.capture_network,
            "capture_elements": self.capture_elements,
            "element_selectors": self.element_selectors,
            "auto_compare_previous": self.auto_compare_previous,
            "diff_threshold": self.diff_threshold,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersioningConfig:
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            storage_path=data.get("storage_path", ".autoqa/history"),
            retention_days=data.get("retention_days", 90),
            capture_screenshots=data.get("capture_screenshots", True),
            capture_network=data.get("capture_network", True),
            capture_elements=data.get("capture_elements", True),
            element_selectors=data.get("element_selectors", []),
            auto_compare_previous=data.get("auto_compare_previous", False),
            diff_threshold=data.get("diff_threshold", 0.05),
        )
