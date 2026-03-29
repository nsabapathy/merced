"""Socket.IO event handlers for chat streaming."""
from socketio import AsyncServer, Server
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.chat_service import save_message, get_context_window
from app.services.llm_service import llm_service
from app.models.chat import MessageRole
from app.models.model_config import ModelConfig


def setup_socket_handlers(sio: AsyncServer, db: Session = None):
    """Setup Socket.IO event handlers."""

    @sio.event
    async def stream_message(sid, data):
        """Handle streaming chat message."""
        chat_id = data.get("chat_id")
        content = data.get("content")
        model_id = data.get("model_id")
        knowledge_id = data.get("knowledge_id")

        # Get database session
        db = SessionLocal()

        try:
            # Save user message
            user_msg = save_message(
                chat_id=chat_id,
                role=MessageRole.USER,
                content=content,
                model_id=model_id,
                knowledge_used=bool(knowledge_id),
                db=db
            )

            # Get model config
            model = db.query(ModelConfig).filter(ModelConfig.id == model_id).first()
            if not model:
                await sio.emit("stream_error", {"error": "Model not found"}, to=sid)
                return

            # Get context window
            context_messages = get_context_window(chat_id, db=db)
            messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in context_messages
            ]

            # Add RAG context if enabled
            system_context = ""
            if knowledge_id:
                # TODO: Implement RAG context
                system_context = ""

            if system_context:
                messages.insert(0, {"role": "system", "content": system_context})

            # Stream response
            full_response = ""
            async for chunk in llm_service.stream_chat_completion(
                base_url=model.base_url,
                api_key=model.api_key,
                model_id=model.model_id,
                messages=messages
            ):
                full_response += chunk
                await sio.emit("stream_chunk", {"chunk": chunk}, to=f"chat_{chat_id}")

            # Save assistant message
            save_message(
                chat_id=chat_id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                model_id=model_id,
                knowledge_used=bool(knowledge_id),
                db=db
            )

            await sio.emit("stream_end", {"content": full_response}, to=f"chat_{chat_id}")

        except Exception as e:
            await sio.emit("stream_error", {"error": str(e)}, to=sid)
        finally:
            db.close()

    @sio.event
    async def join_chat(sid, data):
        """Join a chat room."""
        chat_id = data.get("chat_id")
        await sio.enter_room(sid, f"chat_{chat_id}")

    @sio.event
    async def leave_chat(sid, data):
        """Leave a chat room."""
        chat_id = data.get("chat_id")
        await sio.leave_room(sid, f"chat_{chat_id}")
