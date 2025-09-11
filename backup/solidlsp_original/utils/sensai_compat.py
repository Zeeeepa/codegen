"""
SensAI compatibility layer for SolidLSP integration.

Provides minimal replacements for sensai.util.string.ToStringMixin
and sensai.util.logging.LogTime to avoid external dependency.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Generator


class ToStringMixin:
    """Minimal replacement for sensai.util.string.ToStringMixin"""
    
    def __str__(self) -> str:
        """Default string representation using class name and key attributes."""
        class_name = self.__class__.__name__
        attrs = []
        
        # Get key attributes (non-private, non-callable)
        for key, value in self.__dict__.items():
            if not key.startswith('_') and not callable(value):
                # Limit string length for readability
                value_str = repr(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
                attrs.append(f"{key}={value_str}")
        
        if attrs:
            return f"{class_name}({', '.join(attrs)})"
        else:
            return f"{class_name}()"


@contextmanager
def LogTime(message: str, logger: logging.Logger = None) -> Generator[None, None, None]:
    """Minimal replacement for sensai.util.logging.LogTime"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    start_time = time.time()
    logger.debug(f"Starting: {message}")
    
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.debug(f"Completed: {message} (took {elapsed:.3f}s)")
