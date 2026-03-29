"""Permission evaluation utilities for RBAC."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, Role
from app.models.group import GroupMembership, GroupPermission


def get_user_group_ids(user_id: str, db: Session) -> list[str]:
    """Get all group IDs that a user belongs to."""
    memberships = db.query(GroupMembership.group_id).filter(
        GroupMembership.user_id == user_id
    ).all()
    return [m[0] for m in memberships]


def can_access_model(user_id: str, model_id: str, db: Session) -> bool:
    """Check if user can access a specific model."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # Admin has access to all
    if user.role == Role.ADMIN:
        return True

    # Regular user: check group permissions
    group_ids = get_user_group_ids(user_id, db)
    if not group_ids:
        return False

    # Allow if any group has permission for this model or all models (NULL)
    permission = db.query(GroupPermission).filter(
        GroupPermission.group_id.in_(group_ids),
        or_(
            GroupPermission.model_id == model_id,
            GroupPermission.model_id == None  # NULL = all models
        )
    ).first()

    return permission is not None


def can_access_collection(user_id: str, collection_id: str, db: Session) -> bool:
    """Check if user can access a specific collection."""
    from app.models.knowledge import KnowledgeCollection

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # Admin has access to all
    if user.role == Role.ADMIN:
        return True

    # Check if user is the collection creator
    collection = db.query(KnowledgeCollection).filter(
        KnowledgeCollection.id == collection_id
    ).first()
    if collection and collection.created_by == user_id:
        return True

    # Regular user: check group permissions
    group_ids = get_user_group_ids(user_id, db)
    if not group_ids:
        return False

    # Allow if any group has permission for this collection or all collections (NULL)
    permission = db.query(GroupPermission).filter(
        GroupPermission.group_id.in_(group_ids),
        or_(
            GroupPermission.collection_id == collection_id,
            GroupPermission.collection_id == None  # NULL = all collections
        )
    ).first()

    return permission is not None
