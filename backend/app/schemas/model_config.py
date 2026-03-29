from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ModelConfigCreate(BaseModel):
    """Create model config schema."""
    name: str
    base_url: str
    api_key: str
    model_id: str
    is_active: Optional[bool] = True


class ModelConfigUpdate(BaseModel):
    """Update model config schema."""
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    is_active: Optional[bool] = None


class ModelConfigRead(BaseModel):
    """Model config read schema (API key excluded)."""
    id: str
    name: str
    base_url: str
    model_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
