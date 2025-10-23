"""
Voice Assistant API endpoints

Handles voice conversation sessions, processing, and history management.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Initialize voice orchestrator (lazy-loaded)
_voice_orchestrator = None


def get_voice_orchestrator():
    """Get or create voice orchestrator instance"""
    global _voice_orchestrator
    if _voice_orchestrator is None:
        from orchestration.voice_assistant import VoiceOrchestrator
        _voice_orchestrator = VoiceOrchestrator()
    return _voice_orchestrator


class VoiceSessionRequest(BaseModel):
    """Request to create or get a voice session"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class VoiceSessionResponse(BaseModel):
    """Response for voice session"""
    session_id: str
    created_at: datetime
    turn_count: int
    status: str


class VoiceProcessRequest(BaseModel):
    """Request to process voice input"""
    session_id: str
    audio_data: str  # Base64 encoded audio
    audio_format: str = "webm"  # webm, mp3, wav


class VoiceProcessResponse(BaseModel):
    """Response from voice processing"""
    session_id: str
    transcript: str
    intent: str
    confidence: float
    response_text: str
    response_audio: Optional[str] = None
    orchestration_used: str
    thinking: Optional[Dict[str, Any]] = None


@router.post("/session", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceSessionRequest):
    """
    Create or retrieve a voice conversation session
    
    This maintains conversation context across multiple voice interactions.
    """
    logger.info(f"🎤 Voice session request: {request.session_id}")
    
    try:
        orchestrator = get_voice_orchestrator()
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get or create session
        session = orchestrator.session_manager.get_or_create_session(
            session_id,
            request.user_id
        )
        
        return VoiceSessionResponse(
            session_id=session.session_id,
            created_at=session.created_at,
            turn_count=len(session.turns),
            status="active"
        )
        
    except Exception as e:
        logger.error(f"❌ Voice session creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=VoiceProcessResponse)
async def process_voice(request: VoiceProcessRequest):
    """
    Process voice input end-to-end
    
    Flow:
    1. Transcribe audio (STT)
    2. Classify intent
    3. Route to orchestration (commit, GitHub query, general)
    4. Format response for voice
    5. Synthesize speech (TTS)
    
    Returns transcript, intent, response text, and audio.
    """
    logger.info(f"🎤 Processing voice for session: {request.session_id}")
    
    try:
        orchestrator = get_voice_orchestrator()
        
        # Create voice request
        from orchestration.voice_assistant.voice_orchestrator import VoiceRequest
        voice_request = VoiceRequest(
            session_id=request.session_id,
            audio_data=request.audio_data,
            audio_format=request.audio_format
        )
        
        # Process voice request
        result = await orchestrator.process_voice_request(voice_request)
        
        return VoiceProcessResponse(
            session_id=result.session_id,
            transcript=result.transcript,
            intent=result.intent,
            confidence=result.confidence,
            response_text=result.response_text,
            response_audio=result.response_audio,
            orchestration_used=result.orchestration_used,
            thinking=result.thinking
        )
        
    except Exception as e:
        logger.error(f"❌ Voice processing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        orchestrator = get_voice_orchestrator()
        history = orchestrator.session_manager.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))