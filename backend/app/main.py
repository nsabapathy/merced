"""FastAPI application factory and main entry point."""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import socketio

from app.config import settings
from app.db.session import get_db
from app.services.auth_service import create_first_admin
from app.routers import auth, users, groups, chats, models, knowledge, files, prompts
from app.sockets.chat_socket import setup_socket_handlers


# FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Multi-user AI chat application with RAG",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO setup
mgr = socketio.AsyncRedisManager(settings.redis_url)
sio = socketio.AsyncServer(
    async_mode="asgi",
    client_manager=mgr,
    cors_allowed_origins="*"
)
socket_app = socketio.ASGIApp(sio, app)

# Setup Socket.IO handlers
setup_socket_handlers(sio)


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(groups.router)
app.include_router(chats.router)
app.include_router(models.router)
app.include_router(knowledge.router)
app.include_router(files.router)
app.include_router(prompts.router)


# Security scheme for documentation
security = HTTPBearer()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize app on startup."""
    db = next(get_db())
    try:
        # Create first admin if configured
        create_first_admin(db)
    finally:
        db.close()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    pass


# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Dependency for getting bearer token
async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract Bearer token from request."""
    return credentials.credentials


# Update get_current_user dependency to use the bearer token
# This is a workaround - in production, use proper FastAPI auth
from app.dependencies import get_current_user as original_get_current_user

async def get_current_user_with_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user from Bearer token."""
    from app.models.user import User
    from app.services.auth_service import verify_access_token
    from app.services.user_service import get_user_by_id

    token = credentials.credentials
    user_id = verify_access_token(token)
    if not user_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(user_id, db)
    if not user or not user.is_active:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


# Update routers to use the new dependency
# We need to patch the dependency in get_current_user calls
# For now, we'll override it in dependencies.py


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
