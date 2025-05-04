"""
Webhook Handler Module

This module provides functionality for handling webhooks from Git providers.
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# Import from existing analysis modules


class Webhook:
    """
    Represents a webhook registered for a project.

    A webhook is a way for the analysis server to notify external services
    about events that occur in the server.
    """

    def __init__(
        self,
        webhook_id: str,
        project_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None,
        created_at: Optional[datetime] = None,
        last_triggered: Optional[datetime] = None,
    ):
        """
        Initialize a new Webhook.

        Args:
            webhook_id: Unique identifier for the webhook
            project_id: ID of the project the webhook is for
            webhook_url: URL to send webhook notifications to
            events: Events to trigger the webhook
            secret: Optional secret to sign webhook payloads with
            created_at: When the webhook was created
            last_triggered: When the webhook was last triggered
        """
        self.webhook_id = webhook_id
        self.project_id = project_id
        self.webhook_url = webhook_url
        self.events = events
        self.secret = secret
        self.created_at = created_at or datetime.now()
        self.last_triggered = last_triggered

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the webhook to a dictionary.

        Returns:
            A dictionary representation of the webhook
        """
        return {
            "webhook_id": self.webhook_id,
            "project_id": self.project_id,
            "webhook_url": self.webhook_url,
            "events": self.events,
            "secret": self.secret,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered": (
                self.last_triggered.isoformat() if self.last_triggered else None
            ),
        }


class WebhookHandler:
    """
    Handles webhooks for the analysis server.

    This class provides functionality for registering, triggering, and managing
    webhooks for the analysis server.
    """

    def __init__(self):
        """Initialize a new WebhookHandler."""
        self.webhooks: Dict[str, Webhook] = {}
        self.logger = logging.getLogger(__name__)
        self.event_handlers: Dict[str, List[Callable]] = {}

    def register_webhook(
        self,
        project_id: str,
        webhook_url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Webhook:
        """
        Register a new webhook.

        Args:
            project_id: ID of the project to register the webhook for
            webhook_url: URL to send webhook notifications to
            events: Events to trigger the webhook
            secret: Optional secret to sign webhook payloads with

        Returns:
            The registered webhook
        """
        webhook_id = str(uuid.uuid4())

        webhook = Webhook(
            webhook_id=webhook_id,
            project_id=project_id,
            webhook_url=webhook_url,
            events=events,
            secret=secret,
        )

        self.webhooks[webhook_id] = webhook
        self.logger.info(f"Registered webhook {webhook_id} for project {project_id}")

        return webhook

    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """
        Get a webhook by ID.

        Args:
            webhook_id: ID of the webhook

        Returns:
            The webhook, or None if not found
        """
        return self.webhooks.get(webhook_id)

    def get_webhooks_for_project(self, project_id: str) -> List[Webhook]:
        """
        Get all webhooks for a project.

        Args:
            project_id: ID of the project

        Returns:
            A list of webhooks for the project
        """
        return [
            webhook
            for webhook in self.webhooks.values()
            if webhook.project_id == project_id
        ]

    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Delete a webhook.

        Args:
            webhook_id: ID of the webhook

        Returns:
            True if the webhook was deleted, False otherwise
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self.logger.info(f"Deleted webhook {webhook_id}")
            return True

        return False

    def register_event_handler(self, event: str, handler: Callable) -> None:
        """
        Register a handler for an event.

        Args:
            event: Event to handle
            handler: Function to call when the event occurs
        """
        if event not in self.event_handlers:
            self.event_handlers[event] = []

        self.event_handlers[event].append(handler)
        self.logger.info(f"Registered handler for event {event}")

    def trigger_event(
        self, event: str, project_id: str, payload: Dict[str, Any]
    ) -> None:
        """
        Trigger an event.

        Args:
            event: Event to trigger
            project_id: ID of the project the event is for
            payload: Event payload
        """
        self.logger.info(f"Triggering event {event} for project {project_id}")

        # Call event handlers
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(project_id, payload)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event}: {e}")

        # Trigger webhooks
        webhooks = self.get_webhooks_for_project(project_id)

        for webhook in webhooks:
            if event in webhook.events:
                self._trigger_webhook(webhook, event, payload)

    def _trigger_webhook(
        self, webhook: Webhook, event: str, payload: Dict[str, Any]
    ) -> None:
        """
        Trigger a webhook.

        Args:
            webhook: Webhook to trigger
            event: Event that triggered the webhook
            payload: Event payload
        """
        self.logger.info(f"Triggering webhook {webhook.webhook_id} for event {event}")

        # Update last triggered time
        webhook.last_triggered = datetime.now()

        # Create webhook payload
        webhook_payload = {
            "event": event,
            "project_id": webhook.project_id,
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
        }

        # Sign payload if secret is provided
        headers = {"Content-Type": "application/json"}

        if webhook.secret:
            payload_bytes = json.dumps(webhook_payload).encode("utf-8")
            signature = hmac.new(
                webhook.secret.encode("utf-8"), payload_bytes, hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature

        # Send webhook
        try:
            # In a real implementation, we would use requests.post here
            # For now, we just log the webhook
            self.logger.info(
                f"Would send webhook to {webhook.webhook_url} with payload: "
                f"{json.dumps(webhook_payload)}"
            )
        except Exception as e:
            self.logger.error(f"Error triggering webhook {webhook.webhook_id}: {e}")
