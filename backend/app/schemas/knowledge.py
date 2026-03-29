from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CollectionCreate(BaseModel):
    """Create knowledge collection schema."""
    name: str


class CollectionRead(BaseModel):
    """Knowledge collection read schema."""
    id: str
    name: str
    chroma_collection_name: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    """Create document schema."""
    file_id: str
    title: Optional[str] = None


class DocumentRead(BaseModel):
    """Document read schema."""
    id: str
    collection_id: str
    file_id: str
    title: str
    chunk_count: int
    status: str
    error_message: Optional[str]
    indexed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
