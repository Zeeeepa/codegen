"""
Event bus for codegen-on-oss.

This module provides an event bus for publishing and subscribing to events.
"""

import logging
import asyncio
import threading
import queue
import json
import time
from typing import Dict, List, Any, Callable, Optional, Union, Set, Awaitable
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Event types for the event bus."""
    
    # Analysis events
    ANALYSIS_STARTED = auto()
    ANALYSIS_PROGRESS = auto()
    ANALYSIS_COMPLETED = auto()
    ANALYSIS_FAILED = auto()
    
    # Snapshot events
    SNAPSHOT_CREATED = auto()
    SNAPSHOT_UPDATED = auto()
    SNAPSHOT_DELETED = auto()
    
    # Repository events
    REPOSITORY_ADDED = auto()
    REPOSITORY_UPDATED = auto()
    REPOSITORY_DELETED = auto()
    
    # Webhook events
    WEBHOOK_TRIGGERED = auto()
    
    # System events
    SYSTEM_ERROR = auto()
    SYSTEM_WARNING = auto()
    SYSTEM_INFO = auto()


@dataclass
class Event:
    """Event class for the event bus."""
    
    type: EventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary."""
        return {
            'id': self.id,
            'type': self.type.name,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert the event to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create an event from a dictionary."""
        return cls(
            type=EventType[data['type']],
            data=data['data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            id=data['id']
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Create an event from a JSON string."""
        return cls.from_dict(json.loads(json_str))


# Type aliases for event handlers
SyncEventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Awaitable[None]]
EventHandler = Union[SyncEventHandler, AsyncEventHandler]


class EventBus:
    """
    Event bus for publishing and subscribing to events.
    
    This class provides methods for publishing events and subscribing to events
    of specific types. It supports both synchronous and asynchronous event handlers.
    """
    
    def __init__(self, async_mode: bool = False):
        """
        Initialize the event bus.
        
        Args:
            async_mode: If True, use asyncio for event handling.
        """
        self.async_mode = async_mode
        self.subscribers: Dict[EventType, List[EventHandler]] = {}
        self.event_queue: queue.Queue = queue.Queue()
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        
        # For async mode
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Initialize subscribers for all event types
        for event_type in EventType:
            self.subscribers[event_type] = []
    
    def start(self) -> None:
        """Start the event bus."""
        if self.running:
            return
        
        self.running = True
        
        if self.async_mode:
            self.loop = asyncio.new_event_loop()
            self.worker_thread = threading.Thread(target=self._async_worker, daemon=True)
        else:
            self.worker_thread = threading.Thread(target=self._sync_worker, daemon=True)
        
        self.worker_thread.start()
        logger.info("Event bus started")
    
    def stop(self) -> None:
        """Stop the event bus."""
        if not self.running:
            return
        
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
            self.worker_thread = None
        
        if self.async_mode and self.loop:
            self.loop.stop()
            self.loop.close()
            self.loop = None
        
        logger.info("Event bus stopped")
    
    def _sync_worker(self) -> None:
        """Worker thread for synchronous event handling."""
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)
                self._dispatch_sync(event)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in event bus worker: {e}")
    
    def _async_worker(self) -> None:
        """Worker thread for asynchronous event handling."""
        if not self.loop:
            self.loop = asyncio.new_event_loop()
        
        asyncio.set_event_loop(self.loop)
        
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)
                asyncio.run_coroutine_threadsafe(self._dispatch_async(event), self.loop)
                self.event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in event bus worker: {e}")
    
    def _dispatch_sync(self, event: Event) -> None:
        """
        Dispatch an event to synchronous subscribers.
        
        Args:
            event: Event to dispatch.
        """
        handlers = self.subscribers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # Run async handler in a new event loop
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(handler(event))
                    loop.close()
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    async def _dispatch_async(self, event: Event) -> None:
        """
        Dispatch an event to asynchronous subscribers.
        
        Args:
            event: Event to dispatch.
        """
        handlers = self.subscribers.get(event.type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    # Run sync handler in a thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler, event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to the event bus.
        
        Args:
            event: Event to publish.
        """
        self.event_queue.put(event)
        logger.debug(f"Published event: {event.type.name}")
    
    def publish_event(self, event_type: EventType, data: Dict[str, Any]) -> Event:
        """
        Create and publish an event.
        
        Args:
            event_type: Type of the event.
            data: Event data.
            
        Returns:
            Created and published event.
        """
        event = Event(type=event_type, data=data)
        self.publish(event)
        return event
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to.
            handler: Event handler function.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to event type: {event_type.name}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of events to unsubscribe from.
            handler: Event handler function to remove.
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from event type: {event_type.name}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type.name}")
    
    def subscribe_to_all(self, handler: EventHandler) -> None:
        """
        Subscribe to all event types.
        
        Args:
            handler: Event handler function.
        """
        for event_type in EventType:
            self.subscribe(event_type, handler)
        
        logger.debug("Subscribed to all event types")


# Global event bus instance
event_bus = EventBus()

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return event_bus

def initialize_event_bus(async_mode: bool = False) -> EventBus:
    """
    Initialize the event bus.
    
    Args:
        async_mode: If True, use asyncio for event handling.
        
    Returns:
        EventBus instance.
    """
    global event_bus
    event_bus = EventBus(async_mode)
    event_bus.start()
    return event_bus

