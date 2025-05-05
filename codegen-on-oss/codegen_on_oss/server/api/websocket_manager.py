"""
WebSocket manager for the codegen-on-oss system.

This module provides a WebSocket manager for real-time updates.
"""

import json
import logging
from typing import Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

# Update imports to use the new server module structure
from codegen_on_oss.events.event_bus import Event, EventType, event_bus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket manager for real-time updates."""

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[EventType]] = {}
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Set up event handlers for all event types."""
        for event_type in EventType:
            event_bus.subscribe(event_type, self._handle_event)

    async def _handle_event(self, event: Event):
        """
        Handle an event by sending it to subscribed clients.

        Args:
            event: Event to handle
        """
        # Convert event to JSON-serializable format
        event_data = {
            "type": event.event_type.value,
            "data": event.data,
            "timestamp": event.timestamp,
        }

        # Send event to subscribed clients
        for client_id, subscribed_events in self.subscriptions.items():
            if event.event_type in subscribed_events:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_json(event_data)
                    except Exception as e:
                        logger.error(f"Error sending event to client {client_id}: {e}")
                        await self.disconnect(client_id)

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a client.

        Args:
            websocket: WebSocket connection
            client_id: Client ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        # Send welcome message
        await websocket.send_json(
            {
                "type": "welcome",
                "client_id": client_id,
                "message": "Connected to WebSocket server",
            }
        )

        logger.info(f"Client {client_id} connected")

    async def disconnect(self, client_id: str):
        """
        Disconnect a client.

        Args:
            client_id: Client ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected")

    async def subscribe(self, client_id: str, event_types: List[str]):
        """
        Subscribe a client to event types.

        Args:
            client_id: Client ID
            event_types: Event types to subscribe to
        """
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()

        # Convert string event types to enum values
        for event_type_str in event_types:
            try:
                event_type = EventType(event_type_str)
                self.subscriptions[client_id].add(event_type)
            except ValueError:
                logger.warning(f"Invalid event type: {event_type_str}")

        # Send confirmation
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(
                {
                    "type": "subscribed",
                    "event_types": [et.value for et in self.subscriptions[client_id]],
                }
            )

        logger.info(f"Client {client_id} subscribed to {event_types}")

    async def unsubscribe(self, client_id: str, event_types: List[str]):
        """
        Unsubscribe a client from event types.

        Args:
            client_id: Client ID
            event_types: Event types to unsubscribe from
        """
        if client_id not in self.subscriptions:
            return

        # Convert string event types to enum values and remove from subscriptions
        for event_type_str in event_types:
            try:
                event_type = EventType(event_type_str)
                if event_type in self.subscriptions[client_id]:
                    self.subscriptions[client_id].remove(event_type)
            except ValueError:
                logger.warning(f"Invalid event type: {event_type_str}")

        # Send confirmation
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(
                {
                    "type": "unsubscribed",
                    "event_types": event_types,
                }
            )

        logger.info(f"Client {client_id} unsubscribed from {event_types}")

    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """
        Handle a WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Client ID
        """
        await self.connect(websocket, client_id)

        try:
            while True:
                # Receive message
                message = await websocket.receive_text()

                try:
                    # Parse message
                    data = json.loads(message)

                    # Handle message based on type
                    if data.get("type") == "subscribe":
                        await self.subscribe(client_id, data.get("event_types", []))
                    elif data.get("type") == "unsubscribe":
                        await self.unsubscribe(client_id, data.get("event_types", []))
                    elif data.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    else:
                        await websocket.send_json(
                            {
                                "type": "error",
                                "message": f"Unknown message type: {data.get('type')}",
                            }
                        )
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        }
                    )
                except Exception as e:
                    logger.error(f"Error handling message from client {client_id}: {e}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": str(e),
                        }
                    )
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error in WebSocket connection for client {client_id}: {e}")
            await self.disconnect(client_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
