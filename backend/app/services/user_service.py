"""User management service."""
import uuid
from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.services.auth_service import hash_password


def create_user(email: str, username: str, password: str, db: Session) -> User:
    """Create a new user."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        username=username,
        password_hash=hash_password(password),
        role=Role.USER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(user_id: str, db: Session) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(email: str, db: Session) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(username: str, db: Session) -> User | None:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """List all users."""
    return db.query(User).offset(skip).limit(limit).all()


def update_user(user_id: str, email: str | None, username: str | None, password: str | None, db: Session) -> User | None:
    """Update a user."""
    user = get_user_by_id(user_id, db)
    if not user:
        return None

    if email:
        user.email = email
    if username:
        user.username = username
    if password:
        user.password_hash = hash_password(password)

    db.commit()
    db.refresh(user)
    return user


def delete_user(user_id: str, db: Session) -> bool:
    """Delete a user."""
    user = get_user_by_id(user_id, db)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True


def set_user_role(user_id: str, role: Role, db: Session) -> User | None:
    """Set user role."""
    user = get_user_by_id(user_id, db)
    if not user:
        return None

    user.role = role
    db.commit()
    db.refresh(user)
    return user
