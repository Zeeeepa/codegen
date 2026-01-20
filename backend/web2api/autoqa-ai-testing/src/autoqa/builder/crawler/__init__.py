"""
Crawler module for intelligent web crawling.

Provides:
- Priority-based URL crawling
- State-aware crawling with tracking
- Form submission exploration
- Authentication flow handling
"""

from autoqa.builder.crawler.intelligent_crawler import (
    IntelligentCrawler,
    CrawlConfig,
    CrawlResult,
    CrawledPage,
    URLPriority,
    CrawlState,
)
from autoqa.builder.crawler.state_manager import (
    StateManager,
    StateConfig,
    ApplicationState,
    StateTransition,
    StateGraph,
)

__all__ = [
    # Intelligent Crawler
    "IntelligentCrawler",
    "CrawlConfig",
    "CrawlResult",
    "CrawledPage",
    "URLPriority",
    "CrawlState",
    # State Manager
    "StateManager",
    "StateConfig",
    "ApplicationState",
    "StateTransition",
    "StateGraph",
]
