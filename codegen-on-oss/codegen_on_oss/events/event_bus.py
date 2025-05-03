"""
Event bus for the codegen-on-oss system.

This module provides an event bus for publishing and subscribing to events.
"""

import enum
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(enum.Enum):
    """Event types for the event bus."""

    # Analysis events
    ANALYSIS_STARTED = "ANALYSIS_STARTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
    ANALYSIS_PROGRESS = "ANALYSIS_PROGRESS"

    # Snapshot events
    SNAPSHOT_CREATED = "SNAPSHOT_CREATED"
    SNAPSHOT_UPDATED = "SNAPSHOT_UPDATED"
    SNAPSHOT_DELETED = "SNAPSHOT_DELETED"

    # Repository events
    REPOSITORY_ADDED = "REPOSITORY_ADDED"
    REPOSITORY_UPDATED = "REPOSITORY_UPDATED"
    REPOSITORY_DELETED = "REPOSITORY_DELETED"

    # Job events
    JOB_CREATED = "JOB_CREATED"
    JOB_STARTED = "JOB_STARTED"
    JOB_COMPLETED = "JOB_COMPLETED"
    JOB_FAILED = "JOB_FAILED"

    # PR events
    PR_CREATED = "PR_CREATED"
    PR_UPDATED = "PR_UPDATED"
    PR_MERGED = "PR_MERGED"
    PR_CLOSED = "PR_CLOSED"
    PR_ANALYZED = "PR_ANALYZED"

    # Commit events
    COMMIT_CREATED = "COMMIT_CREATED"
    COMMIT_ANALYZED = "COMMIT_ANALYZED"

    # Webhook events
    WEBHOOK_TRIGGERED = "WEBHOOK_TRIGGERED"
    WEBHOOK_FAILED = "WEBHOOK_FAILED"

    # Issue events
    ISSUE_DETECTED = "ISSUE_DETECTED"
    ISSUE_RESOLVED = "ISSUE_RESOLVED"

    # System events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    SYSTEM_INFO = "SYSTEM_INFO"


class Event:
    """Event class for the event bus."""

    def __init__(self, event_type: EventType, data: Dict[str, Any]):
        """
        Initialize an event.

        Args:
            event_type: Event type
            data: Event data
        """
        self.event_type = event_type
        self.data = data
        self.timestamp = time.time()

    def __str__(self) -> str:
        """
        Get a string representation of the event.

        Returns:
            String representation
        """
        return f"Event({self.event_type}, {self.data})"


class EventBus:
    """Event bus for publishing and subscribing to events."""

    def __init__(self):
        """Initialize the event bus."""
        self.subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self.event_queue = queue.Queue()
        self.running = False
        self.worker_thread = None

    def start(self):
        """Start the event bus worker thread."""
        if self.running:
            return

        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Event bus started")

    def stop(self):
        """Stop the event bus worker thread."""
        if not self.running:
            return

        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=1.0)
        logger.info("Event bus stopped")

    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """
        Subscribe to an event type.

        Args:
            event_type: Event type to subscribe to
            callback: Callback function to call when an event of this type is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """
        Unsubscribe from an event type.

        Args:
            event_type: Event type to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type}")

    def publish(self, event: Event):
        """
        Publish an event.

        Args:
            event: Event to publish
        """
        self.event_queue.put(event)
        logger.debug(f"Published event: {event}")

    def _worker(self):
        """Worker thread for processing events."""
        while self.running:
            try:
                # Get an event from the queue with a timeout
                try:
                    event = self.event_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Process the event
                self._process_event(event)

                # Mark the event as processed
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Error in event bus worker: {e}")

    def _process_event(self, event: Event):
        """
        Process an event by calling all subscribers.

        Args:
            event: Event to process
        """
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")


# Global event bus instance
event_bus = EventBus()

