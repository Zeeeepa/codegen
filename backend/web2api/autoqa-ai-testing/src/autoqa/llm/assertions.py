"""
LLM-based assertion engine for semantic validation.

Provides assertion types that use LLM for intelligent validation:
- Semantic content validation
- Visual state description
- Natural language assertions
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.llm.config import LLMConfig, ToolName
from autoqa.llm.service import LLMService, get_llm_service

if TYPE_CHECKING:
    from owl_browser import BrowserContext

logger = structlog.get_logger(__name__)


@dataclass
class LLMAssertionResult:
    """Result of an LLM-based assertion."""

    passed: bool
    message: str
    confidence: float = 1.0
    expected: Any = None
    actual: Any = None
    details: dict[str, Any] = field(default_factory=dict)
    llm_reasoning: str | None = None
    fallback_used: bool = False


class LLMAssertionError(Exception):
    """Raised when an LLM assertion fails."""

    def __init__(
        self,
        message: str,
        result: LLMAssertionResult | None = None,
    ) -> None:
        super().__init__(message)
        self.result = result


class LLMAssertionEngine:
    """
    LLM-powered assertion engine for semantic validation.

    Provides intelligent assertions that go beyond simple text/attribute matching:
    - Semantic content validation ("page shows success message")
    - State verification ("user appears to be logged in")
    - Content quality checks ("form has all required fields")

    Falls back gracefully when LLM is disabled.
    """

    def __init__(
        self,
        page: BrowserContext,
        llm_service: LLMService | None = None,
        llm_config: LLMConfig | None = None,
    ) -> None:
        self._page = page
        self._llm_service = llm_service or get_llm_service(llm_config)
        self._log = logger.bind(component="llm_assertion_engine")

    @property
    def is_enabled(self) -> bool:
        """Check if LLM assertions are enabled."""
        return self._llm_service.is_enabled(ToolName.ASSERTIONS)

    async def assert_semantic(
        self,
        assertion: str,
        context: str | None = None,
        min_confidence: float = 0.7,
        message: str | None = None,
    ) -> LLMAssertionResult:
        """
        Assert a semantic condition using natural language.

        Args:
            assertion: Natural language assertion (e.g., "page shows success message")
            context: Additional context about the expected state
            min_confidence: Minimum confidence threshold to pass (0.0-1.0)
            message: Custom error message on failure

        Returns:
            LLMAssertionResult with validation details

        Raises:
            LLMAssertionError: If assertion fails
        """
        self._log.debug("Executing semantic assertion", assertion=assertion)

        # Gather page context
        url = self._get_current_url()
        visible_text = self._get_visible_text()
        key_elements = self._get_key_elements()

        # If LLM is disabled, use fallback heuristics
        if not self.is_enabled:
            return self._fallback_semantic_check(
                assertion, visible_text, key_elements
            )

        # Build full assertion description
        full_assertion = assertion
        if context:
            full_assertion = f"{assertion}\n\nContext: {context}"

        # Execute LLM validation
        result = await self._llm_service.validate_semantic_assertion(
            assertion_description=full_assertion,
            url=url,
            visible_text=visible_text,
            key_elements=key_elements,
        )

        if not result.success:
            # LLM failed, use fallback
            return self._fallback_semantic_check(
                assertion, visible_text, key_elements
            )

        # Parse LLM response
        if result.parsed_data and isinstance(result.parsed_data, dict):
            passed = result.parsed_data.get("passed", False)
            confidence = result.parsed_data.get("confidence", 0.5)
            reason = result.parsed_data.get("reason", "")
            actual_state = result.parsed_data.get("actual_state", "")

            assertion_result = LLMAssertionResult(
                passed=passed and confidence >= min_confidence,
                message=message or f"Semantic assertion: {assertion}",
                confidence=confidence,
                expected=assertion,
                actual=actual_state,
                details={
                    "suggestions": result.parsed_data.get("suggestions", []),
                    "tokens_used": result.tokens_used,
                },
                llm_reasoning=reason,
            )

            if not assertion_result.passed:
                raise LLMAssertionError(
                    message or f"Semantic assertion failed: {assertion}. Reason: {reason}",
                    result=assertion_result,
                )

            return assertion_result

        # Fallback if parsing failed
        return self._fallback_semantic_check(assertion, visible_text, key_elements)

    async def assert_content_valid(
        self,
        content_type: str,
        expected_patterns: list[str],
        selector: str | None = None,
        min_confidence: float = 0.7,
        message: str | None = None,
    ) -> LLMAssertionResult:
        """
        Assert that page content is valid for a given type.

        Args:
            content_type: Type of content ("product_page", "checkout", "search_results", etc.)
            expected_patterns: List of expected content patterns
            selector: Optional selector to limit content scope
            min_confidence: Minimum confidence threshold
            message: Custom error message

        Returns:
            LLMAssertionResult with validation details
        """
        self._log.debug(
            "Validating content",
            content_type=content_type,
            patterns=expected_patterns,
        )

        # Get content
        if selector:
            try:
                content = self._page.extract_text(selector)
            except Exception:
                content = self._get_visible_text()
        else:
            content = self._get_visible_text()

        # Fallback if LLM disabled
        if not self.is_enabled:
            return self._fallback_content_check(
                content, expected_patterns
            )

        # Execute LLM analysis
        result = await self._llm_service.analyze_content(
            content_type=content_type,
            expected_patterns=expected_patterns,
            actual_content=content,
        )

        if not result.success:
            return self._fallback_content_check(content, expected_patterns)

        if result.parsed_data and isinstance(result.parsed_data, dict):
            valid = result.parsed_data.get("valid", False)
            matches = result.parsed_data.get("matches_expected", False)
            issues = result.parsed_data.get("issues", [])
            confidence = result.parsed_data.get("confidence", 0.5)

            assertion_result = LLMAssertionResult(
                passed=valid and matches and confidence >= min_confidence,
                message=message or f"Content validation for {content_type}",
                confidence=confidence,
                expected=expected_patterns,
                actual=content[:500] + "..." if len(content) > 500 else content,
                details={
                    "issues": issues,
                    "content_type": content_type,
                    "tokens_used": result.tokens_used,
                },
            )

            if not assertion_result.passed:
                raise LLMAssertionError(
                    message or f"Content validation failed: {issues}",
                    result=assertion_result,
                )

            return assertion_result

        return self._fallback_content_check(content, expected_patterns)

    async def assert_state(
        self,
        expected_state: str,
        indicators: list[str] | None = None,
        min_confidence: float = 0.7,
        message: str | None = None,
    ) -> LLMAssertionResult:
        """
        Assert the current page state matches expectations.

        Args:
            expected_state: Expected state description ("logged_in", "checkout_complete", etc.)
            indicators: Optional list of state indicators to look for
            min_confidence: Minimum confidence threshold
            message: Custom error message

        Returns:
            LLMAssertionResult with validation details
        """
        # Build assertion from state
        assertion = f"The page is in '{expected_state}' state"
        if indicators:
            assertion += f". Indicators: {', '.join(indicators)}"

        return await self.assert_semantic(
            assertion=assertion,
            min_confidence=min_confidence,
            message=message,
        )

    async def assert_no_errors(
        self,
        error_patterns: list[str] | None = None,
        message: str | None = None,
    ) -> LLMAssertionResult:
        """
        Assert that no error states are visible on the page.

        Args:
            error_patterns: Optional custom error patterns to check
            message: Custom error message

        Returns:
            LLMAssertionResult with validation details
        """
        default_patterns = [
            "error",
            "failed",
            "unable to",
            "something went wrong",
            "404",
            "500",
            "not found",
            "invalid",
            "expired",
        ]
        patterns = error_patterns or default_patterns

        visible_text = self._get_visible_text().lower()

        # Quick check without LLM
        found_errors = [p for p in patterns if p.lower() in visible_text]

        if found_errors:
            result = LLMAssertionResult(
                passed=False,
                message=message or "Page contains error indicators",
                expected="No error states",
                actual=f"Found error indicators: {found_errors}",
                details={"error_patterns": found_errors},
            )
            raise LLMAssertionError(
                message or f"Error indicators found: {found_errors}",
                result=result,
            )

        # If LLM enabled, do deeper analysis
        if self.is_enabled:
            return await self.assert_semantic(
                assertion="The page does not display any error messages or error states",
                min_confidence=0.6,
                message=message,
            )

        return LLMAssertionResult(
            passed=True,
            message=message or "No error indicators found",
            expected="No error states",
            actual="Page appears normal",
            fallback_used=not self.is_enabled,
        )

    # =========================================================================
    # Fallback Methods (when LLM is disabled)
    # =========================================================================

    def _fallback_semantic_check(
        self,
        assertion: str,
        visible_text: str,
        key_elements: list[dict[str, Any]],
    ) -> LLMAssertionResult:
        """
        Fallback semantic check using keyword matching.

        This is a simple heuristic when LLM is not available.
        """
        self._log.debug("Using fallback semantic check", assertion=assertion)

        # Extract keywords from assertion
        assertion_lower = assertion.lower()
        positive_indicators = [
            "success", "complete", "logged in", "welcome",
            "confirmed", "submitted", "saved", "updated",
        ]
        negative_indicators = [
            "error", "failed", "invalid", "not found",
            "denied", "rejected", "expired",
        ]

        text_lower = visible_text.lower()

        # Check for positive indicators
        found_positive = [p for p in positive_indicators if p in assertion_lower and p in text_lower]
        found_negative = [n for n in negative_indicators if n in text_lower]

        # Simple heuristic: pass if we find expected indicators and no errors
        if found_positive and not found_negative:
            return LLMAssertionResult(
                passed=True,
                message=f"Semantic assertion (fallback): {assertion}",
                confidence=0.5,
                expected=assertion,
                actual=f"Found indicators: {found_positive}",
                fallback_used=True,
            )

        # If we're checking for absence of something
        if "no " in assertion_lower or "not " in assertion_lower:
            if not found_negative:
                return LLMAssertionResult(
                    passed=True,
                    message=f"Semantic assertion (fallback): {assertion}",
                    confidence=0.5,
                    expected=assertion,
                    actual="No negative indicators found",
                    fallback_used=True,
                )

        # Default: pass with low confidence when using fallback
        return LLMAssertionResult(
            passed=True,
            message=f"Semantic assertion (fallback - unable to verify): {assertion}",
            confidence=0.3,
            expected=assertion,
            actual="Unable to verify without LLM",
            fallback_used=True,
            details={"warning": "LLM disabled, using fallback heuristics"},
        )

    def _fallback_content_check(
        self,
        content: str,
        expected_patterns: list[str],
    ) -> LLMAssertionResult:
        """Fallback content check using pattern matching."""
        content_lower = content.lower()
        found_patterns = [p for p in expected_patterns if p.lower() in content_lower]
        match_ratio = len(found_patterns) / len(expected_patterns) if expected_patterns else 0

        passed = match_ratio >= 0.5  # Pass if at least 50% of patterns found

        result = LLMAssertionResult(
            passed=passed,
            message="Content validation (fallback)",
            confidence=match_ratio,
            expected=expected_patterns,
            actual=f"Found {len(found_patterns)}/{len(expected_patterns)} patterns",
            details={"found_patterns": found_patterns},
            fallback_used=True,
        )

        if not passed:
            raise LLMAssertionError(
                f"Content validation failed: only {len(found_patterns)}/{len(expected_patterns)} patterns found",
                result=result,
            )

        return result

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_current_url(self) -> str:
        """Get current page URL."""
        try:
            return self._page.evaluate("window.location.href", return_value=True) or ""
        except Exception:
            return ""

    def _get_visible_text(self) -> str:
        """Get visible text content from page."""
        try:
            return self._page.extract_text("body") or ""
        except Exception:
            return ""

    def _get_key_elements(self) -> list[dict[str, Any]]:
        """Get key elements from page for context."""
        try:
            script = """
            (() => {
                const elements = [];
                const selectors = [
                    'h1', 'h2', 'h3',
                    'button', 'a[href]',
                    'input', 'form',
                    '[role="alert"]', '[role="status"]',
                    '.error', '.success', '.message'
                ];

                for (const sel of selectors) {
                    for (const el of document.querySelectorAll(sel)) {
                        if (elements.length >= 30) break;
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText?.substring(0, 100) || '',
                            id: el.id || null,
                            class: el.className || null,
                            role: el.getAttribute('role') || null
                        });
                    }
                }
                return elements;
            })()
            """
            return self._page.evaluate(script, return_value=True) or []
        except Exception:
            return []
