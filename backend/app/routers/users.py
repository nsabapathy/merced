"""User management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.schemas.user import UserRead, UserCreate, UserUpdate, UserMe
from app.services.user_service import (
    create_user, get_user_by_id, list_users, update_user, delete_user
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.put("/me", response_model=UserMe)
async def update_current_user(
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user."""
    updated = update_user(
        current_user.id,
        email=update.email,
        username=update.username,
        password=update.password,
        db=db
    )
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.get("/", response_model=list[UserRead])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    return list_users(db, skip, limit)


@router.post("/", response_model=UserRead)
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    try:
        return create_user(user_data.email, user_data.username, user_data.password, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a specific user (admin only)."""
    user = get_user_by_id(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_by_id(
    user_id: str,
    update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    updated = update_user(user_id, update.email, update.username, update.password, db)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/{user_id}")
async def delete_user_by_id(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    if not delete_user(user_id, db):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}
