from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Create user schema."""
    email: EmailStr
    username: str
    password: str


class UserUpdate(BaseModel):
    """Update user schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None


class UserRead(BaseModel):
    """User read schema."""
    id: str
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserMe(BaseModel):
    """Current user schema."""
    id: str
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True
