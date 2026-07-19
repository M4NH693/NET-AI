import os
import time
import logging
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
load_dotenv(override=True)

from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.ai.prompts import NETWORK_SYSTEM_PROMPT
from app.ai.token_estimator import estimate_tokens
from app.ai.prompt_builder import PromptBuilder
from app.ai.message_formatter import MessageFormatter
from app.services.llm import get_llm
from models.chat import ChatConversation, ChatMessage

# Configure Logging for LLM operations
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

llm_logger = logging.getLogger("llm_logger")
llm_logger.setLevel(logging.INFO)
if not llm_logger.handlers:
    handler = logging.FileHandler(logs_dir / "llm.log", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    llm_logger.addHandler(handler)

def debug_log(msg: str):
    try:
        with open("logs/debug.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
    except Exception as e:
        print(f"Error writing debug log: {e}")

class ChatService:
    @staticmethod
    async def create_conversation(db: AsyncSession, user_id: UUID, title: str = "Cuộc trò chuyện mới") -> ChatConversation:
        return await ConversationRepository.create(db, user_id, title)

    @staticmethod
    async def get_conversations(db: AsyncSession, user_id: UUID) -> list[ChatConversation]:
        return await ConversationRepository.list_by_user(db, user_id)

    @staticmethod
    async def delete_conversation(db: AsyncSession, user_id: UUID, conversation_id: UUID) -> bool:
        conversation = await ConversationRepository.get(db, user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên trò chuyện."
            )
        await ConversationRepository.delete(db, conversation)
        return True

    @staticmethod
    async def get_messages(db: AsyncSession, user_id: UUID, conversation_id: UUID) -> list[dict]:
        # Verify ownership
        conversation = await ConversationRepository.get(db, user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên trò chuyện hoặc bạn không có quyền truy cập."
            )
            
        messages = await MessageRepository.list_by_conversation(db, conversation_id)
        
        # Format markdown to HTML before returning to API
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "content_html": MessageFormatter.to_html(msg.content),
                "token_count": msg.token_count,
                "created_at": msg.created_at
            })
        return formatted_messages

    @staticmethod
    async def send_message(db: AsyncSession, user_id: UUID, conversation_id: UUID, content: str) -> dict:
        debug_log(f"send_message start: user={user_id} conv={conversation_id} content='{content}'")
        
        # 1. Verify ownership
        conversation = await ConversationRepository.get(db, user_id, conversation_id)
        debug_log(f"send_message step 1: verified conversation exists: {conversation is not None}")
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên trò chuyện."
            )

        # 2. Save user message to database
        user_tokens = estimate_tokens(content)
        user_msg = await MessageRepository.create(
            db, 
            conversation_id, 
            role="user", 
            content=content, 
            token_count=user_tokens
        )
        debug_log(f"send_message step 2: saved user message ID={user_msg.id}")

        # Update conversation title if it is default
        if conversation.title == "Cuộc trò chuyện mới":
            title_text = content.strip()
            new_title = title_text[:37] + "..." if len(title_text) > 40 else title_text
            await ConversationRepository.rename(db, conversation, new_title)
            debug_log(f"send_message step 2.1: updated conversation title to '{new_title}'")

        # 3. Load all conversation history for PromptBuilder context window
        history_messages = await MessageRepository.list_by_conversation(db, conversation_id)
        debug_log(f"send_message step 3: loaded history messages count={len(history_messages)}")
        
        # Build prompt list within 3000 token limit
        contents = PromptBuilder.build_prompt(history_messages, max_tokens=3000)
        debug_log(f"send_message step 3.1: built prompt context count={len(contents)}")

        # 4. Initialize LLM from factory and call asynchronously
        llm = get_llm()
        debug_log("send_message step 4: initialized LLM from factory, starting generate_response...")
        
        start_time = time.time()
        ai_response_text, actual_tokens = await llm.generate_response(contents, NETWORK_SYSTEM_PROMPT)
        latency = time.time() - start_time
        debug_log(f"send_message step 4.1: LLM returned response, latency={latency:.2f}s")

        # If actual token usage is not available, estimate it
        model_tokens = actual_tokens if actual_tokens is not None else estimate_tokens(ai_response_text)

        # 5. Log details to logs/llm.log
        llm_logger.info(
            f"model='gemini-3.1-flash-lite' latency={latency:.2f}s "
            f"prompt_tokens={user_tokens} response_tokens={model_tokens}"
        )

        # 6. Save AI message response to database
        model_msg = await MessageRepository.create(
            db, 
            conversation_id, 
            role="assistant", 
            content=ai_response_text, 
            token_count=model_tokens
        )
        debug_log(f"send_message step 6: saved AI assistant message ID={model_msg.id}")

        # 7. Update last_message_at in conversation
        now_utc = datetime.now(timezone.utc)
        await ConversationRepository.update_last_message_time(db, conversation_id, now_utc)
        debug_log("send_message step 7: updated conversation last_message_at")

        # 8. Return formatted message response
        debug_log("send_message complete, returning response to API router")
        return {
            "id": model_msg.id,
            "conversation_id": model_msg.conversation_id,
            "role": model_msg.role,
            "content": model_msg.content,
            "content_html": MessageFormatter.to_html(model_msg.content),
            "token_count": model_msg.token_count,
            "created_at": model_msg.created_at
        }

    @staticmethod
    async def regenerate_last_response(db: AsyncSession, user_id: UUID, conversation_id: UUID) -> dict:
        """
        Regenerate the last assistant response by:
        - Removing the last assistant message (if exists).
        - Generating a new response based on the previous user messages context.
        """
        # 1. Verify ownership
        conversation = await ConversationRepository.get(db, user_id, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy phiên trò chuyện."
            )

        # 2. Get history messages
        history_messages = await MessageRepository.list_by_conversation(db, conversation_id)
        if not history_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có tin nhắn nào để tạo lại."
            )

        # If the last message is assistant's message, delete it from DB first
        if history_messages[-1].role == "assistant":
            last_msg = history_messages[-1]
            await MessageRepository.delete(db, last_msg.id)
            # Remove from local list as well
            history_messages.pop()

        if not history_messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không có câu hỏi của người dùng để phản hồi."
            )

        # 3. Retrieve user's last message to recalculate tokens
        last_user_msg = history_messages[-1]
        user_tokens = last_user_msg.token_count or estimate_tokens(last_user_msg.content)

        # 4. Build prompt context
        contents = PromptBuilder.build_prompt(history_messages, max_tokens=3000)

        # 5. Initialize LLM and call
        llm = get_llm()
        
        start_time = time.time()
        ai_response_text, actual_tokens = await llm.generate_response(contents, NETWORK_SYSTEM_PROMPT)
        latency = time.time() - start_time

        model_tokens = actual_tokens if actual_tokens is not None else estimate_tokens(ai_response_text)

        # 6. Log details
        llm_logger.info(
            f"action='regenerate' model='gemini-3.1-flash-lite' latency={latency:.2f}s "
            f"prompt_tokens={user_tokens} response_tokens={model_tokens}"
        )

        # 7. Save new response to DB
        model_msg = await MessageRepository.create(
            db, 
            conversation_id, 
            role="assistant", 
            content=ai_response_text, 
            token_count=model_tokens
        )

        # 8. Update conversation last message timestamp
        now_utc = datetime.now(timezone.utc)
        await ConversationRepository.update_last_message_time(db, conversation_id, now_utc)

        # 9. Return formatted response
        return {
            "id": model_msg.id,
            "conversation_id": model_msg.conversation_id,
            "role": model_msg.role,
            "content": model_msg.content,
            "content_html": MessageFormatter.to_html(model_msg.content),
            "token_count": model_msg.token_count,
            "created_at": model_msg.created_at
        }
