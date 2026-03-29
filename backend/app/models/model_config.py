import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime
from datetime import datetime
from app.db.base import Base


class ModelConfig(Base):
    """LLM model configuration."""
    __tablename__ = "models_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    base_url = Column(String(500), nullable=False)
    api_key = Column(Text, nullable=False)  # Fernet-encrypted
    model_id = Column(String(200), nullable=False)  # e.g., "gpt-4o", "claude-3-sonnet"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
