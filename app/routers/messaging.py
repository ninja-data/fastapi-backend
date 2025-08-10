"""
Messaging Module - Real-time Chat System

Components:
1. WebSocket Manager: Handles real-time connections
2. REST Endpoints: Conversation & message management

WebSocket Protocol:
- Endpoint: /messaging/ws/{user_id}
- Heartbeat: Client sends "ping", server responds "pong"
- Notifications:
  "new_message:<conversation_id>" - New message in conversation
  "participant_added:<conversation_id>:<user_id>" - New member added

Security:
- All routes use JWT authentication
- WebSocket accepts connections without auth (demo only - PROD REQUIRES AUTH)

Key Models:
- Conversation: Direct/group chat container
- Participant: Conversation member (admin flag for permissions)
- Message: User-generated content in conversation
- ReadReceipt: Message read status

Endpoint Summary:
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, aliased
from datetime import datetime
from typing import List, Dict
import math

from .. import schemas, models, oauth2
from ..database import get_db

router = APIRouter(prefix="/messaging", tags=["Messaging"])

class ConnectionManager:
    """Manages active WebSocket connections per user ID"""
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # user_id: WebSocket

    async def connect(self, user_id: int, websocket: WebSocket):
        """Register new connection and accept socket"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        """Remove connection on disconnect"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        """Push notification to specific user's active connection"""
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket connection for real-time notifications
    
    Params:
      user_id: Authenticated user ID (no validation in demo - UNSAFE FOR PROD)
    Behavior:
      - Maintains persistent connection
      - Handles heartbeat with ping/pong
      - Broadcasts message notifications to participants
    """
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":  # Heartbeat
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(user_id)


def _create_conversation(db: Session, current_user: models.User, participants: List[int]):
    # Ensure participants exist
    participant_objs = []
    for user_id in participants:
        if user_id == current_user.id:
            continue  # Don't add duplicate
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        participant_objs.append(user)
    
    # Create conversation
    db_conv = models.Conversation(
        conversation_type="direct" if len(participants) == 1 else "group",
        created_at=datetime.utcnow(),
        last_message_at=datetime.utcnow()
    )
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    
    # Add participants
    participants_to_add = [current_user] + participant_objs
    for user in participants_to_add:
        participant = models.Participant(
            user_id=user.id,
            conversation_id=db_conv.id,
            is_admin=(user.id == current_user.id)  # First user is admin
        )
        db.add(participant)
    
    db.commit()
    return db_conv

@router.post("/conversation", response_model=schemas.ConversationResponse)
def create_conversation(
    conv_data: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Create new conversation
    
    - Direct: Auto-reuses existing 1:1 conversation
    - Group: Creates new conversation with participants
    - First member becomes admin
    """
    # Validate participants
    if current_user.id in conv_data.participant_ids:
        raise HTTPException(
            status_code=400,
            detail="Don't include yourself in participant_ids"
        )
    
    # Check for existing direct conversation
    if conv_data.conversation_type == "direct" and len(conv_data.participant_ids) == 1:
        Participant1 = aliased(models.Participant)
        Participant2 = aliased(models.Participant)

        existing = db.query(models.Conversation).join(
            Participant1, models.Conversation.participants
        ).join(
            Participant2, models.Conversation.participants
        ).filter(
            models.Conversation.conversation_type == "direct",
            Participant1.user_id == current_user.id,
            Participant2.user_id == conv_data.participant_ids[0]
        ).first()

        
        if existing:
            return existing
    
    return _create_conversation(db, current_user, conv_data.participant_ids)


@router.get("/conversations", response_model=List[schemas.ConversationResponse])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """
    List user's conversations
    
    Returns:
      - Conversations ordered by last_message_at (desc)
      - Includes participants and last message
      - Pagination via skip/limit
    """
    # Get conversations ordered by last activity
    convs = db.query(models.Conversation).join(models.Participant).filter(
        models.Participant.user_id == current_user.id
    ).order_by(
        models.Conversation.last_message_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Eager load participants and last message
    for conv in convs:
        db.refresh(conv)  # Load relationships
        conv.participants  # Force load
        if conv.messages:
            conv.last_message = conv.messages[-1]  # Last message
    
    return convs


@router.post("/conversations/{conversation_id}/messages", response_model=schemas.Message)
async def send_message(
    conversation_id: int,
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Send message to conversation
    
    Effects:
      1. Stores message
      2. Updates conversation's last_message_at
      3. Notifies participants via WebSocket
    """
    # Verify user is in conversation
    participant = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id,
        models.Participant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not in conversation")
    
    # Create message
    db_message = models.Message(
        **message.model_dump(exclude_unset=True),
        sender_id=current_user.id,
        conversation_id=conversation_id,
        created_at=datetime.utcnow()
    )
    db.add(db_message)
    
    # Update conversation timestamp
    conversation = db.query(models.Conversation).get(conversation_id)
    conversation.last_message_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_message)
    
    # Notify participants via WebSocket
    participants = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id
    ).all()
    
    for p in participants:
        if p.user_id != current_user.id:  # Don't notify self
            await manager.send_personal_message(
                f"new_message:{conversation_id}",
                p.user_id
            )
    
    return db_message


# @router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.Message])
# def get_messages(
#     conversation_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user),
#     skip: int = 0,
#     limit: int = 50
# ):
#     """
#     Get conversation messages
    
#     Returns:
#       - Messages with read receipts (read_by user IDs)
#       - Ordered by created_at (desc)
#       - Pagination via skip/limit
#     """
#     # Verify access
#     participant = db.query(models.Participant).filter(
#         models.Participant.conversation_id == conversation_id,
#         models.Participant.user_id == current_user.id
#     ).first()
    
#     if not participant:
#         raise HTTPException(status_code=403, detail="Not in conversation")
    
#     # Get messages with read status
#     messages = db.query(models.Message).filter(
#         models.Message.conversation_id == conversation_id
#     ).order_by(models.Message.created_at.desc()
#       ).offset(skip).limit(limit).all()
    
#     # Add read_by information
#     for msg in messages:
#         receipts = db.query(models.ReadReceipt).filter(
#             models.ReadReceipt.message_id == msg.id
#         ).all()
#         msg.read_by = [r.participant.user_id for r in receipts]
    
#     return messages


@router.get("/conversations/{conversation_id}/messages", response_model=schemas.PaginatedMessagesResponse)
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    page: int = 1,
    limit: int = 50
):
    """
    Get conversation messages with pagination metadata
    
    Returns:
      - total_pages: Total number of pages available
      - messages: Paginated messages with read receipts
    """
    # Verify access
    participant = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id,
        models.Participant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not in conversation")
    
    # Get total message count
    total_messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).count()

    # Calculate total pages (using ceiling division)
    total_pages = math.ceil(total_messages / limit) if limit > 0 else 0

    offset_value = (page - 1) * limit

    # Get paginated messages
    messages = db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.created_at.desc()
      ).offset(offset_value).limit(limit).all()
    
    # Add read_by information
    for msg in messages:
        receipts = db.query(models.ReadReceipt).filter(
            models.ReadReceipt.message_id == msg.id
        ).all()
        msg.read_by = [r.participant.user_id for r in receipts]
    
    return {
        "count": total_pages,
        "model": messages
    }


@router.post("/messages/mark-read")
def mark_message_read(
    read_data: schemas.MarkReadRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Mark message as read
    
    Creates read receipt if not exists
    Requires message visibility to user
    """
    # Find participant for this message's conversation
    message = db.query(models.Message).get(read_data.message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    participant = db.query(models.Participant).filter(
        models.Participant.conversation_id == message.conversation_id,
        models.Participant.user_id == current_user.id
    ).first()
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not in conversation")
    
    # Check if already marked as read
    existing = db.query(models.ReadReceipt).filter(
        models.ReadReceipt.message_id == read_data.message_id,
        models.ReadReceipt.participant_id == participant.id
    ).first()
    
    if not existing:
        receipt = models.ReadReceipt(
            message_id=read_data.message_id,
            participant_id=participant.id,
            read_at=datetime.utcnow()
        )
        db.add(receipt)
        db.commit()
    
    return {"status": "marked_as_read"}


@router.post("/conversations/{conversation_id}/participants")
async def add_participant(
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Add participant to conversation
    
    Requirements:
      - Requester must be conversation admin
      - User not already in conversation
    Notifies all participants via WebSocket
    """
    # Verify current user is admin in conversation
    current_participant = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id,
        models.Participant.user_id == current_user.id,
        models.Participant.is_admin == True
    ).first()
    
    if not current_participant:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if user already in conversation
    existing = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id,
        models.Participant.user_id == user_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already in conversation")
    
    # Add participant
    participant = models.Participant(
        user_id=user_id,
        conversation_id=conversation_id,
        is_admin=False
    )
    db.add(participant)
    db.commit()
    
    # Notify conversation members
    participants = db.query(models.Participant).filter(
        models.Participant.conversation_id == conversation_id
    ).all()
    
    for p in participants:
        await manager.send_personal_message(
            f"participant_added:{conversation_id}:{user_id}",
            p.user_id
        )
    
    return {"status": "added"}
