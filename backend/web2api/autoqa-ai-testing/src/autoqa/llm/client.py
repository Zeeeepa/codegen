"""
Async HTTP client for OpenAI-compatible LLM APIs.

Provides:
- Async httpx-based HTTP client
- Rate limiting with token bucket algorithm
- Retry logic with exponential backoff
- Support for OpenAI, Azure, and custom endpoints
"""

from __future__ import annotations

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import httpx
import structlog

from autoqa.llm.config import (
    LLMConfig,
    LLMEndpointConfig,
    LLMProvider,
    RateLimitConfig,
    RetryConfig,
    ToolName,
)

logger = structlog.get_logger(__name__)


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMRateLimitError(LLMClientError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class LLMAuthenticationError(LLMClientError):
    """Raised when authentication fails."""

    pass


class LLMAPIError(LLMClientError):
    """Raised when API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class ChatCompletion:
    """Response from a chat completion request."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class TokenBucket:
    """Token bucket rate limiter for API calls."""

    def __init__(self, config: RateLimitConfig) -> None:
        self._requests_per_minute = config.requests_per_minute
        self._tokens_per_minute = config.tokens_per_minute
        self._max_concurrent = config.concurrent_requests

        # Request rate limiting
        self._request_tokens = float(config.requests_per_minute)
        self._request_last_update = time.monotonic()

        # Token rate limiting
        self._token_tokens = float(config.tokens_per_minute)
        self._token_last_update = time.monotonic()

        # Concurrency limiting
        self._semaphore = asyncio.Semaphore(config.concurrent_requests)
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 1000) -> None:
        """Acquire permission to make a request."""
        await self._semaphore.acquire()

        async with self._lock:
            now = time.monotonic()

            # Refill request bucket
            elapsed = now - self._request_last_update
            self._request_tokens = min(
                self._requests_per_minute,
                self._request_tokens + elapsed * (self._requests_per_minute / 60),
            )
            self._request_last_update = now

            # Refill token bucket
            elapsed = now - self._token_last_update
            self._token_tokens = min(
                self._tokens_per_minute,
                self._token_tokens + elapsed * (self._tokens_per_minute / 60),
            )
            self._token_last_update = now

            # Wait if not enough request tokens
            if self._request_tokens < 1:
                wait_time = (1 - self._request_tokens) / (self._requests_per_minute / 60)
                await asyncio.sleep(wait_time)
                self._request_tokens = 1

            # Wait if not enough token budget
            if self._token_tokens < estimated_tokens:
                wait_time = (estimated_tokens - self._token_tokens) / (
                    self._tokens_per_minute / 60
                )
                await asyncio.sleep(wait_time)
                self._token_tokens = estimated_tokens

            # Consume tokens
            self._request_tokens -= 1
            self._token_tokens -= estimated_tokens

    def release(self) -> None:
        """Release the semaphore after request completes."""
        self._semaphore.release()

    def report_usage(self, actual_tokens: int, estimated_tokens: int) -> None:
        """Report actual token usage to adjust the budget."""
        # If we underestimated, deduct the difference
        if actual_tokens > estimated_tokens:
            self._token_tokens -= actual_tokens - estimated_tokens


class LLMClient:
    """
    Async client for OpenAI-compatible LLM APIs.

    Features:
    - Rate limiting with token bucket
    - Retry with exponential backoff
    - Support for OpenAI, Azure, and custom endpoints
    - Proper error handling and typing
    """

    def __init__(
        self,
        endpoint: LLMEndpointConfig,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._endpoint = endpoint
        self._log = logger.bind(
            component="llm_client",
            provider=endpoint.provider,
            model=endpoint.model,
        )

        # Rate limiter
        self._rate_limiter = TokenBucket(endpoint.rate_limit)

        # HTTP client
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            timeout=httpx.Timeout(endpoint.timeout_ms / 1000),
        )

    async def close(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> LLMClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    def _build_url(self) -> str:
        """Build the chat completions URL based on provider."""
        if self._endpoint.provider == LLMProvider.AZURE:
            return (
                f"{self._endpoint.base_url}/openai/deployments/"
                f"{self._endpoint.azure_deployment}/chat/completions"
                f"?api-version={self._endpoint.azure_api_version}"
            )
        return f"{self._endpoint.base_url}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """Build request headers based on provider."""
        headers = {
            "Content-Type": "application/json",
        }

        api_key = self._endpoint.api_key.get_secret_value()
        if not api_key:
            return headers

        if self._endpoint.provider == LLMProvider.AZURE:
            headers["api-key"] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

    def _build_request_body(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request body for chat completions."""
        body: dict[str, Any] = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature or self._endpoint.temperature,
            "max_tokens": max_tokens or self._endpoint.max_tokens,
        }

        # Only include model for non-Azure (Azure uses deployment name in URL)
        if self._endpoint.provider != LLMProvider.AZURE:
            body["model"] = self._endpoint.model

        # Add any additional kwargs (response_format, etc.)
        body.update(kwargs)

        return body

    def _estimate_tokens(self, messages: list[ChatMessage]) -> int:
        """Estimate token count for rate limiting."""
        # Rough estimation: ~4 chars per token
        total_chars = sum(len(m.content) for m in messages)
        return max(100, total_chars // 4 + self._endpoint.max_tokens)

    async def _execute_with_retry(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """Execute request with retry logic."""
        retry_config = self._endpoint.retry
        url = self._build_url()
        headers = self._build_headers()
        body = self._build_request_body(messages, temperature, max_tokens, **kwargs)
        estimated_tokens = self._estimate_tokens(messages)

        last_error: Exception | None = None

        for attempt in range(retry_config.max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limiter.acquire(estimated_tokens)

                try:
                    response = await self._client.post(
                        url,
                        json=body,
                        headers=headers,
                    )

                    # Handle response
                    if response.status_code == 200:
                        data = response.json()
                        completion = self._parse_response(data)

                        # Report actual usage
                        actual_tokens = completion.usage.get("total_tokens", estimated_tokens)
                        self._rate_limiter.report_usage(actual_tokens, estimated_tokens)

                        return completion

                    # Handle errors
                    if response.status_code == 401:
                        raise LLMAuthenticationError("Invalid API key or authentication failed")

                    if response.status_code == 429:
                        retry_after = response.headers.get("retry-after")
                        retry_seconds = float(retry_after) if retry_after else None
                        raise LLMRateLimitError(
                            "Rate limit exceeded",
                            retry_after=retry_seconds,
                        )

                    # Other errors
                    try:
                        error_body = response.json()
                    except Exception:
                        error_body = {"error": response.text}

                    raise LLMAPIError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                        response_body=error_body,
                    )

                finally:
                    self._rate_limiter.release()

            except (LLMRateLimitError, httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e

                if attempt < retry_config.max_retries:
                    delay = self._calculate_backoff(attempt, retry_config)

                    # Use retry-after header if available
                    if isinstance(e, LLMRateLimitError) and e.retry_after:
                        delay = max(delay, e.retry_after * 1000)

                    self._log.warning(
                        "Request failed, retrying",
                        attempt=attempt + 1,
                        max_retries=retry_config.max_retries,
                        delay_ms=delay,
                        error=str(e),
                    )

                    await asyncio.sleep(delay / 1000)
                else:
                    raise

            except LLMAuthenticationError:
                # Don't retry auth errors
                raise

            except LLMAPIError as e:
                last_error = e
                # Retry on 5xx errors
                if e.status_code and 500 <= e.status_code < 600:
                    if attempt < retry_config.max_retries:
                        delay = self._calculate_backoff(attempt, retry_config)
                        self._log.warning(
                            "Server error, retrying",
                            attempt=attempt + 1,
                            delay_ms=delay,
                            status_code=e.status_code,
                        )
                        await asyncio.sleep(delay / 1000)
                    else:
                        raise
                else:
                    raise

        # Should not reach here, but just in case
        raise last_error or LLMClientError("Request failed after retries")

    def _calculate_backoff(self, attempt: int, config: RetryConfig) -> float:
        """Calculate exponential backoff delay with optional jitter."""
        delay = config.initial_delay_ms * (config.exponential_base**attempt)
        delay = min(delay, config.max_delay_ms)

        if config.jitter:
            delay = delay * (0.5 + random.random())

        return delay

    def _parse_response(self, data: dict[str, Any]) -> ChatCompletion:
        """Parse the API response into a ChatCompletion."""
        choices = data.get("choices", [])
        if not choices:
            raise LLMAPIError("No choices in response", response_body=data)

        choice = choices[0]
        message = choice.get("message", {})

        return ChatCompletion(
            content=message.get("content", ""),
            model=data.get("model", self._endpoint.model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatCompletion:
        """
        Send a chat completion request.

        Args:
            messages: List of chat messages
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            **kwargs: Additional API parameters (response_format, etc.)

        Returns:
            ChatCompletion with the response

        Raises:
            LLMClientError: On API errors
            LLMRateLimitError: When rate limited
            LLMAuthenticationError: On auth failures
        """
        self._log.debug(
            "Sending chat request",
            message_count=len(messages),
            temperature=temperature or self._endpoint.temperature,
            max_tokens=max_tokens or self._endpoint.max_tokens,
        )

        result = await self._execute_with_retry(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        self._log.debug(
            "Chat request completed",
            tokens_used=result.usage.get("total_tokens"),
            finish_reason=result.finish_reason,
        )

        return result

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Simplified interface for single prompt completion.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override
            **kwargs: Additional API parameters

        Returns:
            The completion text
        """
        messages = []
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))

        result = await self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return result.content


class LLMClientFactory:
    """Factory for creating LLM clients from configuration."""

    _clients: dict[str, LLMClient] = {}
    _shared_http_client: httpx.AsyncClient | None = None

    @classmethod
    async def get_client(
        cls,
        config: LLMConfig,
        tool: ToolName,
    ) -> LLMClient | None:
        """
        Get or create an LLM client for a specific tool.

        Returns None if LLM is not enabled for the tool.
        """
        if not config.is_tool_enabled(tool):
            return None

        endpoint = config.get_effective_endpoint(tool)
        cache_key = f"{tool}:{endpoint.base_url}:{endpoint.model}"

        if cache_key not in cls._clients:
            # Create shared HTTP client if needed
            if cls._shared_http_client is None:
                cls._shared_http_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(60.0),
                )

            cls._clients[cache_key] = LLMClient(
                endpoint=endpoint,
                http_client=cls._shared_http_client,
            )

        return cls._clients[cache_key]

    @classmethod
    async def close_all(cls) -> None:
        """Close all clients and the shared HTTP client."""
        cls._clients.clear()
        if cls._shared_http_client:
            await cls._shared_http_client.aclose()
            cls._shared_http_client = None


@asynccontextmanager
async def create_llm_client(
    config: LLMConfig,
    tool: ToolName,
) -> AsyncIterator[LLMClient | None]:
    """
    Context manager for creating a temporary LLM client.

    Usage:
        async with create_llm_client(config, ToolName.TEST_BUILDER) as client:
            if client:
                result = await client.complete("Generate a test name")
    """
    if not config.is_tool_enabled(tool):
        yield None
        return

    endpoint = config.get_effective_endpoint(tool)
    client = LLMClient(endpoint=endpoint)

    try:
        yield client
    finally:
        await client.close()
