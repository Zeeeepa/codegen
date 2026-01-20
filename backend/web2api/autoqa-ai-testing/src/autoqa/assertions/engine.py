"""
Assertion engine for test validations.

Provides comprehensive assertions for:
- Element state (visibility, enabled, checked, text, attributes)
- Visual regression
- Network requests (status codes, response times, content)
- URL validation
- Custom JavaScript assertions

SDK v2 Notes:
- All browser operations are async
- Engine takes browser and context_id parameters
- All assertion methods are async
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.dsl.models import (
    AccessibilityAssertionConfig,
    AssertionConfig,
    AssertionOperator,
    ColorAssertionConfig,
    CustomAssertionConfig,
    ElementAssertionConfig,
    IconAssertionConfig,
    LayoutAssertionConfig,
    MLAssertionConfig,
    NetworkAssertionConfig,
    OCRAssertionConfig,
    UIStateAssertionConfig,
    VisualAssertionConfig,
)

if TYPE_CHECKING:
    from owl_browser import OwlBrowser

    from autoqa.assertions.ml_engine import MLAssertionEngine

logger = structlog.get_logger(__name__)


class AssertionError(Exception):
    """Raised when an assertion fails."""

    def __init__(
        self,
        message: str,
        expected: Any = None,
        actual: Any = None,
        operator: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.expected = expected
        self.actual = actual
        self.operator = operator
        self.details = details or {}
        super().__init__(message)


@dataclass
class AssertionResult:
    """Result of an assertion check."""

    passed: bool
    message: str
    expected: Any = None
    actual: Any = None
    duration_ms: int = 0
    details: dict[str, Any] | None = None


class AssertionEngine:
    """
    Executes assertions against the browser context.

    SDK v2 Notes:
    - Takes browser and context_id instead of page object
    - All browser operations are async
    - All assertion methods are async

    Supports:
    - Element assertions (visibility, enabled, checked, text, attributes)
    - Visual regression assertions
    - Network assertions (request made, status codes, response content)
    - URL assertions (current URL matches pattern)
    - Attribute assertions (element attribute comparisons)
    - State assertions (is_visible, is_enabled, is_checked via extract_text)
    - Custom JavaScript assertions
    """

    def __init__(self, browser: OwlBrowser, context_id: str) -> None:
        self._browser = browser
        self._context_id = context_id
        self._log = logger.bind(component="assertion_engine")
        self._network_log_cache: list[dict[str, Any]] | None = None

    async def assert_element(self, config: AssertionConfig) -> bool:
        """
        Execute an element assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If assertion fails
        """
        start_time = time.monotonic()

        for attempt in range(config.retry_count + 1):
            try:
                result = await self._evaluate_assertion(config)
                if result:
                    return True
            except Exception as e:
                if attempt == config.retry_count:
                    raise AssertionError(
                        config.message or f"Assertion failed: {e}",
                        expected=config.expected,
                        actual=None,
                        operator=config.operator,
                    ) from e

            if attempt < config.retry_count:
                await asyncio.sleep(config.timeout / 1000 / (config.retry_count + 1))

        raise AssertionError(
            config.message or f"Assertion failed after {config.retry_count + 1} attempts",
            expected=config.expected,
            operator=config.operator,
        )

    async def _evaluate_assertion(self, config: AssertionConfig) -> bool:
        """Evaluate a single assertion."""
        match config.operator:
            # Element existence
            case AssertionOperator.EXISTS:
                return await self._check_exists(config.selector)
            case AssertionOperator.NOT_EXISTS:
                return not await self._check_exists(config.selector)

            # Element state assertions
            case AssertionOperator.IS_VISIBLE:
                return await self._is_visible(config.selector)
            case AssertionOperator.IS_HIDDEN:
                return not await self._is_visible(config.selector)
            case AssertionOperator.IS_ENABLED:
                return await self._is_enabled(config.selector)
            case AssertionOperator.IS_DISABLED:
                return not await self._is_enabled(config.selector)
            case AssertionOperator.IS_CHECKED:
                return await self._is_checked(config.selector)
            case AssertionOperator.IS_UNCHECKED:
                return not await self._is_checked(config.selector)

            # Value comparisons
            case AssertionOperator.EQUALS:
                actual = await self._get_value(config)
                return actual == config.expected
            case AssertionOperator.NOT_EQUALS:
                actual = await self._get_value(config)
                return actual != config.expected
            case AssertionOperator.CONTAINS:
                actual = await self._get_value(config)
                return config.expected in str(actual)
            case AssertionOperator.NOT_CONTAINS:
                actual = await self._get_value(config)
                return config.expected not in str(actual)
            case AssertionOperator.MATCHES:
                actual = await self._get_value(config)
                return bool(re.search(str(config.expected), str(actual)))
            case AssertionOperator.STARTS_WITH:
                actual = await self._get_value(config)
                return str(actual).startswith(str(config.expected))
            case AssertionOperator.ENDS_WITH:
                actual = await self._get_value(config)
                return str(actual).endswith(str(config.expected))

            # Numeric comparisons
            case AssertionOperator.GREATER_THAN:
                actual = await self._get_numeric_value(config)
                return actual > float(config.expected)
            case AssertionOperator.LESS_THAN:
                actual = await self._get_numeric_value(config)
                return actual < float(config.expected)
            case AssertionOperator.GREATER_OR_EQUAL:
                actual = await self._get_numeric_value(config)
                return actual >= float(config.expected)
            case AssertionOperator.LESS_OR_EQUAL:
                actual = await self._get_numeric_value(config)
                return actual <= float(config.expected)

            # Boolean assertions
            case AssertionOperator.IS_TRUTHY:
                actual = await self._get_value(config)
                return bool(actual)
            case AssertionOperator.IS_FALSY:
                actual = await self._get_value(config)
                return not bool(actual)

            # URL assertions
            case AssertionOperator.URL_EQUALS:
                return await self._get_current_url() == str(config.expected)
            case AssertionOperator.URL_CONTAINS:
                return str(config.expected) in await self._get_current_url()
            case AssertionOperator.URL_MATCHES:
                return bool(re.search(str(config.expected), await self._get_current_url()))

            # Attribute assertions
            case AssertionOperator.HAS_ATTRIBUTE:
                if not config.selector or not config.attribute:
                    return False
                attr_value = await self._get_attribute(config.selector, config.attribute)
                return attr_value is not None
            case AssertionOperator.ATTRIBUTE_EQUALS:
                if not config.selector or not config.attribute:
                    return False
                attr_value = await self._get_attribute(config.selector, config.attribute)
                return attr_value == config.expected
            case AssertionOperator.ATTRIBUTE_CONTAINS:
                if not config.selector or not config.attribute:
                    return False
                attr_value = await self._get_attribute(config.selector, config.attribute)
                return attr_value is not None and str(config.expected) in str(attr_value)

            # Network assertions (handled separately but can be triggered via operator)
            case AssertionOperator.REQUEST_MADE:
                return await self._check_request_made(str(config.expected))
            case AssertionOperator.STATUS_CODE_EQUALS:
                return await self._check_status_code(str(config.selector), int(config.expected))
            case AssertionOperator.STATUS_CODE_IN_RANGE:
                # expected should be "200-299" format
                parts = str(config.expected).split("-")
                if len(parts) == 2:
                    return await self._check_status_code_range(
                        str(config.selector), int(parts[0]), int(parts[1])
                    )
                return False

            case _:
                raise ValueError(f"Unknown operator: {config.operator}")

    async def _check_exists(self, selector: str | None) -> bool:
        """Check if element exists."""
        if not selector:
            return False
        try:
            # Try to check visibility - if no error, element exists
            await self._is_visible(selector)
            return True
        except Exception:
            return False

    async def _is_visible(self, selector: str | None) -> bool:
        """Check if element is visible."""
        if not selector:
            return False
        try:
            result = await self._browser.is_visible(
                context_id=self._context_id,
                selector=selector,
            )
            # SDK returns {'success': True, 'error_code': 'visible', ...} when visible
            # or {'success': False, ...} when not visible
            if isinstance(result, dict):
                # Check for 'success' key (SDK v2 format) or fallback to 'visible' key
                if "success" in result:
                    return result.get("success", False)
                return result.get("visible", False)
            return bool(result)
        except Exception:
            return False

    async def _is_enabled(self, selector: str | None) -> bool:
        """Check if element is enabled."""
        if not selector:
            return False
        try:
            result = await self._browser.is_enabled(
                context_id=self._context_id,
                selector=selector,
            )
            # SDK returns {'success': True, ...} when enabled
            if isinstance(result, dict):
                if "success" in result:
                    return result.get("success", False)
                return result.get("enabled", False)
            return bool(result)
        except Exception:
            return False

    async def _is_checked(self, selector: str | None) -> bool:
        """Check if element is checked."""
        if not selector:
            return False
        try:
            result = await self._browser.is_checked(
                context_id=self._context_id,
                selector=selector,
            )
            # SDK returns {'success': True, ...} when checked
            if isinstance(result, dict):
                if "success" in result:
                    return result.get("success", False)
                return result.get("checked", False)
            return bool(result)
        except Exception:
            return False

    async def _get_attribute(self, selector: str, attribute: str) -> str | None:
        """Get element attribute value."""
        try:
            result = await self._browser.get_attribute(
                context_id=self._context_id,
                selector=selector,
                attribute=attribute,
            )
            return result.get("value") if isinstance(result, dict) else result
        except Exception:
            return None

    async def _get_value(self, config: AssertionConfig) -> Any:
        """Get value for comparison."""
        if config.attribute and config.selector:
            return await self._get_attribute(config.selector, config.attribute)
        elif config.property and config.selector:
            script = f"document.querySelector('{config.selector}').{config.property}"
            result = await self._browser.evaluate(
                context_id=self._context_id,
                script=script,
                return_value=True,
            )
            return result.get("result") if isinstance(result, dict) else result
        elif config.selector:
            result = await self._browser.extract_text(
                context_id=self._context_id,
                selector=config.selector,
            )
            return result.get("text") if isinstance(result, dict) else result
        return None

    async def _get_numeric_value(self, config: AssertionConfig) -> float:
        """Get numeric value for comparison."""
        value = await self._get_value(config)
        if value is None:
            raise AssertionError(f"Could not get value from selector: {config.selector}")
        try:
            cleaned = re.sub(r"[^\d.-]", "", str(value))
            return float(cleaned)
        except ValueError as e:
            raise AssertionError(f"Value '{value}' is not numeric") from e

    async def _get_current_url(self) -> str:
        """Get current page URL."""
        try:
            result = await self._browser.get_page_info(context_id=self._context_id)
            return result.get("url", "") if isinstance(result, dict) else ""
        except Exception:
            return ""

    async def _get_network_log(self) -> list[dict[str, Any]]:
        """Get cached or fresh network log."""
        if self._network_log_cache is None:
            try:
                result = await self._browser.get_network_log(context_id=self._context_id)
                self._network_log_cache = result.get("entries", []) if isinstance(result, dict) else []
            except Exception:
                self._network_log_cache = []
        return self._network_log_cache

    async def _check_request_made(self, url_pattern: str) -> bool:
        """Check if a request matching the pattern was made."""
        network_log = await self._get_network_log()
        for entry in network_log:
            url = entry.get("url", "")
            if url_pattern in url or re.search(url_pattern, url):
                return True
        return False

    async def _check_status_code(self, url_pattern: str, expected_status: int) -> bool:
        """Check if request matching pattern has expected status code."""
        network_log = await self._get_network_log()
        for entry in network_log:
            url = entry.get("url", "")
            if url_pattern in url or re.search(url_pattern, url):
                return entry.get("status") == expected_status
        return False

    async def _check_status_code_range(
        self, url_pattern: str, min_status: int, max_status: int
    ) -> bool:
        """Check if request matching pattern has status code in range."""
        network_log = await self._get_network_log()
        for entry in network_log:
            url = entry.get("url", "")
            if url_pattern in url or re.search(url_pattern, url):
                status = entry.get("status", 0)
                return min_status <= status <= max_status
        return False

    async def assert_url(
        self,
        url_pattern: str,
        is_regex: bool = False,
        message: str | None = None,
    ) -> bool:
        """
        Assert current URL matches pattern.

        Args:
            url_pattern: URL pattern to match (string or regex)
            is_regex: Whether to treat pattern as regex
            message: Custom error message

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If URL does not match
        """
        current_url = await self._get_current_url()

        if is_regex:
            if re.search(url_pattern, current_url):
                return True
        else:
            if url_pattern in current_url:
                return True

        raise AssertionError(
            message or "URL assertion failed",
            expected=url_pattern,
            actual=current_url,
            operator="url_matches" if is_regex else "url_contains",
        )

    async def assert_attribute(
        self,
        selector: str,
        attribute: str,
        expected: str | None = None,
        operator: AssertionOperator = AssertionOperator.EXISTS,
        message: str | None = None,
    ) -> bool:
        """
        Assert element attribute matches expected value.

        Args:
            selector: CSS selector for element
            attribute: Attribute name to check
            expected: Expected value (not needed for EXISTS)
            operator: Comparison operator
            message: Custom error message

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If attribute assertion fails
        """
        try:
            actual = await self._get_attribute(selector, attribute)
        except Exception as e:
            raise AssertionError(
                message or f"Failed to get attribute '{attribute}' from '{selector}'",
                details={"error": str(e)},
            ) from e

        match operator:
            case AssertionOperator.HAS_ATTRIBUTE | AssertionOperator.EXISTS:
                if actual is not None:
                    return True
            case AssertionOperator.EQUALS | AssertionOperator.ATTRIBUTE_EQUALS:
                if actual == expected:
                    return True
            case AssertionOperator.CONTAINS | AssertionOperator.ATTRIBUTE_CONTAINS:
                if actual is not None and expected is not None and expected in actual:
                    return True
            case AssertionOperator.MATCHES:
                if actual is not None and expected is not None:
                    if re.search(expected, actual):
                        return True
            case _:
                raise ValueError(f"Unsupported operator for attribute assertion: {operator}")

        raise AssertionError(
            message or f"Attribute assertion failed for '{attribute}'",
            expected=expected,
            actual=actual,
            operator=str(operator),
        )

    async def assert_state(
        self,
        selector: str,
        state: str,
        expected: bool = True,
        message: str | None = None,
    ) -> bool:
        """
        Assert element state (visible, enabled, checked).

        Args:
            selector: CSS selector for element
            state: State to check ('visible', 'enabled', 'checked')
            expected: Expected state value
            message: Custom error message

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If state assertion fails
        """
        try:
            match state.lower():
                case "visible":
                    actual = await self._is_visible(selector)
                case "enabled":
                    actual = await self._is_enabled(selector)
                case "checked":
                    actual = await self._is_checked(selector)
                case _:
                    raise ValueError(f"Unknown state: {state}")
        except Exception as e:
            raise AssertionError(
                message or f"Failed to check state '{state}' for '{selector}'",
                details={"error": str(e)},
            ) from e

        if actual == expected:
            return True

        raise AssertionError(
            message or f"State assertion failed for '{selector}'",
            expected=f"{state}={expected}",
            actual=f"{state}={actual}",
        )

    async def assert_text(
        self,
        selector: str,
        expected: str,
        operator: AssertionOperator = AssertionOperator.CONTAINS,
        message: str | None = None,
    ) -> bool:
        """
        Assert element text matches expected value.

        Uses extract_text for text comparison.

        Args:
            selector: CSS selector for element
            expected: Expected text value
            operator: Comparison operator
            message: Custom error message

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If text assertion fails
        """
        try:
            result = await self._browser.extract_text(
                context_id=self._context_id,
                selector=selector,
            )
            actual = result.get("text") if isinstance(result, dict) else result
        except Exception as e:
            raise AssertionError(
                message or f"Failed to extract text from '{selector}'",
                details={"error": str(e)},
            ) from e

        passed = False
        match operator:
            case AssertionOperator.EQUALS:
                passed = actual == expected
            case AssertionOperator.CONTAINS:
                passed = expected in (actual or "")
            case AssertionOperator.NOT_CONTAINS:
                passed = expected not in (actual or "")
            case AssertionOperator.MATCHES:
                passed = bool(re.search(expected, actual or ""))
            case AssertionOperator.STARTS_WITH:
                passed = (actual or "").startswith(expected)
            case AssertionOperator.ENDS_WITH:
                passed = (actual or "").endswith(expected)
            case _:
                raise ValueError(f"Unsupported operator for text assertion: {operator}")

        if passed:
            return True

        raise AssertionError(
            message or f"Text assertion failed for '{selector}'",
            expected=expected,
            actual=actual,
            operator=str(operator),
        )

    async def assert_visual(
        self,
        config: VisualAssertionConfig,
        artifact_dir: Path,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
    ) -> bool:
        """
        Execute a visual regression assertion with enterprise features.

        Supports:
        - Selector-based element screenshots
        - Viewport-specific baselines
        - Anti-aliasing tolerance
        - Auto-mask dynamic regions
        - Multiple threshold modes (strict, normal, loose, custom)
        - HTML diff reports

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If visual comparison fails
        """
        from autoqa.visual.regression_engine import VisualRegressionEngine

        engine = VisualRegressionEngine(baseline_dir=artifact_dir / "baselines")

        # FIX: Properly capture element screenshot when selector is provided
        if config.selector:
            # Use element screenshot for selector-based visual assertions
            screenshot = await self._capture_element_screenshot(config.selector)
        else:
            screenshot = await self._take_screenshot()

        result = engine.compare(
            baseline_name=config.baseline_name,
            current_image=screenshot,
            mode=config.mode,
            threshold=config.threshold,
            ignore_regions=config.ignore_regions,
            ignore_colors=config.ignore_colors,
            update_baseline=config.update_baseline,
            # Enterprise features from config
            threshold_mode=config.threshold_mode,
            anti_aliasing_tolerance=config.anti_aliasing_tolerance,
            anti_aliasing_sigma=config.anti_aliasing_sigma,
            auto_mask_dynamic=config.auto_mask_dynamic,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            normalize_scroll=config.normalize_scroll,
            generate_html_report=config.generate_html_report,
        )

        if not result.passed:
            if result.diff_path:
                self._log.info("Visual diff saved", path=result.diff_path)
            if result.html_report_path:
                self._log.info("HTML report generated", path=result.html_report_path)

            details: dict[str, Any] = {
                "diff_percentage": result.diff_percentage,
                "changed_pixel_count": result.changed_pixel_count,
                "total_pixel_count": result.total_pixel_count,
                "changed_regions_count": len(result.changed_regions),
                "similarity_score": result.similarity_score,
            }
            if result.html_report_path:
                details["html_report"] = result.html_report_path

            raise AssertionError(
                config.message or f"Visual assertion failed: {result.message}",
                expected=f"Baseline: {config.baseline_name}",
                actual=f"Diff: {result.diff_percentage:.2%} ({result.changed_pixel_count:,} pixels)",
                details=details,
            )

        return True

    async def _take_screenshot(self) -> bytes:
        """Take a full page screenshot and return as bytes."""
        import base64

        result = await self._browser.screenshot(context_id=self._context_id)
        if isinstance(result, dict):
            image_data = result.get("data") or result.get("image") or result.get("screenshot")
        else:
            image_data = result

        if image_data:
            return base64.b64decode(image_data)
        return b""

    async def _capture_element_screenshot(self, selector: str) -> bytes:
        """
        Capture screenshot of a specific element.

        Args:
            selector: CSS selector for the element

        Returns:
            PNG image bytes of the element
        """
        # Get element bounding box
        script = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            return {{
                x: Math.round(rect.x + window.scrollX),
                y: Math.round(rect.y + window.scrollY),
                width: Math.round(rect.width),
                height: Math.round(rect.height)
            }};
        }})()
        """
        try:
            result = await self._browser.evaluate(
                context_id=self._context_id,
                script=script,
                return_value=True,
            )
            bbox = result.get("result") if isinstance(result, dict) else result
            if bbox is None:
                self._log.warning("Element not found for screenshot", selector=selector)
                return await self._take_screenshot()

            # Take full page screenshot and crop to element
            import io

            from PIL import Image

            full_screenshot = await self._take_screenshot()
            img = Image.open(io.BytesIO(full_screenshot))

            # Calculate crop coordinates
            x = max(0, bbox["x"])
            y = max(0, bbox["y"])
            x2 = min(img.width, x + bbox["width"])
            y2 = min(img.height, y + bbox["height"])

            # Crop to element bounds
            cropped = img.crop((x, y, x2, y2))

            # Convert back to bytes
            buffer = io.BytesIO()
            cropped.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            self._log.warning(
                "Failed to capture element screenshot, falling back to full page",
                selector=selector,
                error=str(e),
            )
            return await self._take_screenshot()

    async def assert_network(self, config: NetworkAssertionConfig) -> bool:
        """
        Execute a network assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If network assertion fails
        """
        start_time = time.monotonic()
        timeout_sec = config.timeout / 1000

        network_log = await self._get_network_log()

        matching_entries = self._filter_network_entries(network_log, config)

        if config.should_be_blocked:
            if matching_entries:
                raise AssertionError(
                    config.message or f"Request to {config.url_pattern} was not blocked",
                    expected="Request blocked",
                    actual=f"Found {len(matching_entries)} matching requests",
                )
            return True

        if not matching_entries:
            raise AssertionError(
                config.message or f"No requests matching {config.url_pattern}",
                expected="At least one matching request",
                actual="No matching requests found",
            )

        for entry in matching_entries:
            if config.status_code and entry.get("status") != config.status_code:
                raise AssertionError(
                    config.message or f"Status code mismatch for {entry.get('url')}",
                    expected=config.status_code,
                    actual=entry.get("status"),
                )

            if config.status_range:
                status = entry.get("status", 0)
                if not (config.status_range[0] <= status <= config.status_range[1]):
                    raise AssertionError(
                        config.message or f"Status code out of range for {entry.get('url')}",
                        expected=f"{config.status_range[0]}-{config.status_range[1]}",
                        actual=status,
                    )

            if config.max_response_time_ms:
                duration = entry.get("duration", 0)
                if duration > config.max_response_time_ms:
                    raise AssertionError(
                        config.message or f"Response too slow for {entry.get('url')}",
                        expected=f"<= {config.max_response_time_ms}ms",
                        actual=f"{duration}ms",
                    )

        return True

    def _filter_network_entries(
        self,
        entries: list[dict[str, Any]],
        config: NetworkAssertionConfig,
    ) -> list[dict[str, Any]]:
        """Filter network log entries by config criteria."""
        result = []

        for entry in entries:
            url = entry.get("url", "")

            if config.is_regex:
                if not re.search(config.url_pattern, url):
                    continue
            else:
                if config.url_pattern not in url:
                    continue

            if config.method and entry.get("method") != config.method:
                continue

            result.append(entry)

        return result

    async def assert_custom(self, config: CustomAssertionConfig) -> bool:
        """
        Execute a custom JavaScript assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If custom assertion fails
        """
        try:
            eval_result = await self._browser.evaluate(
                context_id=self._context_id,
                script=config.script,
                args=config.args if config.args else None,
                return_value=True,
            )
            result = eval_result.get("result") if isinstance(eval_result, dict) else eval_result
        except Exception as e:
            raise AssertionError(
                config.message or f"Script execution failed: {e}"
            ) from e

        match config.operator:
            case AssertionOperator.IS_TRUTHY:
                if not bool(result):
                    raise AssertionError(
                        config.message or "Custom assertion returned falsy value",
                        expected="truthy",
                        actual=result,
                    )
            case AssertionOperator.IS_FALSY:
                if bool(result):
                    raise AssertionError(
                        config.message or "Custom assertion returned truthy value",
                        expected="falsy",
                        actual=result,
                    )
            case AssertionOperator.EQUALS:
                if result != config.expected:
                    raise AssertionError(
                        config.message or "Custom assertion value mismatch",
                        expected=config.expected,
                        actual=result,
                    )
            case AssertionOperator.CONTAINS:
                if config.expected not in str(result):
                    raise AssertionError(
                        config.message or "Custom assertion does not contain expected",
                        expected=config.expected,
                        actual=result,
                    )
            case AssertionOperator.MATCHES:
                if not re.search(str(config.expected), str(result)):
                    raise AssertionError(
                        config.message or "Custom assertion does not match pattern",
                        expected=config.expected,
                        actual=result,
                    )
            case _:
                if not bool(result):
                    raise AssertionError(
                        config.message or "Custom assertion failed",
                        actual=result,
                    )

        return True

    def assert_element_detailed(self, config: ElementAssertionConfig) -> bool:
        """
        Execute a detailed element assertion with multiple checks.

        Returns:
            True if all checks pass

        Raises:
            AssertionError: If any check fails
        """
        elements = self._page.find_element(config.selector, max_results=100)
        element_count = len(elements) if elements else 0

        if config.count is not None:
            if element_count != config.count:
                raise AssertionError(
                    config.message or "Element count mismatch",
                    expected=config.count,
                    actual=element_count,
                )

        if config.count_min is not None and element_count < config.count_min:
            raise AssertionError(
                config.message or "Too few elements",
                expected=f">= {config.count_min}",
                actual=element_count,
            )

        if config.count_max is not None and element_count > config.count_max:
            raise AssertionError(
                config.message or "Too many elements",
                expected=f"<= {config.count_max}",
                actual=element_count,
            )

        if config.text:
            actual_text = self._page.extract_text(config.selector)
            if actual_text != config.text:
                raise AssertionError(
                    config.message or "Text mismatch",
                    expected=config.text,
                    actual=actual_text,
                )

        if config.text_contains:
            actual_text = self._page.extract_text(config.selector)
            if config.text_contains not in actual_text:
                raise AssertionError(
                    config.message or "Text does not contain expected",
                    expected=config.text_contains,
                    actual=actual_text,
                )

        if config.text_matches:
            actual_text = self._page.extract_text(config.selector)
            if not re.search(config.text_matches, actual_text):
                raise AssertionError(
                    config.message or "Text does not match pattern",
                    expected=config.text_matches,
                    actual=actual_text,
                )

        if config.attribute and config.attribute_value is not None:
            actual_attr = self._page.get_attribute(config.selector, config.attribute)
            if actual_attr != config.attribute_value:
                raise AssertionError(
                    config.message or f"Attribute '{config.attribute}' mismatch",
                    expected=config.attribute_value,
                    actual=actual_attr,
                )

        if config.is_visible is not None:
            actual_visible = self._page.is_visible(config.selector)
            if actual_visible != config.is_visible:
                raise AssertionError(
                    config.message or "Visibility mismatch",
                    expected="visible" if config.is_visible else "hidden",
                    actual="visible" if actual_visible else "hidden",
                )

        if config.is_enabled is not None:
            actual_enabled = self._page.is_enabled(config.selector)
            if actual_enabled != config.is_enabled:
                raise AssertionError(
                    config.message or "Enabled state mismatch",
                    expected="enabled" if config.is_enabled else "disabled",
                    actual="enabled" if actual_enabled else "disabled",
                )

        return True

    # =========================================================================
    # ML-based Assertion Methods (no LLM required)
    # =========================================================================

    def _get_ml_engine(self) -> MLAssertionEngine:
        """Get or create ML assertion engine (lazy-loaded)."""
        if not hasattr(self, "_ml_engine"):
            from autoqa.assertions.ml_engine import MLAssertionEngine

            self._ml_engine = MLAssertionEngine()
        return self._ml_engine

    def assert_ml(self, config: MLAssertionConfig) -> bool:
        """
        Execute a unified ML-based assertion.

        Runs all specified ML assertion types in the config.

        Returns:
            True if all assertions passed

        Raises:
            AssertionError: If any ML assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        if config.ocr is not None:
            result = ml_engine.ocr.validate(
                screenshot,
                expected_text=config.ocr.expected_text,
                contains=config.ocr.contains,
                min_confidence=config.ocr.min_confidence,
                region=config.ocr.region,
            )
            if not result.passed:
                raise AssertionError(
                    config.ocr.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        if config.ui_state is not None:
            result = ml_engine.classifier.validate(
                screenshot,
                expected_state=config.ui_state.expected_state,
                min_confidence=config.ui_state.min_confidence,
            )
            if not result.passed:
                raise AssertionError(
                    config.ui_state.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        if config.color is not None:
            color_kwargs: dict[str, Any] = {
                "color_tolerance": config.color.tolerance,
                "min_percentage": config.color.min_percentage,
            }
            if config.color.dominant_color:
                color_kwargs["dominant_color"] = config.color.dominant_color
            if config.color.has_color:
                color_kwargs["has_color"] = config.color.has_color

            result = ml_engine.color_analyzer.validate(screenshot, **color_kwargs)
            if not result.passed:
                raise AssertionError(
                    config.color.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        if config.layout is not None:
            result = ml_engine.layout_analyzer.validate(
                screenshot,
                expected_count=config.layout.expected_count,
                min_count=config.layout.min_count,
                max_count=config.layout.max_count,
                alignment=config.layout.alignment,
                element_type=config.layout.element_type,
                alignment_tolerance=config.layout.alignment_tolerance,
            )
            if not result.passed:
                raise AssertionError(
                    config.layout.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        if config.icon is not None:
            result = ml_engine.icon_matcher.validate(
                screenshot,
                template_path=config.icon.template_path,
                method=config.icon.method,
                min_confidence=config.icon.min_confidence,
            )
            if not result.passed:
                raise AssertionError(
                    config.icon.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        if config.accessibility is not None:
            result = ml_engine.accessibility_checker.validate(
                screenshot,
                min_contrast_ratio=config.accessibility.min_contrast_ratio,
                wcag_level=config.accessibility.wcag_level,
                region=config.accessibility.region,
            )
            if not result.passed:
                raise AssertionError(
                    config.accessibility.message or result.message,
                    expected=result.expected,
                    actual=result.actual,
                    details=result.details,
                )

        return True

    def assert_ocr(self, config: OCRAssertionConfig) -> bool:
        """
        Execute an OCR-based text assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If OCR assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        result = ml_engine.ocr.validate(
            screenshot,
            expected_text=config.expected_text,
            contains=config.contains,
            min_confidence=config.min_confidence,
            region=config.region,
        )

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True

    def assert_ui_state(self, config: UIStateAssertionConfig) -> bool:
        """
        Execute a UI state classification assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If UI state assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        result = ml_engine.classifier.validate(
            screenshot,
            expected_state=config.expected_state,
            min_confidence=config.min_confidence,
        )

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True

    def assert_color(self, config: ColorAssertionConfig) -> bool:
        """
        Execute a color analysis assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If color assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        color_kwargs: dict[str, Any] = {
            "color_tolerance": config.tolerance,
            "min_percentage": config.min_percentage,
        }
        if config.dominant_color:
            color_kwargs["dominant_color"] = config.dominant_color
        if config.has_color:
            color_kwargs["has_color"] = config.has_color

        result = ml_engine.color_analyzer.validate(screenshot, **color_kwargs)

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True

    def assert_layout(self, config: LayoutAssertionConfig) -> bool:
        """
        Execute a layout analysis assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If layout assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        result = ml_engine.layout_analyzer.validate(
            screenshot,
            expected_count=config.expected_count,
            min_count=config.min_count,
            max_count=config.max_count,
            alignment=config.alignment,
            element_type=config.element_type,
            alignment_tolerance=config.alignment_tolerance,
        )

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True

    def assert_icon(self, config: IconAssertionConfig) -> bool:
        """
        Execute an icon/logo matching assertion.

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If icon assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        result = ml_engine.icon_matcher.validate(
            screenshot,
            template_path=config.template_path,
            method=config.method,
            min_confidence=config.min_confidence,
        )

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True

    def assert_accessibility(self, config: AccessibilityAssertionConfig) -> bool:
        """
        Execute an accessibility assertion (contrast ratio, WCAG compliance).

        Returns:
            True if assertion passed

        Raises:
            AssertionError: If accessibility assertion fails
        """
        screenshot = self._page.screenshot()
        ml_engine = self._get_ml_engine()

        result = ml_engine.accessibility_checker.validate(
            screenshot,
            min_contrast_ratio=config.min_contrast_ratio,
            wcag_level=config.wcag_level,
            region=config.region,
        )

        if not result.passed:
            raise AssertionError(
                config.message or result.message,
                expected=result.expected,
                actual=result.actual,
                details=result.details,
            )

        return True
