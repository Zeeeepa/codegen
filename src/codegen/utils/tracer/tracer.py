"""
Tracer implementation for Codegen.

This module provides tracing functionality for the Codegen application.
"""

import functools
import inspect
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from codegen.utils.logger import get_logger

# Logger for the tracer
logger = get_logger("codegen.tracer")

# Type variable for function return type
T = TypeVar("T")


@dataclass
class TraceEvent:
    """
    Represents a trace event in the system.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str = "trace"
    function_name: str = ""
    module_name: str = ""
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    return_value: Any = None
    exception: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the trace event to a dictionary.

        Returns:
            A dictionary representation of the trace event.
        """
        return asdict(self)

    def to_json(self) -> str:
        """
        Convert the trace event to a JSON string.

        Returns:
            A JSON string representation of the trace event.
        """
        return json.dumps(self.to_dict(), default=str)


class CodegenTracer:
    """
    Tracer for Codegen operations.
    """

    def __init__(self, enabled: bool = True):
        """
        Initialize the tracer.

        Args:
            enabled: Whether tracing is enabled (default: True).
        """
        self.enabled = enabled
        self.events: List[TraceEvent] = []

    def add_event(self, event: TraceEvent) -> None:
        """
        Add a trace event.

        Args:
            event: The trace event to add.
        """
        if not self.enabled:
            return

        self.events.append(event)
        logger.debug(f"Trace event: {event.to_json()}")

    def clear(self) -> None:
        """
        Clear all trace events.
        """
        self.events.clear()

    def get_events(self) -> List[TraceEvent]:
        """
        Get all trace events.

        Returns:
            A list of all trace events.
        """
        return self.events

    def export_events(self, format_type: str = "json") -> str:
        """
        Export all trace events in the specified format.

        Args:
            format_type: The format to export the events in (default: "json").

        Returns:
            A string representation of all trace events in the specified format.
        """
        if format_type == "json":
            return json.dumps([event.to_dict() for event in self.events], default=str)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")


# Global tracer instance
_tracer = CodegenTracer()


def get_tracer() -> CodegenTracer:
    """
    Get the global tracer instance.

    Returns:
        The global tracer instance.
    """
    return _tracer


def trace(func: Optional[Callable[..., T]] = None, **trace_kwargs: Any) -> Callable[..., T]:
    """
    Decorator to trace function calls.

    Args:
        func: The function to trace.
        **trace_kwargs: Additional metadata to include in the trace event.

    Returns:
        The decorated function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if not _tracer.enabled:
                return func(*args, **kwargs)

            # Create trace event
            event = TraceEvent(
                function_name=func.__name__,
                module_name=func.__module__,
                args=[arg for arg in args if not inspect.isclass(arg)],
                kwargs={k: v for k, v in kwargs.items()},
                metadata=trace_kwargs,
            )

            # Record start time
            start_time = time.time()

            try:
                # Call the function
                result = func(*args, **kwargs)
                # Record return value
                event.return_value = result
                return result
            except Exception as e:
                # Record exception
                event.exception = f"{type(e).__name__}: {str(e)}"
                raise
            finally:
                # Record duration
                event.duration_ms = (time.time() - start_time) * 1000
                # Add event to tracer
                _tracer.add_event(event)

        return cast(Callable[..., T], wrapper)

    if func is None:
        return decorator
    return decorator(func)
