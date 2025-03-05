"""Retry utilities for handling rate limits and other transient errors."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar, cast

import anthropic
import openai

logger = logging.getLogger(__name__)

# Type variable for the decorator
T = TypeVar("T")


def retry_on_rate_limit(max_retries: int = 3, base_delay: float = 45.0) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry functions on rate limit errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries (will be multiplied by 2^retry_count)

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except (openai.RateLimitError, anthropic.RateLimitError) as e:
                    retries += 1
                    if retries > max_retries:
                        logger.exception(f"Rate limit exceeded after {max_retries} retries. Giving up.")
                        raise

                    # Calculate delay with exponential backoff: base_delay * 2^(retry_count-1)
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"Rate limit hit. Retrying in {delay:.1f} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(delay)
                except Exception as e:
                    # Re-raise other exceptions
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except (openai.RateLimitError, anthropic.RateLimitError) as e:
                    retries += 1
                    if retries > max_retries:
                        logger.exception(f"Rate limit exceeded after {max_retries} retries. Giving up.")
                        raise

                    # Calculate delay with exponential backoff: base_delay * 2^(retry_count-1)
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"Rate limit hit. Retrying in {delay:.1f} seconds... (Attempt {retries}/{max_retries})")
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Re-raise other exceptions
                    raise

        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return cast(Callable[..., T], async_wrapper)
        return cast(Callable[..., T], wrapper)

    return decorator
