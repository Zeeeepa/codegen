"""
LLM service for AutoQA tool integration.

Provides high-level interfaces for each AutoQA tool to use LLM capabilities
with clean fallback behavior when LLM is disabled.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

from autoqa.llm.client import (
    ChatMessage,
    LLMClient,
    LLMClientError,
    LLMClientFactory,
    create_llm_client,
)
from autoqa.llm.config import LLMConfig, ToolName, load_llm_config
from autoqa.llm.prompts import (
    PromptType,
    format_prompt,
    get_prompt,
    get_prompt_config,
)

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


@dataclass
class LLMResult:
    """Result from an LLM operation."""

    success: bool
    content: str
    parsed_data: dict[str, Any] | list[Any] | None = None
    error: str | None = None
    tokens_used: int = 0
    fallback_used: bool = False


class LLMServiceError(Exception):
    """Error from LLM service operations."""

    pass


class LLMService:
    """
    High-level LLM service for AutoQA tools.

    Provides tool-specific methods with automatic fallback behavior
    when LLM is disabled or fails.
    """

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._config = config or load_llm_config()
        self._log = logger.bind(component="llm_service")
        self._clients: dict[ToolName, LLMClient] = {}

    @property
    def config(self) -> LLMConfig:
        """Get the current LLM configuration."""
        return self._config

    def is_enabled(self, tool: ToolName) -> bool:
        """Check if LLM is enabled for a specific tool."""
        return self._config.is_tool_enabled(tool)

    async def _get_client(self, tool: ToolName) -> LLMClient | None:
        """Get or create an LLM client for a tool."""
        if not self.is_enabled(tool):
            return None

        if tool not in self._clients:
            client = await LLMClientFactory.get_client(self._config, tool)
            if client:
                self._clients[tool] = client

        return self._clients.get(tool)

    async def _execute_prompt(
        self,
        tool: ToolName,
        prompt_type: PromptType,
        variables: dict[str, Any],
        custom_system_prompt: str | None = None,
    ) -> LLMResult:
        """Execute a prompt and return the result."""
        client = await self._get_client(tool)
        if not client:
            return LLMResult(
                success=False,
                content="",
                error="LLM not enabled for this tool",
                fallback_used=True,
            )

        try:
            # Get prompt configuration
            prompt_config = get_prompt_config(prompt_type)
            system_prompt, user_prompt = format_prompt(prompt_type, **variables)

            # Allow custom system prompt override
            tool_config = self._config.get_tool_config(tool)
            if tool_config.custom_system_prompt:
                system_prompt = tool_config.custom_system_prompt
            if custom_system_prompt:
                system_prompt = custom_system_prompt

            # Execute the request
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt),
            ]

            result = await client.chat(
                messages,
                temperature=self._config.get_effective_temperature(tool),
                max_tokens=prompt_config.get("max_tokens", 512),
            )

            # Parse JSON if expected
            parsed_data = None
            if prompt_config.get("expected_format") == "json":
                try:
                    # Handle potential markdown code blocks
                    content = result.content.strip()
                    if content.startswith("```"):
                        # Remove code block markers
                        lines = content.split("\n")
                        if lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        content = "\n".join(lines)

                    parsed_data = json.loads(content)
                except json.JSONDecodeError as e:
                    self._log.warning(
                        "Failed to parse JSON response",
                        error=str(e),
                        content=result.content[:200],
                    )

            return LLMResult(
                success=True,
                content=result.content,
                parsed_data=parsed_data,
                tokens_used=result.usage.get("total_tokens", 0),
            )

        except LLMClientError as e:
            self._log.error(
                "LLM request failed",
                tool=tool,
                prompt_type=prompt_type,
                error=str(e),
            )
            return LLMResult(
                success=False,
                content="",
                error=str(e),
                fallback_used=True,
            )

    # =========================================================================
    # Test Builder Methods
    # =========================================================================

    async def generate_test_name(
        self,
        url: str,
        page_title: str,
        elements_summary: str,
        has_login: bool = False,
        form_count: int = 0,
        fallback: str = "Auto-generated Test",
    ) -> str:
        """
        Generate a meaningful test name using LLM.

        Args:
            url: Page URL
            page_title: Page title
            elements_summary: Summary of discovered elements
            has_login: Whether login form was detected
            form_count: Number of forms on page
            fallback: Fallback name if LLM fails or is disabled

        Returns:
            Generated test name or fallback
        """
        if not self.is_enabled(ToolName.TEST_BUILDER):
            return fallback

        result = await self._execute_prompt(
            ToolName.TEST_BUILDER,
            PromptType.GENERATE_TEST_NAME,
            {
                "url": url,
                "page_title": page_title,
                "elements_summary": elements_summary,
                "has_login": str(has_login),
                "form_count": str(form_count),
            },
        )

        if result.success and result.content.strip():
            return result.content.strip()

        return fallback

    async def generate_test_description(
        self,
        test_name: str,
        url: str,
        page_title: str,
        elements_summary: str,
        forms_summary: str,
        steps_count: int,
        fallback: str = "",
    ) -> str:
        """
        Generate a test description using LLM.

        Returns:
            Generated description or fallback
        """
        if not self.is_enabled(ToolName.TEST_BUILDER):
            return fallback

        result = await self._execute_prompt(
            ToolName.TEST_BUILDER,
            PromptType.GENERATE_TEST_DESCRIPTION,
            {
                "test_name": test_name,
                "url": url,
                "page_title": page_title,
                "elements_summary": elements_summary,
                "forms_summary": forms_summary,
                "steps_count": str(steps_count),
            },
        )

        if result.success and result.content.strip():
            return result.content.strip()

        return fallback

    async def generate_step_name(
        self,
        action: str,
        selector: str | None = None,
        text: str | None = None,
        element_description: str | None = None,
        context: str | None = None,
        fallback: str | None = None,
    ) -> str:
        """
        Generate a meaningful step name using LLM.

        Returns:
            Generated step name or fallback
        """
        default_fallback = f"{action.title()}: {selector or text or 'action'}"

        if not self.is_enabled(ToolName.TEST_BUILDER):
            return fallback or default_fallback

        result = await self._execute_prompt(
            ToolName.TEST_BUILDER,
            PromptType.GENERATE_STEP_NAME,
            {
                "action": action,
                "selector": selector or "N/A",
                "text": text or "N/A",
                "element_description": element_description or "N/A",
                "context": context or "N/A",
            },
        )

        if result.success and result.content.strip():
            return result.content.strip()

        return fallback or default_fallback

    async def suggest_assertions(
        self,
        url: str,
        page_title: str,
        elements: list[dict[str, Any]],
        forms: list[dict[str, Any]],
        test_purpose: str = "",
        previous_actions: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Suggest assertions for a page state using LLM.

        Returns:
            List of suggested assertion configurations
        """
        if not self.is_enabled(ToolName.TEST_BUILDER):
            return []

        result = await self._execute_prompt(
            ToolName.TEST_BUILDER,
            PromptType.SUGGEST_ASSERTIONS,
            {
                "url": url,
                "page_title": page_title,
                "elements": json.dumps(elements[:20]),  # Limit for token count
                "forms": json.dumps(forms[:10]),
                "test_purpose": test_purpose,
                "previous_actions": json.dumps(previous_actions or []),
            },
        )

        if result.success and result.parsed_data and isinstance(result.parsed_data, list):
            return result.parsed_data

        return []

    # =========================================================================
    # Step Transformer Methods
    # =========================================================================

    async def translate_natural_language(
        self,
        instruction: str,
        current_url: str = "",
        available_elements: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """
        Translate natural language instruction to browser action.

        Returns:
            Action configuration dict or None if translation fails
        """
        if not self.is_enabled(ToolName.STEP_TRANSFORMER):
            return None

        result = await self._execute_prompt(
            ToolName.STEP_TRANSFORMER,
            PromptType.NATURAL_LANGUAGE_TO_ACTION,
            {
                "instruction": instruction,
                "current_url": current_url,
                "available_elements": json.dumps(available_elements or [])[:2000],
            },
        )

        if result.success and result.parsed_data and isinstance(result.parsed_data, dict):
            return result.parsed_data

        return None

    async def enhance_selector(
        self,
        tag: str,
        element_id: str | None = None,
        name: str | None = None,
        class_name: str | None = None,
        text: str | None = None,
        aria_label: str | None = None,
        data_attributes: dict[str, str] | None = None,
        parent_context: str | None = None,
    ) -> str | None:
        """
        Generate an enhanced, robust selector for an element.

        Returns:
            Enhanced selector string or None
        """
        if not self.is_enabled(ToolName.STEP_TRANSFORMER):
            return None

        result = await self._execute_prompt(
            ToolName.STEP_TRANSFORMER,
            PromptType.ENHANCE_SELECTOR,
            {
                "tag": tag,
                "id": element_id or "",
                "name": name or "",
                "class_name": class_name or "",
                "text": text or "",
                "aria_label": aria_label or "",
                "data_attributes": json.dumps(data_attributes or {}),
                "parent_context": parent_context or "",
            },
        )

        if result.success and result.content.strip():
            return result.content.strip()

        return None

    # =========================================================================
    # Assertion Methods
    # =========================================================================

    async def validate_semantic_assertion(
        self,
        assertion_description: str,
        url: str,
        visible_text: str,
        key_elements: list[dict[str, Any]],
    ) -> LLMResult:
        """
        Validate a semantic assertion using LLM.

        Returns:
            LLMResult with validation details
        """
        if not self.is_enabled(ToolName.ASSERTIONS):
            return LLMResult(
                success=False,
                content="",
                error="LLM assertions not enabled",
                fallback_used=True,
            )

        return await self._execute_prompt(
            ToolName.ASSERTIONS,
            PromptType.SEMANTIC_VALIDATION,
            {
                "assertion_description": assertion_description,
                "url": url,
                "visible_text": visible_text[:3000],  # Limit for tokens
                "key_elements": json.dumps(key_elements[:30]),
            },
        )

    async def analyze_content(
        self,
        content_type: str,
        expected_patterns: list[str],
        actual_content: str,
    ) -> LLMResult:
        """
        Analyze page content for correctness.

        Returns:
            LLMResult with analysis details
        """
        if not self.is_enabled(ToolName.ASSERTIONS):
            return LLMResult(
                success=False,
                content="",
                error="LLM assertions not enabled",
                fallback_used=True,
            )

        return await self._execute_prompt(
            ToolName.ASSERTIONS,
            PromptType.CONTENT_ANALYSIS,
            {
                "content_type": content_type,
                "expected_patterns": json.dumps(expected_patterns),
                "actual_content": actual_content[:4000],
            },
        )

    # =========================================================================
    # Self-Healing Methods
    # =========================================================================

    async def suggest_selector_alternatives(
        self,
        failed_selector: str,
        action: str,
        element_description: str | None = None,
        similar_elements: list[dict[str, Any]] | None = None,
        page_structure: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Suggest alternative selectors for a failed selector.

        Returns:
            List of alternative selector suggestions with confidence scores
        """
        if not self.is_enabled(ToolName.SELF_HEALING):
            return []

        result = await self._execute_prompt(
            ToolName.SELF_HEALING,
            PromptType.SELECTOR_RECOVERY,
            {
                "failed_selector": failed_selector,
                "action": action,
                "element_description": element_description or "N/A",
                "similar_elements": json.dumps(similar_elements or [])[:2000],
                "page_structure": page_structure or "N/A",
            },
        )

        if result.success and result.parsed_data and isinstance(result.parsed_data, dict):
            return result.parsed_data.get("alternatives", [])

        return []

    async def identify_element(
        self,
        element_description: str,
        page_elements: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Identify an element based on natural language description.

        Returns:
            Element identification result or None
        """
        if not self.is_enabled(ToolName.SELF_HEALING):
            return None

        result = await self._execute_prompt(
            ToolName.SELF_HEALING,
            PromptType.ELEMENT_IDENTIFICATION,
            {
                "element_description": element_description,
                "page_elements": json.dumps(page_elements[:50]),
            },
        )

        if result.success and result.parsed_data and isinstance(result.parsed_data, dict):
            return result.parsed_data

        return None

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    async def close(self) -> None:
        """Close all LLM clients."""
        await LLMClientFactory.close_all()
        self._clients.clear()


# =============================================================================
# Global Service Instance
# =============================================================================

_global_service: LLMService | None = None


def get_llm_service(config: LLMConfig | None = None) -> LLMService:
    """
    Get the global LLM service instance.

    Creates a new service if one doesn't exist or if config is provided.
    """
    global _global_service

    if config is not None or _global_service is None:
        _global_service = LLMService(config)

    return _global_service


async def shutdown_llm_service() -> None:
    """Shutdown the global LLM service."""
    global _global_service

    if _global_service:
        await _global_service.close()
        _global_service = None
