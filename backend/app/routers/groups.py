"""Group management routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.group import Group, GroupMembership, GroupPermission
from app.schemas.group import GroupCreate, GroupUpdate, GroupRead, GroupMemberAdd, GroupPermissionUpdate

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("/", response_model=list[GroupRead])
async def list_groups(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all groups (admin only)."""
    return db.query(Group).offset(skip).limit(limit).all()


@router.post("/", response_model=GroupRead)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a group (admin only)."""
    group = Group(
        id=str(uuid.uuid4()),
        name=group_data.name,
        description=group_data.description,
        created_by=current_user.id
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(
    group_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a group (admin only)."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.put("/{group_id}", response_model=GroupRead)
async def update_group(
    group_id: str,
    update: GroupUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a group (admin only)."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if update.name:
        group.name = update.name
    if update.description:
        group.description = update.description

    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}")
async def delete_group(
    group_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a group (admin only)."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(group)
    db.commit()
    return {"message": "Group deleted"}


@router.post("/{group_id}/members")
async def add_group_member(
    group_id: str,
    member_data: GroupMemberAdd,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Add a member to a group (admin only)."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    membership = GroupMembership(
        id=str(uuid.uuid4()),
        group_id=group_id,
        user_id=member_data.user_id
    )
    db.add(membership)
    db.commit()
    return {"message": "Member added"}


@router.delete("/{group_id}/members/{user_id}")
async def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove a member from a group (admin only)."""
    membership = db.query(GroupMembership).filter(
        GroupMembership.group_id == group_id,
        GroupMembership.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    db.delete(membership)
    db.commit()
    return {"message": "Member removed"}


@router.put("/{group_id}/permissions")
async def update_group_permissions(
    group_id: str,
    perm_data: GroupPermissionUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update group permissions (admin only)."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Clear existing permissions
    db.query(GroupPermission).filter(GroupPermission.group_id == group_id).delete()

    # Add new permissions
    for perm in perm_data.permissions:
        permission = GroupPermission(
            id=str(uuid.uuid4()),
            group_id=group_id,
            model_id=perm.model_id,
            collection_id=perm.collection_id
        )
        db.add(permission)

    db.commit()
    return {"message": "Permissions updated"}
