"""
Pydantic models for YAML test DSL definitions.

Provides strict type validation for natural language test specifications.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class StepAction(StrEnum):
    """Supported test step actions mapping to owl-browser methods."""

    # Navigation
    NAVIGATE = "navigate"
    WAIT = "wait"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_NETWORK_IDLE = "wait_for_network_idle"
    WAIT_FOR_URL = "wait_for_url"

    # Clicks & Interactions
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    HOVER = "hover"
    DRAG_DROP = "drag_drop"

    # Forms
    TYPE = "type"
    PICK = "pick"
    PRESS_KEY = "press_key"
    SUBMIT = "submit"
    UPLOAD = "upload"

    # Scroll
    SCROLL = "scroll"
    SCROLL_TO = "scroll_to"
    SCROLL_TO_ELEMENT = "scroll_to_element"

    # Extraction
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_JSON = "extract_json"
    GET_HTML = "get_html"
    GET_MARKDOWN = "get_markdown"
    GET_ATTRIBUTE = "get_attribute"
    GET_NETWORK_LOG = "get_network_log"

    # Script execution
    EVALUATE = "evaluate"
    FIND_ELEMENT = "find_element"

    # State checks (for conditional flows)
    CHECK_VISIBLE = "check_visible"
    CHECK_ENABLED = "check_enabled"
    CHECK_CHECKED = "check_checked"

    # Cookies
    SET_COOKIE = "set_cookie"
    DELETE_COOKIES = "delete_cookies"

    # Viewport & Pages
    SET_VIEWPORT = "set_viewport"
    NEW_PAGE = "new_page"
    CLOSE_PAGE = "close_page"

    # Recording
    START_VIDEO = "start_video"
    STOP_VIDEO = "stop_video"

    # Assertions
    ASSERT = "assert"
    VISUAL_ASSERT = "visual_assert"
    NETWORK_ASSERT = "network_assert"
    URL_ASSERT = "url_assert"
    CUSTOM = "custom"

    # ML-based assertions (no LLM required)
    ML_ASSERT = "ml_assert"
    OCR_ASSERT = "ocr_assert"
    UI_STATE_ASSERT = "ui_state_assert"
    COLOR_ASSERT = "color_assert"
    LAYOUT_ASSERT = "layout_assert"
    ICON_ASSERT = "icon_assert"
    ACCESSIBILITY_ASSERT = "accessibility_assert"

    # LLM-based assertions (optional, requires LLM configuration)
    LLM_ASSERT = "llm_assert"
    SEMANTIC_ASSERT = "semantic_assert"
    CONTENT_ASSERT = "content_assert"


class AssertionOperator(StrEnum):
    """Operators for assertion comparisons."""

    # Value comparisons
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    MATCHES = "matches"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"

    # Numeric comparisons
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"

    # Element state assertions
    IS_VISIBLE = "is_visible"
    IS_HIDDEN = "is_hidden"
    IS_ENABLED = "is_enabled"
    IS_DISABLED = "is_disabled"
    IS_CHECKED = "is_checked"
    IS_UNCHECKED = "is_unchecked"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"

    # Boolean assertions
    IS_TRUTHY = "is_truthy"
    IS_FALSY = "is_falsy"

    # URL assertions
    URL_EQUALS = "url_equals"
    URL_CONTAINS = "url_contains"
    URL_MATCHES = "url_matches"

    # Network assertions
    REQUEST_MADE = "request_made"
    STATUS_CODE_EQUALS = "status_code_equals"
    STATUS_CODE_IN_RANGE = "status_code_in_range"

    # Attribute assertions
    HAS_ATTRIBUTE = "has_attribute"
    ATTRIBUTE_EQUALS = "attribute_equals"
    ATTRIBUTE_CONTAINS = "attribute_contains"

    # ML-based OCR assertions
    OCR_TEXT_EQUALS = "ocr_text_equals"
    OCR_TEXT_CONTAINS = "ocr_text_contains"

    # ML-based UI state assertions
    UI_STATE_IS = "ui_state_is"

    # ML-based icon/logo assertions
    ICON_PRESENT = "icon_present"
    LOGO_MATCHES = "logo_matches"

    # ML-based color assertions
    COLOR_DOMINANT_IS = "color_dominant_is"
    HAS_COLOR = "has_color"

    # ML-based layout assertions
    LAYOUT_ALIGNED = "layout_aligned"
    ELEMENTS_COUNT = "elements_count"

    # ML-based accessibility assertions
    CONTRAST_RATIO_MIN = "contrast_ratio_min"
    WCAG_COMPLIANT = "wcag_compliant"

    # ML-based form field assertions
    FORM_FIELDS_MATCH = "form_fields_match"

    # ML-based region diff assertions
    REGION_DIFF_MAX = "region_diff_max"


class VisualComparisonMode(StrEnum):
    """Visual comparison algorithms."""

    PIXEL = "pixel"
    PERCEPTUAL = "perceptual"
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"


class VisualThresholdMode(StrEnum):
    """Preset threshold modes for visual comparison."""

    STRICT = "strict"    # 0.99 similarity required (1% tolerance)
    NORMAL = "normal"    # 0.95 similarity required (5% tolerance)
    LOOSE = "loose"      # 0.85 similarity required (15% tolerance)
    CUSTOM = "custom"    # Use custom threshold value


class SecretSource(StrEnum):
    """Secret storage backends."""

    ENV = "env"
    VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    K8S_SECRET = "k8s_secret"


class SecretReference(BaseModel):
    """Reference to a secret value from external storage."""

    model_config = ConfigDict(frozen=True)

    source: SecretSource
    key: str
    path: str | None = None
    version: str | None = None

    def __str__(self) -> str:
        return f"${{{self.source}:{self.key}}}"


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""

    model_config = ConfigDict(extra="forbid")

    base_url: str | None = None
    variables: dict[str, str | SecretReference] = Field(default_factory=dict)
    timeouts: dict[str, int] = Field(default_factory=dict)
    proxy: dict[str, Any] | None = None
    headers: dict[str, str] = Field(default_factory=dict)


class AssertionConfig(BaseModel):
    """Configuration for element/text assertions."""

    model_config = ConfigDict(extra="forbid")

    selector: str | None = None
    attribute: str | None = None
    property: str | None = None
    operator: AssertionOperator = AssertionOperator.EXISTS
    expected: Any = None
    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)
    retry_count: int = Field(default=3, ge=0, le=10)

    @model_validator(mode="after")
    def validate_assertion(self) -> AssertionConfig:
        """Ensure assertion has required fields based on operator."""
        operators_needing_selector = {
            AssertionOperator.IS_VISIBLE,
            AssertionOperator.IS_HIDDEN,
            AssertionOperator.IS_ENABLED,
            AssertionOperator.IS_DISABLED,
            AssertionOperator.IS_CHECKED,
            AssertionOperator.IS_UNCHECKED,
            AssertionOperator.EXISTS,
            AssertionOperator.NOT_EXISTS,
        }
        if self.operator in operators_needing_selector and not self.selector:
            raise ValueError(f"Operator {self.operator} requires a selector")
        return self


class VisualAssertionConfig(BaseModel):
    """
    Configuration for visual regression assertions.

    Enterprise features:
    - Anti-aliasing tolerance with Gaussian blur preprocessing
    - Automatic dynamic region detection (ads, timestamps, avatars)
    - Device/breakpoint-specific baselines with auto-selection
    - Scroll position normalization
    - Multi-threshold modes (strict, normal, loose, custom)
    - Enhanced diff reporting with HTML reports
    """

    model_config = ConfigDict(extra="forbid")

    # Core settings
    baseline_name: str
    selector: str | None = None
    mode: VisualComparisonMode = VisualComparisonMode.SEMANTIC
    threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    ignore_regions: list[dict[str, int]] = Field(default_factory=list)
    ignore_colors: bool = False
    message: str | None = None
    update_baseline: bool = False

    # Enterprise: Multi-threshold modes
    threshold_mode: VisualThresholdMode = VisualThresholdMode.CUSTOM

    # Enterprise: Anti-aliasing tolerance
    anti_aliasing_tolerance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Anti-aliasing tolerance (0-1). Higher values apply more blur to reduce font rendering differences.",
    )
    anti_aliasing_sigma: float = Field(
        default=1.0,
        ge=0.1,
        le=5.0,
        description="Gaussian blur sigma for anti-aliasing preprocessing.",
    )

    # Enterprise: Auto-mask dynamic regions
    auto_mask_dynamic: bool = Field(
        default=False,
        description="Automatically detect and mask dynamic regions (ads, timestamps, avatars).",
    )

    # Enterprise: Scroll position normalization
    normalize_scroll: bool = Field(
        default=True,
        description="Normalize scroll position and attempt to crop browser chrome.",
    )

    # Enterprise: HTML diff report
    generate_html_report: bool = Field(
        default=False,
        description="Generate detailed HTML diff report with side-by-side comparison.",
    )

    # Legacy field (kept for backwards compatibility)
    anti_aliasing_threshold: float = Field(default=0.1, ge=0.0, le=1.0)

    @field_validator("ignore_regions")
    @classmethod
    def validate_regions(cls, v: list[dict[str, int]]) -> list[dict[str, int]]:
        """Validate ignore region format."""
        for region in v:
            required_keys = {"x", "y", "width", "height"}
            if not required_keys.issubset(region.keys()):
                raise ValueError(f"Ignore region must have keys: {required_keys}")
            if any(region[k] < 0 for k in required_keys):
                raise ValueError("Ignore region values must be non-negative")
        return v

    @model_validator(mode="after")
    def validate_threshold_mode(self) -> VisualAssertionConfig:
        """Validate threshold configuration."""
        # If using non-custom mode, threshold is determined by the mode
        if self.threshold_mode != VisualThresholdMode.CUSTOM and self.threshold != 0.05:
            # Log warning but don't error - threshold_mode takes precedence
            pass
        return self


class NetworkAssertionConfig(BaseModel):
    """Configuration for network-level assertions."""

    model_config = ConfigDict(extra="forbid")

    url_pattern: str
    is_regex: bool = False
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"] | None = None
    status_code: int | None = Field(default=None, ge=100, le=599)
    status_range: tuple[int, int] | None = None
    response_contains: str | None = None
    response_matches: str | None = None
    headers_contain: dict[str, str] | None = None
    max_response_time_ms: int | None = Field(default=None, ge=0)
    should_be_blocked: bool = False
    message: str | None = None
    timeout: int = Field(default=30000, ge=0, le=300000)

    @field_validator("url_pattern")
    @classmethod
    def validate_url_pattern(cls, v: str) -> str:
        """Validate URL pattern is not empty."""
        if not v.strip():
            raise ValueError("URL pattern cannot be empty")
        return v

    @model_validator(mode="after")
    def validate_status(self) -> NetworkAssertionConfig:
        """Validate status code configuration."""
        if self.status_range is not None:
            if self.status_range[0] > self.status_range[1]:
                raise ValueError("Status range start must be <= end")
            if not (100 <= self.status_range[0] <= 599) or not (100 <= self.status_range[1] <= 599):
                raise ValueError("Status codes must be between 100 and 599")
        return self


class ElementAssertionConfig(BaseModel):
    """Configuration for element-specific assertions."""

    model_config = ConfigDict(extra="forbid")

    selector: str
    count: int | None = Field(default=None, ge=0)
    count_min: int | None = Field(default=None, ge=0)
    count_max: int | None = Field(default=None, ge=0)
    text: str | None = None
    text_contains: str | None = None
    text_matches: str | None = None
    attribute: str | None = None
    attribute_value: str | None = None
    css_property: str | None = None
    css_value: str | None = None
    is_visible: bool | None = None
    is_enabled: bool | None = None
    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @model_validator(mode="after")
    def validate_count_constraints(self) -> ElementAssertionConfig:
        """Validate count constraints are consistent."""
        if self.count_min is not None and self.count_max is not None:
            if self.count_min > self.count_max:
                raise ValueError("count_min must be <= count_max")
        if self.count is not None and (self.count_min is not None or self.count_max is not None):
            raise ValueError("Cannot specify both exact count and min/max count")
        return self


class CustomAssertionConfig(BaseModel):
    """Configuration for custom JavaScript assertions."""

    model_config = ConfigDict(extra="forbid")

    script: str
    args: list[Any] = Field(default_factory=list)
    expected: Any = None
    operator: AssertionOperator = AssertionOperator.IS_TRUTHY
    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @field_validator("script")
    @classmethod
    def validate_script(cls, v: str) -> str:
        """Validate script is not empty."""
        if not v.strip():
            raise ValueError("Script cannot be empty")
        return v


# =============================================================================
# ML-based Assertion Configurations (no LLM required)
# =============================================================================


class UIStateType(StrEnum):
    """UI state types for ML classification."""

    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"
    EMPTY = "empty"
    NORMAL = "normal"


class AlignmentType(StrEnum):
    """Element alignment types."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    VERTICAL_CENTER = "vertical_center"


class OCRAssertionConfig(BaseModel):
    """Configuration for OCR-based text assertions."""

    model_config = ConfigDict(extra="forbid")

    # OCR extraction settings
    backend: Literal["pytesseract", "easyocr"] = "easyocr"
    languages: list[str] = Field(default_factory=lambda: ["en"])

    # Region to extract from (x, y, width, height)
    region: tuple[int, int, int, int] | None = None

    # Assertion settings
    expected_text: str | None = None
    contains: str | None = None
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=10000, ge=0, le=300000)


class UIStateAssertionConfig(BaseModel):
    """Configuration for UI state classification assertions."""

    model_config = ConfigDict(extra="forbid")

    expected_state: UIStateType
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)


class ColorAssertionConfig(BaseModel):
    """Configuration for color-based assertions."""

    model_config = ConfigDict(extra="forbid")

    # Color can be RGB tuple "(255, 0, 0)" or hex "#ff0000"
    dominant_color: str | None = None
    has_color: str | None = None

    # Tolerance for color matching (0-255)
    tolerance: int = Field(default=30, ge=0, le=255)

    # Minimum percentage of image for has_color check
    min_percentage: float = Field(default=0.01, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @model_validator(mode="after")
    def validate_color_assertion(self) -> ColorAssertionConfig:
        """Ensure at least one color assertion is specified."""
        if self.dominant_color is None and self.has_color is None:
            raise ValueError("Must specify either dominant_color or has_color")
        return self


class LayoutAssertionConfig(BaseModel):
    """Configuration for layout analysis assertions."""

    model_config = ConfigDict(extra="forbid")

    # Element counting
    expected_count: int | None = Field(default=None, ge=0)
    min_count: int | None = Field(default=None, ge=0)
    max_count: int | None = Field(default=None, ge=0)

    # Alignment checking
    alignment: AlignmentType | None = None
    alignment_tolerance: int = Field(default=10, ge=0)

    # Filter by element type (icon, button, input_field, container, etc.)
    element_type: str | None = None

    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @model_validator(mode="after")
    def validate_layout_assertion(self) -> LayoutAssertionConfig:
        """Validate layout assertion configuration."""
        if self.min_count is not None and self.max_count is not None:
            if self.min_count > self.max_count:
                raise ValueError("min_count must be <= max_count")
        if self.expected_count is not None and (self.min_count is not None or self.max_count is not None):
            raise ValueError("Cannot specify both expected_count and min/max count")
        return self


class IconAssertionConfig(BaseModel):
    """Configuration for icon/logo matching assertions."""

    model_config = ConfigDict(extra="forbid")

    # Path to template image to match
    template_path: str

    # Matching method: 'feature' (ORB) or 'correlation' (template matching)
    method: Literal["feature", "correlation"] = "feature"

    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @field_validator("template_path")
    @classmethod
    def validate_template_path(cls, v: str) -> str:
        """Validate template path is not empty."""
        if not v.strip():
            raise ValueError("Template path cannot be empty")
        return v


class AccessibilityAssertionConfig(BaseModel):
    """Configuration for accessibility assertions (contrast, WCAG)."""

    model_config = ConfigDict(extra="forbid")

    # Minimum contrast ratio (WCAG AA = 4.5, AAA = 7.0)
    min_contrast_ratio: float | None = Field(default=None, ge=1.0, le=21.0)

    # WCAG compliance level
    wcag_level: Literal["AA", "AAA"] | None = None

    # Region to analyze (x, y, width, height)
    region: tuple[int, int, int, int] | None = None

    message: str | None = None
    timeout: int = Field(default=5000, ge=0, le=300000)

    @model_validator(mode="after")
    def validate_accessibility_assertion(self) -> AccessibilityAssertionConfig:
        """Ensure at least one accessibility check is specified."""
        if self.min_contrast_ratio is None and self.wcag_level is None:
            raise ValueError("Must specify either min_contrast_ratio or wcag_level")
        return self


class MLAssertionConfig(BaseModel):
    """
    Unified configuration for ML-based assertions.

    Supports all ML assertion types through nested configs.
    """

    model_config = ConfigDict(extra="forbid")

    # OCR assertions
    ocr: OCRAssertionConfig | None = None

    # UI state classification
    ui_state: UIStateAssertionConfig | None = None

    # Color analysis
    color: ColorAssertionConfig | None = None

    # Layout analysis
    layout: LayoutAssertionConfig | None = None

    # Icon/logo matching
    icon: IconAssertionConfig | None = None

    # Accessibility checks
    accessibility: AccessibilityAssertionConfig | None = None

    # General settings
    message: str | None = None
    timeout: int = Field(default=10000, ge=0, le=300000)

    @model_validator(mode="after")
    def validate_ml_assertion(self) -> MLAssertionConfig:
        """Ensure at least one ML assertion type is specified."""
        has_assertion = any([
            self.ocr is not None,
            self.ui_state is not None,
            self.color is not None,
            self.layout is not None,
            self.icon is not None,
            self.accessibility is not None,
        ])
        if not has_assertion:
            raise ValueError("Must specify at least one ML assertion type")
        return self


# =============================================================================
# LLM-based Assertion Configurations (optional, requires LLM enabled)
# =============================================================================


class LLMAssertionConfig(BaseModel):
    """
    Configuration for LLM-based semantic assertions.

    LLM assertions use large language models for intelligent validation:
    - Semantic understanding of page state
    - Natural language assertions
    - Content quality analysis

    Gracefully falls back when LLM is disabled.
    """

    model_config = ConfigDict(extra="forbid")

    # Semantic assertion: natural language condition
    assertion: str = Field(
        description="Natural language assertion (e.g., 'page shows success message')",
    )

    # Optional context for the assertion
    context: str | None = Field(
        default=None,
        description="Additional context to help validate the assertion",
    )

    # Confidence threshold (0.0-1.0)
    min_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to pass the assertion",
    )

    # Custom error message
    message: str | None = None
    timeout: int = Field(default=30000, ge=0, le=300000)

    @field_validator("assertion")
    @classmethod
    def validate_assertion(cls, v: str) -> str:
        """Ensure assertion is not empty."""
        if not v.strip():
            raise ValueError("Assertion cannot be empty")
        return v


class SemanticAssertionConfig(BaseModel):
    """
    Configuration for semantic state assertions.

    Validates that the page is in an expected semantic state.
    """

    model_config = ConfigDict(extra="forbid")

    # Expected state description
    expected_state: str = Field(
        description="Expected state (e.g., 'logged_in', 'checkout_complete')",
    )

    # State indicators to look for
    indicators: list[str] = Field(
        default_factory=list,
        description="Specific indicators that signal the state",
    )

    # Confidence threshold
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=30000, ge=0, le=300000)


class ContentAssertionConfig(BaseModel):
    """
    Configuration for content validation assertions.

    Uses LLM to analyze and validate page content quality and correctness.
    """

    model_config = ConfigDict(extra="forbid")

    # Content type for context
    content_type: str = Field(
        description="Type of content (e.g., 'product_page', 'search_results')",
    )

    # Expected content patterns
    expected_patterns: list[str] = Field(
        description="List of expected content patterns",
    )

    # Optional selector to scope content
    selector: str | None = Field(
        default=None,
        description="CSS selector to limit content scope",
    )

    # Confidence threshold
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    message: str | None = None
    timeout: int = Field(default=30000, ge=0, le=300000)

    @field_validator("expected_patterns")
    @classmethod
    def validate_patterns(cls, v: list[str]) -> list[str]:
        """Ensure at least one pattern is specified."""
        if not v:
            raise ValueError("At least one expected pattern must be specified")
        return v


class TestStep(BaseModel):
    """A single test step with natural language support."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str | None = None
    action: StepAction
    description: str | None = None

    # Common parameters
    selector: str | None = None
    text: str | None = None
    value: str | None = None
    url: str | None = None
    timeout: int | None = Field(default=None, ge=0, le=300000)
    wait_until: Literal["load", "domcontentloaded", "networkidle"] | None = None

    # Coordinate parameters
    x: int | None = None
    y: int | None = None
    start_x: int | None = None
    start_y: int | None = None
    end_x: int | None = None
    end_y: int | None = None

    # Scroll parameters
    scroll_x: int | None = None
    scroll_y: int | None = None

    # Key parameters
    key: str | None = None
    modifiers: list[str] | None = None

    # File upload
    file_paths: list[str] | None = None

    # Screenshot/video
    filename: str | None = None
    fps: int | None = Field(default=None, ge=1, le=60)

    # Extraction parameters
    template: str | None = None
    clean_level: Literal["minimal", "basic", "aggressive"] | None = None
    attribute_name: str | None = None

    # Script execution
    script: str | None = None
    args: list[Any] | None = None

    # Cookie parameters
    cookie_name: str | None = None
    cookie_value: str | None = None
    cookie_domain: str | None = None
    cookie_path: str | None = None
    cookie_secure: bool | None = None
    cookie_http_only: bool | None = None
    cookie_expires: int | None = None

    # Viewport
    width: int | None = Field(default=None, ge=1, le=10000)
    height: int | None = Field(default=None, ge=1, le=10000)

    # URL assertion
    url_pattern: str | None = None
    is_regex: bool = False

    # Assertion configurations
    assertion: AssertionConfig | None = None
    visual_assertion: VisualAssertionConfig | None = None
    network_assertion: NetworkAssertionConfig | None = None
    element_assertion: ElementAssertionConfig | None = None
    custom_assertion: CustomAssertionConfig | None = None

    # ML-based assertion configurations (no LLM required)
    ml_assertion: MLAssertionConfig | None = None
    ocr_assertion: OCRAssertionConfig | None = None
    ui_state_assertion: UIStateAssertionConfig | None = None
    color_assertion: ColorAssertionConfig | None = None
    layout_assertion: LayoutAssertionConfig | None = None
    icon_assertion: IconAssertionConfig | None = None
    accessibility_assertion: AccessibilityAssertionConfig | None = None

    # LLM-based assertion configurations (optional, requires LLM enabled)
    llm_assertion: LLMAssertionConfig | None = None
    semantic_assertion: SemanticAssertionConfig | None = None
    content_assertion: ContentAssertionConfig | None = None

    # Flow control
    skip_if: str | None = None
    continue_on_failure: bool = False
    retry_count: int = Field(default=0, ge=0, le=10)
    retry_delay_ms: int = Field(default=1000, ge=0, le=60000)

    # Variable capture
    capture_as: str | None = None

    # Recovery/healing metadata (used by test runner for URL-aware recovery)
    # If step fails, runner can navigate to this URL and retry
    expected_url: str | None = Field(
        default=None,
        alias="_expected_url",
        description="Expected page URL for this step. Used for recovery when element not found.",
    )

    @model_validator(mode="after")
    def validate_step_params(self) -> TestStep:
        """Validate required parameters based on action type."""
        action_requirements: dict[StepAction, list[str]] = {
            # Navigation
            StepAction.NAVIGATE: ["url"],
            StepAction.WAIT_FOR_SELECTOR: ["selector"],
            StepAction.WAIT_FOR_URL: ["url"],
            # Clicks & Interactions
            StepAction.CLICK: ["selector"],
            StepAction.DOUBLE_CLICK: ["selector"],
            StepAction.RIGHT_CLICK: ["selector"],
            StepAction.HOVER: ["selector"],
            StepAction.DRAG_DROP: ["start_x", "start_y", "end_x", "end_y"],
            # Forms
            StepAction.TYPE: ["selector", "text"],
            StepAction.PICK: ["selector", "value"],
            StepAction.PRESS_KEY: ["key"],
            StepAction.UPLOAD: ["selector", "file_paths"],
            # Scroll
            StepAction.SCROLL_TO_ELEMENT: ["selector"],
            # Extraction
            StepAction.GET_ATTRIBUTE: ["selector", "attribute_name"],
            # Script execution
            StepAction.EVALUATE: ["script"],
            # State checks
            StepAction.CHECK_VISIBLE: ["selector"],
            StepAction.CHECK_ENABLED: ["selector"],
            StepAction.CHECK_CHECKED: ["selector"],
            # Cookies
            StepAction.SET_COOKIE: ["cookie_name", "cookie_value"],
            # Viewport
            StepAction.SET_VIEWPORT: ["width", "height"],
            # Assertions
            StepAction.VISUAL_ASSERT: [],
            StepAction.ASSERT: [],
            StepAction.NETWORK_ASSERT: [],
            StepAction.URL_ASSERT: ["url_pattern"],
        }

        if self.action in action_requirements:
            for param in action_requirements[self.action]:
                if getattr(self, param) is None:
                    raise ValueError(f"Action '{self.action}' requires parameter '{param}'")

        if self.action == StepAction.ASSERT and not self.assertion:
            raise ValueError("Action 'assert' requires 'assertion' configuration")
        if self.action == StepAction.VISUAL_ASSERT and not self.visual_assertion:
            raise ValueError("Action 'visual_assert' requires 'visual_assertion' configuration")
        if self.action == StepAction.NETWORK_ASSERT and not self.network_assertion:
            raise ValueError("Action 'network_assert' requires 'network_assertion' configuration")

        # ML-based assertion validations
        if self.action == StepAction.ML_ASSERT and not self.ml_assertion:
            raise ValueError("Action 'ml_assert' requires 'ml_assertion' configuration")
        if self.action == StepAction.OCR_ASSERT and not self.ocr_assertion:
            raise ValueError("Action 'ocr_assert' requires 'ocr_assertion' configuration")
        if self.action == StepAction.UI_STATE_ASSERT and not self.ui_state_assertion:
            raise ValueError("Action 'ui_state_assert' requires 'ui_state_assertion' configuration")
        if self.action == StepAction.COLOR_ASSERT and not self.color_assertion:
            raise ValueError("Action 'color_assert' requires 'color_assertion' configuration")
        if self.action == StepAction.LAYOUT_ASSERT and not self.layout_assertion:
            raise ValueError("Action 'layout_assert' requires 'layout_assertion' configuration")
        if self.action == StepAction.ICON_ASSERT and not self.icon_assertion:
            raise ValueError("Action 'icon_assert' requires 'icon_assertion' configuration")
        if self.action == StepAction.ACCESSIBILITY_ASSERT and not self.accessibility_assertion:
            raise ValueError("Action 'accessibility_assert' requires 'accessibility_assertion' configuration")

        # LLM-based assertion validations
        if self.action == StepAction.LLM_ASSERT and not self.llm_assertion:
            raise ValueError("Action 'llm_assert' requires 'llm_assertion' configuration")
        if self.action == StepAction.SEMANTIC_ASSERT and not self.semantic_assertion:
            raise ValueError("Action 'semantic_assert' requires 'semantic_assertion' configuration")
        if self.action == StepAction.CONTENT_ASSERT and not self.content_assertion:
            raise ValueError("Action 'content_assert' requires 'content_assertion' configuration")

        return self


class TestMetadata(BaseModel):
    """Metadata for test specifications."""

    model_config = ConfigDict(extra="forbid")

    tags: list[str] = Field(default_factory=list)
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    owner: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    jira_ticket: str | None = None
    retry_count: int = Field(default=2, ge=0, le=10)
    timeout_ms: int = Field(default=300000, ge=0, le=3600000)
    parallel: bool = False
    browser_profiles: list[str] = Field(default_factory=list)


class HookConfig(BaseModel):
    """Configuration for test lifecycle hooks."""

    model_config = ConfigDict(extra="forbid")

    steps: list[TestStep] = Field(default_factory=list)
    on_failure_only: bool = False
    continue_on_error: bool = True


class VersioningConfigModel(BaseModel):
    """Configuration for versioned test tracking in YAML specs."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    storage_path: str = ".autoqa/history"
    retention_days: int = Field(default=90, ge=1, le=365)
    capture_screenshots: bool = True
    capture_network: bool = True
    capture_elements: bool = True
    element_selectors: list[str] = Field(default_factory=list)
    auto_compare_previous: bool = False
    diff_threshold: float = Field(default=0.05, ge=0.0, le=1.0)


class TestSpec(BaseModel):
    """Complete test specification."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    metadata: TestMetadata = Field(default_factory=TestMetadata)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    variables: dict[str, str | SecretReference] = Field(default_factory=dict)

    before_all: HookConfig | None = None
    before_each: HookConfig | None = None
    steps: list[TestStep] = Field(min_length=1)
    after_each: HookConfig | None = None
    after_all: HookConfig | None = None

    # Versioning configuration
    versioning: VersioningConfigModel = Field(default_factory=VersioningConfigModel)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate test name format."""
        if not re.match(r"^[\w\s\-_.]+$", v):
            raise ValueError(
                "Test name can only contain alphanumeric characters, spaces, "
                "hyphens, underscores, and periods"
            )
        return v


class TestSuite(BaseModel):
    """Collection of test specifications."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    metadata: TestMetadata = Field(default_factory=TestMetadata)
    environment: EnvironmentConfig = Field(default_factory=EnvironmentConfig)
    variables: dict[str, str | SecretReference] = Field(default_factory=dict)

    before_suite: HookConfig | None = None
    tests: list[TestSpec] = Field(min_length=1)
    after_suite: HookConfig | None = None

    parallel_execution: bool = False
    max_parallel: int = Field(default=5, ge=1, le=100)
    fail_fast: bool = False

    # Versioning configuration
    versioning: VersioningConfigModel = Field(default_factory=VersioningConfigModel)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate suite name format."""
        if not re.match(r"^[\w\s\-_.]+$", v):
            raise ValueError(
                "Suite name can only contain alphanumeric characters, spaces, "
                "hyphens, underscores, and periods"
            )
        return v
