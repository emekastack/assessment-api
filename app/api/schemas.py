from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.db.models import RequestStatus

# User schemas
class UserBase(BaseModel):
    email: str
    name: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Partner Request schemas
class PartnerRequestCreate(BaseModel):
    sender_id: int
    recipient_id: int

class PartnerRequestResponse(BaseModel):
    request_id: int
    action: str  # "accept" or "reject"

class PartnerRequest(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    status: RequestStatus
    created_at: datetime
    sender_name: Optional[str] = None
    recipient_name: Optional[str] = None
    
    model_config = {"from_attributes": True}

# Partnership schemas
class Partnership(BaseModel):
    id: int
    user_a_id: int
    user_b_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Chat schemas
class ChatChannelCreate(BaseModel):
    name: Optional[str] = None
    member_ids: List[int]

class ChatChannel(BaseModel):
    id: int
    name: Optional[str] = None
    created_at: datetime
    members: List[User]
    
    model_config = {"from_attributes": True}

class MessageCreate(BaseModel):
    sender_id: int
    body: str

class Message(BaseModel):
    id: int
    sender_id: int
    channel_id: int
    body: str
    is_read: bool
    created_at: datetime
    sender_name: Optional[str] = None
    
    model_config = {"from_attributes": True}

class MessageMarkRead(BaseModel):
    message_id: int

class Presence(BaseModel):
    user_id: int
    online: bool
    last_seen: Optional[datetime] = None

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str  # "new_message", "read_receipt", "presence_change"
    data: dict

class NewMessageEvent(BaseModel):
    type: str = "new_message"
    message: Message

class ReadReceiptEvent(BaseModel):
    type: str = "read_receipt"
    message_id: int
    user_id: int
    timestamp: datetime

class PresenceChangeEvent(BaseModel):
    type: str = "presence_change"
    user_id: int
    online: bool
    last_seen: Optional[datetime] = None
