"""
Self-healing test engine for automatic recovery from UI changes.

Uses deterministic strategies (no AI/LLM dependency) to find alternative selectors.
Strategies: text matching, fuzzy attributes, XPath fallbacks, DOM structure analysis.

SDK v2 Notes:
- heal_selector_async method added for async browser operations
- Uses OwlBrowser and context_id pattern
- Browser methods like is_visible require await
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from owl_browser import OwlBrowser

logger = structlog.get_logger(__name__)


class HealingStrategy(StrEnum):
    """Strategies for healing broken selectors (deterministic, no AI)."""

    TEXT_MATCH = "text_match"
    ATTRIBUTE_FUZZY = "attribute_fuzzy"
    ID_FALLBACK = "id_fallback"
    NAME_FALLBACK = "name_fallback"
    PLACEHOLDER_FALLBACK = "placeholder_fallback"
    DATA_TESTID = "data_testid"
    ARIA_LABEL = "aria_label"
    XPATH_FALLBACK = "xpath_fallback"
    DOM_STRUCTURE = "dom_structure"
    CACHED_HISTORY = "cached_history"


@dataclass
class SelectorCandidate:
    """A candidate selector found during healing."""

    selector: str
    strategy: HealingStrategy
    confidence: float
    element_text: str | None = None
    element_tag: str | None = None
    bounding_box: dict[str, float] | None = None


@dataclass
class HealingResult:
    """Result of a healing attempt."""

    success: bool
    original_selector: str
    healed_selector: str | None = None
    strategy_used: HealingStrategy | None = None
    confidence: float = 0.0
    candidates_evaluated: int = 0
    healing_time_ms: int = 0
    error: str | None = None


@dataclass
class SelectorHistory:
    """Historical data for a selector."""

    original_selector: str
    last_working_selector: str
    healed_selectors: list[str] = field(default_factory=list)
    failure_count: int = 0
    last_healed_at: float | None = None
    element_signature: dict[str, Any] | None = None


class SelfHealingEngine:
    """
    Self-healing engine that automatically adapts to UI changes.

    Uses deterministic strategies (NO AI/LLM dependency) to find elements:
    1. Cached history from previous successful healings
    2. Text content matching (contains, exact)
    3. Fuzzy attribute matching (id, name, class variants)
    4. Common fallback patterns (data-testid, aria-label, placeholder)
    5. XPath alternatives
    6. DOM structure analysis
    """

    MIN_CONFIDENCE_THRESHOLD = 0.6
    MAX_CANDIDATES = 15

    def __init__(
        self,
        history_path: str | Path | None = None,
        min_confidence: float = 0.6,
        enable_learning: bool = True,
    ) -> None:
        self._history_path = Path(history_path) if history_path else None
        self._min_confidence = min_confidence
        self._enable_learning = enable_learning
        self._selector_history: dict[str, SelectorHistory] = {}
        self._selector_cache: dict[str, str] = {}
        self._log = logger.bind(component="self_healing")

        if self._history_path and self._history_path.exists():
            self._load_history()

    def heal_selector(
        self,
        page: BrowserContext,
        original_selector: str,
        action_context: str | None = None,
        element_description: str | None = None,
    ) -> HealingResult:
        """
        Attempt to heal a broken selector using deterministic strategies.

        Args:
            page: Browser context to search in
            original_selector: The selector that failed
            action_context: Context about what action was being performed
            element_description: Text hint for the element (not AI-based)

        Returns:
            HealingResult with success status and healed selector if found
        """
        start_time = time.monotonic()
        self._log.info(
            "Starting selector healing (deterministic)",
            original=original_selector,
            context=action_context,
        )

        # Strategy 1: Check cached successful selector
        if original_selector in self._selector_cache:
            cached = self._selector_cache[original_selector]
            if self._try_selector(page, cached):
                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=cached,
                    strategy_used=HealingStrategy.CACHED_HISTORY,
                    confidence=0.98,
                    healing_time_ms=int((time.monotonic() - start_time) * 1000),
                )

        # Strategy 2: Check history for last working selector
        history = self._selector_history.get(original_selector)
        if history and history.last_working_selector != original_selector:
            if self._try_selector(page, history.last_working_selector):
                self._selector_cache[original_selector] = history.last_working_selector
                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=history.last_working_selector,
                    strategy_used=HealingStrategy.DOM_STRUCTURE,
                    confidence=0.95,
                    healing_time_ms=int((time.monotonic() - start_time) * 1000),
                )

        candidates: list[SelectorCandidate] = []

        # Strategy 3: Common ID/name/data-testid fallbacks from selector parsing
        common_fallbacks = self._find_by_common_patterns(page, original_selector)
        candidates.extend(common_fallbacks)

        # Strategy 4: Text content matching (from selector or description)
        text_hint = element_description or self._extract_text_hint(original_selector)
        if text_hint:
            text_candidates = self._find_by_text_match(page, text_hint)
            candidates.extend(text_candidates)

        # Strategy 5: Fuzzy attribute matching
        attr_candidates = self._find_by_attribute_fuzzy(page, original_selector)
        candidates.extend(attr_candidates)

        # Strategy 6: XPath alternatives
        xpath_candidates = self._find_by_xpath_fallback(page, original_selector)
        candidates.extend(xpath_candidates)

        # Strategy 7: CSS selector variations
        css_candidates = self._find_by_css_variations(page, original_selector)
        candidates.extend(css_candidates)

        # Sort by confidence and limit
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        candidates = candidates[: self.MAX_CANDIDATES]

        for candidate in candidates:
            if candidate.confidence < self._min_confidence:
                continue

            if self._try_selector(page, candidate.selector):
                self._update_history(
                    original_selector,
                    candidate.selector,
                    candidate,
                )
                self._selector_cache[original_selector] = candidate.selector

                healing_time = int((time.monotonic() - start_time) * 1000)
                self._log.info(
                    "Selector healed successfully",
                    original=original_selector,
                    healed=candidate.selector,
                    strategy=candidate.strategy,
                    confidence=candidate.confidence,
                    time_ms=healing_time,
                )

                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=candidate.selector,
                    strategy_used=candidate.strategy,
                    confidence=candidate.confidence,
                    candidates_evaluated=len(candidates),
                    healing_time_ms=healing_time,
                )

        healing_time = int((time.monotonic() - start_time) * 1000)
        self._log.warning(
            "Selector healing failed",
            original=original_selector,
            candidates_tried=len(candidates),
            time_ms=healing_time,
        )

        if history:
            history.failure_count += 1

        return HealingResult(
            success=False,
            original_selector=original_selector,
            candidates_evaluated=len(candidates),
            healing_time_ms=healing_time,
            error="No suitable replacement selector found",
        )

    async def heal_selector_async(
        self,
        browser: OwlBrowser,
        context_id: str,
        original_selector: str,
        action_context: str | None = None,
        element_description: str | None = None,
    ) -> HealingResult:
        """
        Attempt to heal a broken selector using deterministic strategies (SDK v2 async).

        Args:
            browser: OwlBrowser instance
            context_id: Browser context ID
            original_selector: The selector that failed
            action_context: Context about what action was being performed
            element_description: Text hint for the element (not AI-based)

        Returns:
            HealingResult with success status and healed selector if found
        """
        start_time = time.monotonic()
        self._log.info(
            "Starting selector healing (deterministic, async)",
            original=original_selector,
            context=action_context,
        )

        # Strategy 1: Check cached successful selector
        if original_selector in self._selector_cache:
            cached = self._selector_cache[original_selector]
            if await self._try_selector_async(browser, context_id, cached):
                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=cached,
                    strategy_used=HealingStrategy.CACHED_HISTORY,
                    confidence=0.98,
                    healing_time_ms=int((time.monotonic() - start_time) * 1000),
                )

        # Strategy 2: Check history for last working selector
        history = self._selector_history.get(original_selector)
        if history and history.last_working_selector != original_selector:
            if await self._try_selector_async(browser, context_id, history.last_working_selector):
                self._selector_cache[original_selector] = history.last_working_selector
                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=history.last_working_selector,
                    strategy_used=HealingStrategy.DOM_STRUCTURE,
                    confidence=0.95,
                    healing_time_ms=int((time.monotonic() - start_time) * 1000),
                )

        candidates: list[SelectorCandidate] = []

        # Strategy 3: Common ID/name/data-testid fallbacks from selector parsing
        common_fallbacks = await self._find_by_common_patterns_async(browser, context_id, original_selector)
        candidates.extend(common_fallbacks)

        # Strategy 4: Text content matching (from selector or description)
        text_hint = element_description or self._extract_text_hint(original_selector)
        if text_hint:
            text_candidates = await self._find_by_text_match_async(browser, context_id, text_hint)
            candidates.extend(text_candidates)

        # Strategy 5: Fuzzy attribute matching
        attr_candidates = await self._find_by_attribute_fuzzy_async(browser, context_id, original_selector)
        candidates.extend(attr_candidates)

        # Strategy 6: XPath alternatives
        xpath_candidates = await self._find_by_xpath_fallback_async(browser, context_id, original_selector)
        candidates.extend(xpath_candidates)

        # Strategy 7: CSS selector variations
        css_candidates = await self._find_by_css_variations_async(browser, context_id, original_selector)
        candidates.extend(css_candidates)

        # Sort by confidence and limit
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        candidates = candidates[: self.MAX_CANDIDATES]

        for candidate in candidates:
            if candidate.confidence < self._min_confidence:
                continue

            if await self._try_selector_async(browser, context_id, candidate.selector):
                self._update_history(
                    original_selector,
                    candidate.selector,
                    candidate,
                )
                self._selector_cache[original_selector] = candidate.selector

                healing_time = int((time.monotonic() - start_time) * 1000)
                self._log.info(
                    "Selector healed successfully",
                    original=original_selector,
                    healed=candidate.selector,
                    strategy=candidate.strategy,
                    confidence=candidate.confidence,
                    time_ms=healing_time,
                )

                return HealingResult(
                    success=True,
                    original_selector=original_selector,
                    healed_selector=candidate.selector,
                    strategy_used=candidate.strategy,
                    confidence=candidate.confidence,
                    candidates_evaluated=len(candidates),
                    healing_time_ms=healing_time,
                )

        healing_time = int((time.monotonic() - start_time) * 1000)
        self._log.warning(
            "Selector healing failed",
            original=original_selector,
            candidates_tried=len(candidates),
            time_ms=healing_time,
        )

        if history:
            history.failure_count += 1

        return HealingResult(
            success=False,
            original_selector=original_selector,
            candidates_evaluated=len(candidates),
            healing_time_ms=healing_time,
            error="No suitable replacement selector found",
        )

    async def _try_selector_async(self, browser: OwlBrowser, context_id: str, selector: str) -> bool:
        """Test if a selector finds an element (async version)."""
        try:
            result = await browser.is_visible(context_id=context_id, selector=selector)
            return result.get("visible", False) if isinstance(result, dict) else bool(result)
        except Exception:
            return False

    async def _find_by_common_patterns_async(
        self, browser: OwlBrowser, context_id: str, original_selector: str
    ) -> list[SelectorCandidate]:
        """Find elements using common selector patterns (no AI, async version)."""
        candidates: list[SelectorCandidate] = []
        attrs = self._parse_selector_attributes(original_selector)

        patterns_to_try: list[tuple[str, HealingStrategy, float]] = []

        if "id" in attrs:
            element_id = attrs["id"]
            patterns_to_try.extend([
                (f"#{element_id}", HealingStrategy.ID_FALLBACK, 0.95),
                (f"[id='{element_id}']", HealingStrategy.ID_FALLBACK, 0.94),
                (f"[id*='{element_id}']", HealingStrategy.ID_FALLBACK, 0.80),
            ])

        if "name" in attrs:
            name = attrs["name"]
            patterns_to_try.extend([
                (f"[name='{name}']", HealingStrategy.NAME_FALLBACK, 0.90),
                (f"[name*='{name}']", HealingStrategy.NAME_FALLBACK, 0.75),
            ])

        if "data-testid" in attrs:
            testid = attrs["data-testid"]
            patterns_to_try.extend([
                (f"[data-testid='{testid}']", HealingStrategy.DATA_TESTID, 0.92),
                (f"[data-testid*='{testid}']", HealingStrategy.DATA_TESTID, 0.78),
            ])

        if "aria-label" in attrs:
            label = attrs["aria-label"]
            patterns_to_try.extend([
                (f"[aria-label='{label}']", HealingStrategy.ARIA_LABEL, 0.88),
                (f"[aria-label*='{label}']", HealingStrategy.ARIA_LABEL, 0.72),
            ])

        if "placeholder" in attrs:
            placeholder = attrs["placeholder"]
            patterns_to_try.extend([
                (f"[placeholder='{placeholder}']", HealingStrategy.PLACEHOLDER_FALLBACK, 0.85),
                (f"[placeholder*='{placeholder}']", HealingStrategy.PLACEHOLDER_FALLBACK, 0.70),
            ])

        for selector, strategy, confidence in patterns_to_try:
            if selector != original_selector and await self._try_selector_async(browser, context_id, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=strategy,
                        confidence=confidence,
                    )
                )

        return candidates

    async def _find_by_text_match_async(
        self, browser: OwlBrowser, context_id: str, text_hint: str
    ) -> list[SelectorCandidate]:
        """Find elements by text content matching (deterministic, async)."""
        candidates: list[SelectorCandidate] = []

        safe_hint = text_hint.replace("'", "\\'")
        normalized_hint = text_hint.lower().replace(" ", "-").replace("_", "-")

        selectors_to_try: list[tuple[str, float]] = [
            (f"//*[normalize-space(text())='{safe_hint}']", 0.90),
            (f"//*[contains(text(), '{safe_hint}')]", 0.82),
            (f"[data-testid*='{normalized_hint}']", 0.80),
            (f"[aria-label*='{text_hint}']", 0.79),
            (f"[title*='{text_hint}']", 0.75),
            (f"[placeholder*='{text_hint}']", 0.74),
            (f"[value='{text_hint}']", 0.82),
        ]

        for selector, confidence in selectors_to_try:
            if await self._try_selector_async(browser, context_id, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=HealingStrategy.TEXT_MATCH,
                        confidence=confidence,
                        element_text=text_hint,
                    )
                )

        return candidates

    async def _find_by_attribute_fuzzy_async(
        self, browser: OwlBrowser, context_id: str, original_selector: str
    ) -> list[SelectorCandidate]:
        """Find elements by fuzzy attribute matching (async)."""
        candidates: list[SelectorCandidate] = []

        attributes = self._parse_selector_attributes(original_selector)
        if not attributes:
            return candidates

        for attr_name, attr_value in attributes.items():
            fuzzy_selectors = [
                f"[{attr_name}='{attr_value}']",
                f"[{attr_name}*='{attr_value}']",
                f"[{attr_name}^='{attr_value[:len(attr_value)//2]}']" if len(attr_value) > 4 else None,
            ]

            for selector in filter(None, fuzzy_selectors):
                if selector != original_selector and await self._try_selector_async(browser, context_id, selector):
                    confidence = 0.75 if "*=" in selector else 0.85
                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            strategy=HealingStrategy.ATTRIBUTE_FUZZY,
                            confidence=confidence,
                        )
                    )

        return candidates

    async def _find_by_xpath_fallback_async(
        self, browser: OwlBrowser, context_id: str, original_selector: str
    ) -> list[SelectorCandidate]:
        """Generate XPath fallback selectors (async)."""
        candidates: list[SelectorCandidate] = []

        if original_selector.startswith("//") or original_selector.startswith("/"):
            return candidates

        if original_selector.startswith("#"):
            element_id = original_selector[1:].split("[")[0].split(".")[0]
            xpath = f"//*[@id='{element_id}']"
            if await self._try_selector_async(browser, context_id, xpath):
                candidates.append(
                    SelectorCandidate(
                        selector=xpath,
                        strategy=HealingStrategy.XPATH_FALLBACK,
                        confidence=0.9,
                    )
                )

        if "." in original_selector:
            classes = original_selector.replace("#", " ").replace("[", " ").split(".")
            classes = [c.strip() for c in classes if c.strip() and not c.startswith("=")]
            if classes:
                xpath = f"//*[contains(@class, '{classes[0]}')]"
                if await self._try_selector_async(browser, context_id, xpath):
                    candidates.append(
                        SelectorCandidate(
                            selector=xpath,
                            strategy=HealingStrategy.XPATH_FALLBACK,
                            confidence=0.7,
                        )
                    )

        return candidates

    async def _find_by_css_variations_async(
        self, browser: OwlBrowser, context_id: str, original_selector: str
    ) -> list[SelectorCandidate]:
        """Generate CSS selector variations (async)."""
        candidates: list[SelectorCandidate] = []
        attrs = self._parse_selector_attributes(original_selector)

        tag_match = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", original_selector)
        tag = tag_match.group(1) if tag_match else "*"

        variations: list[tuple[str, float]] = []

        if "class" in attrs:
            classes = attrs["class"].split()
            for cls in classes[:3]:
                variations.extend([
                    (f"{tag}.{cls}", 0.75),
                    (f".{cls}", 0.70),
                    (f"[class*='{cls}']", 0.65),
                ])

        if "id" in attrs:
            element_id = attrs["id"]
            if len(element_id) > 5:
                partial = element_id[:len(element_id)//2]
                variations.append((f"[id^='{partial}']", 0.72))

        for attr in ["type", "role", "data-type"]:
            if attr in attrs:
                variations.append((f"{tag}[{attr}='{attrs[attr]}']", 0.68))

        for selector, confidence in variations:
            if selector != original_selector and await self._try_selector_async(browser, context_id, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=HealingStrategy.ATTRIBUTE_FUZZY,
                        confidence=confidence,
                    )
                )

        return candidates

    def _find_by_common_patterns(
        self, page: OwlBrowser, original_selector: str
    ) -> list[SelectorCandidate]:
        """Find elements using common selector patterns (no AI)."""
        candidates: list[SelectorCandidate] = []
        attrs = self._parse_selector_attributes(original_selector)

        # Try variations based on extracted attributes
        patterns_to_try: list[tuple[str, HealingStrategy, float]] = []

        # ID-based fallbacks
        if "id" in attrs:
            element_id = attrs["id"]
            patterns_to_try.extend([
                (f"#{element_id}", HealingStrategy.ID_FALLBACK, 0.95),
                (f"[id='{element_id}']", HealingStrategy.ID_FALLBACK, 0.94),
                (f"[id*='{element_id}']", HealingStrategy.ID_FALLBACK, 0.80),
            ])

        # Name-based fallbacks
        if "name" in attrs:
            name = attrs["name"]
            patterns_to_try.extend([
                (f"[name='{name}']", HealingStrategy.NAME_FALLBACK, 0.90),
                (f"[name*='{name}']", HealingStrategy.NAME_FALLBACK, 0.75),
            ])

        # data-testid fallbacks (common testing convention)
        if "data-testid" in attrs:
            testid = attrs["data-testid"]
            patterns_to_try.extend([
                (f"[data-testid='{testid}']", HealingStrategy.DATA_TESTID, 0.92),
                (f"[data-testid*='{testid}']", HealingStrategy.DATA_TESTID, 0.78),
            ])

        # aria-label fallbacks
        if "aria-label" in attrs:
            label = attrs["aria-label"]
            patterns_to_try.extend([
                (f"[aria-label='{label}']", HealingStrategy.ARIA_LABEL, 0.88),
                (f"[aria-label*='{label}']", HealingStrategy.ARIA_LABEL, 0.72),
            ])

        # Placeholder fallbacks (for inputs)
        if "placeholder" in attrs:
            placeholder = attrs["placeholder"]
            patterns_to_try.extend([
                (f"[placeholder='{placeholder}']", HealingStrategy.PLACEHOLDER_FALLBACK, 0.85),
                (f"[placeholder*='{placeholder}']", HealingStrategy.PLACEHOLDER_FALLBACK, 0.70),
            ])

        # Try each pattern
        for selector, strategy, confidence in patterns_to_try:
            if selector != original_selector and self._try_selector(page, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=strategy,
                        confidence=confidence,
                    )
                )

        return candidates

    def _find_by_css_variations(
        self, page: BrowserContext, original_selector: str
    ) -> list[SelectorCandidate]:
        """Generate CSS selector variations."""
        candidates: list[SelectorCandidate] = []
        attrs = self._parse_selector_attributes(original_selector)

        # Extract tag name if present
        tag_match = re.match(r"^([a-zA-Z][a-zA-Z0-9]*)", original_selector)
        tag = tag_match.group(1) if tag_match else "*"

        variations: list[tuple[str, float]] = []

        # Class-based variations
        if "class" in attrs:
            classes = attrs["class"].split()
            for cls in classes[:3]:  # Limit to first 3 classes
                variations.extend([
                    (f"{tag}.{cls}", 0.75),
                    (f".{cls}", 0.70),
                    (f"[class*='{cls}']", 0.65),
                ])

        # ID partial match
        if "id" in attrs:
            element_id = attrs["id"]
            # Try partial ID (common for generated IDs)
            if len(element_id) > 5:
                partial = element_id[:len(element_id)//2]
                variations.append((f"[id^='{partial}']", 0.72))

        # Combine tag + common attributes
        for attr in ["type", "role", "data-type"]:
            if attr in attrs:
                variations.append((f"{tag}[{attr}='{attrs[attr]}']", 0.68))

        for selector, confidence in variations:
            if selector != original_selector and self._try_selector(page, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=HealingStrategy.ATTRIBUTE_FUZZY,
                        confidence=confidence,
                    )
                )

        return candidates

    def _find_by_text_match(
        self, page: BrowserContext, text_hint: str
    ) -> list[SelectorCandidate]:
        """Find elements by text content matching (deterministic)."""
        candidates: list[SelectorCandidate] = []

        # Escape special characters for XPath
        safe_hint = text_hint.replace("'", "\\'")
        normalized_hint = text_hint.lower().replace(" ", "-").replace("_", "-")

        selectors_to_try: list[tuple[str, float]] = [
            # XPath text matching
            (f"//*[normalize-space(text())='{safe_hint}']", 0.90),
            (f"//*[contains(text(), '{safe_hint}')]", 0.82),
            (f"//*[contains(normalize-space(), '{safe_hint}')]", 0.78),
            # Button/link specific
            (f"button[contains(., '{safe_hint}')]", 0.85),
            (f"a[contains(., '{safe_hint}')]", 0.83),
            # Common attributes containing text
            (f"[data-testid*='{normalized_hint}']", 0.80),
            (f"[aria-label*='{text_hint}']", 0.79),
            (f"[title*='{text_hint}']", 0.75),
            (f"[placeholder*='{text_hint}']", 0.74),
            (f"[value='{text_hint}']", 0.82),
            # Label association
            (f"label:contains('{text_hint}') + input", 0.76),
            (f"label:contains('{text_hint}') + select", 0.76),
        ]

        for selector, confidence in selectors_to_try:
            if self._try_selector(page, selector):
                candidates.append(
                    SelectorCandidate(
                        selector=selector,
                        strategy=HealingStrategy.TEXT_MATCH,
                        confidence=confidence,
                        element_text=text_hint,
                    )
                )

        return candidates

    def _find_by_attribute_fuzzy(
        self, page: BrowserContext, original_selector: str
    ) -> list[SelectorCandidate]:
        """Find elements by fuzzy attribute matching."""
        candidates: list[SelectorCandidate] = []

        attributes = self._parse_selector_attributes(original_selector)
        if not attributes:
            return candidates

        for attr_name, attr_value in attributes.items():
            fuzzy_selectors = [
                f"[{attr_name}='{attr_value}']",
                f"[{attr_name}*='{attr_value}']",
                f"[{attr_name}^='{attr_value[:len(attr_value)//2]}']" if len(attr_value) > 4 else None,
            ]

            for selector in filter(None, fuzzy_selectors):
                if selector != original_selector and self._try_selector(page, selector):
                    confidence = 0.75 if "*=" in selector else 0.85
                    candidates.append(
                        SelectorCandidate(
                            selector=selector,
                            strategy=HealingStrategy.ATTRIBUTE_FUZZY,
                            confidence=confidence,
                        )
                    )

        return candidates

    def _find_by_xpath_fallback(
        self, page: BrowserContext, original_selector: str
    ) -> list[SelectorCandidate]:
        """Generate XPath fallback selectors."""
        candidates: list[SelectorCandidate] = []

        if original_selector.startswith("//") or original_selector.startswith("/"):
            return candidates

        if original_selector.startswith("#"):
            element_id = original_selector[1:].split("[")[0].split(".")[0]
            xpath = f"//*[@id='{element_id}']"
            if self._try_selector(page, xpath):
                candidates.append(
                    SelectorCandidate(
                        selector=xpath,
                        strategy=HealingStrategy.XPATH_FALLBACK,
                        confidence=0.9,
                    )
                )

        if "." in original_selector:
            classes = original_selector.replace("#", " ").replace("[", " ").split(".")
            classes = [c.strip() for c in classes if c.strip() and not c.startswith("=")]
            if classes:
                xpath = f"//*[contains(@class, '{classes[0]}')]"
                if self._try_selector(page, xpath):
                    candidates.append(
                        SelectorCandidate(
                            selector=xpath,
                            strategy=HealingStrategy.XPATH_FALLBACK,
                            confidence=0.7,
                        )
                    )

        return candidates

    def _try_selector(self, page: BrowserContext, selector: str) -> bool:
        """Test if a selector finds an element."""
        try:
            visible = page.is_visible(selector)
            return visible
        except Exception:
            return False

    def _extract_text_hint(self, selector: str) -> str | None:
        """Extract potential text hint from selector."""
        import re

        patterns = [
            r"contains\(text\(\),\s*['\"]([^'\"]+)['\"]\)",
            r"contains\(.,\s*['\"]([^'\"]+)['\"]\)",
            r"\[aria-label[*~^$]?=['\"]([^'\"]+)['\"]\]",
            r"\[title[*~^$]?=['\"]([^'\"]+)['\"]\]",
            r"\[placeholder[*~^$]?=['\"]([^'\"]+)['\"]\]",
        ]

        for pattern in patterns:
            match = re.search(pattern, selector, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _parse_selector_attributes(self, selector: str) -> dict[str, str]:
        """Parse attributes from a CSS selector."""
        import re

        attributes: dict[str, str] = {}

        attr_pattern = r"\[([a-zA-Z-]+)([*~^$|]?=)['\"]([^'\"]+)['\"]\]"
        for match in re.finditer(attr_pattern, selector):
            attr_name = match.group(1)
            attr_value = match.group(3)
            attributes[attr_name] = attr_value

        id_match = re.search(r"#([a-zA-Z0-9_-]+)", selector)
        if id_match:
            attributes["id"] = id_match.group(1)

        class_matches = re.findall(r"\.([a-zA-Z0-9_-]+)", selector)
        if class_matches:
            attributes["class"] = " ".join(class_matches)

        return attributes

    def _update_history(
        self,
        original_selector: str,
        healed_selector: str,
        candidate: SelectorCandidate,
    ) -> None:
        """Update selector history after successful healing."""
        if not self._enable_learning:
            return

        if original_selector not in self._selector_history:
            self._selector_history[original_selector] = SelectorHistory(
                original_selector=original_selector,
                last_working_selector=healed_selector,
            )

        history = self._selector_history[original_selector]
        history.last_working_selector = healed_selector
        history.last_healed_at = time.time()

        if healed_selector not in history.healed_selectors:
            history.healed_selectors.append(healed_selector)

        if candidate.bounding_box:
            history.element_signature = {
                "bounding_box": candidate.bounding_box,
                "tag": candidate.element_tag,
                "text": candidate.element_text,
            }

        self._save_history()

    def capture_element_signature(
        self, page: BrowserContext, selector: str
    ) -> dict[str, Any] | None:
        """Capture element signature for future healing."""
        try:
            bbox = page.get_bounding_box(selector)
            text = None
            try:
                text = page.extract_text(selector)
            except Exception:
                pass

            signature = {
                "selector": selector,
                "bounding_box": bbox,
                "text": text[:100] if text else None,
                "captured_at": time.time(),
            }

            if selector not in self._selector_history:
                self._selector_history[selector] = SelectorHistory(
                    original_selector=selector,
                    last_working_selector=selector,
                )

            self._selector_history[selector].element_signature = signature
            return signature

        except Exception as e:
            self._log.debug("Failed to capture element signature", error=str(e))
            return None

    def _load_history(self) -> None:
        """Load selector history from file."""
        if not self._history_path or not self._history_path.exists():
            return

        try:
            data = json.loads(self._history_path.read_text())
            for key, value in data.items():
                self._selector_history[key] = SelectorHistory(
                    original_selector=value["original_selector"],
                    last_working_selector=value["last_working_selector"],
                    healed_selectors=value.get("healed_selectors", []),
                    failure_count=value.get("failure_count", 0),
                    last_healed_at=value.get("last_healed_at"),
                    element_signature=value.get("element_signature"),
                )
            self._log.info("Loaded selector history", count=len(self._selector_history))
        except Exception as e:
            self._log.warning("Failed to load selector history", error=str(e))

    def _save_history(self) -> None:
        """Save selector history to file."""
        if not self._history_path:
            return

        try:
            data = {}
            for key, history in self._selector_history.items():
                data[key] = {
                    "original_selector": history.original_selector,
                    "last_working_selector": history.last_working_selector,
                    "healed_selectors": history.healed_selectors,
                    "failure_count": history.failure_count,
                    "last_healed_at": history.last_healed_at,
                    "element_signature": history.element_signature,
                }

            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            self._history_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            self._log.warning("Failed to save selector history", error=str(e))

    def get_healing_stats(self) -> dict[str, Any]:
        """Get statistics about healing operations."""
        total_selectors = len(self._selector_history)
        healed_count = sum(
            1 for h in self._selector_history.values() if h.healed_selectors
        )
        total_healings = sum(
            len(h.healed_selectors) for h in self._selector_history.values()
        )
        failure_count = sum(
            h.failure_count for h in self._selector_history.values()
        )

        return {
            "total_tracked_selectors": total_selectors,
            "selectors_healed": healed_count,
            "total_healing_operations": total_healings,
            "total_failures": failure_count,
            "healing_success_rate": (
                total_healings / (total_healings + failure_count)
                if (total_healings + failure_count) > 0
                else 0.0
            ),
        }
