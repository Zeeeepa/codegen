"""
Intelligent web crawler for comprehensive application exploration.

Features:
- Priority-based URL queue (important pages first)
- State-aware crawling (track app state changes)
- Form submission exploration
- Authentication flow detection and handling
- Rate limiting and politeness
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum, StrEnum, auto
from heapq import heappop, heappush
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

import structlog

if TYPE_CHECKING:
    from owl_browser import Browser, BrowserContext

    from autoqa.builder.analyzer.page_analyzer import PageAnalysisResult
    from autoqa.builder.crawler.state_manager import ApplicationState, StateManager

logger = structlog.get_logger(__name__)


class URLPriority(IntEnum):
    """URL crawl priority (lower = higher priority)."""

    CRITICAL = 1  # Login, checkout, main actions
    HIGH = 2  # Navigation, main content
    MEDIUM = 3  # Secondary pages
    LOW = 4  # Less important pages
    DEFERRED = 5  # External or low-value pages


class CrawlState(StrEnum):
    """State of a crawl operation."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


@dataclass
class CrawlConfig:
    """Configuration for intelligent crawling."""

    start_url: str = ""  # Can be provided at crawl time
    max_depth: int = 3
    max_pages: int = 50
    max_duration_seconds: int = 300
    same_domain_only: bool = True
    respect_robots_txt: bool = True
    rate_limit_ms: int = 500
    timeout_ms: int = 30000
    wait_after_navigation_ms: int = 2000
    explore_forms: bool = True
    explore_dynamic_content: bool = True
    follow_redirects: bool = True
    exclude_patterns: list[str] = field(default_factory=list)
    include_patterns: list[str] = field(default_factory=list)
    priority_patterns: dict[str, URLPriority] = field(default_factory=dict)
    max_retries: int = 2
    authentication: dict[str, str] | None = None


@dataclass
class CrawlQueueItem:
    """Item in the crawl queue."""

    url: str
    priority: URLPriority
    depth: int
    parent_url: str | None
    context: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    added_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __lt__(self, other: CrawlQueueItem) -> bool:
        """Compare for priority queue ordering."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.added_at < other.added_at


@dataclass
class CrawledPage:
    """Information about a crawled page."""

    url: str
    final_url: str  # After redirects
    title: str
    depth: int
    state: CrawlState
    analysis: PageAnalysisResult | None = None
    app_state: ApplicationState | None = None
    screenshot: bytes | None = None
    html_content: str | None = None
    discovered_urls: list[str] = field(default_factory=list)
    forms_found: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    crawl_time_ms: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CrawlResult:
    """Result of a complete crawl operation."""

    start_url: str
    pages_crawled: list[CrawledPage]
    pages_failed: list[CrawledPage]
    pages_skipped: list[str]
    total_duration_ms: int
    urls_discovered: int
    forms_found: int
    authentication_detected: bool
    authentication_completed: bool
    state_transitions: int
    coverage_score: float
    errors: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class IntelligentCrawler:
    """
    Intelligent crawler for comprehensive web application exploration.

    Features:
    - Priority-based crawling with configurable URL priorities
    - State tracking across pages
    - Form exploration and submission
    - Authentication detection and handling
    - Rate limiting for politeness
    - Deduplication and cycle detection
    """

    # URL patterns for priority assignment
    DEFAULT_PRIORITY_PATTERNS: dict[str, URLPriority] = {
        r"(login|signin|sign-in|auth)": URLPriority.CRITICAL,
        r"(checkout|payment|purchase)": URLPriority.CRITICAL,
        r"(register|signup|sign-up)": URLPriority.CRITICAL,
        r"(dashboard|admin|account)": URLPriority.HIGH,
        r"(home|index|main)": URLPriority.HIGH,
        r"(search|product|item)": URLPriority.MEDIUM,
        r"(about|contact|help|faq)": URLPriority.LOW,
        r"(terms|privacy|legal)": URLPriority.DEFERRED,
        r"\.(pdf|doc|zip|exe)$": URLPriority.DEFERRED,
    }

    # Form types to explore
    EXPLORABLE_FORM_TYPES = {"search", "filter", "newsletter", "contact"}

    # Skip these form types during exploration
    SKIP_FORM_TYPES = {"login", "register", "payment", "delete"}

    def __init__(
        self,
        browser: Browser,
        config: CrawlConfig,
        state_manager: StateManager | None = None,
    ) -> None:
        self._browser = browser
        self._config = config
        self._state_manager = state_manager
        self._log = logger.bind(component="intelligent_crawler")

        # Crawl state
        self._queue: list[CrawlQueueItem] = []  # Priority queue
        self._visited_urls: set[str] = set()
        self._visited_content_hashes: set[str] = set()
        self._url_redirects: dict[str, str] = {}
        self._crawled_pages: list[CrawledPage] = []
        self._failed_pages: list[CrawledPage] = []
        self._skipped_urls: list[str] = []

        # Statistics
        self._start_time: float = 0
        self._last_request_time: float = 0
        self._urls_discovered = 0
        self._forms_found = 0
        self._state_transitions = 0
        self._auth_detected = False
        self._auth_completed = False

        # Domain extraction
        parsed = urlparse(config.start_url)
        self._base_domain = parsed.netloc
        self._base_scheme = parsed.scheme

        # Compile patterns
        self._exclude_patterns = [re.compile(p, re.IGNORECASE) for p in config.exclude_patterns]
        self._include_patterns = [re.compile(p, re.IGNORECASE) for p in config.include_patterns]
        self._priority_patterns = {
            re.compile(k, re.IGNORECASE): v
            for k, v in {**self.DEFAULT_PRIORITY_PATTERNS, **config.priority_patterns}.items()
        }

    async def crawl(self, start_url: str | None = None) -> CrawlResult:
        """
        Execute the crawl operation.

        Args:
            start_url: Optional starting URL (overrides config.start_url if provided)

        Returns:
            Complete crawl result with all discovered pages
        """
        # Use provided start_url or fall back to config
        crawl_start_url = start_url or self._config.start_url
        if not crawl_start_url:
            raise ValueError("start_url must be provided either at crawl time or in config")

        # Update base domain if start_url was provided at crawl time
        if start_url:
            parsed = urlparse(start_url)
            self._base_domain = parsed.netloc
            self._base_scheme = parsed.scheme

        self._start_time = time.time()
        self._log.info(
            "Starting intelligent crawl",
            url=crawl_start_url,
            max_depth=self._config.max_depth,
            max_pages=self._config.max_pages,
        )

        # Add start URL to queue
        self._enqueue(crawl_start_url, URLPriority.HIGH, depth=0)

        # Create page context
        page = self._browser.new_page()

        try:
            # Process queue
            while self._queue and not self._should_stop():
                item = heappop(self._queue)

                # Check if already visited (could be added multiple times)
                normalized_url = self._normalize_url(item.url)
                if normalized_url in self._visited_urls:
                    continue

                # Rate limiting
                await self._apply_rate_limit()

                # Crawl the page
                crawled_page = await self._crawl_page(page, item)

                if crawled_page.state == CrawlState.COMPLETED:
                    self._crawled_pages.append(crawled_page)
                    self._visited_urls.add(normalized_url)

                    # Discover and enqueue new URLs
                    for url in crawled_page.discovered_urls:
                        self._enqueue(url, self._determine_priority(url), item.depth + 1, item.url)

                elif crawled_page.state == CrawlState.FAILED:
                    if item.retry_count < self._config.max_retries:
                        # Re-enqueue for retry
                        item.retry_count += 1
                        heappush(self._queue, item)
                    else:
                        self._failed_pages.append(crawled_page)

                elif crawled_page.state == CrawlState.SKIPPED:
                    self._skipped_urls.append(item.url)

            # Calculate coverage score
            coverage_score = self._calculate_coverage_score()

        finally:
            page.close()

        # Build result
        total_duration = int((time.time() - self._start_time) * 1000)

        result = CrawlResult(
            start_url=self._config.start_url,
            pages_crawled=self._crawled_pages,
            pages_failed=self._failed_pages,
            pages_skipped=self._skipped_urls,
            total_duration_ms=total_duration,
            urls_discovered=self._urls_discovered,
            forms_found=self._forms_found,
            authentication_detected=self._auth_detected,
            authentication_completed=self._auth_completed,
            state_transitions=self._state_transitions,
            coverage_score=coverage_score,
            errors=[],
        )

        self._log.info(
            "Crawl complete",
            pages_crawled=len(self._crawled_pages),
            pages_failed=len(self._failed_pages),
            urls_discovered=self._urls_discovered,
            coverage_score=coverage_score,
        )

        return result

    async def _crawl_page(
        self,
        page: BrowserContext,
        item: CrawlQueueItem,
    ) -> CrawledPage:
        """Crawl a single page."""
        url = item.url
        start_time = time.time()

        self._log.debug("Crawling page", url=url, depth=item.depth, priority=item.priority.name)

        crawled = CrawledPage(
            url=url,
            final_url=url,
            title="",
            depth=item.depth,
            state=CrawlState.IN_PROGRESS,
        )

        try:
            # Navigate to URL
            page.goto(url, timeout=self._config.timeout_ms)

            # Wait for page load
            time.sleep(self._config.wait_after_navigation_ms / 1000)

            # Get final URL (after redirects)
            final_url = page.get_current_url()
            crawled.final_url = final_url

            # Track redirects
            if final_url != url:
                self._url_redirects[url] = final_url

            # Check if we've already seen this content
            content_hash = self._get_content_hash(page)
            if content_hash in self._visited_content_hashes:
                crawled.state = CrawlState.SKIPPED
                self._log.debug("Skipping duplicate content", url=url)
                return crawled

            self._visited_content_hashes.add(content_hash)

            # Get page title
            crawled.title = page.get_title() or "Untitled"

            # Capture HTML content for analysis
            crawled.html_content = page.get_html()

            # Capture screenshot if needed
            crawled.screenshot = page.screenshot()

            # Discover URLs
            crawled.discovered_urls = self._discover_urls(page, url)
            self._urls_discovered += len(crawled.discovered_urls)

            # Discover forms
            crawled.forms_found = self._discover_forms(page)
            self._forms_found += len(crawled.forms_found)

            # Check for authentication
            if self._detect_authentication_form(crawled.forms_found):
                self._auth_detected = True
                if self._config.authentication:
                    auth_success = await self._handle_authentication(page)
                    self._auth_completed = auth_success

            # Track state if state manager available
            if self._state_manager:
                current_state = await self._state_manager.capture_state(page)
                crawled.app_state = current_state

            crawled.state = CrawlState.COMPLETED

        except Exception as e:
            crawled.state = CrawlState.FAILED
            crawled.errors.append(str(e))
            self._log.warning("Page crawl failed", url=url, error=str(e))

        crawled.crawl_time_ms = int((time.time() - start_time) * 1000)
        return crawled

    def _enqueue(
        self,
        url: str,
        priority: URLPriority,
        depth: int,
        parent_url: str | None = None,
    ) -> None:
        """Add URL to crawl queue."""
        normalized_url = self._normalize_url(url)

        # Skip if already visited or queued
        if normalized_url in self._visited_urls:
            return

        # Skip if exceeds depth limit
        if depth > self._config.max_depth:
            return

        # Skip if doesn't match include/exclude patterns
        if not self._should_crawl_url(url):
            return

        item = CrawlQueueItem(
            url=url,
            priority=priority,
            depth=depth,
            parent_url=parent_url,
        )

        heappush(self._queue, item)

    def _should_crawl_url(self, url: str) -> bool:
        """Check if URL should be crawled."""
        # Parse URL
        parsed = urlparse(url)

        # Check domain restriction
        if self._config.same_domain_only and parsed.netloc != self._base_domain:
            return False

        # Check exclude patterns
        for pattern in self._exclude_patterns:
            if pattern.search(url):
                return False

        # Check include patterns
        if self._include_patterns:
            if not any(pattern.search(url) for pattern in self._include_patterns):
                return False

        # Skip non-HTTP URLs
        if parsed.scheme not in ("http", "https"):
            return False

        # Skip file downloads
        skip_extensions = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".exe", ".dmg")
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        return True

    def _determine_priority(self, url: str) -> URLPriority:
        """Determine crawl priority for a URL."""
        for pattern, priority in self._priority_patterns.items():
            if pattern.search(url):
                return priority
        return URLPriority.MEDIUM

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison."""
        parsed = urlparse(url)

        # Remove fragment
        path = parsed.path.rstrip("/") or "/"

        # Reconstruct without fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
        if parsed.query:
            # Sort query parameters for consistent comparison
            params = sorted(parsed.query.split("&"))
            normalized += f"?{'&'.join(params)}"

        return normalized

    def _discover_urls(self, page: BrowserContext, base_url: str) -> list[str]:
        """Discover URLs from the current page."""
        script = """
        (() => {
            const urls = new Set();

            // Links
            document.querySelectorAll('a[href]').forEach(a => {
                if (a.href && !a.href.startsWith('javascript:')) {
                    urls.add(a.href);
                }
            });

            // Form actions
            document.querySelectorAll('form[action]').forEach(form => {
                if (form.action) {
                    urls.add(form.action);
                }
            });

            // Data attributes that might contain URLs
            document.querySelectorAll('[data-href], [data-url], [data-link]').forEach(el => {
                const url = el.dataset.href || el.dataset.url || el.dataset.link;
                if (url) {
                    urls.add(url);
                }
            });

            return Array.from(urls);
        })()
        """

        raw_urls = page.expression(script)
        discovered: list[str] = []

        for url in raw_urls:
            # Resolve relative URLs
            absolute_url = urljoin(base_url, url)
            if self._should_crawl_url(absolute_url):
                discovered.append(absolute_url)

        return list(set(discovered))

    def _discover_forms(self, page: BrowserContext) -> list[dict[str, Any]]:
        """Discover forms on the current page."""
        script = """
        (() => {
            const forms = [];

            document.querySelectorAll('form').forEach((form, index) => {
                const inputs = Array.from(form.querySelectorAll('input, select, textarea')).map(input => ({
                    type: input.type || input.tagName.toLowerCase(),
                    name: input.name || null,
                    id: input.id || null,
                    required: input.required,
                    placeholder: input.placeholder || null
                }));

                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');

                forms.push({
                    id: form.id || `form_${index}`,
                    action: form.action || window.location.href,
                    method: form.method || 'GET',
                    inputs: inputs,
                    inputCount: inputs.length,
                    hasPassword: inputs.some(i => i.type === 'password'),
                    hasEmail: inputs.some(i => i.type === 'email'),
                    hasSearch: inputs.some(i => i.type === 'search'),
                    submitText: submitBtn ? submitBtn.innerText || submitBtn.value : null
                });
            });

            return forms;
        })()
        """

        return page.expression(script)

    def _detect_authentication_form(self, forms: list[dict[str, Any]]) -> bool:
        """Detect if any form is an authentication form."""
        for form in forms:
            if form.get("hasPassword"):
                return True
            submit_text = (form.get("submitText") or "").lower()
            if any(word in submit_text for word in ["login", "sign in", "log in"]):
                return True
        return False

    async def _handle_authentication(self, page: BrowserContext) -> bool:
        """Handle authentication if credentials provided."""
        if not self._config.authentication:
            return False

        username = self._config.authentication.get("username", "")
        password = self._config.authentication.get("password", "")

        if not username or not password:
            return False

        try:
            # Find username/email field
            username_selectors = [
                "input[type='email']",
                "input[name*='user']",
                "input[name*='email']",
                "input[id*='user']",
                "input[id*='email']",
            ]

            for selector in username_selectors:
                try:
                    page.type(selector, username)
                    break
                except Exception:
                    continue

            # Find password field
            page.type("input[type='password']", password)

            # Submit
            page.click("button[type='submit'], input[type='submit']")

            # Wait for response
            time.sleep(2)

            self._log.info("Authentication submitted")
            return True

        except Exception as e:
            self._log.warning("Authentication failed", error=str(e))
            return False

    def _get_content_hash(self, page: BrowserContext) -> str:
        """Get hash of page content for deduplication."""
        script = """
        (() => {
            const body = document.body;
            const text = body ? body.innerText : '';
            // Include structural info for better deduplication
            const structure = document.querySelectorAll('h1, h2, h3, main, article').length;
            return text.substring(0, 1000) + '|' + structure;
        })()
        """

        content = page.expression(script)
        return hashlib.md5(content.encode()).hexdigest()

    def _should_stop(self) -> bool:
        """Check if crawling should stop."""
        # Max pages reached
        if len(self._crawled_pages) >= self._config.max_pages:
            return True

        # Max duration reached
        elapsed = time.time() - self._start_time
        if elapsed >= self._config.max_duration_seconds:
            return True

        return False

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time > 0:
            elapsed = (time.time() - self._last_request_time) * 1000
            if elapsed < self._config.rate_limit_ms:
                wait_time = (self._config.rate_limit_ms - elapsed) / 1000
                await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    def _calculate_coverage_score(self) -> float:
        """Calculate crawl coverage score (0-1)."""
        if not self._crawled_pages:
            return 0.0

        # Factors for coverage
        pages_factor = min(len(self._crawled_pages) / self._config.max_pages, 1.0)

        # Depth coverage
        max_depth_reached = max(p.depth for p in self._crawled_pages) if self._crawled_pages else 0
        depth_factor = min(max_depth_reached / self._config.max_depth, 1.0)

        # Form coverage
        form_factor = min(self._forms_found / 10, 1.0) if self._forms_found > 0 else 0

        # Auth factor
        auth_factor = 1.0 if (not self._auth_detected or self._auth_completed) else 0.5

        # Calculate weighted score
        coverage = (
            0.4 * pages_factor
            + 0.3 * depth_factor
            + 0.2 * form_factor
            + 0.1 * auth_factor
        )

        return round(coverage, 3)

    def get_statistics(self) -> dict[str, Any]:
        """Get current crawl statistics."""
        return {
            "pages_crawled": len(self._crawled_pages),
            "pages_failed": len(self._failed_pages),
            "pages_skipped": len(self._skipped_urls),
            "queue_size": len(self._queue),
            "urls_discovered": self._urls_discovered,
            "forms_found": self._forms_found,
            "auth_detected": self._auth_detected,
            "auth_completed": self._auth_completed,
            "elapsed_seconds": time.time() - self._start_time if self._start_time else 0,
        }
