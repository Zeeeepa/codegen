"""
Auto Test Builder for generating YAML test specifications from page analysis.

Provides:
- Automatic page crawling with depth control
- Login form detection and authentication
- Element discovery with semantic descriptions
- YAML test generation compatible with TestRunner

SDK v2 Notes:
- Uses OwlBrowser instead of Browser
- All browser operations are async and require context_id
- build() method is now async
"""

from __future__ import annotations

import asyncio
import contextlib
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import structlog
import yaml

if TYPE_CHECKING:
    from owl_browser import OwlBrowser

logger = structlog.get_logger(__name__)


class ElementType(StrEnum):
    """Types of interactable elements."""

    BUTTON = "button"
    LINK = "link"
    INPUT_TEXT = "input_text"
    INPUT_EMAIL = "input_email"
    INPUT_PASSWORD = "input_password"
    INPUT_NUMBER = "input_number"
    INPUT_SEARCH = "input_search"
    INPUT_TEL = "input_tel"
    INPUT_URL = "input_url"
    INPUT_DATE = "input_date"
    INPUT_CHECKBOX = "checkbox"
    INPUT_RADIO = "radio"
    INPUT_FILE = "file_upload"
    SELECT = "select"
    TEXTAREA = "textarea"
    FORM = "form"
    NAVIGATION = "navigation"


@dataclass
class ElementInfo:
    """Information about a discovered element."""

    element_type: ElementType
    selector: str
    semantic_description: str
    text_content: str | None = None
    placeholder: str | None = None
    name: str | None = None
    id: str | None = None
    aria_label: str | None = None
    href: str | None = None
    form_id: str | None = None
    is_required: bool = False
    is_visible: bool = True
    bounding_box: dict[str, float] | None = None


@dataclass
class PageAnalysis:
    """Complete analysis of a page."""

    url: str
    title: str
    timestamp: datetime
    elements: list[ElementInfo] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    navigation_links: list[ElementInfo] = field(default_factory=list)
    has_login_form: bool = False
    login_form_info: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)


@dataclass
class BuilderConfig:
    """Configuration for the Auto Test Builder."""

    url: str
    username: str | None = None
    password: str | None = None
    depth: int = 1
    max_pages: int = 10
    include_hidden: bool = False
    timeout_ms: int = 10000  # Navigation timeout - 10 seconds is sufficient for most pages
    wait_after_navigation_ms: int = 0  # Deprecated - network idle is sufficient
    same_domain_only: bool = True
    exclude_patterns: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=list)


class AutoTestBuilder:
    """
    Automatically builds YAML test specifications from web pages.

    Features:
    - Crawls pages to specified depth
    - Detects and handles login forms
    - Catalogs all interactable elements
    - Generates semantic selectors for owl-browser
    - Produces complete, runnable YAML test specs
    """

    # Login form detection patterns
    LOGIN_INDICATORS: frozenset[str] = frozenset({
        "login",
        "signin",
        "sign-in",
        "sign_in",
        "log-in",
        "log_in",
        "authenticate",
        "auth",
    })

    USERNAME_INDICATORS: frozenset[str] = frozenset({
        "username",
        "user",
        "email",
        "login",
        "userid",
        "user_id",
        "user-id",
        "account",
    })

    PASSWORD_INDICATORS: frozenset[str] = frozenset({
        "password",
        "passwd",
        "pass",
        "pwd",
        "secret",
    })

    def __init__(
        self,
        browser: OwlBrowser,
        config: BuilderConfig,
    ) -> None:
        self._browser = browser
        self._config = config
        self._log = logger.bind(component="auto_test_builder")
        self._visited_urls: set[str] = set()
        self._page_analyses: list[PageAnalysis] = []
        self._base_domain: str = urlparse(config.url).netloc

    async def build(self) -> str:
        """
        Build a complete YAML test specification.

        SDK v2 Notes:
            - Async method
            - Creates and manages its own context
            - Uses navigate instead of goto

        Returns:
            YAML string containing the test specification
        """
        self._log.info(
            "Starting test build",
            url=self._config.url,
            depth=self._config.depth,
        )

        # Create a new context for the build
        ctx = await self._browser.create_context()
        context_id = ctx["context_id"]

        try:
            # Navigate to initial URL
            await self._navigate_with_wait(context_id, self._config.url)

            # Handle authentication if credentials provided
            if self._config.username and self._config.password:
                await self._handle_authentication(context_id)

            # Crawl and analyze pages
            await self._crawl_pages(context_id, self._config.url, depth=0)

            # Generate YAML spec
            yaml_content = self._generate_yaml_spec()

            self._log.info(
                "Test build complete",
                pages_analyzed=len(self._page_analyses),
                total_elements=sum(len(p.elements) for p in self._page_analyses),
            )

            return yaml_content

        finally:
            await self._browser.close_context(context_id=context_id)

    async def _navigate_with_wait(self, context_id: str, url: str) -> None:
        """Navigate to URL and wait for stability."""
        # Use domcontentloaded instead of load for faster navigation
        # domcontentloaded fires when HTML is parsed, before images/styles finish
        await self._browser.navigate(
            context_id=context_id,
            url=url,
            wait_until="domcontentloaded",
            timeout=self._config.timeout_ms,
        )
        # Short network idle wait to ensure key resources are loaded
        with contextlib.suppress(Exception):
            await self._browser.wait_for_network_idle(
                context_id=context_id,
                idle_time=200,
                timeout=2000,
            )

    async def _handle_authentication(self, context_id: str) -> bool:
        """
        Detect and fill login form if present.

        Returns:
            True if login was attempted, False otherwise
        """
        self._log.info("Checking for login form")

        analysis = await self._analyze_page(context_id)

        if not analysis.has_login_form or not analysis.login_form_info:
            self._log.info("No login form detected")
            return False

        login_info = analysis.login_form_info
        username_selector = login_info.get("username_selector")
        password_selector = login_info.get("password_selector")
        submit_selector = login_info.get("submit_selector")

        if not username_selector or not password_selector:
            self._log.warning("Login form incomplete - missing username or password field")
            return False

        try:
            # Fill username
            await self._browser.type(
                context_id=context_id,
                selector=username_selector,
                text=self._config.username or "",
            )
            await asyncio.sleep(0.2)

            # Fill password
            await self._browser.type(
                context_id=context_id,
                selector=password_selector,
                text=self._config.password or "",
            )
            await asyncio.sleep(0.2)

            # Submit form
            if submit_selector:
                await self._browser.click(context_id=context_id, selector=submit_selector)
            else:
                await self._browser.press_key(context_id=context_id, key="Enter")

            # Wait for navigation/response
            await asyncio.sleep(2)
            with contextlib.suppress(Exception):
                await self._browser.wait_for_network_idle(
                    context_id=context_id,
                    idle_time=500,
                    timeout=5000,
                )

            page_info = await self._browser.get_page_info(context_id=context_id)
            current_url = page_info.get("url") if isinstance(page_info, dict) else "unknown"
            self._log.info("Login form submitted", url=current_url)
            return True

        except Exception as e:
            self._log.error("Failed to complete login", error=str(e))
            return False

    async def _crawl_pages(
        self,
        context_id: str,
        url: str,
        depth: int,
    ) -> None:
        """Recursively crawl and analyze pages."""
        # Normalize URL
        normalized_url = self._normalize_url(url)

        # Check if already visited or depth exceeded
        if normalized_url in self._visited_urls:
            return
        if depth > self._config.depth:
            return
        if len(self._visited_urls) >= self._config.max_pages:
            return

        # Check domain constraint
        if self._config.same_domain_only:
            url_domain = urlparse(url).netloc
            if url_domain != self._base_domain:
                return

        # Check exclude/include patterns
        if not self._should_crawl_url(url):
            return

        self._visited_urls.add(normalized_url)

        # Navigate if not already on this page
        page_info = await self._browser.get_page_info(context_id=context_id)
        current_url = page_info.get("url") if isinstance(page_info, dict) else ""
        if self._normalize_url(current_url) != normalized_url:
            try:
                await self._navigate_with_wait(context_id, url)
            except Exception as e:
                self._log.warning("Failed to navigate", url=url, error=str(e))
                return

        # Analyze current page
        analysis = await self._analyze_page(context_id)
        self._page_analyses.append(analysis)

        self._log.info(
            "Analyzed page",
            url=url,
            depth=depth,
            elements=len(analysis.elements),
            links=len(analysis.navigation_links),
        )

        # Crawl child links if depth allows
        if depth < self._config.depth:
            child_urls = [
                link.href
                for link in analysis.navigation_links
                if link.href and self._is_valid_crawl_target(link.href)
            ]

            # Process all valid child URLs (coverage is controlled by max_pages)
            for child_url in child_urls:
                # Early exit if we've hit max_pages
                if len(self._visited_urls) >= self._config.max_pages:
                    break
                absolute_url = urljoin(url, child_url)
                await self._crawl_pages(context_id, absolute_url, depth + 1)

    async def _analyze_page(self, context_id: str) -> PageAnalysis:
        """Perform complete analysis of current page."""
        page_info = await self._browser.get_page_info(context_id=context_id)
        url = page_info.get("url", "") if isinstance(page_info, dict) else ""
        title = page_info.get("title", "Untitled") if isinstance(page_info, dict) else "Untitled"

        analysis = PageAnalysis(
            url=url,
            title=title,
            timestamp=datetime.now(UTC),
        )

        try:
            # Discover all elements
            analysis.elements = await self._discover_elements(context_id)

            # Separate navigation links
            analysis.navigation_links = [
                el for el in analysis.elements
                if el.element_type == ElementType.LINK
            ]

            # Detect forms
            analysis.forms = await self._discover_forms(context_id, analysis.elements)

            # Check for login form
            login_info = await self._detect_login_form(context_id, analysis)
            if login_info:
                analysis.has_login_form = True
                analysis.login_form_info = login_info

        except Exception as e:
            analysis.errors.append(f"Analysis error: {e}")
            self._log.error("Page analysis failed", url=url, error=str(e))

        return analysis

    async def _discover_elements(self, context_id: str) -> list[ElementInfo]:
        """Discover all interactable elements on the page using a single batched query."""
        # PERFORMANCE: Single JavaScript call to get ALL elements at once
        # This replaces 18+ separate queries with ONE round-trip
        script = """
        (() => {
            const results = [];
            const seen = new Set();

            // Type mapping for inputs
            const inputTypeMap = {
                'text': 'input_text',
                'email': 'input_email',
                'password': 'input_password',
                'number': 'input_number',
                'search': 'input_search',
                'tel': 'input_tel',
                'url': 'input_url',
                'date': 'input_date',
                'checkbox': 'checkbox',
                'radio': 'radio',
                'file': 'file_upload',
                'button': 'button',
                'submit': 'button',
            };

            function processElement(el, elementType) {
                // Generate unique key to avoid duplicates
                const key = el.outerHTML.substring(0, 200);
                if (seen.has(key)) return null;
                seen.add(key);

                const style = window.getComputedStyle(el);
                const isVisible = style.display !== 'none' &&
                                  style.visibility !== 'hidden' &&
                                  el.offsetWidth > 0 &&
                                  el.offsetHeight > 0;

                const rect = el.getBoundingClientRect();

                return {
                    elementType: elementType,
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    text: el.innerText?.trim()?.substring(0, 100) || null,
                    value: el.value || null,
                    placeholder: el.placeholder || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    title: el.title || null,
                    href: el.href || null,
                    required: el.required || false,
                    isVisible: isVisible,
                    className: el.className || null,
                    formId: el.form?.id || null,
                    boundingBox: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                };
            }

            // Process buttons
            document.querySelectorAll('button, [role="button"]').forEach(el => {
                const r = processElement(el, 'button');
                if (r) results.push(r);
            });

            // Process links
            document.querySelectorAll('a[href]').forEach(el => {
                const r = processElement(el, 'link');
                if (r) results.push(r);
            });

            // Process all inputs
            document.querySelectorAll('input').forEach(el => {
                const inputType = (el.type || 'text').toLowerCase();
                const elementType = inputTypeMap[inputType] || 'input_text';
                const r = processElement(el, elementType);
                if (r) results.push(r);
            });

            // Process selects
            document.querySelectorAll('select').forEach(el => {
                const r = processElement(el, 'select');
                if (r) results.push(r);
            });

            // Process textareas
            document.querySelectorAll('textarea').forEach(el => {
                const r = processElement(el, 'textarea');
                if (r) results.push(r);
            });

            return results;
        })()
        """

        try:
            # SDK v2: use evaluate for JavaScript execution
            result = await self._browser.evaluate(context_id=context_id, expression=script)
            raw_elements = result.get("result") if isinstance(result, dict) else result

            if not raw_elements or not isinstance(raw_elements, list):
                self._log.debug("No elements returned from batched query")
                return []

            elements: list[ElementInfo] = []
            for raw in raw_elements:
                if not self._config.include_hidden and not raw.get("isVisible"):
                    continue

                # Map string type to ElementType enum
                element_type_str = raw.get("elementType", "button")
                element_type = self._map_element_type(element_type_str)

                semantic_desc = self._generate_semantic_description(raw, element_type)
                element_selector = self._generate_semantic_selector(raw, element_type)

                elements.append(ElementInfo(
                    element_type=element_type,
                    selector=element_selector,
                    semantic_description=semantic_desc,
                    text_content=raw.get("text"),
                    placeholder=raw.get("placeholder"),
                    name=raw.get("name"),
                    id=raw.get("id"),
                    aria_label=raw.get("ariaLabel"),
                    href=raw.get("href"),
                    form_id=raw.get("formId"),
                    is_required=raw.get("required", False),
                    is_visible=raw.get("isVisible", True),
                    bounding_box=raw.get("boundingBox"),
                ))

            return elements

        except Exception as e:
            self._log.debug("Batched element query failed", error=str(e))
            return []

    def _map_element_type(self, type_str: str) -> ElementType:
        """Map string type to ElementType enum."""
        type_mapping = {
            "button": ElementType.BUTTON,
            "link": ElementType.LINK,
            "input_text": ElementType.INPUT_TEXT,
            "input_email": ElementType.INPUT_EMAIL,
            "input_password": ElementType.INPUT_PASSWORD,
            "input_number": ElementType.INPUT_NUMBER,
            "input_search": ElementType.INPUT_SEARCH,
            "input_tel": ElementType.INPUT_TEL,
            "input_url": ElementType.INPUT_URL,
            "input_date": ElementType.INPUT_DATE,
            "checkbox": ElementType.INPUT_CHECKBOX,
            "radio": ElementType.INPUT_RADIO,
            "file_upload": ElementType.INPUT_FILE,
            "select": ElementType.SELECT,
            "textarea": ElementType.TEXTAREA,
        }
        return type_mapping.get(type_str, ElementType.BUTTON)

    async def _query_elements(
        self,
        context_id: str,
        selector: str,
        element_type: ElementType,
    ) -> list[ElementInfo]:
        """Query and extract information about elements matching selector."""
        elements: list[ElementInfo] = []

        # JavaScript to extract element info
        script = f"""
        (() => {{
            const elements = document.querySelectorAll("{selector}");
            const results = [];

            for (const el of elements) {{
                // Skip hidden elements unless configured otherwise
                const style = window.getComputedStyle(el);
                const isVisible = style.display !== 'none' &&
                                  style.visibility !== 'hidden' &&
                                  el.offsetWidth > 0 &&
                                  el.offsetHeight > 0;

                const rect = el.getBoundingClientRect();

                results.push({{
                    tagName: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    text: el.innerText?.trim()?.substring(0, 100) || null,
                    value: el.value || null,
                    placeholder: el.placeholder || null,
                    ariaLabel: el.getAttribute('aria-label') || null,
                    title: el.title || null,
                    href: el.href || null,
                    required: el.required || false,
                    isVisible: isVisible,
                    className: el.className || null,
                    formId: el.form?.id || null,
                    boundingBox: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }}
                }});
            }}

            return results;
        }})()
        """

        try:
            # SDK v2: use evaluate for JavaScript execution
            result = await self._browser.evaluate(context_id=context_id, expression=script)
            raw_elements = result.get("result") if isinstance(result, dict) else result

            # Handle case where result might be None or not a list
            if not raw_elements or not isinstance(raw_elements, list):
                self._log.debug("No elements returned from query", selector=selector)
                return elements

            for raw in raw_elements:
                if not self._config.include_hidden and not raw.get("isVisible"):
                    continue

                semantic_desc = self._generate_semantic_description(raw, element_type)
                element_selector = self._generate_semantic_selector(raw, element_type)

                elements.append(ElementInfo(
                    element_type=element_type,
                    selector=element_selector,
                    semantic_description=semantic_desc,
                    text_content=raw.get("text"),
                    placeholder=raw.get("placeholder"),
                    name=raw.get("name"),
                    id=raw.get("id"),
                    aria_label=raw.get("ariaLabel"),
                    href=raw.get("href"),
                    form_id=raw.get("formId"),
                    is_required=raw.get("required", False),
                    is_visible=raw.get("isVisible", True),
                    bounding_box=raw.get("boundingBox"),
                ))

        except Exception as e:
            self._log.debug("Element query failed", selector=selector, error=str(e))

        return elements

    def _generate_semantic_description(
        self,
        raw: dict[str, Any],
        element_type: ElementType,
    ) -> str:
        """Generate a human-readable semantic description for an element."""
        parts: list[str] = []

        # Primary identifier
        if raw.get("ariaLabel"):
            parts.append(raw["ariaLabel"])
        elif raw.get("text"):
            parts.append(raw["text"][:50])
        elif raw.get("placeholder"):
            parts.append(f"{raw['placeholder']} input")
        elif raw.get("name"):
            # Convert name to readable format
            name = raw["name"].replace("_", " ").replace("-", " ")
            parts.append(f"{name} field")
        elif raw.get("id"):
            # Convert id to readable format
            id_text = raw["id"].replace("_", " ").replace("-", " ")
            parts.append(id_text)
        elif raw.get("title"):
            parts.append(raw["title"])

        # Add type context if not obvious
        if element_type == ElementType.BUTTON and not parts:
            parts.append("button")
        elif element_type == ElementType.LINK:
            if not parts:
                parts.append("link")
        elif (
            element_type in (ElementType.INPUT_TEXT, ElementType.INPUT_EMAIL,
                            ElementType.INPUT_PASSWORD, ElementType.TEXTAREA)
            and not parts
        ):
            parts.append(f"{element_type.value.replace('_', ' ')} field")

        return " ".join(parts) if parts else f"unnamed {element_type.value}"

    def _generate_semantic_selector(
        self,
        raw: dict[str, Any],
        element_type: ElementType,  # noqa: ARG002
    ) -> str:
        """
        Generate a valid CSS selector for the element.

        Priority order for selector generation:
        1. ID selector (#id) - most reliable
        2. data-testid attribute - testing best practice
        3. name attribute - useful for form elements
        4. aria-label attribute - accessible elements
        5. class-based selector with tag
        6. Tag + type/role attributes
        """
        tag = raw.get("tagName", "div")

        # 1. ID selector - most reliable and unique
        if raw.get("id"):
            return f"#{raw['id']}"

        # 2. data-testid attribute - testing best practice
        # (Would need to be added to the JS extraction)

        # 3. Name attribute - very useful for form elements
        if raw.get("name"):
            return f"{tag}[name='{raw['name']}']"

        # 4. aria-label attribute - good for accessible elements
        if raw.get("ariaLabel"):
            # Escape quotes in aria-label value
            label = raw["ariaLabel"].replace("'", "\\'")
            return f"{tag}[aria-label='{label}']"

        # 5. Class-based selector with tag (use first non-generic class)
        if raw.get("className"):
            classes = raw["className"].split()
            # Filter out common generic/utility classes
            generic_classes = frozenset({
                "active", "disabled", "hidden", "visible", "show", "hide",
                "btn", "button", "input", "form-control", "container",
                "row", "col", "flex", "grid", "block", "inline",
            })
            meaningful_classes = [
                c for c in classes
                if c and c not in generic_classes and not c.startswith("_")
            ]
            if meaningful_classes:
                return f"{tag}.{meaningful_classes[0]}"

        # 6. Type attribute for inputs
        if raw.get("type") and tag == "input":
            input_type = raw["type"]
            # For common types, add placeholder/title context if available
            if raw.get("placeholder"):
                placeholder = raw["placeholder"].replace("'", "\\'")
                return f"input[type='{input_type}'][placeholder='{placeholder}']"
            return f"input[type='{input_type}']"

        # 7. href attribute for links (partial match for paths)
        if raw.get("href") and tag == "a":
            href = raw["href"]
            # Use partial match for relative paths
            if href.startswith("/") or href.startswith("#"):
                return f"a[href='{href}']"
            # For full URLs, match the path portion
            if "://" in href:
                from urllib.parse import urlparse
                path = urlparse(href).path
                if path and path != "/":
                    return f"a[href*='{path}']"

        # 8. Fallback: tag with any distinguishing attribute
        if raw.get("title"):
            title = raw["title"].replace("'", "\\'")
            return f"{tag}[title='{title}']"

        # 9. Last resort: just the tag (may match multiple elements)
        return tag

    def _build_css_fallback(
        self,
        raw: dict[str, Any],
        element_type: ElementType,  # noqa: ARG002
    ) -> str:
        """Build a CSS selector as fallback."""
        tag = raw.get("tagName", "div")

        if raw.get("id"):
            return f"#{raw['id']}"

        if raw.get("name"):
            return f"{tag}[name='{raw['name']}']"

        if raw.get("className"):
            first_class = raw["className"].split()[0]
            if first_class:
                return f"{tag}.{first_class}"

        if raw.get("type"):
            return f"{tag}[type='{raw['type']}']"

        return tag

    async def _discover_forms(
        self,
        context_id: str,
        elements: list[ElementInfo],
    ) -> list[dict[str, Any]]:
        """Discover and analyze forms on the page."""
        forms: list[dict[str, Any]] = []

        script = """
        (() => {
            const forms = document.querySelectorAll('form');
            return Array.from(forms).map(form => ({
                id: form.id || null,
                name: form.name || null,
                action: form.action || null,
                method: form.method || 'get',
                inputCount: form.querySelectorAll('input, select, textarea').length
            }));
        })()
        """

        try:
            # SDK v2: use evaluate for JavaScript execution
            result = await self._browser.evaluate(context_id=context_id, expression=script)
            raw_forms = result.get("result") if isinstance(result, dict) else result

            # Handle case where result might be None or not a list
            if not raw_forms or not isinstance(raw_forms, list):
                return forms

            for raw in raw_forms:
                form_elements = [
                    el for el in elements
                    if el.form_id == raw.get("id")
                ] if raw.get("id") else []

                forms.append({
                    "id": raw.get("id"),
                    "name": raw.get("name"),
                    "action": raw.get("action"),
                    "method": raw.get("method"),
                    "input_count": raw.get("inputCount", 0),
                    "elements": form_elements,
                })

        except Exception as e:
            self._log.debug("Form discovery failed", error=str(e))

        return forms

    async def _detect_login_form(
        self,
        context_id: str,
        analysis: PageAnalysis,
    ) -> dict[str, Any] | None:
        """Detect login form and extract field selectors."""
        page_info = await self._browser.get_page_info(context_id=context_id)
        url_lower = (page_info.get("url", "") if isinstance(page_info, dict) else "").lower()

        # Check URL for login indicators
        url_has_login = any(ind in url_lower for ind in self.LOGIN_INDICATORS)

        # Find potential username/password fields
        username_candidates: list[ElementInfo] = []
        password_candidates: list[ElementInfo] = []
        submit_candidates: list[ElementInfo] = []

        for element in analysis.elements:
            element_lower = (
                (element.name or "").lower() +
                (element.id or "").lower() +
                (element.placeholder or "").lower() +
                (element.aria_label or "").lower()
            )

            if element.element_type == ElementType.INPUT_PASSWORD:
                password_candidates.append(element)
            elif element.element_type in (
                ElementType.INPUT_TEXT,
                ElementType.INPUT_EMAIL,
            ):
                if any(ind in element_lower for ind in self.USERNAME_INDICATORS):
                    username_candidates.append(element)
            elif element.element_type == ElementType.BUTTON:
                text_lower = (element.text_content or "").lower()
                if any(ind in text_lower or ind in element_lower
                       for ind in self.LOGIN_INDICATORS):
                    submit_candidates.append(element)

        # Require at least username and password fields
        if not password_candidates:
            return None

        # If no explicit username field found but we have password,
        # look for any text/email input near the password field
        if not username_candidates:
            for element in analysis.elements:
                if element.element_type in (
                    ElementType.INPUT_TEXT,
                    ElementType.INPUT_EMAIL,
                ):
                    username_candidates.append(element)
                    break

        if not username_candidates:
            return None

        return {
            "username_selector": username_candidates[0].selector,
            "password_selector": password_candidates[0].selector,
            "submit_selector": submit_candidates[0].selector if submit_candidates else None,
            "is_likely_login": url_has_login or bool(submit_candidates),
        }

    def _generate_yaml_spec(self) -> str:
        """Generate complete YAML test specification from analyses."""
        if not self._page_analyses:
            return self._generate_empty_spec()

        first_analysis = self._page_analyses[0]

        # Build test specification
        spec: dict[str, Any] = {
            "name": f"Auto-generated test for {first_analysis.title}",
            "description": self._generate_description(),
            "metadata": {
                "tags": ["auto-generated", "builder"],
                "priority": "medium",
                "timeout_ms": 60000,
            },
            "variables": {
                "base_url": self._extract_base_url(self._config.url),
            },
            "steps": [],
        }

        # Add initial navigation step
        spec["steps"].append({
            "name": "Navigate to starting page",
            "action": "navigate",
            "url": self._config.url,
            "wait_until": "domcontentloaded",
            "timeout": 10000,
        })

        # Add wait for page load
        spec["steps"].append({
            "name": "Wait for page to load",
            "action": "wait_for_network_idle",
            "timeout": 5000,
        })

        # Add login steps if credentials were provided
        if self._config.username and self._config.password:
            login_steps = self._generate_login_steps()
            spec["steps"].extend(login_steps)

        # Generate test steps for each analyzed page
        for analysis in self._page_analyses:
            page_steps = self._generate_page_steps(analysis)
            spec["steps"].extend(page_steps)

        # Add final assertions
        final_assertions = self._generate_final_assertions()
        spec["steps"].extend(final_assertions)

        # Remove internal fields (starting with _) from steps before YAML output
        # These fields are for internal use and not part of the DSL schema
        for step in spec["steps"]:
            keys_to_remove = [k for k in step.keys() if k.startswith("_")]
            for key in keys_to_remove:
                del step[key]

        # Convert to YAML
        yaml_content = yaml.dump(
            spec,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=100,
        )

        # Add header comment
        header = f"""# Auto-generated test specification
# Generated: {datetime.now(UTC).isoformat()}
# URL: {self._config.url}
# Pages analyzed: {len(self._page_analyses)}
# Total elements discovered: {sum(len(p.elements) for p in self._page_analyses)}
#
# Review and customize before running in production.
# Semantic selectors are used for owl-browser compatibility.

"""
        return header + yaml_content

    def _generate_empty_spec(self) -> str:
        """Generate an empty specification when no pages were analyzed."""
        spec = {
            "name": f"Test for {self._config.url}",
            "description": "Auto-generated test (no pages analyzed)",
            "steps": [
                {
                    "name": "Navigate to page",
                    "action": "navigate",
                    "url": self._config.url,
                },
                {
                    "name": "Verify page loads",
                    "action": "assert",
                    "assertion": {
                        "selector": "body",
                        "operator": "exists",
                    },
                },
            ],
        }

        return yaml.dump(spec, default_flow_style=False, sort_keys=False)

    def _generate_description(self) -> str:
        """Generate test description from analyses."""
        total_elements = sum(len(p.elements) for p in self._page_analyses)
        total_forms = sum(len(p.forms) for p in self._page_analyses)

        parts = [
            f"Automated test covering {len(self._page_analyses)} page(s),",
            f"{total_elements} interactive elements,",
        ]

        if total_forms > 0:
            parts.append(f"and {total_forms} form(s).")
        else:
            parts.append("discovered by Auto Test Builder.")

        return " ".join(parts)

    def _generate_login_steps(self) -> list[dict[str, Any]]:
        """Generate login-related test steps."""
        steps: list[dict[str, Any]] = []

        # Find login form info
        login_analysis = next(
            (a for a in self._page_analyses if a.has_login_form),
            None,
        )

        if not login_analysis or not login_analysis.login_form_info:
            return steps

        login_info = login_analysis.login_form_info

        steps.append({
            "name": "Enter username",
            "action": "type",
            "selector": login_info["username_selector"],
            "text": "${username}",
        })

        steps.append({
            "name": "Enter password",
            "action": "type",
            "selector": login_info["password_selector"],
            "text": "${password}",
        })

        if login_info.get("submit_selector"):
            steps.append({
                "name": "Click login button",
                "action": "click",
                "selector": login_info["submit_selector"],
                "timeout": 5000,
            })
        else:
            steps.append({
                "name": "Submit login form",
                "action": "press_key",
                "key": "Enter",
            })

        steps.append({
            "name": "Wait for login response",
            "action": "wait_for_network_idle",
            "timeout": 5000,
        })

        return steps

    def _generate_page_steps(self, analysis: PageAnalysis) -> list[dict[str, Any]]:
        """
        Generate test steps for a single page.

        IMPORTANT: Each page section starts with navigation to ensure
        the browser is on the correct page before testing its elements.
        This prevents tests from running against wrong pages when
        crawling multiple pages.
        """
        steps: list[dict[str, Any]] = []

        # Extract path for readable step names
        parsed_url = urlparse(analysis.url)
        page_path = parsed_url.path or "/"

        # CRITICAL: Navigate to this page before testing its elements
        # This ensures tests don't run on the wrong page
        steps.append({
            "name": f"Navigate to {page_path}",
            "action": "navigate",
            "url": analysis.url,
            "wait_until": "domcontentloaded",
            "timeout": 10000,
        })

        # Wait for page load after navigation
        steps.append({
            "name": f"Wait for {page_path} to load",
            "action": "wait_for_network_idle",
            "timeout": 5000,
        })

        # CRITICAL: Verify we're on the correct page
        # This assertion enables recovery if navigation failed
        steps.append({
            "name": f"Verify URL contains {page_path}",
            "action": "assert",
            "assertion": {
                "operator": "url_contains",
                "expected": page_path,
                "message": f"Expected to be on page {page_path}",
                "timeout": 5000,
            },
            # Store expected URL for recovery purposes
            "_expected_url": analysis.url,
            "continue_on_failure": True,
        })

        # Take screenshot of page
        safe_title = re.sub(r"[^\w\-_]", "_", analysis.title[:30])
        # Use dash instead of colon to avoid YAML parsing issues
        steps.append({
            "name": f"Screenshot - {self._sanitize_step_name(analysis.title[:40])}",
            "action": "screenshot",
            "filename": f"page_{safe_title}.png",
        })

        # Add visibility assertions for key elements
        key_elements = self._select_key_elements(analysis.elements)

        for element in key_elements[:5]:  # Limit assertions per page
            steps.append({
                "name": f"Verify visible - {self._sanitize_step_name(element.semantic_description[:40])}",
                "action": "assert",
                "assertion": {
                    "selector": element.selector,
                    "operator": "is_visible",
                    "timeout": 5000,
                    "message": f"Element '{element.semantic_description}' should be visible on {page_path}",
                },
                # Store expected URL for recovery - if element not found,
                # runner can navigate to this URL and retry
                "_expected_url": analysis.url,
                "continue_on_failure": True,
            })

        # Generate form interaction steps
        for form in analysis.forms[:2]:  # Limit forms
            form_steps = self._generate_form_steps(form, expected_url=analysis.url)
            steps.extend(form_steps)

        # Generate button click steps (sample)
        buttons = [
            el for el in analysis.elements
            if el.element_type == ElementType.BUTTON and el.is_visible
        ]

        for button in buttons[:3]:  # Limit button clicks
            # Skip login/logout buttons
            btn_text = (button.text_content or "").lower()
            if any(skip in btn_text for skip in ["logout", "sign out", "delete", "remove"]):
                continue

            steps.append({
                "name": f"Click - {self._sanitize_step_name(button.semantic_description[:40])}",
                "action": "click",
                "selector": button.selector,
                "timeout": 5000,
                # Store expected URL for recovery
                "_expected_url": analysis.url,
                "continue_on_failure": True,
            })

        return steps

    def _select_key_elements(
        self,
        elements: list[ElementInfo],
    ) -> list[ElementInfo]:
        """Select key elements for assertion generation."""
        key_elements: list[ElementInfo] = []

        # Prioritize elements by type
        priority_types = [
            ElementType.BUTTON,
            ElementType.INPUT_TEXT,
            ElementType.INPUT_EMAIL,
            ElementType.INPUT_PASSWORD,
            ElementType.SELECT,
            ElementType.TEXTAREA,
            ElementType.LINK,
        ]

        for elem_type in priority_types:
            type_elements = [
                el for el in elements
                if el.element_type == elem_type and el.is_visible
            ]
            key_elements.extend(type_elements[:2])

        return key_elements[:10]

    def _generate_form_steps(
        self,
        form: dict[str, Any],
        expected_url: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate test steps for form interaction.

        Args:
            form: Form dictionary with elements
            expected_url: URL where this form exists, for recovery purposes
        """
        steps: list[dict[str, Any]] = []
        form_elements: list[ElementInfo] = form.get("elements", [])

        if not form_elements:
            return steps

        # Group by type - include all fillable input types
        text_inputs = [
            el for el in form_elements
            if el.element_type in (
                ElementType.INPUT_TEXT,
                ElementType.INPUT_EMAIL,
                ElementType.INPUT_PASSWORD,
                ElementType.INPUT_NUMBER,
                ElementType.INPUT_TEL,
                ElementType.INPUT_URL,
                ElementType.INPUT_SEARCH,
                ElementType.TEXTAREA,
            )
        ]

        for inp in text_inputs[:3]:  # Limit inputs
            sample_text = self._generate_sample_input(inp)
            step: dict[str, Any] = {
                "name": f"Fill - {self._sanitize_step_name(inp.semantic_description[:40])}",
                "action": "type",
                "selector": inp.selector,
                "text": sample_text,
                "continue_on_failure": True,
            }
            # Add expected URL for recovery if provided
            if expected_url:
                step["_expected_url"] = expected_url
            steps.append(step)

        return steps

    def _generate_sample_input(self, element: ElementInfo) -> str:
        """Generate appropriate sample input for a field."""
        if element.element_type == ElementType.INPUT_EMAIL:
            return "test@example.com"
        elif element.element_type == ElementType.INPUT_NUMBER:
            return "42"
        elif element.element_type == ElementType.INPUT_TEL:
            return "+1234567890"
        elif element.element_type == ElementType.INPUT_URL:
            return "https://example.com"
        elif element.element_type == ElementType.INPUT_DATE:
            return "2025-01-01"
        else:
            return "Test input"

    def _sanitize_step_name(self, name: str) -> str:
        """
        Sanitize step name for YAML compatibility.

        Removes/replaces characters that could cause YAML parsing issues,
        particularly colons which indicate key-value pairs in YAML.
        """
        # Replace colons with dashes (colons break YAML parsing in strings)
        sanitized = name.replace(":", " -")
        # Remove other potentially problematic characters
        sanitized = sanitized.replace("\n", " ").replace("\r", "")
        # Collapse multiple spaces
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized

    def _generate_final_assertions(self) -> list[dict[str, Any]]:
        """Generate final assertions for the test."""
        steps: list[dict[str, Any]] = []

        # Body exists assertion
        steps.append({
            "name": "Verify page is functional",
            "action": "assert",
            "assertion": {
                "selector": "body",
                "operator": "exists",
                "message": "Page body should exist",
            },
        })

        # Final screenshot
        steps.append({
            "name": "Final screenshot",
            "action": "screenshot",
            "filename": "test_complete.png",
        })

        return steps

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        parsed = urlparse(url)
        # Remove fragment and trailing slash
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized

    def _should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled based on patterns."""
        # Check exclude patterns
        for pattern in self._config.exclude_patterns:
            if re.search(pattern, url):
                return False

        # Check include patterns (if any specified)
        if self._config.include_patterns:
            return any(re.search(p, url) for p in self._config.include_patterns)

        return True

    def _is_valid_crawl_target(self, url: str) -> bool:
        """Check if URL is a valid crawl target."""
        if not url:
            return False

        # Skip non-HTTP URLs
        if url.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            return False

        # Skip file downloads
        extensions = (".pdf", ".zip", ".doc", ".docx", ".xls", ".xlsx", ".png",
                     ".jpg", ".jpeg", ".gif", ".svg", ".mp4", ".mp3")
        return not any(url.lower().endswith(ext) for ext in extensions)

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL from full URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
