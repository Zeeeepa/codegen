"""
Event Bus Module

This module provides an event bus system for decoupling components in the application.
It allows components to publish events and subscribe to events of interest.
"""

import logging
import asyncio
import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Set, Optional, Union, Awaitable
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Enumeration of event types in the system."""
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_FAILED = "analysis_failed"
    
    # Snapshot events
    SNAPSHOT_CREATED = "snapshot_created"
    SNAPSHOT_UPDATED = "snapshot_updated"
    SNAPSHOT_DELETED = "snapshot_deleted"
    
    # Repository events
    REPOSITORY_ADDED = "repository_added"
    REPOSITORY_UPDATED = "repository_updated"
    REPOSITORY_DELETED = "repository_deleted"
    
    # Issue events
    ISSUE_DETECTED = "issue_detected"
    ISSUE_RESOLVED = "issue_resolved"
    
    # PR events
    PR_CREATED = "pr_created"
    PR_UPDATED = "pr_updated"
    PR_MERGED = "pr_merged"
    PR_CLOSED = "pr_closed"
    PR_ANALYZED = "pr_analyzed"
    
    # Commit events
    COMMIT_CREATED = "commit_created"
    COMMIT_ANALYZED = "commit_analyzed"
    
    # Job events
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    
    # Webhook events
    WEBHOOK_TRIGGERED = "webhook_triggered"
    WEBHOOK_FAILED = "webhook_failed"

class Event:
    """
    Event class representing an event in the system.
    
    An event has a type, a payload, and metadata such as timestamp and source.
    """
    
    def __init__(
        self, 
        event_type: EventType, 
        payload: Dict[str, Any],
        source: Optional[str] = None
    ):
        """
        Initialize a new event.
        
        Args:
            event_type: The type of the event
            payload: The event payload
            source: Optional source of the event
        """
        self.event_type = event_type
        self.payload = payload
        self.source = source
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        """Get a string representation of the event."""
        return f"Event({self.event_type}, source={self.source}, timestamp={self.timestamp})"

class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    This class provides methods for components to publish events and subscribe to
    events of interest. It supports both synchronous and asynchronous event handlers.
    """
    
    def __init__(self):
        """Initialize a new event bus."""
        self.subscribers = defaultdict(list)
        self.history: List[Event] = []
        self.max_history_size = 1000
    
    def subscribe(self, event_type: EventType, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The event type to subscribe to
            callback: The callback function to invoke when the event occurs
        """
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Dict[str, Any]], Any]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self.subscribers:
            self.subscribers[event_type] = [
                cb for cb in self.subscribers[event_type] if cb != callback
            ]
            logger.debug(f"Unsubscribed from {event_type}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event.
        
        This method invokes all subscribers to the event type. If a subscriber
        is a coroutine function, it is scheduled to run asynchronously.
        
        Args:
            event: The event to publish
        """
        logger.debug(f"Publishing event: {event}")
        
        # Add to history
        self.history.append(event)
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
        
        # Notify subscribers
        for callback in self.subscribers[event.event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Schedule coroutine to run
                    asyncio.create_task(callback(event.payload))
                else:
                    # Call synchronous function directly
                    callback(event.payload)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.
        
        This method awaits all asynchronous subscribers to the event type and
        calls all synchronous subscribers.
        
        Args:
            event: The event to publish
        """
        logger.debug(f"Publishing event asynchronously: {event}")
        
        # Add to history
        self.history.append(event)
        if len(self.history) > self.max_history_size:
            self.history = self.history[-self.max_history_size:]
        
        # Notify subscribers
        tasks = []
        for callback in self.subscribers[event.event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Create task for coroutine
                    tasks.append(asyncio.create_task(callback(event.payload)))
                else:
                    # Call synchronous function directly
                    callback(event.payload)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        # Await all asynchronous tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """
        Get the event history.
        
        Args:
            event_type: Optional event type to filter by
            
        Returns:
            A list of events
        """
        if event_type:
            return [event for event in self.history if event.event_type == event_type]
        return self.history

# Create a global event bus instance
event_bus = EventBus()

def subscribe(event_type: EventType):
    """
    Decorator for subscribing a function to an event type.
    
    Args:
        event_type: The event type to subscribe to
        
    Returns:
        A decorator function
    """
    def decorator(func):
        event_bus.subscribe(event_type, func)
        return func
    return decorator
"""

