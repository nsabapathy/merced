from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    """Create message schema."""
    content: str
    model_id: str
    knowledge_id: Optional[str] = None


class MessageRead(BaseModel):
    """Message read schema."""
    id: str
    chat_id: str
    role: str
    content: str
    token_count: int
    model_id: Optional[str]
    knowledge_used: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    """Create chat schema."""
    title: Optional[str] = None


class ChatUpdate(BaseModel):
    """Update chat schema."""
    title: Optional[str] = None


class ChatRead(BaseModel):
    """Chat read schema."""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatDetail(ChatRead):
    """Chat detail with messages."""
    messages: list[MessageRead] = []
