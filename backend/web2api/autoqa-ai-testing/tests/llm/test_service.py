"""Tests for LLM service module."""

from __future__ import annotations

import pytest
from pydantic import SecretStr

from autoqa.llm.config import (
    LLMConfig,
    LLMEndpointConfig,
    ToolLLMConfig,
    ToolName,
)
from autoqa.llm.service import LLMResult, LLMService


class TestLLMService:
    """Tests for LLMService."""

    @pytest.fixture
    def disabled_service(self) -> LLMService:
        """Create a service with LLM disabled."""
        config = LLMConfig(enabled=False)
        return LLMService(config)

    @pytest.fixture
    def enabled_service(self) -> LLMService:
        """Create a service with LLM enabled (but no API key)."""
        config = LLMConfig(
            enabled=True,
            default_endpoint=LLMEndpointConfig(
                api_key=SecretStr("test-key"),
            ),
            test_builder=ToolLLMConfig(enabled=True),
            assertions=ToolLLMConfig(enabled=True),
        )
        return LLMService(config)

    def test_is_enabled_when_disabled(self, disabled_service: LLMService) -> None:
        """Test is_enabled returns False when disabled."""
        assert not disabled_service.is_enabled(ToolName.TEST_BUILDER)
        assert not disabled_service.is_enabled(ToolName.ASSERTIONS)

    def test_is_enabled_when_enabled(self, enabled_service: LLMService) -> None:
        """Test is_enabled returns True when enabled."""
        assert enabled_service.is_enabled(ToolName.TEST_BUILDER)
        assert enabled_service.is_enabled(ToolName.ASSERTIONS)
        # Step transformer not enabled in fixture
        assert not enabled_service.is_enabled(ToolName.STEP_TRANSFORMER)

    @pytest.mark.asyncio
    async def test_generate_test_name_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test generate_test_name returns fallback when disabled."""
        result = await disabled_service.generate_test_name(
            url="https://example.com",
            page_title="Example Page",
            elements_summary="5 buttons, 3 inputs",
            fallback="Default Test Name",
        )
        assert result == "Default Test Name"

    @pytest.mark.asyncio
    async def test_generate_test_description_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test generate_test_description returns fallback when disabled."""
        result = await disabled_service.generate_test_description(
            test_name="Test Name",
            url="https://example.com",
            page_title="Example Page",
            elements_summary="5 buttons",
            forms_summary="1 form",
            steps_count=10,
            fallback="Default description",
        )
        assert result == "Default description"

    @pytest.mark.asyncio
    async def test_generate_step_name_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test generate_step_name returns fallback when disabled."""
        result = await disabled_service.generate_step_name(
            action="click",
            selector="button.submit",
            fallback="Click submit button",
        )
        assert result == "Click submit button"

    @pytest.mark.asyncio
    async def test_suggest_assertions_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test suggest_assertions returns empty list when disabled."""
        result = await disabled_service.suggest_assertions(
            url="https://example.com",
            page_title="Example",
            elements=[],
            forms=[],
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_translate_natural_language_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test translate_natural_language returns None when disabled."""
        result = await disabled_service.translate_natural_language(
            instruction="Click the login button",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_semantic_assertion_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test validate_semantic_assertion returns fallback result when disabled."""
        result = await disabled_service.validate_semantic_assertion(
            assertion_description="Page shows success message",
            url="https://example.com",
            visible_text="Success! Your action completed.",
            key_elements=[],
        )
        assert isinstance(result, LLMResult)
        assert not result.success
        assert result.fallback_used

    @pytest.mark.asyncio
    async def test_suggest_selector_alternatives_disabled(
        self, disabled_service: LLMService
    ) -> None:
        """Test suggest_selector_alternatives returns empty list when disabled."""
        result = await disabled_service.suggest_selector_alternatives(
            failed_selector="#old-button",
            action="click",
        )
        assert result == []


class TestLLMResult:
    """Tests for LLMResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful result."""
        result = LLMResult(
            success=True,
            content="Generated content",
            tokens_used=100,
        )
        assert result.success
        assert result.content == "Generated content"
        assert result.tokens_used == 100
        assert not result.fallback_used

    def test_failed_result(self) -> None:
        """Test creating a failed result."""
        result = LLMResult(
            success=False,
            content="",
            error="API error",
            fallback_used=True,
        )
        assert not result.success
        assert result.error == "API error"
        assert result.fallback_used

    def test_parsed_data(self) -> None:
        """Test result with parsed JSON data."""
        result = LLMResult(
            success=True,
            content='{"key": "value"}',
            parsed_data={"key": "value"},
        )
        assert result.parsed_data == {"key": "value"}
