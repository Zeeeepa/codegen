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
from langchain_xai import ChatXAI
from pydantic import Field

logger = logging.getLogger(__name__)


class LLM(BaseChatModel):
    """A unified chat model that supports both OpenAI and Anthropic."""

    model_provider: str = Field(default="anthropic", description="The model provider to use.")

    model_name: str = Field(default="claude-3-5-sonnet-latest", description="Name of the model to use.")

    temperature: float = Field(default=0, description="Temperature parameter for the model.", ge=0, le=1)

    top_p: Optional[float] = Field(default=None, description="Top-p sampling parameter.", ge=0, le=1)

    top_k: Optional[int] = Field(default=None, description="Top-k sampling parameter.", ge=1)

    max_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate.", ge=1)

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
        """
        # Set model provider and name before calling super().__init__
        kwargs["model_provider"] = model_provider
        kwargs["model_name"] = model_name

        # Filter out unsupported kwargs
        supported_kwargs = {"model_provider", "model_name", "temperature", "top_p", "top_k", "max_tokens", "callbacks", "tags", "metadata"}
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
        elif self.model_provider == "xai":
            xai_api_base = os.getenv("XAI_API_BASE", "https://api.x.ai/v1/")
            return {**base_kwargs, "model": self.model_name, "xai_api_base": xai_api_base}
        else:  # openai
            return {**base_kwargs, "model": self.model_name}

    def _get_model(self) -> BaseChatModel:
        """Get the appropriate model instance based on configuration.
        
        Supports custom Anthropic-compatible endpoints via ANTHROPIC_BASE_URL environment variable.
        This enables using alternative models like GLM that implement the Anthropic API.
        """
        if self.model_provider == "anthropic":
            # Check for API key
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                msg = "ANTHROPIC_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            
            # Get base kwargs
            kwargs = self._get_model_kwargs()
            
            # Check for custom base URL (e.g., for GLM or other Anthropic-compatible endpoints)
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            if base_url:
                logger.info(f"Using custom Anthropic endpoint: {base_url}")
                kwargs["base_url"] = base_url
                kwargs["api_key"] = api_key  # Explicitly set API key when using custom endpoint
            
            # Check for custom model name override
            custom_model = os.getenv("ANTHROPIC_MODEL")
            if custom_model:
                logger.info(f"Using custom Anthropic model: {custom_model}")
                kwargs["model"] = custom_model
            
            max_tokens = 8192
            return ChatAnthropic(**kwargs, max_tokens=max_tokens, max_retries=10, timeout=1000)

        elif self.model_provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                msg = "OPENAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatOpenAI(**self._get_model_kwargs(), max_tokens=4096, max_retries=10, timeout=1000)

        elif self.model_provider == "xai":
            if not os.getenv("XAI_API_KEY"):
                msg = "XAI_API_KEY not found in environment. Please set it in your .env file or environment variables."
                raise ValueError(msg)
            return ChatXAI(**self._get_model_kwargs(), max_tokens=12000)

        msg = f"Unknown model provider: {self.model_provider}. Must be one of: anthropic, openai, xai"
        raise ValueError(msg)

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
        return self._model._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

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
