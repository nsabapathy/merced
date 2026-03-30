from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Merced Chat"
    debug: bool = False

    # Database
    database_url: str = "sqlite:////data/app.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Chroma
    chroma_url: str = "http://localhost:8001"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    encryption_key: str = "your-fernet-key-change-in-production"
    algorithm: str = "HS256"
    cookie_secure: bool = False  # Set True in production (HTTPS only)

    # Token expiry
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Azure Storage (optional)
    azure_storage_connection_string: Optional[str] = None
    azure_storage_container: str = "uploads"

    # RAG
    rag_chunk_size: int = 512
    rag_top_k: int = 5
    rag_overlap: int = 50

    # First-run admin
    first_admin_email: Optional[str] = None
    first_admin_password: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
