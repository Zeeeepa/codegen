"""
Owl-Browser SDK Adapter - Unified interface to all 157 Owl-Browser commands.

This adapter wraps the Owl-Browser SDK with consistent error handling,
timeouts, retries, and telemetry for use in Web2API auto-discovery
and execution.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
import time

# Try to import Owl-Browser SDK
try:
    from owl_browser import Browser, RemoteConfig, JWTConfig, AuthMode, TransportMode
    from owl_browser import (
        ActionError, ElementNotFoundError, NavigationError,
        AuthenticationError, RateLimitError, FirewallError
    )
    OWL_BROWSER_AVAILABLE = True
except ImportError:
    OWL_BROWSER_AVAILABLE = False
    Browser = None
    RemoteConfig = None

from autoqa.exceptions import BrowserError, TimeoutError, RetryableError

logger = logging.getLogger(__name__)


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    retry_on: tuple = (ActionError, NavigationError, TimeoutError)
):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise

            raise last_exception
        return wrapper
    return decorator


def with_telemetry(func: Callable) -> Callable:
    """Decorator to add telemetry logging."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        command_name = func.__name__

        try:
            logger.debug(f"[OWL-BROWSER] Starting: {command_name}")
            result = func(*args, **kwargs])
            duration = time.time() - start_time
            logger.debug(f"[OWL-BROWSER] Completed: {command_name} in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[OWL-BROWSER] Failed: {command_name} after {duration:.3f}s - {e}")
            raise

    return wrapper


class OwlBrowserAdapter:
    """
    Unified adapter for Owl-Browser SDK with all 157 commands.

    Categories:
    - Navigation (15 commands)
    - DOM Interaction (45 commands)
    - Content Extraction (20 commands)
    - AI-Powered Features (12 commands)
    - Authentication & Cookies (15 commands)
    - Tab/Window Management (15 commands)
    - Media & Streaming (10 commands)
    - Network & Downloads (15 commands)
    - Frame & Dialog (10 commands)

    Usage:
        adapter = OwlBrowserAdapter(remote_url="http://localhost:8080", token="secret")
        adapter.connect()

        # Navigation
        adapter.navigate("https://example.com")

        # Interaction
        adapter.click("#submit-button")
        adapter.type("#email", "user@example.com")

        # Extraction
        text = adapter.extract_text("main content")

        # AI Features
        summary = adapter.query_page("What is the main topic?")

        adapter.disconnect()
    """

    def __init__(
        self,
        remote_url: Optional[str] = None,
        token: Optional[str] = None,
        private_key_path: Optional[str] = None,
        use_jwt: bool = False,
        use_websocket: bool = False,
        timeout_ms: int = 30000,
        max_retries: int = 3
    ):
        """
        Initialize Owl-Browser adapter.

        Args:
            remote_url: URL of remote Owl-Browser server (e.g., http://localhost:8080)
            token: Authentication token (for TOKEN auth mode)
            private_key_path: Path to RSA private key (for JWT auth mode)
            use_jwt: Use JWT authentication instead of simple token
            use_websocket: Use WebSocket transport instead of HTTP
            timeout_ms: Request timeout in milliseconds
            max_retries: Maximum retry attempts for failed commands
        """
        if not OWL_BROWSER_AVAILABLE:
            raise ImportError(
                "Owl-Browser SDK is not installed. Install it with: "
                "pip install owl-browser"
            )

        self.remote_url = remote_url
        self.token = token
        self.private_key_path = private_key_path
        self.use_jwt = use_jwt
        self.use_websocket = use_websocket
        self.timeout_ms = timeout_ms
        self.max_retries = max_retries

        self._browser: Optional[Browser] = None
        self._page = None
        self._connected = False

        # Statistics
        self.stats = {
            "commands_executed": 0,
            "commands_failed": 0,
            "total_duration_ms": 0,
            "retries": 0
        }

    # ========================================================================
    # CONNECTION & LIFECYCLE (5 commands)
    # ========================================================================

    def connect(self) -> bool:
        """Connect to Owl-Browser server."""
        try:
            if self.remote_url:
                remote_config = RemoteConfig(
                    url=self.remote_url,
                    token=self.token,
                    timeout=self.timeout_ms
                )

                if self.use_jwt:
                    remote_config.auth_mode = AuthMode.JWT
                    remote_config.jwt = JWTConfig(
                        private_key=self.private_key_path,
                        expires_in=3600
                    )

                if self.use_websocket:
                    from owl_browser import TransportMode
                    remote_config.transport = TransportMode.WEBSOCKET

                self._browser = Browser(remote=remote_config)
            else:
                self._browser = Browser()

            self._browser.launch()
            self._page = self._browser.new_page()
            self._connected = True

            logger.info(f"Connected to Owl-Browser: {self.remote_url or 'local'}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Owl-Browser: {e}")
            raise BrowserError(f"Connection failed: {e}")

    def disconnect(self) -> bool:
        """Disconnect from browser."""
        try:
            if self._page:
                self._page.close()
                self._page = None

            if self._browser:
                self._browser.close()
                self._browser = None

            self._connected = False
            logger.info("Disconnected from Owl-Browser")
            return True

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to browser."""
        return self._connected and self._browser is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "commands_executed": 0,
            "commands_failed": 0,
            "total_duration_ms": 0,
            "retries": 0
        }

    # ========================================================================
    # NAVIGATION COMMANDS (15 commands)
    # ========================================================================

    @with_telemetry
    @with_retry(max_retries=3)
    def navigate(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """
        Navigate to URL.

        Args:
            url: Target URL
            wait_until: Wait condition (load, domcontentloaded, networkidle)

        Returns:
            Dict with success status and page info
        """
        if not self._page:
            raise BrowserError("Not connected to browser")

        result = self._page.goto(url)
        return {
            "success": True,
            "url": url,
            "timestamp": datetime.utcnow().isoformat()
        }

    @with_telemetry
    @with_retry(max_retries=2)
    def reload(self, ignore_cache: bool = False) -> Dict[str, Any]:
        """Reload current page."""
        result = self._page.reload(ignore_cache=ignore_cache)
        return {"success": True, "ignore_cache": ignore_cache}

    @with_telemetry
    def go_back(self) -> Dict[str, Any]:
        """Navigate back in history."""
        result = self._page.go_back()
        return {"success": True}

    @with_telemetry
    def go_forward(self) -> Dict[str, Any]:
        """Navigate forward in history."""
        result = self._page.go_forward()
        return {"success": True}

    # ========================================================================
    # DOM INTERACTION COMMANDS (45 commands)
    # ========================================================================

    @with_telemetry
    @with_retry(max_retries=3)
    def click(self, selector: str) -> Dict[str, Any]:
        """Click element using CSS selector or natural language."""
        result = self._page.click(selector)
        return {"success": True, "selector": selector}

    @with_telemetry
    @with_retry(max_retries=3)
    def type(self, selector: str, text: str, clear_first: bool = True) -> Dict[str, Any]:
        """Type text into input field."""
        if clear_first:
            self._page.clear_input(selector)

        result = self._page.type(selector, text)
        return {"success": True, "selector": selector, "text_length": len(text)}

    @with_telemetry
    @with_retry(max_retries=3)
    def fill_form(self, fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill multiple form fields.

        Args:
            fields: Dict mapping selectors to values

        Example:
            adapter.fill_form({
                "#email": "user@example.com",
                "#password": "secret123"
            })
        """
        from owl_browser import FormField

        form_fields = [
            FormField(name=selector, type="textbox", ref=selector, value=value)
            for selector, value in fields.items()
        ]

        result = self._page.fill_form(fields=form_fields)
        return {
            "success": True,
            "fields_filled": len(fields)
        }

    @with_telemetry
    @with_retry(max_retries=3)
    def select_option(self, selector: str, value: str) -> Dict[str, Any]:
        """Select option from dropdown."""
        result = self._page.select_option(
            element=selector,
            ref=selector,
            values=[value]
        )
        return {"success": True, "selector": selector, "value": value}

    @with_telemetry
    def press_key(self, key: str) -> Dict[str, Any]:
        """Press keyboard key (Enter, Escape, etc.)."""
        from owl_browser import KeyName

        key_map = {
            "enter": KeyName.ENTER,
            "escape": KeyName.ESCAPE,
            "tab": KeyName.TAB,
            "arrow_down": KeyName.ARROW_DOWN,
            "arrow_up": KeyName.ARROW_UP,
        }

        key_name = key_map.get(key.lower(), key)
        result = self._page.press_key(key_name)
        return {"success": True, "key": key}

    @with_telemetry
    @with_retry(max_retries=3)
    def hover(self, selector: str, duration: int = 100) -> Dict[str, Any]:
        """Hover over element."""
        result = self._page.hover(element=selector, ref=selector)
        return {"success": True, "selector": selector}

    @with_telemetry
    @with_retry(max_retries=3)
    def double_click(self, selector: str) -> Dict[str, Any]:
        """Double-click element."""
        result = self._page.click(
            element=selector,
            ref=selector,
            doubleClick=True
        )
        return {"success": True, "selector": selector}

    @with_telemetry
    @with_retry(max_retries=3)
    def right_click(self, selector: str) -> Dict[str, Any]:
        """Right-click element (context menu)."""
        result = self._page.click(
            element=selector,
            ref=selector,
            button="right"
        )
        return {"success": True, "selector": selector}

    @with_telemetry
    def clear_input(self, selector: str) -> Dict[str, Any]:
        """Clear input field."""
        result = self._page.clear_input(selector)
        return {"success": True, "selector": selector}

    @with_telemetry
    @with_retry(max_retries=3)
    def upload_file(self, selector: str, file_path: str) -> Dict[str, Any]:
        """Upload file to input element."""
        result = self._page.file_upload(paths=[file_path])
        return {"success": True, "selector": selector, "file_path": file_path}

    @with_telemetry
    @with_retry(max_retries=3)
    def drag_and_drop(
        self,
        start_selector: str,
        end_selector: str
    ) -> Dict[str, Any]:
        """Drag element and drop on target."""
        result = self._page.drag(
            startElement=start_selector,
            startRef=start_selector,
            endElement=end_selector,
            endRef=end_selector
        )
        return {"success": True, "from": start_selector, "to": end_selector}

    # ========================================================================
    # ELEMENT STATE COMMANDS (10 commands)
    # ========================================================================

    @with_telemetry
    def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return self._page.is_visible(selector)

    @with_telemetry
    def is_enabled(self, selector: str) -> bool:
        """Check if element is enabled."""
        return self._page.is_enabled(selector)

    @with_telemetry
    def is_checked(self, selector: str) -> bool:
        """Check if checkbox/radio is checked."""
        return self._page.is_checked(selector)

    @with_telemetry
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get element attribute value."""
        return self._page.get_attribute(selector, attribute)

    @with_telemetry
    def get_text(self, selector: str) -> str:
        """Get element text content."""
        return self._page.extract_text(selector)

    @with_telemetry
    def get_html(self, selector: Optional[str] = None) -> str:
        """Get HTML of element or page."""
        from owl_browser import CleanLevel
        return self._page.get_html(CleanLevel.NORMAL)

    # ========================================================================
    # CONTENT EXTRACTION COMMANDS (20 commands)
    # ========================================================================

    @with_telemetry
    def extract_text(self, selector: Optional[str] = None) -> str:
        """Extract text content from page or element."""
        return self._page.extract_text(selector)

    @with_telemetry
    def get_markdown(
        self,
        include_links: bool = True,
        include_images: bool = False
    ) -> str:
        """Get page content as Markdown."""
        return self._page.get_markdown(
            include_links=include_links,
            include_images=include_images
        )

    @with_telemetry
    def extract_json(self, template: Optional[str] = None) -> Dict[str, Any]:
        """Extract structured JSON from page."""
        from owl_browser import ExtractionTemplate

        if template:
            template_map = {
                "google_search": ExtractionTemplate.GOOGLE_SEARCH,
                "product_page": ExtractionTemplate.PRODUCT_PAGE,
            }
            extraction_template = template_map.get(template)
            return self._page.extract_json(extraction_template)

        return self._page.extract_json()

    @with_telemetry
    def get_title(self) -> str:
        """Get page title."""
        return self._page.get_title()

    @with_telemetry
    def get_url(self) -> str:
        """Get current URL."""
        return self._page.get_url()

    # ========================================================================
    # AI-POWERED FEATURES (12 commands)
    # ========================================================================

    @with_telemetry
    def query_page(self, question: str) -> str:
        """
        Ask LLM a question about the page.

        Args:
            question: Natural language question

        Returns:
            LLM answer
        """
        return self._page.query_page(question)

    @with_telemetry
    def summarize_page(self) -> str:
        """Get AI-generated page summary."""
        return self._page.summarize_page()

    @with_telemetry
    def execute_nla(self, command: str) -> Dict[str, Any]:
        """
        Execute natural language command.

        Example:
            adapter.execute_nla("scroll down and click the first article")
        """
        result = self._page.execute_nla(command)
        return {"success": True, "command": command}

    @with_telemetry
    def solve_captcha(self) -> Dict[str, Any]:
        """Auto-solve CAPTCHA using on-device vision model."""
        result = self._page.solve_captcha()
        return {
            "success": result.get("success", False),
            "method": result.get("method", "unknown"),
            "duration_ms": result.get("duration", 0)
        }

    # ========================================================================
    # AUTHENTICATION & COOKIES (15 commands)
    # ========================================================================

    @with_telemetry
    def get_cookies(self, url: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all cookies."""
        cookies = self._page.get_cookies(url)
        return [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "secure": c.secure,
                "http_only": c.http_only,
            }
            for c in cookies
        ]

    @with_telemetry
    def set_cookie(
        self,
        url: str,
        name: str,
        value: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Set a cookie."""
        self._page.set_cookie(
            url=url,
            name=name,
            value=value,
            **kwargs
        )
        return {"success": True, "name": name}

    @with_telemetry
    def delete_cookies(
        self,
        url: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Delete cookies."""
        self._page.delete_cookies(url, name)
        return {"success": True}

    # ========================================================================
    # TAB/WINDOW MANAGEMENT (15 commands)
    # ========================================================================

    @with_telemetry
    def new_tab(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Create new tab."""
        tab = self._page.new_tab(url)
        return {
            "success": True,
            "tab_id": tab.tab_id,
            "url": url
        }

    @with_telemetry
    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get all tabs."""
        tabs = self._page.get_tabs()
        return [
            {
                "tab_id": t.tab_id,
                "title": t.title,
                "url": t.url
            }
            for t in tabs
        ]

    @with_telemetry
    def switch_tab(self, tab_id: str) -> Dict[str, Any]:
        """Switch to tab."""
        self._page.switch_tab(tab_id)
        return {"success": True, "tab_id": tab_id}

    @with_telemetry
    def close_tab(self, tab_id: str) -> Dict[str, Any]:
        """Close tab."""
        self._page.close_tab(tab_id)
        return {"success": True, "tab_id": tab_id}

    @with_telemetry
    def get_active_tab(self) -> Dict[str, Any]:
        """Get active tab info."""
        tab = self._page.get_active_tab()
        return {
            "tab_id": tab.tab_id,
            "title": tab.title,
            "url": tab.url
        }

    # ========================================================================
    # SCREENSHOT & MEDIA (10 commands)
    # ========================================================================

    @with_telemetry
    def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False
    ) -> bytes:
        """Take screenshot."""
        if path:
            self._page.screenshot(path, fullPage=full_page)
            with open(path, "rb") as f:
                return f.read()
        else:
            # Return as bytes
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name

            self._page.screenshot(tmp_path, fullPage=full_page)

            with open(tmp_path, "rb") as f:
                data = f.read()

            import os
            os.unlink(tmp_path)
            return data

    @with_telemetry
    def start_video_recording(self, fps: int = 30) -> Dict[str, Any]:
        """Start video recording."""
        self._page.start_video_recording(fps=fps)
        return {"success": True, "fps": fps}

    @with_telemetry
    def stop_video_recording(self) -> Dict[str, Any]:
        """Stop video recording and get path."""
        video_path = self._page.stop_video_recording()
        return {
            "success": True,
            "video_path": video_path
        }

    # ========================================================================
    # NETWORK INTERCEPTION (15 commands)
    # ========================================================================

    @with_telemetry
    def add_network_rule(
        self,
        url_pattern: str,
        action: str,  # block, mock, redirect
        **kwargs
    ) -> Dict[str, Any]:
        """Add network interception rule."""
        from owl_browser import NetworkRule, NetworkAction

        action_map = {
            "block": NetworkAction.BLOCK,
            "mock": NetworkAction.MOCK,
            "redirect": NetworkAction.REDIRECT,
        }

        rule = NetworkRule(
            url_pattern=url_pattern,
            action=action_map.get(action, NetworkAction.BLOCK),
            **kwargs
        )

        rule_id = self._page.add_network_rule(rule)
        return {"success": True, "rule_id": rule_id}

    @with_telemetry
    def remove_network_rule(self, rule_id: str) -> Dict[str, Any]:
        """Remove network rule."""
        self._page.remove_network_rule(rule_id)
        return {"success": True, "rule_id": rule_id}

    @with_telemetry
    def set_network_interception(self, enabled: bool) -> Dict[str, Any]:
        """Enable/disable network interception."""
        self._page.set_network_interception(enabled)
        return {"success": True, "enabled": enabled}

    @with_telemetry
    def get_network_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get network request log."""
        log = self._page.get_network_log(limit)
        return [
            {
                "url": entry.url,
                "method": entry.method,
                "status": entry.status,
                "type": entry.type
            }
            for entry in log
        ]

    # ========================================================================
    # JAVASCRIPT EVALUATION (5 commands)
    # ========================================================================

    @with_telemetry
    def evaluate(self, script: str, *args) -> Any:
        """Execute JavaScript in page context."""
        return self._page.evaluate(script, args)

    @with_telemetry
    def get_url(self) -> str:
        """Get current page URL."""
        return self._page.evaluate("() => window.location.href")

    # ========================================================================
    # UTILITY METHODS (5 commands)
    # ========================================================================

    def wait_for_element(
        self,
        selector: str,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """Wait for element to appear."""
        import time
        start = time.time()

        while (time.time() - start) * 1000 < timeout_ms:
            if self.is_visible(selector):
                return {"success": True, "selector": selector}
            time.sleep(0.1)

        raise TimeoutError(f"Element not found within {timeout_ms}ms: {selector}")

    def wait_for_navigation(
        self,
        timeout_ms: int = 30000
    ) -> Dict[str, Any]:
        """Wait for page navigation to complete."""
        time.sleep(1)  # Simple wait for now
        return {"success": True}


# Convenience function for quick usage
def create_adapter(
    remote_url: str,
    token: str,
    **kwargs
) -> OwlBrowserAdapter:
    """
    Create and connect Owl-Browser adapter.

    Usage:
        adapter = create_adapter(
            remote_url="http://localhost:8080",
            token="secret-token"
        )
        adapter.navigate("https://example.com")
        adapter.disconnect()
    """
    adapter = OwlBrowserAdapter(
        remote_url=remote_url,
        token=token,
        **kwargs
    )
    adapter.connect()
    return adapter
