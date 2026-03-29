"""SQLAlchemy declarative base and model registration."""
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def load_models():
    """Import all models to register them with Base.

    This is called by Alembic to ensure all models are available for migrations.
    """
    # Import models - they will register themselves with Base upon import
    from app.models.user import User  # noqa: F401
    from app.models.group import Group, GroupMembership, GroupPermission  # noqa: F401
    from app.models.chat import Chat, Message  # noqa: F401
    from app.models.model_config import ModelConfig  # noqa: F401
    from app.models.file import File  # noqa: F401
    from app.models.knowledge import KnowledgeCollection, KnowledgeDocument  # noqa: F401
    from app.models.prompt import Prompt  # noqa: F401
