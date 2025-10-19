"""
Conversation Context Manager
Manages context injection and intelligent query augmentation
"""

import logging
from typing import List, Dict, Any, Optional
from .context_extractor import ConversationContextExtractor
from .models import ConversationContext

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """Manages conversation context for multi-turn interactions"""
    
    def __init__(self):
        """Initialize context manager"""
        self.extractor = ConversationContextExtractor()
        logger.info("🧠 Conversation Context Manager initialized")
    
    def augment_query_with_context(
        self,
        query: str,
        conversation_history: List[Dict[str, Any]],
        force_context: bool = False
    ) -> tuple[str, ConversationContext]:
        """
        Augment query with conversation context
        
        Args:
            query: Current user query
            conversation_history: Previous messages
            force_context: Force context injection even if query seems complete
            
        Returns:
            Tuple of (augmented_query, extracted_context)
        """
        logger.info(f"🔍 Augmenting query with context from {len(conversation_history)} messages")
        
        # Extract context from conversation
        context = self.extractor.extract_context(conversation_history, query)
        
        # Decide if we need to augment the query
        needs_augmentation = self._needs_context_augmentation(query, context, force_context)
        
        if not needs_augmentation:
            logger.info("ℹ️  Query appears complete, no augmentation needed")
            return query, context
        
        # Build augmented query
        augmented = self._build_augmented_query(query, context)
        
        if augmented != query:
            logger.info(f"✨ Query augmented with context")
            logger.info(f"   Original: {query[:100]}")
            logger.info(f"   Augmented: {augmented[:150]}")
        
        return augmented, context
    
    def _needs_context_augmentation(
        self, 
        query: str, 
        context: ConversationContext,
        force: bool
    ) -> bool:
        """
        Determine if query needs context augmentation
        
        Args:
            query: User query
            context: Extracted context
            force: Force augmentation
            
        Returns:
            True if augmentation is needed
        """
        if force:
            return True
        
        # Check if query is a follow-up question (lacks repository context but history has it)
        query_lower = query.lower()
        
        # Query explicitly mentions repository - no augmentation needed
        repo_keywords = ['repo', 'repository', 'github.com']
        if any(keyword in query_lower for keyword in repo_keywords):
            # Has explicit repo mention
            if '/' in query:  # Likely has full repo path
                return False
            # Has keyword but maybe not full path
            if context.has_repository_context():
                return True  # Augment with full path
        
        # Follow-up indicators (pronouns, implied context)
        followup_indicators = [
            'it', 'this', 'that', 'there', 'these', 'those',
            'same', 'also', 'too', 'as well',
            'next', 'another', 'other', 'more',
            'what about', 'how about', 'tell me about'
        ]
        
        has_followup = any(indicator in query_lower for indicator in followup_indicators)
        
        # Code/file references without explicit repository
        code_keywords = [
            'function', 'class', 'method', 'api', 'endpoint',
            'file', 'code', 'implementation', 'show me', 'explain'
        ]
        has_code_query = any(keyword in query_lower for keyword in code_keywords)
        
        # Need augmentation if:
        # 1. Has follow-up indicators AND we have context
        # 2. Has code query AND we have repository context (assume they mean current repo)
        # 3. Very short query (< 20 chars) with existing context
        
        if has_followup and context.has_repository_context():
            logger.info("📌 Follow-up query detected with repository context")
            return True
        
        if has_code_query and context.has_repository_context():
            # Only augment if query doesn't already have a repo
            if '/' not in query:
                logger.info("📌 Code query detected without explicit repository")
                return True
        
        if len(query) < 20 and context.has_repository_context():
            logger.info("📌 Short query with existing repository context")
            return True
        
        return False
    
    def _build_augmented_query(self, query: str, context: ConversationContext) -> str:
        """
        Build augmented query by prepending context
        
        Args:
            query: Original query
            context: Extracted context
            
        Returns:
            Augmented query string
        """
        # Build context prefix
        context_parts = []
        
        # Add repository context if available
        if context.current_repository:
            # Check if query already mentions this repo
            if context.current_repository not in query:
                context_parts.append(f"In repository {context.current_repository}")
        
        # Add file context if relevant (only if query mentions "file" or similar)
        query_lower = query.lower()
        if context.has_file_context() and any(kw in query_lower for kw in ['file', 'this', 'it', 'that']):
            recent_files = context.files_mentioned[-2:]  # Last 2 files
            if recent_files:
                context_parts.append(f"(files: {', '.join(recent_files)})")
        
        # Build augmented query
        if context_parts:
            prefix = ", ".join(context_parts)
            augmented = f"{prefix}: {query}"
            return augmented
        
        return query
    
    def get_context_summary(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Get human-readable context summary
        
        Args:
            conversation_history: Conversation messages
            
        Returns:
            Context summary string
        """
        context = self.extractor.extract_context(conversation_history)
        return context.get_context_summary()
