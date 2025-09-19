from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime, timezone
from app.core.logging import get_logger
from app.services.presence_service import presence_service
from app.api.schemas import NewMessageEvent, ReadReceiptEvent, PresenceChangeEvent

logger = get_logger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Map of user_id -> WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}
        # Map of channel_id -> Set of user_ids
        self.channel_subscriptions: Dict[int, Set[int]] = {}
        # Map of user_id -> Set of channel_ids they're subscribed to
        self.user_subscriptions: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept WebSocket connection and mark user as online"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        # Mark user as online
        presence_service.set_user_online(user_id)
        
        # Broadcast presence change
        await self.broadcast_presence_change(user_id, True)
        
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, user_id: int):
        """Remove WebSocket connection and mark user as offline"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Mark user as offline
        presence_service.set_user_offline(user_id)
        
        # Clean up subscriptions
        if user_id in self.user_subscriptions:
            for channel_id in self.user_subscriptions[user_id]:
                if channel_id in self.channel_subscriptions:
                    self.channel_subscriptions[channel_id].discard(user_id)
            del self.user_subscriptions[user_id]
        
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: str, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_channel(self, message: str, channel_id: int, exclude_user: int = None):
        """Broadcast message to all users in a channel"""
        if channel_id not in self.channel_subscriptions:
            return
        
        for user_id in self.channel_subscriptions[channel_id].copy():
            if user_id != exclude_user and user_id in self.active_connections:
                try:
                    await self.active_connections[user_id].send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    self.disconnect(user_id)
    
    async def subscribe_to_channel(self, user_id: int, channel_id: int):
        """Subscribe user to channel updates"""
        if channel_id not in self.channel_subscriptions:
            self.channel_subscriptions[channel_id] = set()
        
        self.channel_subscriptions[channel_id].add(user_id)
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        self.user_subscriptions[user_id].add(channel_id)
        
        logger.info(f"User {user_id} subscribed to channel {channel_id}")
    
    async def unsubscribe_from_channel(self, user_id: int, channel_id: int):
        """Unsubscribe user from channel updates"""
        if channel_id in self.channel_subscriptions:
            self.channel_subscriptions[channel_id].discard(user_id)
        
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel_id)
        
        logger.info(f"User {user_id} unsubscribed from channel {channel_id}")
    
    async def broadcast_new_message(self, message_data: dict, channel_id: int):
        """Broadcast new message to channel subscribers"""
        event = NewMessageEvent(
            type="new_message",
            message=message_data
        )
        
        await self.broadcast_to_channel(
            event.model_dump_json(),
            channel_id,
            exclude_user=message_data.get("sender_id")
        )
    
    async def broadcast_read_receipt(self, message_id: int, user_id: int, channel_id: int):
        """Broadcast read receipt to channel subscribers"""
        event = ReadReceiptEvent(
            type="read_receipt",
            message_id=message_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc)
        )
        
        await self.broadcast_to_channel(
            event.model_dump_json(),
            channel_id,
            exclude_user=user_id  # Don't send to the user who read it
        )
    
    async def broadcast_presence_change(self, user_id: int, online: bool):
        """Broadcast presence change to all connected users"""
        event = PresenceChangeEvent(
            type="presence_change",
            user_id=user_id,
            online=online,
            last_seen=datetime.now(timezone.utc) if not online else None
        )
        
        message = event.model_dump_json()
        for connected_user_id in self.active_connections.copy():
            if connected_user_id != user_id:  # Don't send to the user whose presence changed
                try:
                    await self.active_connections[connected_user_id].send_text(message)
                except Exception as e:
                    logger.error(f"Failed to send presence update to user {connected_user_id}: {e}")
                    self.disconnect(connected_user_id)
    
    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs"""
        return list(self.active_connections.keys())
    
    def is_user_connected(self, user_id: int) -> bool:
        """Check if user is currently connected"""
        return user_id in self.active_connections

# Global connection manager instance
manager = ConnectionManager()
