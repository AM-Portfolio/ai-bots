"""
Session Manager for Voice Assistant

Maintains conversation context across multiple turns for each user session.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConversationTurn(BaseModel):
    """Represents a single turn in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    intent: Optional[str] = None
    orchestration_used: Optional[str] = None


class VoiceSession(BaseModel):
    """Represents a voice conversation session"""
    session_id: str
    user_id: Optional[str] = None
    turns: List[ConversationTurn] = []
    created_at: datetime
    last_activity: datetime
    context: Dict[str, Any] = {}


class SessionManager:
    """
    Manages voice conversation sessions with context retention
    
    Features:
    - Session creation and lifecycle management
    - Conversation history storage
    - Context tracking (detected intents, repository mentions, etc.)
    - Automatic session cleanup
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        self.sessions: Dict[str, VoiceSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        logger.info("✅ SessionManager initialized")
    
    def create_session(self, session_id: str, user_id: Optional[str] = None) -> VoiceSession:
        """Create a new conversation session"""
        now = datetime.now()
        session = VoiceSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_activity=now
        )
        self.sessions[session_id] = session
        logger.info(f"📝 Created voice session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Retrieve an existing session"""
        session = self.sessions.get(session_id)
        if session:
            # Check if session expired
            if datetime.now() - session.last_activity > self.session_timeout:
                logger.warning(f"⏰ Session {session_id} expired, creating new one")
                del self.sessions[session_id]
                return None
        return session
    
    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> VoiceSession:
        """Get existing session or create new one"""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id, user_id)
        return session
    
    def add_turn(self, session_id: str, role: str, content: str, 
                 intent: Optional[str] = None, orchestration: Optional[str] = None) -> None:
        """Add a conversation turn to the session"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"❌ Session {session_id} not found")
            return
        
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(),
            intent=intent,
            orchestration_used=orchestration
        )
        session.turns.append(turn)
        session.last_activity = datetime.now()
        
        logger.info(f"💬 Added {role} turn to session {session_id}: {content[:50]}...")
    
    def get_conversation_history(self, session_id: str, max_turns: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        # Return last N turns in LLM format
        history = []
        for turn in session.turns[-max_turns:]:
            history.append({
                "role": turn.role,
                "content": turn.content
            })
        return history
    
    def update_context(self, session_id: str, key: str, value: Any) -> None:
        """Update session context (e.g., detected repository, last commit)"""
        session = self.get_session(session_id)
        if session:
            session.context[key] = value
            logger.info(f"🔧 Updated context for {session_id}: {key} = {value}")
    
    def get_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """Retrieve context value"""
        session = self.get_session(session_id)
        if session:
            return session.context.get(key, default)
        return default
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions"""
        now = datetime.now()
        expired = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_activity > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
        
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
