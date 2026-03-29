"""Authentication service for user login, JWT creation, and session management."""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import redis
import uuid

from app.config import settings
from app.models.user import User, Role


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis client for refresh token storage
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token and store in Redis."""
    token = str(uuid.uuid4())
    expire_seconds = settings.refresh_token_expire_days * 24 * 60 * 60

    redis_client.setex(
        f"refresh_token:{token}",
        expire_seconds,
        user_id
    )

    return token


def verify_access_token(token: str) -> str | None:
    """Verify a JWT access token and return user_id."""
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def verify_refresh_token(token: str) -> str | None:
    """Verify a refresh token in Redis and return user_id."""
    user_id = redis_client.get(f"refresh_token:{token}")
    return user_id


def revoke_refresh_token(token: str) -> None:
    """Revoke a refresh token."""
    redis_client.delete(f"refresh_token:{token}")


def authenticate_user(email: str, password: str, db: Session) -> User | None:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_first_admin(db: Session) -> User | None:
    """Create first admin user from environment variables."""
    if not settings.first_admin_email or not settings.first_admin_password:
        return None

    # Check if any admin exists
    admin_exists = db.query(User).filter(User.role == Role.ADMIN).first()
    if admin_exists:
        return None

    # Create admin user
    admin = User(
        id=str(uuid.uuid4()),
        email=settings.first_admin_email,
        username=settings.first_admin_email.split("@")[0],
        password_hash=hash_password(settings.first_admin_password),
        role=Role.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
