"""
Smart assertion generation for intelligent test creation.

Provides:
- Visibility assertions
- Text content validation
- State change verification
- Visual regression checkpoints
- Accessibility assertions (WCAG)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autoqa.builder.analyzer.page_analyzer import (
        PageAnalysisResult,
        InteractiveElement,
        ComponentInfo,
    )
    from autoqa.builder.analyzer.visual_analyzer import VisualAnalysisResult, AccessibilityCheck

logger = structlog.get_logger(__name__)


class AssertionType(StrEnum):
    """Types of assertions."""

    # Element assertions
    VISIBLE = auto()
    NOT_VISIBLE = auto()
    EXISTS = auto()
    NOT_EXISTS = auto()
    ENABLED = auto()
    DISABLED = auto()
    FOCUSED = auto()
    CHECKED = auto()
    UNCHECKED = auto()
    SELECTED = auto()

    # Text assertions
    TEXT_EQUALS = auto()
    TEXT_CONTAINS = auto()
    TEXT_MATCHES = auto()
    TEXT_NOT_EMPTY = auto()
    PLACEHOLDER_EQUALS = auto()

    # Attribute assertions
    ATTRIBUTE_EQUALS = auto()
    ATTRIBUTE_CONTAINS = auto()
    CLASS_CONTAINS = auto()
    VALUE_EQUALS = auto()

    # State assertions
    URL_EQUALS = auto()
    URL_CONTAINS = auto()
    URL_MATCHES = auto()
    TITLE_EQUALS = auto()
    TITLE_CONTAINS = auto()
    PAGE_LOADED = auto()
    NETWORK_IDLE = auto()

    # Count assertions
    ELEMENT_COUNT = auto()
    ELEMENT_COUNT_MIN = auto()
    ELEMENT_COUNT_MAX = auto()

    # Visual assertions
    SCREENSHOT_MATCH = auto()
    VISUAL_DIFF = auto()
    LAYOUT_STABLE = auto()
    COLOR_PRESENT = auto()

    # Accessibility assertions
    WCAG_CONTRAST = auto()
    HAS_ALT_TEXT = auto()
    HAS_LABEL = auto()
    FOCUS_VISIBLE = auto()
    HEADING_STRUCTURE = auto()
    ARIA_VALID = auto()

    # Form assertions
    FORM_VALID = auto()
    FORM_INVALID = auto()
    VALIDATION_ERROR = auto()
    NO_VALIDATION_ERRORS = auto()

    # Performance assertions
    LOAD_TIME = auto()
    RESPONSE_TIME = auto()

    # Custom assertions
    JAVASCRIPT_EVAL = auto()
    CUSTOM = auto()


class AssertionSeverity(StrEnum):
    """Severity of assertion failures."""

    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


@dataclass
class AssertionConfig:
    """Configuration for assertion generation."""

    include_visibility: bool = True
    include_text_content: bool = True
    include_state: bool = True
    include_visual: bool = True
    include_accessibility: bool = True
    include_performance: bool = True
    default_timeout_ms: int = 5000
    strict_mode: bool = False
    continue_on_failure: bool = False


@dataclass
class Assertion:
    """A single assertion."""

    assertion_id: str
    assertion_type: AssertionType
    selector: str | None
    expected_value: Any
    actual_value: Any | None = None
    message: str = ""
    timeout_ms: int = 5000
    severity: AssertionSeverity = AssertionSeverity.MAJOR
    continue_on_failure: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML output."""
        result: dict[str, Any] = {
            "type": self.assertion_type.value,
        }

        if self.selector:
            result["selector"] = self.selector

        if self.expected_value is not None:
            result["expected"] = self.expected_value

        if self.message:
            result["message"] = self.message

        if self.timeout_ms != 5000:
            result["timeout"] = self.timeout_ms

        if self.continue_on_failure:
            result["continue_on_failure"] = True

        return result


@dataclass
class AssertionGroup:
    """Group of related assertions."""

    name: str
    description: str
    assertions: list[Assertion]
    fail_fast: bool = False


class AssertionGenerator:
    """
    Generates smart assertions from page analysis.

    Features:
    - Context-aware assertion selection
    - Accessibility assertions
    - Visual regression assertions
    - State verification assertions
    """

    def __init__(self, config: AssertionConfig | None = None) -> None:
        self._config = config or AssertionConfig()
        self._log = logger.bind(component="assertion_generator")
        self._assertion_counter = 0

    def generate_assertions(
        self,
        page_analysis: PageAnalysisResult,
        visual_analysis: VisualAnalysisResult | None = None,
        context: str = "default",
    ) -> list[Assertion]:
        """
        Generate assertions for a page.

        Args:
            page_analysis: Page analysis result
            visual_analysis: Optional visual analysis
            context: Context for assertion generation (e.g., "after_login")

        Returns:
            List of generated assertions
        """
        assertions: list[Assertion] = []

        # Page-level assertions
        assertions.extend(self._generate_page_assertions(page_analysis))

        # Element visibility assertions
        if self._config.include_visibility:
            assertions.extend(self._generate_visibility_assertions(page_analysis))

        # Text content assertions
        if self._config.include_text_content:
            assertions.extend(self._generate_text_assertions(page_analysis))

        # State assertions
        if self._config.include_state:
            assertions.extend(self._generate_state_assertions(page_analysis, context))

        # Visual assertions
        if self._config.include_visual and visual_analysis:
            assertions.extend(self._generate_visual_assertions(visual_analysis))

        # Accessibility assertions
        if self._config.include_accessibility:
            assertions.extend(self._generate_accessibility_assertions(page_analysis, visual_analysis))

        self._log.debug("Generated assertions", count=len(assertions))

        return assertions

    def _generate_page_assertions(
        self, analysis: PageAnalysisResult
    ) -> list[Assertion]:
        """Generate page-level assertions."""
        assertions: list[Assertion] = []

        # Page loaded assertion
        assertions.append(Assertion(
            assertion_id=self._next_id("page"),
            assertion_type=AssertionType.PAGE_LOADED,
            selector=None,
            expected_value=True,
            message="Page should load successfully",
            severity=AssertionSeverity.BLOCKER,
        ))

        # Title assertion if title exists
        if analysis.title:
            assertions.append(Assertion(
                assertion_id=self._next_id("title"),
                assertion_type=AssertionType.TITLE_CONTAINS,
                selector=None,
                expected_value=analysis.title[:30],
                message=f"Page title should contain '{analysis.title[:30]}'",
            ))

        # URL assertion
        assertions.append(Assertion(
            assertion_id=self._next_id("url"),
            assertion_type=AssertionType.URL_CONTAINS,
            selector=None,
            expected_value=analysis.url.split("?")[0],  # Without query params
            message="Page URL should be correct",
        ))

        return assertions

    def _generate_visibility_assertions(
        self, analysis: PageAnalysisResult
    ) -> list[Assertion]:
        """Generate visibility assertions for key elements."""
        assertions: list[Assertion] = []

        # Get key elements to assert visibility
        key_elements = self._select_key_elements(analysis.interactive_elements)

        for element in key_elements:
            assertions.append(Assertion(
                assertion_id=self._next_id("visible"),
                assertion_type=AssertionType.VISIBLE,
                selector=element.semantic_selector or element.selector,
                expected_value=True,
                message=f"'{element.semantic_selector or element.selector}' should be visible",
                continue_on_failure=self._config.continue_on_failure,
            ))

        # Assert key components are visible
        for component in analysis.components[:3]:
            assertions.append(Assertion(
                assertion_id=self._next_id("component"),
                assertion_type=AssertionType.EXISTS,
                selector=component.selector,
                expected_value=True,
                message=f"Component '{component.component_type.value}' should exist",
                continue_on_failure=True,
            ))

        return assertions

    def _generate_text_assertions(
        self, analysis: PageAnalysisResult
    ) -> list[Assertion]:
        """Generate text content assertions."""
        assertions: list[Assertion] = []

        # Find elements with meaningful text content
        text_elements = [
            el for el in analysis.interactive_elements
            if el.text_content and len(el.text_content) > 2 and len(el.text_content) < 100
        ]

        # Select important text elements
        important_text = text_elements[:5]

        for element in important_text:
            assertions.append(Assertion(
                assertion_id=self._next_id("text"),
                assertion_type=AssertionType.TEXT_CONTAINS,
                selector=element.semantic_selector or element.selector,
                expected_value=element.text_content[:50] if element.text_content else "",
                message=f"Element should contain expected text",
                continue_on_failure=True,
            ))

        # Assert placeholder text for input fields
        input_elements = [
            el for el in analysis.interactive_elements
            if el.placeholder and el.tag_name in ("input", "textarea")
        ][:3]

        for element in input_elements:
            assertions.append(Assertion(
                assertion_id=self._next_id("placeholder"),
                assertion_type=AssertionType.PLACEHOLDER_EQUALS,
                selector=element.selector,
                expected_value=element.placeholder,
                message=f"Input placeholder should be '{element.placeholder}'",
                continue_on_failure=True,
            ))

        return assertions

    def _generate_state_assertions(
        self,
        analysis: PageAnalysisResult,
        context: str,
    ) -> list[Assertion]:
        """Generate state-based assertions."""
        assertions: list[Assertion] = []

        # Context-specific assertions
        if context == "after_login":
            assertions.append(Assertion(
                assertion_id=self._next_id("state"),
                assertion_type=AssertionType.URL_CONTAINS,
                selector=None,
                expected_value="dashboard",
                message="Should redirect to dashboard after login",
            ))
            assertions.append(Assertion(
                assertion_id=self._next_id("state"),
                assertion_type=AssertionType.NOT_EXISTS,
                selector="[href*='login'], [href*='signin']",
                expected_value=True,
                message="Login link should not be visible when logged in",
                continue_on_failure=True,
            ))

        elif context == "after_logout":
            assertions.append(Assertion(
                assertion_id=self._next_id("state"),
                assertion_type=AssertionType.EXISTS,
                selector="[href*='login'], [href*='signin']",
                expected_value=True,
                message="Login link should be visible after logout",
            ))

        elif context == "form_submit":
            assertions.append(Assertion(
                assertion_id=self._next_id("state"),
                assertion_type=AssertionType.NO_VALIDATION_ERRORS,
                selector="form",
                expected_value=True,
                message="Form should have no validation errors",
            ))

        # Network idle assertion
        assertions.append(Assertion(
            assertion_id=self._next_id("network"),
            assertion_type=AssertionType.NETWORK_IDLE,
            selector=None,
            expected_value=True,
            timeout_ms=10000,
            message="Network should be idle",
            severity=AssertionSeverity.MINOR,
        ))

        return assertions

    def _generate_visual_assertions(
        self, visual_analysis: VisualAnalysisResult
    ) -> list[Assertion]:
        """Generate visual regression assertions."""
        assertions: list[Assertion] = []

        # Screenshot comparison
        assertions.append(Assertion(
            assertion_id=self._next_id("visual"),
            assertion_type=AssertionType.VISUAL_DIFF,
            selector=None,
            expected_value={"max_diff_percent": 5},
            message="Visual appearance should match baseline",
            metadata={
                "baseline_hash": visual_analysis.screenshot_hash,
                "complexity": visual_analysis.visual_complexity_score,
            },
            continue_on_failure=True,
        ))

        # Layout stability
        assertions.append(Assertion(
            assertion_id=self._next_id("layout"),
            assertion_type=AssertionType.LAYOUT_STABLE,
            selector=None,
            expected_value={
                "layout_type": visual_analysis.layout.layout_type.value,
                "columns": visual_analysis.layout.columns,
            },
            message="Layout should be stable",
            continue_on_failure=True,
        ))

        # Dominant color presence
        if visual_analysis.dominant_colors:
            primary_color = visual_analysis.dominant_colors[0]
            assertions.append(Assertion(
                assertion_id=self._next_id("color"),
                assertion_type=AssertionType.COLOR_PRESENT,
                selector=None,
                expected_value={
                    "color": primary_color.hex_code,
                    "min_percentage": 0.1,
                },
                message=f"Primary color {primary_color.hex_code} should be present",
                continue_on_failure=True,
            ))

        return assertions

    def _generate_accessibility_assertions(
        self,
        page_analysis: PageAnalysisResult,
        visual_analysis: VisualAnalysisResult | None,
    ) -> list[Assertion]:
        """Generate accessibility assertions."""
        assertions: list[Assertion] = []

        # WCAG contrast check
        assertions.append(Assertion(
            assertion_id=self._next_id("a11y"),
            assertion_type=AssertionType.WCAG_CONTRAST,
            selector=None,
            expected_value={"level": "AA"},
            message="Color contrast should meet WCAG AA requirements",
            severity=AssertionSeverity.MAJOR,
            continue_on_failure=True,
        ))

        # Alt text for images
        assertions.append(Assertion(
            assertion_id=self._next_id("a11y"),
            assertion_type=AssertionType.HAS_ALT_TEXT,
            selector="img",
            expected_value=True,
            message="All images should have alt text",
            severity=AssertionSeverity.MAJOR,
            continue_on_failure=True,
        ))

        # Form labels
        form_inputs = [
            el for el in page_analysis.interactive_elements
            if el.tag_name in ("input", "select", "textarea")
               and el.element_type not in ("hidden", "submit", "button")
        ]

        if form_inputs:
            assertions.append(Assertion(
                assertion_id=self._next_id("a11y"),
                assertion_type=AssertionType.HAS_LABEL,
                selector="input:not([type='hidden']):not([type='submit']), select, textarea",
                expected_value=True,
                message="All form inputs should have labels",
                severity=AssertionSeverity.MAJOR,
                continue_on_failure=True,
            ))

        # Heading structure
        assertions.append(Assertion(
            assertion_id=self._next_id("a11y"),
            assertion_type=AssertionType.HEADING_STRUCTURE,
            selector=None,
            expected_value={"valid": True, "has_h1": True},
            message="Heading structure should be valid",
            severity=AssertionSeverity.MINOR,
            continue_on_failure=True,
        ))

        # Focus visibility
        assertions.append(Assertion(
            assertion_id=self._next_id("a11y"),
            assertion_type=AssertionType.FOCUS_VISIBLE,
            selector="button, a[href], input, select, textarea, [tabindex]",
            expected_value=True,
            message="Interactive elements should have visible focus indicators",
            severity=AssertionSeverity.MINOR,
            continue_on_failure=True,
        ))

        # Include results from visual accessibility checks
        if visual_analysis:
            for check in visual_analysis.accessibility_checks:
                if not check.passed:
                    assertions.append(Assertion(
                        assertion_id=self._next_id("a11y"),
                        assertion_type=AssertionType.CUSTOM,
                        selector=check.selector,
                        expected_value={"passed": True},
                        message=check.message,
                        severity=self._map_severity(check.severity.value),
                        metadata=check.details,
                        continue_on_failure=True,
                    ))

        return assertions

    def generate_form_assertions(
        self,
        form_selector: str,
        expected_state: str = "valid",
    ) -> list[Assertion]:
        """Generate assertions for form state."""
        assertions: list[Assertion] = []

        if expected_state == "valid":
            assertions.append(Assertion(
                assertion_id=self._next_id("form"),
                assertion_type=AssertionType.FORM_VALID,
                selector=form_selector,
                expected_value=True,
                message="Form should be valid",
            ))
            assertions.append(Assertion(
                assertion_id=self._next_id("form"),
                assertion_type=AssertionType.NO_VALIDATION_ERRORS,
                selector=form_selector,
                expected_value=True,
                message="Form should have no validation errors",
            ))
        else:
            assertions.append(Assertion(
                assertion_id=self._next_id("form"),
                assertion_type=AssertionType.FORM_INVALID,
                selector=form_selector,
                expected_value=True,
                message="Form should be invalid",
            ))
            assertions.append(Assertion(
                assertion_id=self._next_id("form"),
                assertion_type=AssertionType.VALIDATION_ERROR,
                selector=form_selector,
                expected_value=True,
                message="Form should show validation errors",
            ))

        return assertions

    def generate_element_assertions(
        self,
        element: InteractiveElement,
        expected_state: dict[str, Any],
    ) -> list[Assertion]:
        """Generate assertions for a specific element."""
        assertions: list[Assertion] = []
        selector = element.semantic_selector or element.selector

        if expected_state.get("visible", True):
            assertions.append(Assertion(
                assertion_id=self._next_id("el"),
                assertion_type=AssertionType.VISIBLE,
                selector=selector,
                expected_value=True,
                message=f"Element '{selector}' should be visible",
            ))

        if "text" in expected_state:
            assertions.append(Assertion(
                assertion_id=self._next_id("el"),
                assertion_type=AssertionType.TEXT_CONTAINS,
                selector=selector,
                expected_value=expected_state["text"],
                message=f"Element should contain text '{expected_state['text']}'",
            ))

        if "value" in expected_state:
            assertions.append(Assertion(
                assertion_id=self._next_id("el"),
                assertion_type=AssertionType.VALUE_EQUALS,
                selector=selector,
                expected_value=expected_state["value"],
                message=f"Element value should be '{expected_state['value']}'",
            ))

        if "enabled" in expected_state:
            assertion_type = AssertionType.ENABLED if expected_state["enabled"] else AssertionType.DISABLED
            assertions.append(Assertion(
                assertion_id=self._next_id("el"),
                assertion_type=assertion_type,
                selector=selector,
                expected_value=True,
                message=f"Element should be {'enabled' if expected_state['enabled'] else 'disabled'}",
            ))

        if "checked" in expected_state:
            assertion_type = AssertionType.CHECKED if expected_state["checked"] else AssertionType.UNCHECKED
            assertions.append(Assertion(
                assertion_id=self._next_id("el"),
                assertion_type=assertion_type,
                selector=selector,
                expected_value=True,
                message=f"Element should be {'checked' if expected_state['checked'] else 'unchecked'}",
            ))

        return assertions

    def _select_key_elements(
        self, elements: list[InteractiveElement]
    ) -> list[InteractiveElement]:
        """Select key elements for visibility assertions."""
        # Prioritize by element type
        priority_types = ["button", "submit", "link", "input", "select"]
        key_elements: list[InteractiveElement] = []

        for elem_type in priority_types:
            type_elements = [
                el for el in elements
                if el.element_type.lower() == elem_type or el.tag_name == elem_type
            ]
            key_elements.extend(type_elements[:2])

        # Limit total
        return key_elements[:10]

    def _map_severity(self, severity_str: str) -> AssertionSeverity:
        """Map severity string to AssertionSeverity."""
        mapping = {
            "critical": AssertionSeverity.CRITICAL,
            "high": AssertionSeverity.MAJOR,
            "medium": AssertionSeverity.MAJOR,
            "low": AssertionSeverity.MINOR,
            "info": AssertionSeverity.INFO,
        }
        return mapping.get(severity_str.lower(), AssertionSeverity.MAJOR)

    def _next_id(self, prefix: str) -> str:
        """Generate next assertion ID."""
        self._assertion_counter += 1
        return f"assert_{prefix}_{self._assertion_counter}"
