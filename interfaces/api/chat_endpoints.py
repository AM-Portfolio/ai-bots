"""
Chat conversation management API endpoints

Handles chat history, conversation persistence, and message management.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from db import ChatRepository, ChatConversation, ChatMessage
from interfaces.api.core import get_db
from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessageModel(BaseModel):
    role: str
    content: str
    duration: Optional[float] = None


class SaveConversationRequest(BaseModel):
    conversation_id: Optional[int] = None
    title: str
    provider: str
    messages: List[ChatMessageModel]


class ConversationResponse(BaseModel):
    id: int
    title: str
    provider: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    duration: Optional[float]
    created_at: datetime


@router.post("/conversations")
async def save_conversation(request: SaveConversationRequest, db: Session = Depends(get_db)):
    """Save or update a chat conversation"""
    try:
        chat_repo = ChatRepository(db)
        
        if request.conversation_id:
            # Update existing conversation
            conversation = chat_repo.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            # Create new conversation
            conversation = chat_repo.create_conversation(
                title=request.title,
                provider=request.provider
            )
        
        # Add messages
        for msg in request.messages:
            chat_repo.add_message(
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                duration=msg.duration
            )
        
        return {"success": True, "conversation_id": conversation.id}
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(db: Session = Depends(get_db)):
    """List all chat conversations"""
    try:
        chat_repo = ChatRepository(db)
        conversations = chat_repo.list_conversations(limit=50)
        
        result = []
        for conv in conversations:
            result.append(ConversationResponse(
                id=conv.id,
                title=conv.title,
                provider=conv.provider,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages) if conv.messages else 0
            ))
        
        return result
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Get all messages for a conversation"""
    try:
        chat_repo = ChatRepository(db)
        messages = chat_repo.get_messages(conversation_id)
        
        return [
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                duration=msg.duration,
                created_at=msg.created_at
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a chat conversation"""
    try:
        chat_repo = ChatRepository(db)
        success = chat_repo.delete_conversation(conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))