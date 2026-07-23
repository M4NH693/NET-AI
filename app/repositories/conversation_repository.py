from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat import ChatConversation

class ConversationRepository:
    @staticmethod
    async def create(db: AsyncSession, user_id: UUID, title: str) -> ChatConversation:
        conversation = ChatConversation(user_id=user_id, title=title)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def get(db: AsyncSession, user_id: UUID, conversation_id: UUID) -> ChatConversation | None:
        result = await db.execute(
            select(ChatConversation).where(
                ChatConversation.id == conversation_id,
                ChatConversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(db: AsyncSession, user_id: UUID) -> list[ChatConversation]:
        result = await db.execute(
            select(ChatConversation)
            .where(ChatConversation.user_id == user_id)
            .order_by(ChatConversation.last_message_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete(db: AsyncSession, conversation: ChatConversation) -> None:
        await db.delete(conversation)
        await db.commit()

    @staticmethod
    async def update_last_message_time(db: AsyncSession, conversation_id: UUID, last_message_at: datetime) -> None:
        result = await db.execute(
            select(ChatConversation).where(ChatConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            conversation.last_message_at = last_message_at
            db.add(conversation)
            await db.commit()

    @staticmethod
    async def rename(db: AsyncSession, conversation: ChatConversation, new_title: str) -> ChatConversation:
        conversation.title = new_title
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
