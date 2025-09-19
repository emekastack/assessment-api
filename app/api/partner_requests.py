from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db.database import get_db
from app.db.models import User, PartnerRequest, Partnership, RequestStatus
from app.api.schemas import (
    PartnerRequestCreate, 
    PartnerRequestResponse, 
    PartnerRequest as PartnerRequestSchema,
    Partnership as PartnershipSchema
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/partner-requests", tags=["Partner Requests"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_partner_request(
    request_data: PartnerRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new partner request"""
    
    # Validate that sender and recipient exist
    sender = db.query(User).filter(User.id == request_data.sender_id).first()
    recipient = db.query(User).filter(User.id == request_data.recipient_id).first()
    
    if not sender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sender with id {request_data.sender_id} not found"
        )
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with id {request_data.recipient_id} not found"
        )
    
    # Check if sender and recipient are the same
    if request_data.sender_id == request_data.recipient_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send partner request to yourself"
        )
    
    # Check if there's already a pending request between these users
    existing_request = db.query(PartnerRequest).filter(
        and_(
            PartnerRequest.sender_id == request_data.sender_id,
            PartnerRequest.recipient_id == request_data.recipient_id,
            PartnerRequest.status == RequestStatus.PENDING
        )
    ).first()
    
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending partner request already exists between these users"
        )
    
    # Create the partner request
    partner_request = PartnerRequest(
        sender_id=request_data.sender_id,
        recipient_id=request_data.recipient_id,
        status=RequestStatus.PENDING
    )
    
    db.add(partner_request)
    db.commit()
    db.refresh(partner_request)
    
    # Send notification to recipient
    NotificationService.send_partner_request_notification(
        recipient_name=recipient.name,
        sender_name=sender.name
    )
    
    return {
        "message": "Partner request created successfully",
        "request_id": partner_request.id,
        "status": partner_request.status
    }

@router.get("/received/{user_id}/")
async def get_received_requests(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all pending partner requests received by a user"""
    
    # Validate that user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Get pending requests for this user
    requests = db.query(PartnerRequest).filter(
        and_(
            PartnerRequest.recipient_id == user_id,
            PartnerRequest.status == RequestStatus.PENDING
        )
    ).all()
    
    # Format response with sender names
    result = []
    for req in requests:
        sender = db.query(User).filter(User.id == req.sender_id).first()
        result.append({
            "id": req.id,
            "sender_id": req.sender_id,
            "sender_name": sender.name if sender else "Unknown",
            "recipient_id": req.recipient_id,
            "status": req.status,
            "created_at": req.created_at
        })
    
    return {
        "user_id": user_id,
        "pending_requests": result,
        "count": len(result)
    }

@router.post("/respond/")
async def respond_to_request(
    response_data: PartnerRequestResponse,
    db: Session = Depends(get_db)
):
    """Respond to a partner request (accept or reject)"""
    
    # Validate request exists
    partner_request = db.query(PartnerRequest).filter(
        PartnerRequest.id == response_data.request_id
    ).first()
    
    if not partner_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner request with id {response_data.request_id} not found"
        )
    
    # Validate action
    if response_data.action not in ["accept", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be either 'accept' or 'reject'"
        )
    
    # Check if request is still pending
    if partner_request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request has already been responded to"
        )
    
    # Get sender and recipient names for notifications
    sender = db.query(User).filter(User.id == partner_request.sender_id).first()
    recipient = db.query(User).filter(User.id == partner_request.recipient_id).first()
    
    # Update request status
    if response_data.action == "accept":
        partner_request.status = RequestStatus.ACCEPTED
        
        # Create partnership record
        partnership = Partnership(
            user_a_id=partner_request.sender_id,
            user_b_id=partner_request.recipient_id
        )
        db.add(partnership)
        
        # Send acceptance notification to sender
        NotificationService.send_request_accepted_notification(
            sender_name=sender.name if sender else "Unknown",
            recipient_name=recipient.name if recipient else "Unknown"
        )
        
        message = "Partner request accepted and partnership created"
    else:
        partner_request.status = RequestStatus.REJECTED
        message = "Partner request rejected"
    
    db.commit()
    db.refresh(partner_request)
    
    return {
        "message": message,
        "request_id": partner_request.id,
        "status": partner_request.status,
        "action": response_data.action
    }
