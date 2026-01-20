"""
Tests for the Auto Test Builder module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from autoqa.builder.test_builder import (
    AutoTestBuilder,
    BuilderConfig,
    ElementInfo,
    ElementType,
    PageAnalysis,
)


class TestBuilderConfig:
    """Tests for BuilderConfig dataclass."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = BuilderConfig(url="https://example.com")

        assert config.url == "https://example.com"
        assert config.username is None
        assert config.password is None
        assert config.depth == 1
        assert config.max_pages == 10
        assert config.include_hidden is False
        assert config.timeout_ms == 30000
        assert config.same_domain_only is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = BuilderConfig(
            url="https://example.com/login",
            username="testuser",
            password="testpass",
            depth=3,
            max_pages=20,
            include_hidden=True,
        )

        assert config.username == "testuser"
        assert config.password == "testpass"
        assert config.depth == 3
        assert config.max_pages == 20
        assert config.include_hidden is True


class TestElementInfo:
    """Tests for ElementInfo dataclass."""

    def test_element_info_creation(self) -> None:
        """Test creating an ElementInfo instance."""
        element = ElementInfo(
            element_type=ElementType.BUTTON,
            selector="Submit",
            semantic_description="submit button",
            text_content="Submit",
            is_visible=True,
        )

        assert element.element_type == ElementType.BUTTON
        assert element.selector == "Submit"
        assert element.semantic_description == "submit button"
        assert element.text_content == "Submit"
        assert element.is_visible is True
        assert element.is_required is False


class TestPageAnalysis:
    """Tests for PageAnalysis dataclass."""

    def test_page_analysis_creation(self) -> None:
        """Test creating a PageAnalysis instance."""
        from datetime import UTC, datetime

        analysis = PageAnalysis(
            url="https://example.com",
            title="Example Page",
            timestamp=datetime.now(UTC),
        )

        assert analysis.url == "https://example.com"
        assert analysis.title == "Example Page"
        assert analysis.elements == []
        assert analysis.forms == []
        assert analysis.has_login_form is False


class TestAutoTestBuilder:
    """Tests for AutoTestBuilder class."""

    def test_normalize_url(self) -> None:
        """Test URL normalization."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com/page/")

        builder = AutoTestBuilder(browser=browser_mock, config=config)

        assert builder._normalize_url("https://example.com/page/") == "https://example.com/page"
        assert builder._normalize_url("https://example.com/page") == "https://example.com/page"
        assert builder._normalize_url("https://example.com/page?q=1") == "https://example.com/page?q=1"

    def test_is_valid_crawl_target(self) -> None:
        """Test crawl target validation."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")

        builder = AutoTestBuilder(browser=browser_mock, config=config)

        # Valid targets
        assert builder._is_valid_crawl_target("https://example.com/page") is True
        assert builder._is_valid_crawl_target("/relative/path") is True

        # Invalid targets
        assert builder._is_valid_crawl_target("javascript:void(0)") is False
        assert builder._is_valid_crawl_target("mailto:test@example.com") is False
        assert builder._is_valid_crawl_target("#anchor") is False
        assert builder._is_valid_crawl_target("document.pdf") is False
        assert builder._is_valid_crawl_target("image.png") is False

    def test_extract_base_url(self) -> None:
        """Test base URL extraction."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com/path/to/page")

        builder = AutoTestBuilder(browser=browser_mock, config=config)

        assert builder._extract_base_url("https://example.com/path") == "https://example.com"
        assert builder._extract_base_url("http://localhost:8080/api") == "http://localhost:8080"

    def test_should_crawl_url_with_patterns(self) -> None:
        """Test URL filtering with include/exclude patterns."""
        browser_mock = MagicMock()
        config = BuilderConfig(
            url="https://example.com",
            exclude_patterns=[r"/admin/", r"/api/"],
            include_patterns=[],
        )

        builder = AutoTestBuilder(browser=browser_mock, config=config)

        assert builder._should_crawl_url("https://example.com/page") is True
        assert builder._should_crawl_url("https://example.com/admin/dashboard") is False
        assert builder._should_crawl_url("https://example.com/api/users") is False

    def test_generate_sample_input(self) -> None:
        """Test sample input generation for different element types."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")

        builder = AutoTestBuilder(browser=browser_mock, config=config)

        email_element = ElementInfo(
            element_type=ElementType.INPUT_EMAIL,
            selector="email",
            semantic_description="email input",
        )
        assert builder._generate_sample_input(email_element) == "test@example.com"

        number_element = ElementInfo(
            element_type=ElementType.INPUT_NUMBER,
            selector="quantity",
            semantic_description="quantity input",
        )
        assert builder._generate_sample_input(number_element) == "42"

        text_element = ElementInfo(
            element_type=ElementType.INPUT_TEXT,
            selector="name",
            semantic_description="name input",
        )
        assert builder._generate_sample_input(text_element) == "Test input"


class TestSemanticDescriptionGeneration:
    """Tests for semantic description generation."""

    def test_description_from_aria_label(self) -> None:
        """Test description uses aria-label when available."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": "Search products", "text": None}
        desc = builder._generate_semantic_description(raw, ElementType.BUTTON)
        assert desc == "Search products"

    def test_description_from_text(self) -> None:
        """Test description uses text content when aria-label missing."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": None, "text": "Submit Form"}
        desc = builder._generate_semantic_description(raw, ElementType.BUTTON)
        assert desc == "Submit Form"

    def test_description_from_placeholder(self) -> None:
        """Test description uses placeholder for inputs."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": None, "text": None, "placeholder": "Enter email"}
        desc = builder._generate_semantic_description(raw, ElementType.INPUT_EMAIL)
        assert desc == "Enter email input"


class TestSemanticSelectorGeneration:
    """Tests for semantic selector generation."""

    def test_selector_prefers_aria_label(self) -> None:
        """Test selector generation prefers aria-label."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": "Search", "text": "Go", "placeholder": "Search..."}
        selector = builder._generate_semantic_selector(raw, ElementType.BUTTON)
        assert selector == "Search"

    def test_selector_uses_text_content(self) -> None:
        """Test selector uses text when aria-label missing."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": None, "text": "Click Me"}
        selector = builder._generate_semantic_selector(raw, ElementType.BUTTON)
        assert selector == "Click Me"

    def test_selector_formats_input_name(self) -> None:
        """Test selector formats input name properly."""
        browser_mock = MagicMock()
        config = BuilderConfig(url="https://example.com")
        builder = AutoTestBuilder(browser=browser_mock, config=config)

        raw = {"ariaLabel": None, "text": None, "placeholder": None, "name": "user_name"}
        selector = builder._generate_semantic_selector(raw, ElementType.INPUT_TEXT)
        assert selector == "user name input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
