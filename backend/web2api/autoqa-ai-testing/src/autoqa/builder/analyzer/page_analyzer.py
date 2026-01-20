"""
Deep page analysis for intelligent test generation.

Provides comprehensive DOM and component analysis:
- DOM structure analysis (depth, complexity metrics)
- Component detection (forms, tables, modals, navigation, cards)
- Interactive element cataloging with context
- Shadow DOM and iframe handling
- Single Page Application (SPA) detection
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import structlog

if TYPE_CHECKING:
    from owl_browser import BrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class AnalyzerConfig:
    """Configuration for page analyzer."""

    max_depth: int = 50
    """Maximum DOM depth to traverse."""

    max_elements: int = 1000
    """Maximum elements to analyze."""

    detect_shadow_dom: bool = True
    """Whether to detect Shadow DOM components."""

    detect_iframes: bool = True
    """Whether to analyze iframe content."""

    detect_spa: bool = True
    """Whether to detect SPA patterns."""

    extract_accessibility: bool = True
    """Whether to extract accessibility attributes."""

    element_timeout: int = 5000
    """Timeout for element queries in ms."""


class PageComplexity(StrEnum):
    """Page complexity classification."""

    SIMPLE = auto()
    """Few elements, flat structure."""

    MODERATE = auto()
    """Standard web application page."""

    COMPLEX = auto()
    """Many nested components, rich interactivity."""

    HIGHLY_COMPLEX = auto()
    """SPA with dynamic content, deep nesting."""


class ComponentType(StrEnum):
    """Types of UI components."""

    FORM = "form"
    TABLE = "table"
    MODAL = "modal"
    NAVIGATION = "navigation"
    CARD = "card"
    CAROUSEL = "carousel"
    ACCORDION = "accordion"
    TABS = "tabs"
    DROPDOWN = "dropdown"
    SIDEBAR = "sidebar"
    HEADER = "header"
    FOOTER = "footer"
    SEARCH = "search"
    PAGINATION = "pagination"
    BREADCRUMB = "breadcrumb"
    ALERT = "alert"
    TOAST = "toast"
    TOOLTIP = "tooltip"
    MENU = "menu"
    LIST = "list"


class InteractionType(StrEnum):
    """Types of element interactions."""

    CLICK = "click"
    INPUT = "input"
    SELECT = "select"
    HOVER = "hover"
    DRAG = "drag"
    SCROLL = "scroll"
    FOCUS = "focus"
    SUBMIT = "submit"
    TOGGLE = "toggle"
    UPLOAD = "upload"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Element bounding box."""

    x: float
    y: float
    width: float
    height: float

    @property
    def center_x(self) -> float:
        """Get center X coordinate."""
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        """Get center Y coordinate."""
        return self.y + self.height / 2

    @property
    def area(self) -> float:
        """Get area in pixels squared."""
        return self.width * self.height


@dataclass
class InteractiveElement:
    """Information about an interactive element."""

    tag_name: str
    element_type: str
    selector: str
    semantic_selector: str
    interactions: list[InteractionType]
    text_content: str | None = None
    placeholder: str | None = None
    name: str | None = None
    element_id: str | None = None
    aria_label: str | None = None
    aria_role: str | None = None
    href: str | None = None
    value: str | None = None
    is_required: bool = False
    is_disabled: bool = False
    is_visible: bool = True
    is_in_viewport: bool = True
    bounding_box: BoundingBox | None = None
    parent_component: str | None = None
    data_attributes: dict[str, str] = field(default_factory=dict)
    computed_styles: dict[str, str] = field(default_factory=dict)
    event_listeners: list[str] = field(default_factory=list)
    validation_attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ComponentInfo:
    """Information about a detected UI component."""

    component_type: ComponentType
    selector: str
    bounding_box: BoundingBox | None = None
    children_count: int = 0
    interactive_elements: list[InteractiveElement] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class DOMAnalysis:
    """Complete DOM analysis result."""

    total_elements: int
    max_depth: int
    average_depth: float
    interactive_count: int
    form_count: int
    link_count: int
    image_count: int
    script_count: int
    iframe_count: int
    shadow_dom_count: int
    custom_elements_count: int
    complexity_score: float
    complexity: PageComplexity
    dom_hash: str
    structure_signature: str


@dataclass
class FrameInfo:
    """Information about an iframe or frame."""

    frame_id: str
    url: str
    name: str | None
    is_same_origin: bool
    bounding_box: BoundingBox | None
    elements_count: int


@dataclass
class PageAnalysisResult:
    """Complete page analysis result."""

    url: str
    title: str
    dom_analysis: DOMAnalysis
    components: list[ComponentInfo]
    interactive_elements: list[InteractiveElement]
    frames: list[FrameInfo]
    is_spa: bool
    spa_framework: str | None
    has_shadow_dom: bool
    page_load_time_ms: float
    dynamic_content_regions: list[str]
    meta_info: dict[str, str]


class PageAnalyzer:
    """
    Deep page analyzer for comprehensive DOM and component analysis.

    Provides:
    - DOM structure analysis with complexity metrics
    - Component detection (forms, tables, modals, etc.)
    - Interactive element cataloging
    - Shadow DOM and iframe handling
    - SPA detection and framework identification
    """

    # SPA framework detection patterns
    SPA_INDICATORS: dict[str, list[str]] = {
        "react": ["__REACT_DEVTOOLS_GLOBAL_HOOK__", "_reactRootContainer", "data-reactroot"],
        "vue": ["__VUE__", "__vue__", "data-v-"],
        "angular": ["ng-version", "ng-app", "_nghost", "_ngcontent"],
        "svelte": ["__svelte"],
        "next": ["__NEXT_DATA__", "_next"],
        "nuxt": ["__NUXT__", "_nuxt"],
        "ember": ["EmberENV", "data-ember-action"],
        "backbone": ["Backbone"],
    }

    # Component detection selectors and patterns
    COMPONENT_PATTERNS: dict[ComponentType, dict[str, Any]] = {
        ComponentType.FORM: {
            "selectors": ["form", "[role='form']"],
            "indicators": ["action", "method", "novalidate"],
        },
        ComponentType.TABLE: {
            "selectors": ["table", "[role='grid']", "[role='table']"],
            "indicators": ["thead", "tbody", "tr", "td", "th"],
        },
        ComponentType.MODAL: {
            "selectors": [
                "[role='dialog']",
                "[role='alertdialog']",
                ".modal",
                "[data-modal]",
                "[aria-modal='true']",
            ],
            "indicators": ["aria-modal", "aria-hidden"],
        },
        ComponentType.NAVIGATION: {
            "selectors": ["nav", "[role='navigation']", ".navbar", ".nav"],
            "indicators": ["aria-label", "aria-labelledby"],
        },
        ComponentType.CARD: {
            "selectors": [".card", "[data-card]", "article"],
            "indicators": ["card-body", "card-header", "card-footer"],
        },
        ComponentType.TABS: {
            "selectors": ["[role='tablist']", ".tabs", ".tab-content"],
            "indicators": ["role='tab'", "aria-selected", "aria-controls"],
        },
        ComponentType.ACCORDION: {
            "selectors": [".accordion", "[data-accordion]"],
            "indicators": ["aria-expanded", "aria-controls", "collapse"],
        },
        ComponentType.DROPDOWN: {
            "selectors": ["[role='listbox']", "[role='menu']", ".dropdown"],
            "indicators": ["aria-expanded", "aria-haspopup"],
        },
        ComponentType.HEADER: {
            "selectors": ["header", "[role='banner']", ".header"],
            "indicators": [],
        },
        ComponentType.FOOTER: {
            "selectors": ["footer", "[role='contentinfo']", ".footer"],
            "indicators": [],
        },
        ComponentType.SIDEBAR: {
            "selectors": ["aside", "[role='complementary']", ".sidebar"],
            "indicators": [],
        },
        ComponentType.SEARCH: {
            "selectors": ["[role='search']", "[type='search']", ".search"],
            "indicators": ["search", "query", "q"],
        },
        ComponentType.PAGINATION: {
            "selectors": [".pagination", "[role='navigation'][aria-label*='page']"],
            "indicators": ["page", "prev", "next"],
        },
        ComponentType.BREADCRUMB: {
            "selectors": [".breadcrumb", "[aria-label='breadcrumb']", "nav[aria-label*='bread']"],
            "indicators": [],
        },
        ComponentType.ALERT: {
            "selectors": ["[role='alert']", ".alert", "[role='status']"],
            "indicators": ["aria-live"],
        },
        ComponentType.CAROUSEL: {
            "selectors": [".carousel", ".slider", "[role='region'][aria-roledescription='carousel']"],
            "indicators": ["slide", "carousel-item"],
        },
    }

    def __init__(self, config: AnalyzerConfig | None = None) -> None:
        self.config = config or AnalyzerConfig()
        self._log = logger.bind(component="page_analyzer")

    async def analyze(self, page: BrowserContext) -> PageAnalysisResult:
        """
        Perform comprehensive page analysis.

        Args:
            page: Browser context with loaded page

        Returns:
            Complete page analysis result
        """
        url = page.get_current_url()
        title = page.get_title() or "Untitled"

        self._log.info("Starting page analysis", url=url)

        # Perform analyses in parallel where possible
        dom_analysis = await self._analyze_dom(page)
        components = await self._detect_components(page)
        interactive_elements = await self._catalog_interactive_elements(page)
        frames = await self._analyze_frames(page)
        spa_info = await self._detect_spa(page)
        meta_info = await self._extract_meta_info(page)
        dynamic_regions = await self._detect_dynamic_regions(page)

        result = PageAnalysisResult(
            url=url,
            title=title,
            dom_analysis=dom_analysis,
            components=components,
            interactive_elements=interactive_elements,
            frames=frames,
            is_spa=spa_info["is_spa"],
            spa_framework=spa_info["framework"],
            has_shadow_dom=dom_analysis.shadow_dom_count > 0,
            page_load_time_ms=spa_info.get("load_time", 0),
            dynamic_content_regions=dynamic_regions,
            meta_info=meta_info,
        )

        self._log.info(
            "Page analysis complete",
            url=url,
            complexity=dom_analysis.complexity,
            components=len(components),
            interactive_elements=len(interactive_elements),
        )

        return result

    async def _analyze_dom(self, page: BrowserContext) -> DOMAnalysis:
        """Analyze DOM structure and compute complexity metrics."""
        script = """
        (() => {
            const analysis = {
                totalElements: 0,
                maxDepth: 0,
                depthSum: 0,
                interactiveCount: 0,
                formCount: 0,
                linkCount: 0,
                imageCount: 0,
                scriptCount: 0,
                iframeCount: 0,
                shadowDomCount: 0,
                customElementsCount: 0,
                structure: []
            };

            const interactiveTags = new Set([
                'button', 'input', 'select', 'textarea', 'a', 'details', 'summary'
            ]);

            const interactiveRoles = new Set([
                'button', 'link', 'textbox', 'checkbox', 'radio', 'combobox',
                'listbox', 'menu', 'menuitem', 'tab', 'slider', 'spinbutton'
            ]);

            function analyzeNode(node, depth = 0) {
                if (node.nodeType !== Node.ELEMENT_NODE) return;

                analysis.totalElements++;
                analysis.maxDepth = Math.max(analysis.maxDepth, depth);
                analysis.depthSum += depth;

                const tagName = node.tagName.toLowerCase();
                const role = node.getAttribute('role');

                // Track structure signature
                if (depth <= 3) {
                    analysis.structure.push(tagName);
                }

                // Count specific elements
                if (interactiveTags.has(tagName) || interactiveRoles.has(role)) {
                    analysis.interactiveCount++;
                }
                if (tagName === 'form') analysis.formCount++;
                if (tagName === 'a') analysis.linkCount++;
                if (tagName === 'img') analysis.imageCount++;
                if (tagName === 'script') analysis.scriptCount++;
                if (tagName === 'iframe') analysis.iframeCount++;

                // Check for shadow DOM
                if (node.shadowRoot) {
                    analysis.shadowDomCount++;
                    Array.from(node.shadowRoot.children).forEach(child => {
                        analyzeNode(child, depth + 1);
                    });
                }

                // Check for custom elements
                if (tagName.includes('-')) {
                    analysis.customElementsCount++;
                }

                // Recurse to children
                Array.from(node.children).forEach(child => {
                    analyzeNode(child, depth + 1);
                });
            }

            analyzeNode(document.documentElement);

            return {
                ...analysis,
                averageDepth: analysis.totalElements > 0
                    ? analysis.depthSum / analysis.totalElements
                    : 0,
                structureSignature: analysis.structure.slice(0, 50).join(',')
            };
        })()
        """

        result = page.expression(script)

        # Calculate complexity score (0-1)
        complexity_score = self._calculate_complexity_score(result)
        complexity = self._classify_complexity(complexity_score)

        # Generate DOM hash for change detection
        dom_hash = hashlib.md5(result["structureSignature"].encode()).hexdigest()[:16]

        return DOMAnalysis(
            total_elements=result["totalElements"],
            max_depth=result["maxDepth"],
            average_depth=result["averageDepth"],
            interactive_count=result["interactiveCount"],
            form_count=result["formCount"],
            link_count=result["linkCount"],
            image_count=result["imageCount"],
            script_count=result["scriptCount"],
            iframe_count=result["iframeCount"],
            shadow_dom_count=result["shadowDomCount"],
            custom_elements_count=result["customElementsCount"],
            complexity_score=complexity_score,
            complexity=complexity,
            dom_hash=dom_hash,
            structure_signature=result["structureSignature"],
        )

    def _calculate_complexity_score(self, analysis: dict[str, Any]) -> float:
        """Calculate normalized complexity score from DOM analysis."""
        # Weighted factors
        weights = {
            "elements": 0.2,
            "depth": 0.2,
            "interactive": 0.2,
            "forms": 0.1,
            "shadow_dom": 0.15,
            "custom_elements": 0.15,
        }

        # Normalize each factor (0-1)
        element_score = min(analysis["totalElements"] / 500, 1.0)
        depth_score = min(analysis["maxDepth"] / 15, 1.0)
        interactive_score = min(analysis["interactiveCount"] / 100, 1.0)
        form_score = min(analysis["formCount"] / 5, 1.0)
        shadow_score = min(analysis["shadowDomCount"] / 10, 1.0)
        custom_score = min(analysis["customElementsCount"] / 20, 1.0)

        complexity = (
            weights["elements"] * element_score
            + weights["depth"] * depth_score
            + weights["interactive"] * interactive_score
            + weights["forms"] * form_score
            + weights["shadow_dom"] * shadow_score
            + weights["custom_elements"] * custom_score
        )

        return round(complexity, 3)

    def _classify_complexity(self, score: float) -> PageComplexity:
        """Classify page complexity from score."""
        if score < 0.25:
            return PageComplexity.SIMPLE
        if score < 0.5:
            return PageComplexity.MODERATE
        if score < 0.75:
            return PageComplexity.COMPLEX
        return PageComplexity.HIGHLY_COMPLEX

    async def _detect_components(self, page: BrowserContext) -> list[ComponentInfo]:
        """Detect UI components on the page."""
        components: list[ComponentInfo] = []

        for component_type, config in self.COMPONENT_PATTERNS.items():
            for selector in config["selectors"]:
                try:
                    detected = await self._find_components(
                        page, selector, component_type, config.get("indicators", [])
                    )
                    components.extend(detected)
                except Exception as e:
                    self._log.debug(
                        "Component detection failed",
                        selector=selector,
                        error=str(e),
                    )

        # Remove duplicates based on selector
        seen_selectors: set[str] = set()
        unique_components: list[ComponentInfo] = []
        for comp in components:
            if comp.selector not in seen_selectors:
                seen_selectors.add(comp.selector)
                unique_components.append(comp)

        return unique_components

    async def _find_components(
        self,
        page: BrowserContext,
        selector: str,
        component_type: ComponentType,
        indicators: list[str],
    ) -> list[ComponentInfo]:
        """Find components matching selector."""
        script = f"""
        (() => {{
            const elements = document.querySelectorAll("{selector}");
            const results = [];

            for (const el of elements) {{
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                // Skip hidden elements
                if (style.display === 'none' || style.visibility === 'hidden') {{
                    continue;
                }}

                // Count interactive children
                const interactiveChildren = el.querySelectorAll(
                    'button, input, select, textarea, a, [role="button"], [role="link"]'
                ).length;

                // Generate unique selector
                let uniqueSelector = '';
                if (el.id) {{
                    uniqueSelector = '#' + el.id;
                }} else {{
                    // Build path selector
                    const path = [];
                    let current = el;
                    while (current && current !== document.body) {{
                        let part = current.tagName.toLowerCase();
                        if (current.id) {{
                            part = '#' + current.id;
                            path.unshift(part);
                            break;
                        }}
                        if (current.className && typeof current.className === 'string') {{
                            const classes = current.className.trim().split(/\\s+/)
                                .filter(c => !c.startsWith('ng-') && !c.startsWith('v-'))
                                .slice(0, 2);
                            if (classes.length) {{
                                part += '.' + classes.join('.');
                            }}
                        }}
                        path.unshift(part);
                        current = current.parentElement;
                    }}
                    uniqueSelector = path.join(' > ');
                }}

                results.push({{
                    selector: uniqueSelector,
                    boundingBox: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }},
                    childrenCount: el.children.length,
                    interactiveCount: interactiveChildren,
                    attributes: {{
                        id: el.id || null,
                        className: el.className || null,
                        ariaLabel: el.getAttribute('aria-label'),
                        role: el.getAttribute('role')
                    }}
                }});
            }}

            return results;
        }})()
        """

        raw_results = page.expression(script)
        components: list[ComponentInfo] = []

        for raw in raw_results:
            bbox = raw.get("boundingBox")
            bounding_box = None
            if bbox and bbox.get("width", 0) > 0:
                bounding_box = BoundingBox(
                    x=bbox["x"],
                    y=bbox["y"],
                    width=bbox["width"],
                    height=bbox["height"],
                )

            components.append(
                ComponentInfo(
                    component_type=component_type,
                    selector=raw["selector"],
                    bounding_box=bounding_box,
                    children_count=raw["childrenCount"],
                    attributes=raw["attributes"],
                    confidence=0.8 if indicators else 0.6,
                )
            )

        return components

    async def _catalog_interactive_elements(
        self, page: BrowserContext
    ) -> list[InteractiveElement]:
        """Catalog all interactive elements with context."""
        script = """
        (() => {
            const interactiveSelectors = [
                'button', 'input', 'select', 'textarea', 'a[href]',
                '[role="button"]', '[role="link"]', '[role="textbox"]',
                '[role="checkbox"]', '[role="radio"]', '[role="combobox"]',
                '[role="listbox"]', '[role="menu"]', '[role="menuitem"]',
                '[role="tab"]', '[role="slider"]', '[role="switch"]',
                '[tabindex]:not([tabindex="-1"])',
                '[onclick]', '[data-action]', '[data-click]'
            ];

            const elements = document.querySelectorAll(interactiveSelectors.join(','));
            const results = [];

            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                const isVisible = style.display !== 'none' &&
                                  style.visibility !== 'hidden' &&
                                  style.opacity !== '0' &&
                                  rect.width > 0 &&
                                  rect.height > 0;

                const isInViewport = rect.top < window.innerHeight &&
                                     rect.bottom > 0 &&
                                     rect.left < window.innerWidth &&
                                     rect.right > 0;

                // Determine interaction types
                const interactions = [];
                const tagName = el.tagName.toLowerCase();
                const inputType = el.type?.toLowerCase() || '';
                const role = el.getAttribute('role');

                if (tagName === 'button' || role === 'button' || inputType === 'button' || inputType === 'submit') {
                    interactions.push('click');
                }
                if (tagName === 'a' || role === 'link') {
                    interactions.push('click');
                }
                if (['text', 'email', 'password', 'search', 'tel', 'url', 'number'].includes(inputType)) {
                    interactions.push('input');
                    interactions.push('focus');
                }
                if (tagName === 'textarea') {
                    interactions.push('input');
                    interactions.push('focus');
                }
                if (tagName === 'select' || role === 'listbox' || role === 'combobox') {
                    interactions.push('select');
                }
                if (inputType === 'checkbox' || role === 'checkbox') {
                    interactions.push('toggle');
                }
                if (inputType === 'radio' || role === 'radio') {
                    interactions.push('click');
                }
                if (inputType === 'file') {
                    interactions.push('upload');
                }
                if (role === 'slider') {
                    interactions.push('drag');
                }

                // Collect data attributes
                const dataAttributes = {};
                for (const attr of el.attributes) {
                    if (attr.name.startsWith('data-')) {
                        dataAttributes[attr.name] = attr.value;
                    }
                }

                // Collect validation attributes
                const validationAttributes = {};
                ['required', 'minlength', 'maxlength', 'min', 'max', 'pattern', 'type'].forEach(attr => {
                    if (el.hasAttribute(attr)) {
                        validationAttributes[attr] = el.getAttribute(attr);
                    }
                });

                // Generate semantic selector
                let semanticSelector = '';
                if (el.getAttribute('aria-label')) {
                    semanticSelector = el.getAttribute('aria-label');
                } else if (el.innerText?.trim()) {
                    semanticSelector = el.innerText.trim().substring(0, 50);
                } else if (el.placeholder) {
                    semanticSelector = el.placeholder;
                } else if (el.name) {
                    semanticSelector = el.name.replace(/[_-]/g, ' ');
                } else if (el.id) {
                    semanticSelector = el.id.replace(/[_-]/g, ' ');
                }

                // Generate CSS selector
                let cssSelector = '';
                if (el.id) {
                    cssSelector = '#' + el.id;
                } else if (el.name) {
                    cssSelector = `${tagName}[name="${el.name}"]`;
                } else {
                    const path = [];
                    let current = el;
                    for (let i = 0; i < 3 && current && current !== document.body; i++) {
                        let part = current.tagName.toLowerCase();
                        if (current.id) {
                            part = '#' + current.id;
                            path.unshift(part);
                            break;
                        }
                        const idx = Array.from(current.parentNode?.children || [])
                            .filter(c => c.tagName === current.tagName)
                            .indexOf(current);
                        if (idx > 0) {
                            part += `:nth-of-type(${idx + 1})`;
                        }
                        path.unshift(part);
                        current = current.parentElement;
                    }
                    cssSelector = path.join(' > ');
                }

                // Find parent component
                let parentComponent = null;
                let parent = el.closest('form, nav, [role="dialog"], .modal, .card, table');
                if (parent) {
                    parentComponent = parent.tagName.toLowerCase();
                    if (parent.id) {
                        parentComponent += '#' + parent.id;
                    }
                }

                results.push({
                    tagName: tagName,
                    elementType: inputType || role || tagName,
                    selector: cssSelector,
                    semanticSelector: semanticSelector,
                    interactions: interactions,
                    textContent: el.innerText?.trim()?.substring(0, 100) || null,
                    placeholder: el.placeholder || null,
                    name: el.name || null,
                    elementId: el.id || null,
                    ariaLabel: el.getAttribute('aria-label'),
                    ariaRole: role,
                    href: el.href || null,
                    value: el.value || null,
                    isRequired: el.required || el.getAttribute('aria-required') === 'true',
                    isDisabled: el.disabled || el.getAttribute('aria-disabled') === 'true',
                    isVisible: isVisible,
                    isInViewport: isInViewport,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    parentComponent: parentComponent,
                    dataAttributes: dataAttributes,
                    validationAttributes: validationAttributes
                });
            }

            return results;
        })()
        """

        raw_elements = page.expression(script)
        elements: list[InteractiveElement] = []

        for raw in raw_elements:
            bbox = raw.get("boundingBox", {})
            bounding_box = None
            if bbox.get("width", 0) > 0:
                bounding_box = BoundingBox(
                    x=bbox.get("x", 0),
                    y=bbox.get("y", 0),
                    width=bbox.get("width", 0),
                    height=bbox.get("height", 0),
                )

            interactions = [InteractionType(i) for i in raw.get("interactions", []) if i in InteractionType.__members__.values()]

            elements.append(
                InteractiveElement(
                    tag_name=raw["tagName"],
                    element_type=raw["elementType"],
                    selector=raw["selector"],
                    semantic_selector=raw["semanticSelector"],
                    interactions=interactions,
                    text_content=raw.get("textContent"),
                    placeholder=raw.get("placeholder"),
                    name=raw.get("name"),
                    element_id=raw.get("elementId"),
                    aria_label=raw.get("ariaLabel"),
                    aria_role=raw.get("ariaRole"),
                    href=raw.get("href"),
                    value=raw.get("value"),
                    is_required=raw.get("isRequired", False),
                    is_disabled=raw.get("isDisabled", False),
                    is_visible=raw.get("isVisible", True),
                    is_in_viewport=raw.get("isInViewport", True),
                    bounding_box=bounding_box,
                    parent_component=raw.get("parentComponent"),
                    data_attributes=raw.get("dataAttributes", {}),
                    validation_attributes=raw.get("validationAttributes", {}),
                )
            )

        return elements

    async def _analyze_frames(self, page: BrowserContext) -> list[FrameInfo]:
        """Analyze iframes and frames."""
        current_url = page.get_current_url()
        current_origin = urlparse(current_url).netloc

        script = """
        (() => {
            const frames = document.querySelectorAll('iframe, frame');
            const results = [];

            for (const frame of frames) {
                const rect = frame.getBoundingClientRect();
                let elementsCount = 0;

                try {
                    if (frame.contentDocument) {
                        elementsCount = frame.contentDocument.querySelectorAll('*').length;
                    }
                } catch (e) {
                    // Cross-origin iframe
                }

                results.push({
                    frameId: frame.id || `frame_${results.length}`,
                    url: frame.src || '',
                    name: frame.name || null,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    },
                    elementsCount: elementsCount
                });
            }

            return results;
        })()
        """

        raw_frames = page.expression(script)
        frames: list[FrameInfo] = []

        for raw in raw_frames:
            frame_url = raw.get("url", "")
            frame_origin = urlparse(frame_url).netloc if frame_url else ""
            is_same_origin = frame_origin == current_origin or not frame_origin

            bbox = raw.get("boundingBox", {})
            bounding_box = None
            if bbox.get("width", 0) > 0:
                bounding_box = BoundingBox(
                    x=bbox.get("x", 0),
                    y=bbox.get("y", 0),
                    width=bbox.get("width", 0),
                    height=bbox.get("height", 0),
                )

            frames.append(
                FrameInfo(
                    frame_id=raw["frameId"],
                    url=frame_url,
                    name=raw.get("name"),
                    is_same_origin=is_same_origin,
                    bounding_box=bounding_box,
                    elements_count=raw.get("elementsCount", 0),
                )
            )

        return frames

    async def _detect_spa(self, page: BrowserContext) -> dict[str, Any]:
        """Detect if page is a Single Page Application and identify framework."""
        script = """
        (() => {
            const indicators = {
                react: ['__REACT_DEVTOOLS_GLOBAL_HOOK__', '_reactRootContainer'],
                vue: ['__VUE__', '__vue__'],
                angular: ['ng-version', 'getAllAngularRootElements'],
                svelte: ['__svelte'],
                next: ['__NEXT_DATA__'],
                nuxt: ['__NUXT__'],
                ember: ['EmberENV'],
            };

            const result = {
                isSPA: false,
                framework: null,
                indicators: []
            };

            // Check window properties
            for (const [framework, props] of Object.entries(indicators)) {
                for (const prop of props) {
                    if (window[prop] !== undefined || document.querySelector(`[${prop}]`)) {
                        result.isSPA = true;
                        result.framework = framework;
                        result.indicators.push(prop);
                        break;
                    }
                }
                if (result.framework) break;
            }

            // Check for common SPA patterns
            if (!result.isSPA) {
                // Check for hash-based routing
                if (window.location.hash && window.location.hash.length > 1) {
                    result.indicators.push('hash_routing');
                }

                // Check for history API usage (common in SPAs)
                if (document.querySelectorAll('[data-router-link], [routerlink]').length > 0) {
                    result.isSPA = true;
                    result.indicators.push('router_links');
                }

                // Check for single root element pattern
                const rootChildren = document.body.children;
                if (rootChildren.length <= 2 && document.getElementById('root') || document.getElementById('app')) {
                    result.isSPA = true;
                    result.indicators.push('single_root');
                }
            }

            // Measure load time
            result.loadTime = performance.timing ?
                performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart : 0;

            return result;
        })()
        """

        result = page.expression(script)

        return {
            "is_spa": result.get("isSPA", False),
            "framework": result.get("framework"),
            "indicators": result.get("indicators", []),
            "load_time": result.get("loadTime", 0),
        }

    async def _extract_meta_info(self, page: BrowserContext) -> dict[str, str]:
        """Extract page meta information."""
        script = """
        (() => {
            const meta = {};

            // Title
            meta.title = document.title || '';

            // Meta tags
            const metaTags = document.querySelectorAll('meta[name], meta[property]');
            for (const tag of metaTags) {
                const name = tag.getAttribute('name') || tag.getAttribute('property');
                const content = tag.getAttribute('content');
                if (name && content) {
                    meta[name] = content;
                }
            }

            // Canonical URL
            const canonical = document.querySelector('link[rel="canonical"]');
            if (canonical) {
                meta.canonical = canonical.href;
            }

            // Language
            meta.lang = document.documentElement.lang || '';

            // Viewport
            const viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                meta.viewport = viewport.getAttribute('content') || '';
            }

            return meta;
        })()
        """

        return page.expression(script)

    async def _detect_dynamic_regions(self, page: BrowserContext) -> list[str]:
        """Detect regions with dynamic content (AJAX, WebSocket updates)."""
        script = """
        (() => {
            const dynamicRegions = [];

            // Look for common dynamic content patterns
            const patterns = [
                '[data-live]',
                '[data-realtime]',
                '[data-socket]',
                '[data-poll]',
                '[aria-live]',
                '.live-region',
                '[data-refresh]',
                '.dynamic-content',
                '[data-async]'
            ];

            for (const pattern of patterns) {
                const elements = document.querySelectorAll(pattern);
                for (const el of elements) {
                    let selector = '';
                    if (el.id) {
                        selector = '#' + el.id;
                    } else if (el.className) {
                        selector = '.' + el.className.split(' ')[0];
                    } else {
                        selector = el.tagName.toLowerCase();
                    }
                    if (!dynamicRegions.includes(selector)) {
                        dynamicRegions.push(selector);
                    }
                }
            }

            return dynamicRegions;
        })()
        """

        return page.expression(script)
