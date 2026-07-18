from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from datasabe import get_db
from models.user import User
from app.auth import get_current_active_user
from app.services.chat_service import ChatService
from schemas.chat import ConversationCreate, ConversationResponse, MessageSend, MessageResponse

router = APIRouter(prefix="/api/chat", tags=["Chat AI"])

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    title = conv_data.title or "Cuộc trò chuyện mới"
    return await ChatService.create_conversation(db, current_user.id, title)

@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await ChatService.get_conversations(db, current_user.id)

@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await ChatService.delete_conversation(db, current_user.id, id)
    return None

@router.get("/conversations/{id}/messages", response_model=list[MessageResponse])
async def get_messages(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await ChatService.get_messages(db, current_user.id, id)

@router.post("/conversations/{id}/messages", response_model=MessageResponse)
async def send_message(
    id: UUID,
    msg_data: MessageSend,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if not msg_data.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung tin nhắn không thể bỏ trống."
        )
    return await ChatService.send_message(db, current_user.id, id, msg_data.content)

@router.post("/conversations/{id}/regenerate", response_model=MessageResponse)
async def regenerate_message(
    id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    return await ChatService.regenerate_last_response(db, current_user.id, id)
