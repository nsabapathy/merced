import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger
from datetime import datetime
from app.db.base import Base


class File(Base):
    """Uploaded file metadata."""
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(500), nullable=False)
    blob_path = Column(String(500), nullable=False)  # Azure Blob path
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
