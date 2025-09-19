from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
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
