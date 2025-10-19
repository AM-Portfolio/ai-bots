"""
Context Manager Data Models
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ContextType(str, Enum):
    """Types of context that can be tracked"""
    REPOSITORY = "repository"
    FILE_PATH = "file_path"
    CODE_ENTITY = "code_entity"
    TOPIC = "topic"
    FEATURE = "feature"
    TASK = "task"


class ConversationContext(BaseModel):
    """Structured conversation context"""
    
    # Repository context
    current_repository: Optional[str] = Field(None, description="Currently active repository (owner/repo format)")
    repositories_mentioned: List[str] = Field(default_factory=list, description="All repositories mentioned in conversation")
    
    # File and code context
    files_mentioned: List[str] = Field(default_factory=list, description="File paths mentioned")
    code_entities: List[str] = Field(default_factory=list, description="Functions, classes, methods mentioned")
    
    # Topic and task context
    topics: List[str] = Field(default_factory=list, description="Topics discussed (e.g., 'authentication', 'API')")
    features: List[str] = Field(default_factory=list, description="Features being discussed")
    tasks: List[str] = Field(default_factory=list, description="Tasks or action items")
    
    # Metadata
    last_query_type: Optional[str] = Field(None, description="Type of last query")
    conversation_depth: int = Field(0, description="Number of turns in conversation")
    
    def has_repository_context(self) -> bool:
        """Check if repository context exists"""
        return self.current_repository is not None
    
    def has_file_context(self) -> bool:
        """Check if file context exists"""
        return len(self.files_mentioned) > 0
    
    def has_code_context(self) -> bool:
        """Check if code entity context exists"""
        return len(self.code_entities) > 0
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        parts = []
        if self.current_repository:
            parts.append(f"Repository: {self.current_repository}")
        if self.files_mentioned:
            parts.append(f"Files: {', '.join(self.files_mentioned[:3])}")
        if self.topics:
            parts.append(f"Topics: {', '.join(self.topics[:3])}")
        return " | ".join(parts) if parts else "No active context"


class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
