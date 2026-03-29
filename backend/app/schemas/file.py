from pydantic import BaseModel
from datetime import datetime


class FileRead(BaseModel):
    """File read schema."""
    id: str
    user_id: str
    original_name: str
    blob_path: str
    content_type: str
    size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True
