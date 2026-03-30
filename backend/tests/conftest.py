"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid

# Create test engine at module level
# Use file-based SQLite for tests to ensure tables are shared across connections
import tempfile
import os

test_db_fd, test_db_path = tempfile.mkstemp(suffix=".db")
os.close(test_db_fd)

TEST_ENGINE = create_engine(
    f"sqlite:///{test_db_path}",
    connect_args={"check_same_thread": False},
    echo=False
)

# Import Base and create tables before importing app
from app.db.base import Base

# Import all models to register them
from app.models.user import User as UserModel, Role
from app.models.group import Group, GroupMembership, GroupPermission
from app.models.chat import Chat, Message
from app.models.model_config import ModelConfig
from app.models.file import File
from app.models.knowledge import KnowledgeCollection, KnowledgeDocument
from app.models.prompt import Prompt

Base.metadata.create_all(bind=TEST_ENGINE)

# Verify tables were created
insp = inspect(TEST_ENGINE)
tables = insp.get_table_names()
assert "users" in tables, f"Users table not found. Available tables: {tables}"

# Override SessionLocal before importing app
import app.db.session as db_session_module
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)
db_session_module.SessionLocal = TestSessionLocal

# Mock Redis before importing app
mock_redis = MagicMock()
mock_redis.setex = MagicMock(return_value=True)
mock_redis.get = MagicMock(return_value=None)
mock_redis.delete = MagicMock(return_value=True)

@pytest.fixture(autouse=True, scope="session")
def cleanup_test_db():
    """Clean up test database file."""
    yield
    # Clean up temp database file
    try:
        os.unlink(test_db_path)
    except:
        pass


@pytest.fixture(autouse=True)
def mock_redis_fixture():
    """Mock Redis for all tests."""
    with patch('app.services.auth_service.redis_client', mock_redis):
        yield

# Then import app (which will use our overridden SessionLocal)
from app.main import app
from app.db.session import get_db

# Import all models to register them with Base
from app.models.user import User, Role
from app.models.group import Group, GroupMembership, GroupPermission
from app.models.chat import Chat, Message
from app.models.model_config import ModelConfig
from app.models.file import File
from app.models.knowledge import KnowledgeCollection, KnowledgeDocument
from app.models.prompt import Prompt

from app.services.auth_service import hash_password, create_access_token


@pytest.fixture
def db_session():
    """Create a new database session for each test."""
    session = TestSessionLocal()
    yield session
    # Clean up: delete all test data
    from sqlalchemy import text
    try:
        # Delete in order of foreign key dependencies
        session.execute(text("DELETE FROM messages"))
        session.execute(text("DELETE FROM chats"))
        session.execute(text("DELETE FROM knowledge_documents"))
        session.execute(text("DELETE FROM knowledge_collections"))
        session.execute(text("DELETE FROM group_permissions"))
        session.execute(text("DELETE FROM group_memberships"))
        session.execute(text("DELETE FROM groups"))
        session.execute(text("DELETE FROM models_config"))
        session.execute(text("DELETE FROM files"))
        session.execute(text("DELETE FROM prompts"))
        session.execute(text("DELETE FROM users"))
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create a test client with dependency override."""
    from app.dependencies import get_current_user
    from app.services.auth_service import verify_access_token
    from app.services.user_service import get_user_by_id
    from fastapi import HTTPException, status, Request

    def override_get_db():
        yield db_session

    async def override_get_current_user(request: Request):
        """Override get_current_user to extract token from Authorization header."""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header",
            )

        user_id = verify_access_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = get_user_by_id(user_id, db_session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive",
            )

        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Check if test user already exists
    existing_user = db_session.query(User).filter(User.email == "test@example.com").first()
    if existing_user:
        return existing_user

    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        password_hash=hash_password("password123"),
        role=Role.USER,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    """Create a test admin user."""
    # Check if admin already exists
    existing_admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    if existing_admin:
        return existing_admin

    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        username="admin",
        password_hash=hash_password("admin123"),
        role=Role.ADMIN,
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def user_token(test_user):
    """Create access token for test user."""
    return create_access_token(test_user.id)


@pytest.fixture
def admin_token(test_admin):
    """Create access token for test admin."""
    return create_access_token(test_admin.id)


@pytest.fixture
def real_client(db_session):
    """Test client that uses the real get_current_user dependency (no override).

    Use this fixture in wiring tests to verify that the actual FastAPI
    dependency injection chain works end-to-end. If get_current_user is
    ever broken at the wiring level, tests using this fixture will catch it
    while tests using the normal `client` fixture will not.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()
