from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ConversationCreate(BaseModel):
    title: str | None = "Cuộc trò chuyện mới"

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

class MessageSend(BaseModel):
    content: str

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    content_html: str
    token_count: int | None
    created_at: datetime
