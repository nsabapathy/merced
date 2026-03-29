"""Chat routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatUpdate, ChatRead, ChatDetail, MessageCreate
from app.services.chat_service import (
    create_chat, get_chat, list_chats, update_chat, delete_chat, save_message
)
from app.models.chat import MessageRole

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("/", response_model=list[ChatRead])
async def list_user_chats(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's chats."""
    return list_chats(current_user.id, db, skip, limit)


@router.post("/", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_new_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat."""
    return create_chat(current_user.id, chat_data.title, db)


@router.get("/{chat_id}", response_model=ChatDetail)
async def get_chat_detail(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a chat with all messages."""
    chat = get_chat(chat_id, db)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.put("/{chat_id}", response_model=ChatRead)
async def update_chat_title(
    chat_id: str,
    update: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update chat title."""
    chat = get_chat(chat_id, db)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    return update_chat(chat_id, update.title, db)


@router.delete("/{chat_id}")
async def delete_chat_by_id(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat."""
    chat = get_chat(chat_id, db)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")
    delete_chat(chat_id, db)
    return {"message": "Chat deleted"}


@router.post("/{chat_id}/messages", status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    chat_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message (triggers async streaming via Socket.IO)."""
    chat = get_chat(chat_id, db)
    if not chat or chat.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message
    user_msg = save_message(
        chat_id=chat_id,
        role=MessageRole.USER,
        content=message.content,
        model_id=message.model_id,
        knowledge_used=bool(message.knowledge_id),
        db=db
    )

    # Return 202 Accepted - actual streaming happens via Socket.IO
    return {"message_id": user_msg.id, "status": "processing"}
