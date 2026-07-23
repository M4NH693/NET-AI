from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.chat import ChatMessage

class MessageRepository:
    @staticmethod
    async def create(
        db: AsyncSession, 
        conversation_id: UUID, 
        role: str, 
        content: str, 
        token_count: int | None = None
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            token_count=token_count
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def list_by_conversation(db: AsyncSession, conversation_id: UUID) -> list[ChatMessage]:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, message_id: UUID) -> None:
        result = await db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )
        message = result.scalar_one_or_none()
        if message:
            await db.delete(message)
            await db.commit()

    @staticmethod
    async def get_last_user_message(db: AsyncSession, conversation_id: UUID) -> ChatMessage | None:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id, ChatMessage.role == "user")
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_after_timestamp(db: AsyncSession, conversation_id: UUID, created_at) -> None:
        """Delete all messages in a conversation created after a specific message timestamp."""
        await db.execute(
            delete(ChatMessage).where(
                ChatMessage.conversation_id == conversation_id,
                ChatMessage.created_at >= created_at
            )
        )
        await db.commit()
