"""
Event handlers for Codegen-on-OSS

This module provides base classes and utilities for event handlers.
"""

import abc
import logging
from typing import Any, Dict, List, Optional, Set, Type, Union

from codegen_on_oss.events.event_bus import Event, EventType, EventBus

logger = logging.getLogger(__name__)


class EventHandler(abc.ABC):
    """Base class for event handlers."""
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the event handler.
        
        Args:
            event_bus: The event bus to use. If None, a new event bus will be created.
        """
        self.event_bus = event_bus or EventBus()
        self.subscribed_events: Set[EventType] = set()
    
    def subscribe(self, event_types: Union[EventType, List[EventType], None] = None) -> None:
        """
        Subscribe to events.
        
        Args:
            event_types: The event types to subscribe to. If None, subscribe to all events.
        """
        if event_types is None:
            self.event_bus.subscribe(None, self.handle_event)
            self.subscribed_events = set(EventType)
        elif isinstance(event_types, list):
            for event_type in event_types:
                self.event_bus.subscribe(event_type, self.handle_event)
                self.subscribed_events.add(event_type)
        else:
            self.event_bus.subscribe(event_types, self.handle_event)
            self.subscribed_events.add(event_types)
    
    def unsubscribe(self, event_types: Union[EventType, List[EventType], None] = None) -> None:
        """
        Unsubscribe from events.
        
        Args:
            event_types: The event types to unsubscribe from. If None, unsubscribe from all events.
        """
        if event_types is None:
            self.event_bus.unsubscribe(None, self.handle_event)
            for event_type in self.subscribed_events:
                self.event_bus.unsubscribe(event_type, self.handle_event)
            self.subscribed_events.clear()
        elif isinstance(event_types, list):
            for event_type in event_types:
                self.event_bus.unsubscribe(event_type, self.handle_event)
                if event_type in self.subscribed_events:
                    self.subscribed_events.remove(event_type)
        else:
            self.event_bus.unsubscribe(event_types, self.handle_event)
            if event_types in self.subscribed_events:
                self.subscribed_events.remove(event_types)
    
    def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        Args:
            event: The event to publish.
        """
        self.event_bus.publish(event)
    
    @abc.abstractmethod
    def handle_event(self, event: Event) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle.
        """
        pass

