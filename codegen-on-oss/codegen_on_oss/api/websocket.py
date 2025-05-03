"""
WebSocket support for Codegen-on-OSS

This module provides WebSocket support for real-time updates.
"""

import json
import logging
import asyncio
from typing import Dict, List, Set, Any, Optional, Callable, Awaitable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from codegen_on_oss.events import EventBus, Event, EventType, EventHandler

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket manager for real-time updates.
    
    This class manages WebSocket connections and forwards events from the
    event bus to connected clients.
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the WebSocket manager.
        
        Args:
            event_bus: The event bus to use. If None, a new event bus will be created.
        """
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[EventType]] = {}
        self.event_bus = event_bus or EventBus()
        
        # Subscribe to all events
        self.event_bus.subscribe(None, self._handle_event)
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Connect a WebSocket client.
        
        Args:
            websocket: The WebSocket connection.
            client_id: A unique ID for the client.
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_subscriptions[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str) -> None:
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: The ID of the client to disconnect.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.connection_subscriptions:
            del self.connection_subscriptions[client_id]
        
        logger.info(f"WebSocket client {client_id} disconnected")
    
    async def subscribe(self, client_id: str, event_types: List[EventType]) -> None:
        """
        Subscribe a client to events.
        
        Args:
            client_id: The ID of the client.
            event_types: The event types to subscribe to.
        """
        if client_id not in self.connection_subscriptions:
            return
        
        for event_type in event_types:
            self.connection_subscriptions[client_id].add(event_type)
        
        logger.info(f"WebSocket client {client_id} subscribed to {event_types}")
    
    async def unsubscribe(self, client_id: str, event_types: List[EventType]) -> None:
        """
        Unsubscribe a client from events.
        
        Args:
            client_id: The ID of the client.
            event_types: The event types to unsubscribe from.
        """
        if client_id not in self.connection_subscriptions:
            return
        
        for event_type in event_types:
            if event_type in self.connection_subscriptions[client_id]:
                self.connection_subscriptions[client_id].remove(event_type)
        
        logger.info(f"WebSocket client {client_id} unsubscribed from {event_types}")
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast.
        """
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: The ID of the client.
            message: The message to send.
            
        Returns:
            True if the message was sent, False otherwise.
        """
        if client_id not in self.active_connections:
            return False
        
        try:
            await self.active_connections[client_id].send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            self.disconnect(client_id)
            return False
    
    async def _handle_event(self, event: Event) -> None:
        """
        Handle an event from the event bus.
        
        Args:
            event: The event to handle.
        """
        # Convert event to a JSON-serializable dict
        event_dict = event.dict()
        
        # Send event to subscribed clients
        for client_id, subscriptions in self.connection_subscriptions.items():
            if event.type in subscriptions or len(subscriptions) == 0:
                await self.send_to_client(client_id, {
                    "type": "event",
                    "event": event_dict,
                })
    
    async def handle_client(self, websocket: WebSocket, client_id: str) -> None:
        """
        Handle a WebSocket client.
        
        Args:
            websocket: The WebSocket connection.
            client_id: The ID of the client.
        """
        await self.connect(websocket, client_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle message
                if "type" not in data:
                    continue
                
                if data["type"] == "subscribe" and "event_types" in data:
                    await self.subscribe(client_id, data["event_types"])
                
                elif data["type"] == "unsubscribe" and "event_types" in data:
                    await self.unsubscribe(client_id, data["event_types"])
        
        except WebSocketDisconnect:
            self.disconnect(client_id)
        
        except Exception as e:
            logger.error(f"Error handling WebSocket client {client_id}: {e}")
            self.disconnect(client_id)


def add_websocket_routes(app: FastAPI, websocket_manager: WebSocketManager) -> None:
    """
    Add WebSocket routes to a FastAPI app.
    
    Args:
        app: The FastAPI app.
        websocket_manager: The WebSocket manager.
    """
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await websocket_manager.handle_client(websocket, client_id)

