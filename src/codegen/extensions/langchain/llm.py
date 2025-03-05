"""LLM implementation supporting both OpenAI and Anthropic models."""

import logging
import os
from collections.abc import Sequence
from typing import Any, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import Field

from codegen.extensions.langchain.utils.retry import retry_on_rate_limit

logger = logging.getLogger(__name__)


class LLM(BaseChatModel):
    """A unified chat model that supports both OpenAI and Anthropic."""

    model_provider: str = Field(default="anthropic", description="The model provider to use.")

    model_name: str = Field(default="claude-3-5-sonnet-latest", description="Name of the model to use.")

    temperature: float = Field(default=0, description="Temperature parameter for the model.", ge=0, le=1)

    top_p: Optional[float] = Field(default=None, description="Top-p sampling parameter.", ge=0, le=1)

    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter.", ge=1)

    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate.", ge=1)

    max_retries: int = Field(default=3, description="Maximum number of retries for rate limit errors.")

    retry_base_delay: float = Field(default=45.0, description="Base delay in seconds for retry backoff.")

    def __init__(self, model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", **kwargs: Any) -> None:
        """Initialize the LLM.

        Args:
            model_provider: "anthropic" or "openai"
            model_name: Name of the model to use
            **kwargs: Additional configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
                - max_retries: Maximum number of retries for rate limit errors
                - retry_base_delay: Base delay in seconds for retry backoff
        """
        # Set model provider and name before calling super().__init__
        kwargs["model_provider"] = model_provider
        kwargs["model_name"] = model_name

        # Filter out unsupported kwargs
        supported_kwargs = {"model_provider", "model_name", "temperature", "top_p", "top_k", "max_tokens", "callbacks", "tags", "metadata", "max_retries", "retry_base_delay"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_kwargs}

        super().__init__(**filtered_kwargs)
        self._model = self._get_model()

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM class."""
        return "unified_chat_model"

    def _get_model_kwargs(self) -> dict[str, Any]:
        """Get kwargs for the specific model provider."""
        base_kwargs = {
            "temperature": self.temperature,
        }

        if self.top_p is not None:
            base_kwargs["top_p"] = self.top_p

        if self.top_k is not None:
            base_kwargs["top_k"] = self.top_k

        if self.max_tokens is not None:
            base_kwargs["max_tokens"] = self.max_tokens

        if self.model_provider == "anthropic":
            return {**base_kwargs, "model": self.model_name}
        else:  # openai
            return {**base_kwargs, "model": self.model_name}

    def _get_model(self) -> BaseChatModel:
        """Get the appropriate model instance based on configuration."""
        if self.model_provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                msg = "ANTHROPIC_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatAnthropic(**self._get_model_kwargs())

        elif self.model_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                msg = "OPENAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatOpenAI(**self._get_model_kwargs())

        msg = f"Unknown model provider: {self.model_provider}. Must be one of: anthropic, openai"
        raise ValueError(msg)

    @retry_on_rate_limit(max_retries=3, base_delay=45.0)
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate chat completion using the underlying model.

        Args:
            messages: The messages to generate from
            stop: Optional list of stop sequences
            run_manager: Optional callback manager for tracking the run
            **kwargs: Additional arguments to pass to the model

        Returns:
            ChatResult containing the generated completion
        """
        # Use instance-specific retry settings if provided
        retry_decorator = retry_on_rate_limit(max_retries=self.max_retries, base_delay=self.retry_base_delay)

        # Apply the retry decorator to the underlying model's _generate method
        # This is a bit of a hack, but it allows us to use the decorator with the instance settings
        generate_with_retry = retry_decorator(self._model._generate)

        return generate_with_retry(messages, stop=stop, run_manager=run_manager, **kwargs)

    def bind_tools(
        self,
        tools: Sequence[BaseTool],
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind tools to the underlying model.

        Args:
            tools: List of tools to bind
            **kwargs: Additional arguments to pass to the model

        Returns:
            Runnable that can be used to invoke the model with tools
        """
        return self._model.bind_tools(tools, **kwargs)
