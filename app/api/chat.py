from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_
import json
from app.db.database import get_db
from app.db.models import User, ChatChannel, Message, channel_members
from app.api.schemas import (
    ChatChannelCreate, 
    ChatChannel as ChatChannelSchema,
    MessageCreate, 
    Message as MessageSchema,
    MessageMarkRead,
    Presence
)
from app.services.websocket_manager import manager
from app.services.presence_service import presence_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# WebSocket endpoint
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time chat functionality"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "subscribe_channel":
                    channel_id = message_data.get("channel_id")
                    if channel_id:
                        await manager.subscribe_to_channel(user_id, channel_id)
                
                elif message_type == "unsubscribe_channel":
                    channel_id = message_data.get("channel_id")
                    if channel_id:
                        await manager.unsubscribe_from_channel(user_id, channel_id)
                
                elif message_type == "ping":
                    # Update last seen
                    presence_service.update_last_seen(user_id)
                    await websocket.send_text(json.dumps({"type": "pong"}))
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message from user {user_id}: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"User {user_id} disconnected from WebSocket")

# Channel endpoints
@router.post("/channels/", status_code=status.HTTP_201_CREATED, response_model=ChatChannelSchema)
async def create_channel(
    channel_data: ChatChannelCreate,
    db: Session = Depends(get_db)
):
    """Create a new chat channel"""
    
    # Validate that all member users exist
    users = db.query(User).filter(User.id.in_(channel_data.member_ids)).all()
    if len(users) != len(channel_data.member_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more user IDs are invalid"
        )
    
    # Create channel
    channel = ChatChannel(
        name=channel_data.name
    )
    db.add(channel)
    db.flush()  # Get the channel ID
    
    # Add members to channel
    for user_id in channel_data.member_ids:
        db.execute(
            channel_members.insert().values(
                channel_id=channel.id,
                user_id=user_id
            )
        )
    
    db.commit()
    db.refresh(channel)
    
    return channel

@router.get("/channels/{channel_id}", response_model=ChatChannelSchema)
async def get_channel(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """Get channel details"""
    channel = db.query(ChatChannel).filter(ChatChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with id {channel_id} not found"
        )
    return channel

# Message endpoints
@router.post("/channels/{channel_id}/messages/", status_code=status.HTTP_201_CREATED, response_model=MessageSchema)
async def send_message(
    channel_id: int,
    message_data: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message to a channel"""
    
    # Validate channel exists
    channel = db.query(ChatChannel).filter(ChatChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with id {channel_id} not found"
        )
    
    # Validate sender exists
    sender = db.query(User).filter(User.id == message_data.sender_id).first()
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sender with id {message_data.sender_id} not found"
        )
    
    # Check if sender is a member of the channel
    is_member = db.query(channel_members).filter(
        and_(
            channel_members.c.channel_id == channel_id,
            channel_members.c.user_id == message_data.sender_id
        )
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sender is not a member of this channel"
        )
    
    # Create message
    message = Message(
        sender_id=message_data.sender_id,
        channel_id=channel_id,
        body=message_data.body,
        is_read=False
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Prepare message data for WebSocket broadcast
    message_data_for_broadcast = {
        "id": message.id,
        "sender_id": message.sender_id,
        "channel_id": message.channel_id,
        "body": message.body,
        "is_read": message.is_read,
        "created_at": message.created_at.isoformat(),
        "sender_name": sender.name
    }
    
    # Broadcast new message via WebSocket
    await manager.broadcast_new_message(message_data_for_broadcast, channel_id)
    
    # Add sender name to response
    message.sender_name = sender.name
    return message

@router.post("/messages/{message_id}/mark-read/")
async def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db)
):
    """Mark a message as read"""
    
    # Get message
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id {message_id} not found"
        )
    
    # Mark as read
    message.is_read = True
    db.commit()
    
    # Broadcast read receipt via WebSocket
    await manager.broadcast_read_receipt(message_id, message.sender_id, message.channel_id)
    
    return {
        "message": "Message marked as read",
        "message_id": message_id,
        "is_read": True
    }

@router.get("/channels/{channel_id}/messages/", response_model=list[MessageSchema])
async def get_channel_messages(
    channel_id: int,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get messages from a channel"""
    
    # Validate channel exists
    channel = db.query(ChatChannel).filter(ChatChannel.id == channel_id).first()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Channel with id {channel_id} not found"
        )
    
    # Get messages with sender names
    messages = db.query(Message).filter(
        Message.channel_id == channel_id
    ).order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    
    # Add sender names
    for message in messages:
        sender = db.query(User).filter(User.id == message.sender_id).first()
        message.sender_name = sender.name if sender else "Unknown"
    
    return messages

# Presence endpoints
@router.get("/presence/{user_id}", response_model=Presence)
async def get_user_presence(user_id: int):
    """Get user presence status"""
    
    presence_data = presence_service.get_user_presence(user_id)
    
    return Presence(
        user_id=user_id,
        online=presence_data.get("online", False),
        last_seen=presence_data.get("last_seen")
    )

@router.get("/presence/online/", response_model=list[int])
async def get_online_users():
    """Get list of currently online user IDs"""
    return presence_service.get_online_users()
