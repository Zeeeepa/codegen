"""
Event bus implementation for Codegen-on-OSS

This module provides an event bus for communication between components.
"""

import enum
import logging
import asyncio
import inspect
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, TypeVar, Generic

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventType(str, enum.Enum):
    """Types of events that can be published on the event bus."""

    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    
    # Issue events
    ISSUE_DETECTED = "issue_detected"
    ISSUE_RESOLVED = "issue_resolved"
    
    # Snapshot events
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_DELETED = "snapshot_deleted"
    SNAPSHOT_COMPARED = "snapshot_compared"
    
    # Codebase events
    CODEBASE_ADDED = "codebase_added"
    CODEBASE_UPDATED = "codebase_updated"
    CODEBASE_REMOVED = "codebase_removed"
    
    # Symbol events
    SYMBOL_ADDED = "symbol_added"
    SYMBOL_UPDATED = "symbol_updated"
    SYMBOL_REMOVED = "symbol_removed"
    
    # Webhook events
    WEBHOOK_RECEIVED = "webhook_received"
    
    # Custom event
    CUSTOM = "custom"


class Event(BaseModel):
    """Base event model for the event bus."""

    type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Type for event handlers
EventHandler = Callable[[Event], Any]


class EventBus:
    """
    Event bus for communication between components.
    
    This class provides a simple event bus implementation that allows components
    to publish and subscribe to events.
    """

    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus."""
        if not getattr(self, "_initialized", False):
            self._subscribers: Dict[EventType, List[EventHandler]] = {
                event_type: [] for event_type in EventType
            }
            self._wildcard_subscribers: List[EventHandler] = []
            self._event_history: List[Event] = []
            self._max_history_size = 1000
            self._initialized = True
    
    def subscribe(self, event_type: Optional[EventType], handler: EventHandler) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to, or None to subscribe to all events.
            handler: The handler function to call when an event of the specified type is published.
        """
        if event_type is None:
            self._wildcard_subscribers.append(handler)
        else:
            self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: Optional[EventType], handler: EventHandler) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from, or None to unsubscribe from all events.
            handler: The handler function to remove.
        """
        if event_type is None:
            if handler in self._wildcard_subscribers:
                self._wildcard_subscribers.remove(handler)
        else:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: The event to publish.
        """
        # Add event to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history.pop(0)
        
        # Call handlers for the specific event type
        for handler in self._subscribers[event.type]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        # Call wildcard handlers
        for handler in self._wildcard_subscribers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in wildcard event handler: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """
        Get the history of events.
        
        Args:
            event_type: Optional event type to filter by.
            
        Returns:
            A list of events, optionally filtered by type.
        """
        if event_type is None:
            return self._event_history.copy()
        return [event for event in self._event_history if event.type == event_type]
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()

