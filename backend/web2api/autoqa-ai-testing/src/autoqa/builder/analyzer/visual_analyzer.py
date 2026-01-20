"""
Visual/UI analysis for intelligent test generation.

Provides visual analysis capabilities:
- Layout detection and validation rules
- Color contrast analysis for accessibility
- Visual hierarchy identification
- Screenshot comparison baseline generation
- Responsive breakpoint detection
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from enum import StrEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

import cv2
import numpy as np
import structlog
from PIL import Image
from sklearn.cluster import KMeans

if TYPE_CHECKING:
    from owl_browser import BrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class VisualConfig:
    """Configuration for visual analyzer."""

    enable_color_analysis: bool = True
    """Whether to perform color palette analysis."""

    enable_contrast_check: bool = True
    """Whether to check color contrast for accessibility."""

    enable_layout_detection: bool = True
    """Whether to detect layout patterns."""

    enable_responsive_check: bool = True
    """Whether to check responsive breakpoints."""

    wcag_level: str = "AA"
    """WCAG compliance level to check (AA or AAA)."""

    color_clusters: int = 5
    """Number of color clusters for palette extraction."""

    screenshot_quality: int = 85
    """Screenshot JPEG quality (1-100)."""

    responsive_breakpoints: list[int] = field(
        default_factory=lambda: [320, 768, 1024, 1280, 1920]
    )
    """Viewport widths to test for responsive design."""


class LayoutType(StrEnum):
    """Detected layout patterns."""

    SINGLE_COLUMN = auto()
    TWO_COLUMN = auto()
    THREE_COLUMN = auto()
    GRID = auto()
    MASONRY = auto()
    SIDEBAR_LEFT = auto()
    SIDEBAR_RIGHT = auto()
    HEADER_FOOTER = auto()
    FULL_WIDTH = auto()
    CENTERED = auto()
    UNKNOWN = auto()


class VisualSeverity(StrEnum):
    """Severity of visual issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ColorInfo:
    """Color information."""

    rgb: tuple[int, int, int]
    hex_code: str
    percentage: float

    @classmethod
    def from_rgb(cls, rgb: tuple[int, int, int], percentage: float) -> ColorInfo:
        """Create ColorInfo from RGB values."""
        hex_code = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        return cls(rgb=rgb, hex_code=hex_code, percentage=percentage)


@dataclass
class ContrastResult:
    """Contrast analysis result."""

    foreground: tuple[int, int, int]
    background: tuple[int, int, int]
    ratio: float
    passes_aa: bool
    passes_aa_large: bool
    passes_aaa: bool
    passes_aaa_large: bool


@dataclass
class AccessibilityCheck:
    """Accessibility check result."""

    check_name: str
    passed: bool
    severity: VisualSeverity
    message: str
    selector: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LayoutInfo:
    """Layout analysis result."""

    layout_type: LayoutType
    columns: int
    has_header: bool
    has_footer: bool
    has_sidebar: bool
    sidebar_position: str | None
    content_width: int
    content_height: int
    margins: dict[str, int]
    grid_areas: list[dict[str, Any]]
    confidence: float


@dataclass
class VisualHierarchy:
    """Visual hierarchy analysis result."""

    primary_elements: list[str]
    secondary_elements: list[str]
    tertiary_elements: list[str]
    focal_points: list[dict[str, Any]]
    reading_order: list[str]
    whitespace_distribution: dict[str, float]


@dataclass
class ResponsiveBreakpoint:
    """Responsive breakpoint information."""

    name: str
    width: int
    layout_changes: list[str]
    hidden_elements: list[str]
    visible_elements: list[str]
    layout_type: LayoutType


@dataclass
class VisualAnalysisResult:
    """Complete visual analysis result."""

    layout: LayoutInfo
    hierarchy: VisualHierarchy
    accessibility_checks: list[AccessibilityCheck]
    dominant_colors: list[ColorInfo]
    contrast_issues: list[ContrastResult]
    responsive_breakpoints: list[ResponsiveBreakpoint]
    screenshot_hash: str
    visual_complexity_score: float


class VisualAnalyzer:
    """
    Visual analyzer for UI/UX analysis.

    Provides:
    - Layout detection and classification
    - Color and contrast analysis
    - Visual hierarchy identification
    - Accessibility checks
    - Responsive breakpoint detection
    - Screenshot comparison baselines
    """

    # Standard responsive breakpoints
    BREAKPOINTS: list[tuple[str, int]] = [
        ("mobile_sm", 320),
        ("mobile", 375),
        ("mobile_lg", 425),
        ("tablet", 768),
        ("laptop", 1024),
        ("desktop", 1280),
        ("desktop_lg", 1440),
        ("desktop_xl", 1920),
    ]

    # WCAG contrast requirements
    WCAG_AA_NORMAL = 4.5
    WCAG_AA_LARGE = 3.0
    WCAG_AAA_NORMAL = 7.0
    WCAG_AAA_LARGE = 4.5

    def __init__(self, config: VisualConfig | None = None) -> None:
        self.config = config or VisualConfig()
        self._log = logger.bind(component="visual_analyzer")

    async def analyze(
        self,
        page: BrowserContext,
        screenshot: bytes | None = None,
    ) -> VisualAnalysisResult:
        """
        Perform comprehensive visual analysis.

        Args:
            page: Browser context with loaded page
            screenshot: Optional pre-captured screenshot

        Returns:
            Complete visual analysis result
        """
        self._log.info("Starting visual analysis")

        # Capture screenshot if not provided
        if screenshot is None:
            screenshot = page.screenshot()

        # Convert screenshot to formats needed for analysis
        pil_image = Image.open(io.BytesIO(screenshot))
        cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Perform analyses
        layout = await self._analyze_layout(page, cv2_image)
        hierarchy = await self._analyze_hierarchy(page, cv2_image)
        colors = self._analyze_colors(cv2_image)
        accessibility = await self._check_accessibility(page, cv2_image)
        contrast_issues = self._find_contrast_issues(cv2_image)
        breakpoints = await self._analyze_responsive(page)
        complexity = self._calculate_visual_complexity(cv2_image)
        screenshot_hash = self._calculate_screenshot_hash(cv2_image)

        result = VisualAnalysisResult(
            layout=layout,
            hierarchy=hierarchy,
            accessibility_checks=accessibility,
            dominant_colors=colors,
            contrast_issues=contrast_issues,
            responsive_breakpoints=breakpoints,
            screenshot_hash=screenshot_hash,
            visual_complexity_score=complexity,
        )

        self._log.info(
            "Visual analysis complete",
            layout_type=layout.layout_type,
            accessibility_issues=sum(1 for c in accessibility if not c.passed),
            complexity_score=complexity,
        )

        return result

    async def _analyze_layout(
        self,
        page: BrowserContext,
        image: np.ndarray[Any, np.dtype[np.uint8]],
    ) -> LayoutInfo:
        """Analyze page layout structure."""
        # Get layout information from DOM
        script = """
        (() => {
            const body = document.body;
            const html = document.documentElement;
            const contentWidth = Math.max(body.scrollWidth, body.offsetWidth, html.clientWidth);
            const contentHeight = Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight);

            // Detect header
            const header = document.querySelector('header, [role="banner"], .header, #header');
            const hasHeader = !!header;

            // Detect footer
            const footer = document.querySelector('footer, [role="contentinfo"], .footer, #footer');
            const hasFooter = !!footer;

            // Detect sidebar
            const sidebar = document.querySelector('aside, [role="complementary"], .sidebar, #sidebar');
            const hasSidebar = !!sidebar;
            let sidebarPosition = null;
            if (sidebar) {
                const rect = sidebar.getBoundingClientRect();
                sidebarPosition = rect.x < contentWidth / 2 ? 'left' : 'right';
            }

            // Detect main content areas
            const mainContent = document.querySelector('main, [role="main"], .main, #main, .content');
            const contentAreas = [];

            // Analyze grid structure
            const potentialGrids = document.querySelectorAll('[class*="grid"], [class*="col-"], [class*="row"]');
            const gridAreas = [];
            for (const grid of potentialGrids) {
                const rect = grid.getBoundingClientRect();
                const style = window.getComputedStyle(grid);
                if (style.display === 'grid' || style.display === 'flex') {
                    gridAreas.push({
                        selector: grid.className || grid.id || grid.tagName,
                        display: style.display,
                        columns: style.gridTemplateColumns || 'auto',
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    });
                }
            }

            // Estimate columns from direct children of body or main
            const container = mainContent || body;
            const children = Array.from(container.children).filter(child => {
                const style = window.getComputedStyle(child);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });

            let columns = 1;
            if (children.length > 1) {
                const firstChildRect = children[0].getBoundingClientRect();
                const childrenInFirstRow = children.filter(child => {
                    const rect = child.getBoundingClientRect();
                    return Math.abs(rect.y - firstChildRect.y) < 50;
                });
                columns = childrenInFirstRow.length;
            }

            // Get margins
            const computedStyle = window.getComputedStyle(body);
            const margins = {
                top: parseInt(computedStyle.marginTop) || 0,
                right: parseInt(computedStyle.marginRight) || 0,
                bottom: parseInt(computedStyle.marginBottom) || 0,
                left: parseInt(computedStyle.marginLeft) || 0
            };

            return {
                contentWidth,
                contentHeight,
                hasHeader,
                hasFooter,
                hasSidebar,
                sidebarPosition,
                columns,
                gridAreas,
                margins
            };
        })()
        """

        layout_data = page.expression(script)

        # Determine layout type
        layout_type = self._classify_layout(layout_data)

        return LayoutInfo(
            layout_type=layout_type,
            columns=layout_data["columns"],
            has_header=layout_data["hasHeader"],
            has_footer=layout_data["hasFooter"],
            has_sidebar=layout_data["hasSidebar"],
            sidebar_position=layout_data["sidebarPosition"],
            content_width=layout_data["contentWidth"],
            content_height=layout_data["contentHeight"],
            margins=layout_data["margins"],
            grid_areas=layout_data["gridAreas"],
            confidence=0.8,
        )

    def _classify_layout(self, layout_data: dict[str, Any]) -> LayoutType:
        """Classify layout type from analysis data."""
        columns = layout_data["columns"]
        has_sidebar = layout_data["hasSidebar"]
        sidebar_position = layout_data["sidebarPosition"]

        if has_sidebar:
            if sidebar_position == "left":
                return LayoutType.SIDEBAR_LEFT
            return LayoutType.SIDEBAR_RIGHT

        if columns == 1:
            return LayoutType.SINGLE_COLUMN
        if columns == 2:
            return LayoutType.TWO_COLUMN
        if columns == 3:
            return LayoutType.THREE_COLUMN
        if columns > 3:
            return LayoutType.GRID

        if layout_data["gridAreas"]:
            return LayoutType.GRID

        return LayoutType.UNKNOWN

    async def _analyze_hierarchy(
        self,
        page: BrowserContext,
        image: np.ndarray[Any, np.dtype[np.uint8]],
    ) -> VisualHierarchy:
        """Analyze visual hierarchy of the page."""
        script = """
        (() => {
            const elements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, a, button, img, [role="heading"]');
            const hierarchy = {
                primary: [],
                secondary: [],
                tertiary: [],
                focalPoints: [],
                readingOrder: []
            };

            // Sort elements by visual prominence
            const elementData = [];
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                if (rect.width === 0 || rect.height === 0) continue;

                const fontSize = parseFloat(style.fontSize);
                const fontWeight = parseInt(style.fontWeight) || 400;
                const area = rect.width * rect.height;

                // Calculate prominence score
                const prominenceScore = (fontSize / 16) * (fontWeight / 400) * (area / 10000);

                elementData.push({
                    selector: el.id ? '#' + el.id : (el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase()),
                    tagName: el.tagName.toLowerCase(),
                    prominenceScore,
                    fontSize,
                    fontWeight,
                    area,
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                });
            }

            // Sort by prominence
            elementData.sort((a, b) => b.prominenceScore - a.prominenceScore);

            // Categorize by prominence
            const total = elementData.length;
            const primaryCount = Math.ceil(total * 0.1);
            const secondaryCount = Math.ceil(total * 0.3);

            hierarchy.primary = elementData.slice(0, primaryCount).map(e => e.selector);
            hierarchy.secondary = elementData.slice(primaryCount, primaryCount + secondaryCount).map(e => e.selector);
            hierarchy.tertiary = elementData.slice(primaryCount + secondaryCount).map(e => e.selector);

            // Identify focal points (large, prominent elements)
            hierarchy.focalPoints = elementData
                .filter(e => e.prominenceScore > 2)
                .slice(0, 5)
                .map(e => ({
                    selector: e.selector,
                    score: e.prominenceScore,
                    position: { x: e.x, y: e.y }
                }));

            // Determine reading order (top-left to bottom-right)
            const sortedByPosition = [...elementData].sort((a, b) => {
                const rowA = Math.floor(a.y / 100);
                const rowB = Math.floor(b.y / 100);
                if (rowA !== rowB) return rowA - rowB;
                return a.x - b.x;
            });
            hierarchy.readingOrder = sortedByPosition.slice(0, 20).map(e => e.selector);

            return hierarchy;
        })()
        """

        hierarchy_data = page.expression(script)

        # Calculate whitespace distribution from image
        whitespace = self._calculate_whitespace_distribution(image)

        return VisualHierarchy(
            primary_elements=hierarchy_data["primary"],
            secondary_elements=hierarchy_data["secondary"],
            tertiary_elements=hierarchy_data["tertiary"],
            focal_points=hierarchy_data["focalPoints"],
            reading_order=hierarchy_data["readingOrder"],
            whitespace_distribution=whitespace,
        )

    def _calculate_whitespace_distribution(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> dict[str, float]:
        """Calculate whitespace distribution in image."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold to find "white" areas (light colored)
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

        height, width = binary.shape

        # Calculate whitespace in different regions
        quadrant_height = height // 2
        quadrant_width = width // 2

        regions = {
            "top_left": binary[:quadrant_height, :quadrant_width],
            "top_right": binary[:quadrant_height, quadrant_width:],
            "bottom_left": binary[quadrant_height:, :quadrant_width],
            "bottom_right": binary[quadrant_height:, quadrant_width:],
        }

        distribution = {}
        for region_name, region in regions.items():
            white_pixels = np.sum(region == 255)
            total_pixels = region.size
            distribution[region_name] = float(white_pixels / total_pixels)

        # Overall whitespace
        total_white = np.sum(binary == 255)
        distribution["total"] = float(total_white / binary.size)

        return distribution

    def _analyze_colors(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> list[ColorInfo]:
        """Analyze dominant colors in the image."""
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Reshape for clustering
        pixels = rgb_image.reshape(-1, 3)

        # Sample pixels for efficiency
        sample_size = min(10000, len(pixels))
        indices = np.random.choice(len(pixels), sample_size, replace=False)
        sampled_pixels = pixels[indices]

        # K-means clustering
        n_colors = 5
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(sampled_pixels)

        # Get colors and percentages
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.predict(sampled_pixels)
        counts = np.bincount(labels)

        total = len(labels)
        color_info_list = []

        for color, count in zip(colors, counts, strict=False):
            percentage = count / total
            rgb = (int(color[0]), int(color[1]), int(color[2]))
            color_info_list.append(ColorInfo.from_rgb(rgb, percentage))

        # Sort by percentage
        color_info_list.sort(key=lambda c: c.percentage, reverse=True)

        return color_info_list

    async def _check_accessibility(
        self,
        page: BrowserContext,
        image: np.ndarray[Any, np.dtype[np.uint8]],
    ) -> list[AccessibilityCheck]:
        """Perform accessibility checks."""
        checks: list[AccessibilityCheck] = []

        # Check for alt text on images
        alt_text_check = await self._check_image_alt_text(page)
        checks.append(alt_text_check)

        # Check for form labels
        label_check = await self._check_form_labels(page)
        checks.append(label_check)

        # Check for heading structure
        heading_check = await self._check_heading_structure(page)
        checks.append(heading_check)

        # Check for focus indicators
        focus_check = await self._check_focus_indicators(page)
        checks.append(focus_check)

        # Check for touch target sizes
        touch_target_check = await self._check_touch_targets(page)
        checks.append(touch_target_check)

        # Check color contrast (basic)
        contrast_check = self._check_color_contrast(image)
        checks.append(contrast_check)

        return checks

    async def _check_image_alt_text(self, page: BrowserContext) -> AccessibilityCheck:
        """Check images for alt text."""
        script = """
        (() => {
            const images = document.querySelectorAll('img');
            const withoutAlt = [];
            const decorative = [];

            for (const img of images) {
                if (!img.alt && !img.getAttribute('role')?.includes('presentation')) {
                    if (img.src && !img.src.startsWith('data:')) {
                        withoutAlt.push(img.src);
                    }
                } else if (img.alt === '' || img.getAttribute('role')?.includes('presentation')) {
                    decorative.push(img.src || 'inline');
                }
            }

            return {
                total: images.length,
                withoutAlt: withoutAlt.length,
                decorative: decorative.length,
                issues: withoutAlt.slice(0, 5)
            };
        })()
        """

        result = page.expression(script)
        passed = result["withoutAlt"] == 0

        return AccessibilityCheck(
            check_name="image_alt_text",
            passed=passed,
            severity=VisualSeverity.HIGH if not passed else VisualSeverity.INFO,
            message=f"{result['withoutAlt']} of {result['total']} images missing alt text" if not passed else "All images have alt text",
            details=result,
        )

    async def _check_form_labels(self, page: BrowserContext) -> AccessibilityCheck:
        """Check form inputs for associated labels."""
        script = """
        (() => {
            const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
            const unlabeled = [];

            for (const input of inputs) {
                const id = input.id;
                const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                const hasAriaLabel = input.getAttribute('aria-label');
                const hasAriaLabelledBy = input.getAttribute('aria-labelledby');
                const hasPlaceholder = input.placeholder;
                const wrappedInLabel = input.closest('label');

                if (!hasLabel && !hasAriaLabel && !hasAriaLabelledBy && !wrappedInLabel) {
                    unlabeled.push({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name || 'unnamed',
                        hasPlaceholder: !!hasPlaceholder
                    });
                }
            }

            return {
                total: inputs.length,
                unlabeled: unlabeled.length,
                issues: unlabeled.slice(0, 5)
            };
        })()
        """

        result = page.expression(script)
        passed = result["unlabeled"] == 0

        return AccessibilityCheck(
            check_name="form_labels",
            passed=passed,
            severity=VisualSeverity.HIGH if not passed else VisualSeverity.INFO,
            message=f"{result['unlabeled']} of {result['total']} inputs missing labels" if not passed else "All form inputs have labels",
            details=result,
        )

    async def _check_heading_structure(self, page: BrowserContext) -> AccessibilityCheck:
        """Check heading hierarchy."""
        script = """
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            const levels = [];
            const issues = [];

            for (const h of headings) {
                const level = parseInt(h.tagName[1]);
                levels.push(level);
            }

            // Check for h1
            const h1Count = levels.filter(l => l === 1).length;
            if (h1Count === 0) {
                issues.push('No h1 element found');
            } else if (h1Count > 1) {
                issues.push(`Multiple h1 elements found (${h1Count})`);
            }

            // Check for skipped levels
            for (let i = 1; i < levels.length; i++) {
                if (levels[i] - levels[i-1] > 1) {
                    issues.push(`Heading level skipped: h${levels[i-1]} to h${levels[i]}`);
                }
            }

            return {
                total: headings.length,
                h1Count,
                levels,
                issues
            };
        })()
        """

        result = page.expression(script)
        passed = len(result["issues"]) == 0

        return AccessibilityCheck(
            check_name="heading_structure",
            passed=passed,
            severity=VisualSeverity.MEDIUM if not passed else VisualSeverity.INFO,
            message="; ".join(result["issues"]) if result["issues"] else "Heading structure is correct",
            details=result,
        )

    async def _check_focus_indicators(self, page: BrowserContext) -> AccessibilityCheck:
        """Check for visible focus indicators."""
        script = """
        (() => {
            const focusableElements = document.querySelectorAll(
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );

            // This is a basic check - can't fully test focus styles without interaction
            const withoutOutline = [];

            for (const el of focusableElements) {
                const style = window.getComputedStyle(el);
                // Check if outline is explicitly removed
                if (style.outlineStyle === 'none' && !style.boxShadow.includes('rgb')) {
                    withoutOutline.push(el.tagName.toLowerCase());
                }
            }

            return {
                total: focusableElements.length,
                potentialIssues: withoutOutline.length,
                issues: [...new Set(withoutOutline)].slice(0, 5)
            };
        })()
        """

        result = page.expression(script)
        # This is a soft check since we can't fully verify focus states
        passed = result["potentialIssues"] < result["total"] * 0.5

        return AccessibilityCheck(
            check_name="focus_indicators",
            passed=passed,
            severity=VisualSeverity.MEDIUM if not passed else VisualSeverity.INFO,
            message=f"{result['potentialIssues']} elements may have removed focus styles" if not passed else "Focus indicators appear present",
            details=result,
        )

    async def _check_touch_targets(self, page: BrowserContext) -> AccessibilityCheck:
        """Check touch target sizes (minimum 44x44px recommended)."""
        script = """
        (() => {
            const minSize = 44;
            const clickable = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"]');
            const tooSmall = [];

            for (const el of clickable) {
                const rect = el.getBoundingClientRect();
                if (rect.width < minSize || rect.height < minSize) {
                    if (rect.width > 0 && rect.height > 0) {  // Visible elements only
                        tooSmall.push({
                            selector: el.id ? '#' + el.id : el.className || el.tagName.toLowerCase(),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        });
                    }
                }
            }

            return {
                total: clickable.length,
                tooSmall: tooSmall.length,
                issues: tooSmall.slice(0, 5)
            };
        })()
        """

        result = page.expression(script)
        passed = result["tooSmall"] < result["total"] * 0.2  # Allow some small elements

        return AccessibilityCheck(
            check_name="touch_targets",
            passed=passed,
            severity=VisualSeverity.LOW if not passed else VisualSeverity.INFO,
            message=f"{result['tooSmall']} of {result['total']} clickable elements below 44x44px" if result["tooSmall"] > 0 else "Touch targets are adequate size",
            details=result,
        )

    def _check_color_contrast(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> AccessibilityCheck:
        """Basic color contrast check using dominant colors."""
        colors = self._analyze_colors(image)

        if len(colors) < 2:
            return AccessibilityCheck(
                check_name="color_contrast",
                passed=True,
                severity=VisualSeverity.INFO,
                message="Insufficient color variation for contrast analysis",
            )

        # Check contrast between two most dominant colors
        color1 = colors[0].rgb
        color2 = colors[1].rgb

        ratio = self._calculate_contrast_ratio(color1, color2)
        passed = ratio >= self.WCAG_AA_NORMAL

        return AccessibilityCheck(
            check_name="color_contrast",
            passed=passed,
            severity=VisualSeverity.HIGH if not passed else VisualSeverity.INFO,
            message=f"Dominant color contrast ratio: {ratio:.2f}:1 (WCAG AA requires 4.5:1)",
            details={
                "color1": colors[0].hex_code,
                "color2": colors[1].hex_code,
                "ratio": ratio,
            },
        )

    def _calculate_contrast_ratio(
        self,
        color1: tuple[int, int, int],
        color2: tuple[int, int, int],
    ) -> float:
        """Calculate WCAG contrast ratio between two colors."""

        def luminance(rgb: tuple[int, int, int]) -> float:
            def adjust(val: int) -> float:
                v = val / 255
                return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

            r, g, b = rgb
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)

        l1 = luminance(color1)
        l2 = luminance(color2)

        lighter = max(l1, l2)
        darker = min(l1, l2)

        return (lighter + 0.05) / (darker + 0.05)

    def _find_contrast_issues(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> list[ContrastResult]:
        """Find potential contrast issues in the image."""
        # This is a simplified check - real contrast analysis would need
        # to analyze text and background specifically
        colors = self._analyze_colors(image)
        issues: list[ContrastResult] = []

        # Check pairs of dominant colors
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                ratio = self._calculate_contrast_ratio(colors[i].rgb, colors[j].rgb)

                issues.append(
                    ContrastResult(
                        foreground=colors[i].rgb,
                        background=colors[j].rgb,
                        ratio=ratio,
                        passes_aa=ratio >= self.WCAG_AA_NORMAL,
                        passes_aa_large=ratio >= self.WCAG_AA_LARGE,
                        passes_aaa=ratio >= self.WCAG_AAA_NORMAL,
                        passes_aaa_large=ratio >= self.WCAG_AAA_LARGE,
                    )
                )

        return issues

    async def _analyze_responsive(
        self, page: BrowserContext
    ) -> list[ResponsiveBreakpoint]:
        """Analyze responsive behavior at different breakpoints."""
        breakpoints: list[ResponsiveBreakpoint] = []

        # Get current viewport size
        current_size = page.expression("""
        (() => ({
            width: window.innerWidth,
            height: window.innerHeight
        }))()
        """)

        # Get baseline visible elements
        baseline_elements = await self._get_visible_elements(page)

        # Only analyze a few key breakpoints to avoid too much time
        key_breakpoints = [
            ("mobile", 375),
            ("tablet", 768),
            ("desktop", 1280),
        ]

        for name, width in key_breakpoints:
            # Note: This would require page resize which may not be possible
            # In a real implementation, this would need special handling
            breakpoints.append(
                ResponsiveBreakpoint(
                    name=name,
                    width=width,
                    layout_changes=[],
                    hidden_elements=[],
                    visible_elements=[],
                    layout_type=LayoutType.UNKNOWN,
                )
            )

        return breakpoints

    async def _get_visible_elements(self, page: BrowserContext) -> list[str]:
        """Get list of visible element selectors."""
        script = """
        (() => {
            const visible = [];
            const elements = document.querySelectorAll('*');

            for (const el of elements) {
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();

                if (style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    rect.width > 0 &&
                    rect.height > 0) {
                    const selector = el.id ? '#' + el.id :
                        el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase();
                    if (!visible.includes(selector)) {
                        visible.push(selector);
                    }
                }
            }

            return visible.slice(0, 100);  // Limit for performance
        })()
        """

        return page.expression(script)

    def _calculate_visual_complexity(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> float:
        """Calculate visual complexity score (0-1)."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Edge detection for complexity measure
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        # Color variety
        colors = self._analyze_colors(image)
        color_entropy = -sum(c.percentage * np.log2(c.percentage + 1e-10) for c in colors)

        # Combine metrics (weighted)
        complexity = 0.6 * min(edge_density * 10, 1.0) + 0.4 * min(color_entropy / 2, 1.0)

        return round(complexity, 3)

    def _calculate_screenshot_hash(
        self, image: np.ndarray[Any, np.dtype[np.uint8]]
    ) -> str:
        """Calculate perceptual hash for screenshot comparison."""
        # Resize to 8x8 and convert to grayscale
        small = cv2.resize(image, (8, 8))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

        # Calculate average
        avg = gray.mean()

        # Create hash based on comparison to average
        hash_bits = (gray > avg).flatten()
        hash_int = int("".join("1" if b else "0" for b in hash_bits), 2)

        return f"{hash_int:016x}"

    def create_baseline(
        self,
        screenshot: bytes,
        output_path: Path,
    ) -> dict[str, Any]:
        """
        Create a baseline for visual regression testing.

        Args:
            screenshot: Screenshot bytes
            output_path: Path to save baseline

        Returns:
            Baseline metadata
        """
        pil_image = Image.open(io.BytesIO(screenshot))
        cv2_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

        # Save screenshot
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pil_image.save(output_path)

        # Generate metadata
        colors = self._analyze_colors(cv2_image)
        complexity = self._calculate_visual_complexity(cv2_image)
        screenshot_hash = self._calculate_screenshot_hash(cv2_image)

        metadata = {
            "path": str(output_path),
            "width": pil_image.width,
            "height": pil_image.height,
            "hash": screenshot_hash,
            "complexity": complexity,
            "dominant_colors": [{"hex": c.hex_code, "percentage": c.percentage} for c in colors[:3]],
        }

        # Save metadata
        import json

        metadata_path = output_path.with_suffix(".json")
        metadata_path.write_text(json.dumps(metadata, indent=2))

        return metadata
