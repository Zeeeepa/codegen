"""
WebSocket Manager Module

This module provides WebSocket support for real-time updates to the frontend.
It manages WebSocket connections and sends updates to connected clients.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket connection manager.
    
    This class manages WebSocket connections and provides methods for sending
    messages to connected clients.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """
        Connect a client.
        
        Args:
            client_id: The client ID
            websocket: The WebSocket connection
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, client_id: str) -> None:
        """
        Disconnect a client.
        
        Args:
            client_id: The client ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        
        logger.info(f"Client {client_id} disconnected")
    
    def subscribe(self, client_id: str, topic: str) -> None:
        """
        Subscribe a client to a topic.
        
        Args:
            client_id: The client ID
            topic: The topic to subscribe to
        """
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].add(topic)
            logger.info(f"Client {client_id} subscribed to {topic}")
    
    def unsubscribe(self, client_id: str, topic: str) -> None:
        """
        Unsubscribe a client from a topic.
        
        Args:
            client_id: The client ID
            topic: The topic to unsubscribe from
        """
        if client_id in self.client_subscriptions and topic in self.client_subscriptions[client_id]:
            self.client_subscriptions[client_id].remove(topic)
            logger.info(f"Client {client_id} unsubscribed from {topic}")
    
    def get_subscriptions(self, client_id: str) -> Set[str]:
        """
        Get a client's subscriptions.
        
        Args:
            client_id: The client ID
            
        Returns:
            A set of topics the client is subscribed to
        """
        return self.client_subscriptions.get(client_id, set())
    
    def get_subscribers(self, topic: str) -> List[str]:
        """
        Get all clients subscribed to a topic.
        
        Args:
            topic: The topic
            
        Returns:
            A list of client IDs subscribed to the topic
        """
        return [
            client_id for client_id, topics in self.client_subscriptions.items()
            if topic in topics
        ]
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str) -> None:
        """
        Send a message to a specific client.
        
        Args:
            message: The message to send
            client_id: The client ID
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
                logger.debug(f"Sent message to client {client_id}")
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
                logger.debug(f"Broadcast message to client {client_id}")
            except Exception as e:
                logger.error(f"Error broadcasting message to client {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all clients subscribed to a topic.
        
        Args:
            topic: The topic
            message: The message to broadcast
        """
        subscribers = self.get_subscribers(topic)
        for client_id in subscribers:
            await self.send_personal_message(message, client_id)
        
        logger.debug(f"Broadcast message to {len(subscribers)} subscribers of topic {topic}")

class WebSocketManager:
    """
    WebSocket manager for real-time updates.
    
    This class provides methods for managing WebSocket connections and sending
    real-time updates to connected clients.
    """
    
    def __init__(self):
        """Initialize the WebSocket manager."""
        self.connection_manager = ConnectionManager()
    
    async def handle_connection(self, websocket: WebSocket, client_id: str) -> None:
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            client_id: The client ID
        """
        await self.connection_manager.connect(client_id, websocket)
        
        try:
            while True:
                # Receive and process messages from the client
                data = await websocket.receive_json()
                await self.handle_client_message(client_id, data)
        except WebSocketDisconnect:
            self.connection_manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"Error handling WebSocket connection for client {client_id}: {e}")
            self.connection_manager.disconnect(client_id)
    
    async def handle_client_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """
        Handle a message from a client.
        
        Args:
            client_id: The client ID
            message: The message from the client
        """
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # Subscribe to a topic
            topic = message.get("topic")
            if topic:
                self.connection_manager.subscribe(client_id, topic)
                await self.connection_manager.send_personal_message(
                    {
                        "type": "subscription",
                        "status": "success",
                        "topic": topic,
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
        elif message_type == "unsubscribe":
            # Unsubscribe from a topic
            topic = message.get("topic")
            if topic:
                self.connection_manager.unsubscribe(client_id, topic)
                await self.connection_manager.send_personal_message(
                    {
                        "type": "subscription",
                        "status": "unsubscribed",
                        "topic": topic,
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
        elif message_type == "ping":
            # Respond to ping with pong
            await self.connection_manager.send_personal_message(
                {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
        else:
            # Unknown message type
            await self.connection_manager.send_personal_message(
                {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
    
    async def send_update(self, client_id: str, data: Dict[str, Any]) -> None:
        """
        Send an update to a specific client.
        
        Args:
            client_id: The client ID
            data: The update data
        """
        message = {
            "type": "update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.send_personal_message(message, client_id)
    
    async def broadcast_update(self, data: Dict[str, Any]) -> None:
        """
        Broadcast an update to all connected clients.
        
        Args:
            data: The update data
        """
        message = {
            "type": "update",
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast(message)
    
    async def broadcast_topic_update(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Broadcast an update to all clients subscribed to a topic.
        
        Args:
            topic: The topic
            data: The update data
        """
        message = {
            "type": "update",
            "topic": topic,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast_to_topic(topic, message)
    
    async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: The event type
            data: The event data
        """
        message = {
            "type": "event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast(message)
    
    async def broadcast_topic_event(self, topic: str, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast an event to all clients subscribed to a topic.
        
        Args:
            topic: The topic
            event_type: The event type
            data: The event data
        """
        message = {
            "type": "event",
            "topic": topic,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.connection_manager.broadcast_to_topic(topic, message)

# Create a global WebSocket manager instance
websocket_manager = WebSocketManager()
"""

