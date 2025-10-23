"""
Voice Response Formatter

Converts orchestration responses into voice-friendly, conversational format.
"""

import logging
import re
from typing import Optional

from shared.llm_providers.resilient_orchestrator import ResilientLLMOrchestrator
from orchestration.summary_layer.beautifier import ResponseBeautifier

logger = logging.getLogger(__name__)


class VoiceResponseFormatter:
    """
    Formats responses for voice output
    
    Features:
    - Summarizes long responses
    - Removes markdown formatting
    - Makes responses conversational
    - Keeps responses concise (configurable max length)
    - Uses existing beautifier for initial cleanup
    """
    
    def __init__(self, llm_orchestrator: ResilientLLMOrchestrator, 
                 beautifier: ResponseBeautifier,
                 max_length: int = 500):
        self.llm = llm_orchestrator
        self.beautifier = beautifier
        self.max_length = max_length
        logger.info(f"✅ VoiceResponseFormatter initialized (max_length={max_length})")
    
    async def format_for_voice(self, response: str, intent_type: str = "general") -> str:
        """
        Format response for voice output
        
        Args:
            response: Original response from orchestration
            intent_type: Type of intent (for context-aware formatting)
            
        Returns:
            Voice-optimized response string
        """
        logger.info(f"🎤 Formatting response for voice (length: {len(response)})")
        
        # Step 1: Remove markdown formatting (skip beautifier for voice)
        # Beautifier needs sources and query_type which we don't have in voice context
        clean_text = self._remove_markdown(response)
        
        # Step 3: If too long, summarize
        if len(clean_text) > self.max_length:
            clean_text = await self._summarize_for_voice(clean_text, intent_type)
        
        # Step 4: Make conversational
        conversational = await self._make_conversational(clean_text, intent_type)
        
        logger.info(f"✅ Voice response ready (final length: {len(conversational)})")
        return conversational
    
    def _remove_markdown(self, text: str) -> str:
        """Remove markdown formatting for voice"""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '[code block]', text)
        text = re.sub(r'`[^`]+`', '', text)
        
        # Remove headers
        text = re.sub(r'#{1,6}\s+', '', text)
        
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove bullets
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Remove numbers from ordered lists
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    async def _summarize_for_voice(self, text: str, intent_type: str) -> str:
        """Summarize long responses for voice"""
        logger.info(f"📝 Summarizing long response ({len(text)} chars)")
        
        prompt = f"""Summarize this response for voice output. Keep it under {self.max_length} characters.
Make it conversational and natural for speaking. Focus on the key points.

Intent type: {intent_type}

Original response:
{text}

Voice-friendly summary:"""
        
        try:
            # Use chat completion instead of generate
            summary, metadata = await self.llm.chat_completion_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_retries=1
            )
            
            return summary if summary else text[:self.max_length]
            
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            # Fallback: truncate intelligently
            return text[:self.max_length] + "..."
    
    async def _make_conversational(self, text: str, intent_type: str) -> str:
        """Make response more conversational for voice"""
        
        # Intent-specific prefixes
        prefixes = {
            "commit": "Alright, ",
            "github_query": "Let me tell you what I found. ",
            "help": "Happy to help! ",
            "general": ""
        }
        
        prefix = prefixes.get(intent_type, "")
        
        # Add conversational transitions
        conversational = prefix + text
        
        # Replace technical jargon with friendlier alternatives
        replacements = {
            "repository": "repo",
            "function": "method",
            "execute": "run",
            "initialize": "set up",
            "terminate": "stop"
        }
        
        for technical, friendly in replacements.items():
            conversational = re.sub(r'\b' + technical + r'\b', friendly, conversational, flags=re.IGNORECASE)
        
        return conversational
