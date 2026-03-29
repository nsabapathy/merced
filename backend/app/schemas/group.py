from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PermissionSet(BaseModel):
    """Permission set for a group."""
    model_id: Optional[str] = None  # NULL = all models
    collection_id: Optional[str] = None  # NULL = all collections


class GroupCreate(BaseModel):
    """Create group schema."""
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    """Update group schema."""
    name: Optional[str] = None
    description: Optional[str] = None


class GroupRead(BaseModel):
    """Group read schema."""
    id: str
    name: str
    description: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GroupMemberAdd(BaseModel):
    """Add member to group schema."""
    user_id: str


class GroupPermissionUpdate(BaseModel):
    """Update group permissions schema."""
    permissions: List[PermissionSet]
