"""
Event Bus for Codegen OSS

This module provides an event bus for publishing and subscribing to events
in the codegen-oss system, enabling event-driven architecture.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Enum of event types in the system."""

    # Repository events
    REPOSITORY_ADDED = auto()
    REPOSITORY_UPDATED = auto()
    REPOSITORY_REMOVED = auto()

    # Snapshot events
    SNAPSHOT_CREATED = auto()
    SNAPSHOT_UPDATED = auto()
    SNAPSHOT_DELETED = auto()

    # Analysis events
    ANALYSIS_REQUESTED = auto()
    ANALYSIS_STARTED = auto()
    ANALYSIS_COMPLETED = auto()
    ANALYSIS_FAILED = auto()

    # Code entity events
    ENTITY_CREATED = auto()
    ENTITY_UPDATED = auto()
    ENTITY_DELETED = auto()

    # System events
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()
    SYSTEM_INFO = auto()


class Event:
    """Represents an event in the system."""

    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an event from a dictionary."""
        return cls(
            event_type=EventType[data["event_type"]],
            data=data["data"],
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )

    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create an event from a JSON string."""
        return cls.from_dict(json.loads(json_str))


EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], asyncio.coroutine]


class EventBus:
    """
    Event bus for publishing and subscribing to events.

    This implementation uses in-memory event handling. For production use,
    consider using a message broker like RabbitMQ, Redis, or Kafka.
    """

    def __init__(self):
        self.subscribers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }
        self.async_subscribers: Dict[EventType, List[AsyncEventHandler]] = {
            event_type: [] for event_type in EventType
        }
        self.event_history: List[Event] = []
        self.max_history_size = 1000

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Subscribe to an event type with a synchronous handler."""
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler {handler.__name__} to {event_type.name}")

    def subscribe_async(
        self, event_type: EventType, handler: AsyncEventHandler
    ) -> None:
        """Subscribe to an event type with an asynchronous handler."""
        self.async_subscribers[event_type].append(handler)
        logger.debug(
            f"Subscribed async handler {handler.__name__} to {event_type.name}"
        )

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type."""
        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            logger.debug(
                f"Unsubscribed handler {handler.__name__} from {event_type.name}"
            )

    def unsubscribe_async(
        self, event_type: EventType, handler: AsyncEventHandler
    ) -> None:
        """Unsubscribe an async handler from an event type."""
        if handler in self.async_subscribers[event_type]:
            self.async_subscribers[event_type].remove(handler)
            logger.debug(
                f"Unsubscribed async handler {handler.__name__} from {event_type.name}"
            )

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.

        This method calls all synchronous handlers immediately and schedules
        asynchronous handlers to be executed in the event loop.
        """
        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history.pop(0)

        # Call synchronous handlers
        for handler in self.subscribers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}")

        # Schedule asynchronous handlers
        for handler in self.async_subscribers[event.event_type]:
            asyncio.create_task(self._call_async_handler(handler, event))

    async def _call_async_handler(
        self, handler: AsyncEventHandler, event: Event
    ) -> None:
        """Call an asynchronous event handler."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in async event handler {handler.__name__}: {e}")

    def publish_from_dict(self, event_dict: Dict[str, Any]) -> None:
        """Publish an event from a dictionary."""
        event = Event.from_dict(event_dict)
        self.publish(event)

    def publish_from_json(self, json_str: str) -> None:
        """Publish an event from a JSON string."""
        event = Event.from_json(json_str)
        self.publish(event)

    def get_recent_events(self, limit: int = 100) -> List[Event]:
        """Get the most recent events."""
        return self.event_history[-limit:]

    def get_events_by_type(
        self, event_type: EventType, limit: int = 100
    ) -> List[Event]:
        """Get recent events of a specific type."""
        return [e for e in self.event_history if e.event_type == event_type][-limit:]


# Global event bus instance
event_bus = EventBus()
