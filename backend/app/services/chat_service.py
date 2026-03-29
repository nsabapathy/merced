"""Chat service for message management."""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.chat import Chat, Message, MessageRole
from app.models.model_config import ModelConfig
from app.utils.chunking import estimate_tokens


def create_chat(user_id: str, title: str = None, db: Session = None) -> Chat:
    """Create a new chat."""
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title or "New Chat"
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_chat(chat_id: str, db: Session) -> Chat | None:
    """Get a chat by ID."""
    return db.query(Chat).filter(Chat.id == chat_id).first()


def list_chats(user_id: str, db: Session, skip: int = 0, limit: int = 50) -> list[Chat]:
    """List chats for a user."""
    return db.query(Chat).filter(
        Chat.user_id == user_id
    ).order_by(Chat.updated_at.desc()).offset(skip).limit(limit).all()


def update_chat(chat_id: str, title: str = None, db: Session = None) -> Chat | None:
    """Update a chat title."""
    chat = get_chat(chat_id, db)
    if not chat:
        return None

    if title:
        chat.title = title
    chat.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(chat)
    return chat


def delete_chat(chat_id: str, db: Session) -> bool:
    """Delete a chat."""
    chat = get_chat(chat_id, db)
    if not chat:
        return False

    db.delete(chat)
    db.commit()
    return True


def save_message(
    chat_id: str,
    role: MessageRole,
    content: str,
    model_id: str = None,
    knowledge_used: bool = False,
    db: Session = None
) -> Message:
    """Save a message to a chat."""
    token_count = estimate_tokens(content)

    message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        role=role,
        content=content,
        token_count=token_count,
        model_id=model_id,
        knowledge_used=knowledge_used
    )
    db.add(message)

    # Update chat title if it's the first user message
    chat = get_chat(chat_id, db)
    if chat and not chat.title or chat.title == "New Chat":
        # Set title from first message
        if role == MessageRole.USER:
            title = content[:50]
            if len(content) > 50:
                title += "..."
            chat.title = title

    db.commit()
    db.refresh(message)
    return message


def get_messages(chat_id: str, db: Session, limit: int = 50) -> list[Message]:
    """Get messages from a chat."""
    return db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at.asc()).limit(limit).all()


def get_context_window(chat_id: str, max_tokens: int = 4000, db: Session = None) -> list[Message]:
    """Get messages for context window, up to max_tokens."""
    messages = get_messages(chat_id, db)

    context_messages = []
    total_tokens = 0

    # Work backwards from most recent
    for msg in reversed(messages):
        if total_tokens + msg.token_count <= max_tokens:
            context_messages.insert(0, msg)
            total_tokens += msg.token_count
        else:
            break

    return context_messages
