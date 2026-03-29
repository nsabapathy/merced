import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Group(Base):
    """User group for permission management."""
    __tablename__ = "groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, default="")
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")
    permissions = relationship("GroupPermission", back_populates="group", cascade="all, delete-orphan")


class GroupMembership(Base):
    """Association between groups and users."""
    __tablename__ = "group_memberships"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    group = relationship("Group", back_populates="memberships")


class GroupPermission(Base):
    """Additive allow-list for group access to models and collections."""
    __tablename__ = "group_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("models_config.id", ondelete="CASCADE"), nullable=True)
    collection_id = Column(String(36), ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=True)

    group = relationship("Group", back_populates="permissions")
