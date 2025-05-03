"""
Event handlers for the codegen-on-oss system.

This module provides base classes for event handlers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from codegen_on_oss.events.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Base class for event handlers."""

    def __init__(self, event_types: List[EventType]):
        """
        Initialize the event handler.

        Args:
            event_types: Event types to handle
        """
        self.event_types = event_types
        self._register()

    def _register(self):
        """Register the event handler with the event bus."""
        for event_type in self.event_types:
            event_bus.subscribe(event_type, self.handle_event)

    def unregister(self):
        """Unregister the event handler from the event bus."""
        for event_type in self.event_types:
            event_bus.unsubscribe(event_type, self.handle_event)

    def handle_event(self, event: Event):
        """
        Handle an event.

        Args:
            event: Event to handle
        """
        try:
            self._handle_event(event)
        except Exception as e:
            logger.error(f"Error handling event {event}: {e}")

    @abstractmethod
    def _handle_event(self, event: Event):
        """
        Handle an event (to be implemented by subclasses).

        Args:
            event: Event to handle
        """
        pass


class AnalysisEventHandler(EventHandler):
    """Base class for analysis event handlers."""

    def __init__(self):
        """Initialize the analysis event handler."""
        super().__init__(
            [
                EventType.ANALYSIS_STARTED,
                EventType.ANALYSIS_COMPLETED,
                EventType.ANALYSIS_FAILED,
                EventType.ANALYSIS_PROGRESS,
            ]
        )


class SnapshotEventHandler(EventHandler):
    """Base class for snapshot event handlers."""

    def __init__(self):
        """Initialize the snapshot event handler."""
        super().__init__(
            [
                EventType.SNAPSHOT_CREATED,
                EventType.SNAPSHOT_UPDATED,
                EventType.SNAPSHOT_DELETED,
            ]
        )


class RepositoryEventHandler(EventHandler):
    """Base class for repository event handlers."""

    def __init__(self):
        """Initialize the repository event handler."""
        super().__init__(
            [
                EventType.REPOSITORY_ADDED,
                EventType.REPOSITORY_UPDATED,
                EventType.REPOSITORY_DELETED,
            ]
        )


class JobEventHandler(EventHandler):
    """Base class for job event handlers."""

    def __init__(self):
        """Initialize the job event handler."""
        super().__init__(
            [
                EventType.JOB_CREATED,
                EventType.JOB_STARTED,
                EventType.JOB_COMPLETED,
                EventType.JOB_FAILED,
            ]
        )


class PREventHandler(EventHandler):
    """Base class for PR event handlers."""

    def __init__(self):
        """Initialize the PR event handler."""
        super().__init__(
            [
                EventType.PR_CREATED,
                EventType.PR_UPDATED,
                EventType.PR_MERGED,
                EventType.PR_CLOSED,
                EventType.PR_ANALYZED,
            ]
        )


class CommitEventHandler(EventHandler):
    """Base class for commit event handlers."""

    def __init__(self):
        """Initialize the commit event handler."""
        super().__init__(
            [
                EventType.COMMIT_CREATED,
                EventType.COMMIT_ANALYZED,
            ]
        )


class WebhookEventHandler(EventHandler):
    """Base class for webhook event handlers."""

    def __init__(self):
        """Initialize the webhook event handler."""
        super().__init__(
            [
                EventType.WEBHOOK_TRIGGERED,
                EventType.WEBHOOK_FAILED,
            ]
        )


class IssueEventHandler(EventHandler):
    """Base class for issue event handlers."""

    def __init__(self):
        """Initialize the issue event handler."""
        super().__init__(
            [
                EventType.ISSUE_DETECTED,
                EventType.ISSUE_RESOLVED,
            ]
        )


class SystemEventHandler(EventHandler):
    """Base class for system event handlers."""

    def __init__(self):
        """Initialize the system event handler."""
        super().__init__(
            [
                EventType.SYSTEM_ERROR,
                EventType.SYSTEM_WARNING,
                EventType.SYSTEM_INFO,
            ]
        )

