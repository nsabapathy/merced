from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromptCreate(BaseModel):
    """Create prompt schema."""
    title: str
    content: str
    is_public: Optional[bool] = False


class PromptUpdate(BaseModel):
    """Update prompt schema."""
    title: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None


class PromptRead(BaseModel):
    """Prompt read schema."""
    id: str
    user_id: str
    title: str
    content: str
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
