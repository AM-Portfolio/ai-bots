"""
Azure Enhanced Summarizer

Uses Azure OpenAI to enhance and improve responses with better formatting,
context, and clarity. Applied to both chat and voice assistant responses.

Features:
- Context-aware summarization
- Better formatting and structure
- Improved readability
- Code section enhancement
- Multilingual support
"""

import logging
from typing import Optional
from shared.llm_providers.resilient_orchestrator import ResilientLLMOrchestrator
from shared.config import settings

logger = logging.getLogger(__name__)


class AzureEnhancedSummarizer:
    """
    Enhanced summarizer using Azure OpenAI for better response quality
    
    Improves responses by:
    - Adding proper context and structure
    - Enhancing code explanations
    - Improving formatting
    - Maintaining technical accuracy
    - Supporting multilingual content
    """
    
    def __init__(self):
        self.llm = ResilientLLMOrchestrator()
        self.enabled = settings.llm_provider == "azure" or settings.chat_provider == "azure"
        
        logger.info("✨ Azure Enhanced Summarizer initialized")
        logger.info(f"   • Enabled: {self.enabled}")
        logger.info(f"   • Provider: {settings.llm_provider}")
    
    async def enhance_response(
        self,
        original_response: str,
        context: Optional[str] = None,
        response_type: str = "general"
    ) -> str:
        """
        Enhance response with Azure LLM for better quality
        
        Args:
            original_response: The original response text
            context: Optional context about the query
            response_type: Type of response (general, code, technical, voice)
            
        Returns:
            Enhanced response with better formatting and clarity
        """
        if not self.enabled:
            logger.info("ℹ️  Azure enhancer disabled, returning original response")
            return original_response
        
        try:
            logger.info(f"✨ Enhancing response (type: {response_type})...")
            logger.info(f"   • Original length: {len(original_response)} chars")
            
            # Build enhancement prompt
            enhancement_prompt = self._build_enhancement_prompt(
                original_response,
                context,
                response_type
            )
            
            # Use Azure LLM to enhance
            provider = self.llm.get_provider_for_role("chat")
            enhanced = await provider.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at improving technical responses. Enhance the given text while maintaining accuracy."
                    },
                    {
                        "role": "user",
                        "content": enhancement_prompt
                    }
                ],
                temperature=0.3
            )
            
            logger.info(f"✅ Response enhanced")
            logger.info(f"   • Enhanced length: {len(enhanced)} chars")
            
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Enhancement error: {e}")
            # Return original if enhancement fails
            return original_response
    
    def _build_enhancement_prompt(
        self,
        response: str,
        context: Optional[str],
        response_type: str
    ) -> str:
        """Build the enhancement prompt based on response type"""
        
        base_instructions = """
        Improve the following response by:
        1. Adding clear structure with proper headings and sections
        2. Enhancing code explanations with inline comments where helpful
        3. Improving formatting (markdown, lists, code blocks)
        4. Adding context where it helps understanding
        5. Maintaining all technical accuracy
        6. Keeping the same language as the original
        
        DO NOT:
        - Change the core information or facts
        - Remove any code examples
        - Add unnecessary verbosity
        - Change technical terms incorrectly
        """
        
        if response_type == "code":
            type_specific = "\n\nFocus on code clarity, add comments, and explain key concepts."
        elif response_type == "voice":
            type_specific = "\n\nMake it more conversational and concise for voice interaction."
        elif response_type == "technical":
            type_specific = "\n\nEnsure technical accuracy and add architectural context."
        else:
            type_specific = "\n\nMake it clear, well-structured, and easy to understand."
        
        context_section = ""
        if context:
            context_section = f"\n\nContext: {context}"
        
        prompt = f"""{base_instructions}{type_specific}{context_section}

Original Response:
{response}

Enhanced Response:"""
        
        return prompt
    
    async def enhance_code_section(
        self,
        code: str,
        language: str,
        explanation: Optional[str] = None
    ) -> str:
        """
        Enhance code sections with better comments and explanations
        
        Args:
            code: The code snippet
            language: Programming language
            explanation: Optional explanation text
            
        Returns:
            Enhanced code with comments and improved explanation
        """
        if not self.enabled:
            return code
        
        try:
            logger.info(f"💻 Enhancing code section ({language})...")
            
            prompt = f"""
            Add helpful inline comments to this {language} code. Make it more understandable without changing the logic.
            
            Code:
            ```{language}
            {code}
            ```
            
            Return only the enhanced code with comments, wrapped in ```{language} code blocks.
            """
            
            provider = self.llm.get_provider_for_role("chat")
            enhanced = await provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            logger.info("✅ Code section enhanced")
            return enhanced
            
        except Exception as e:
            logger.error(f"❌ Code enhancement error: {e}")
            return code
    
    async def summarize_for_voice(
        self,
        text: str,
        max_length: int = 500
    ) -> str:
        """
        Create voice-optimized summary
        
        Args:
            text: Original text
            max_length: Maximum character length
            
        Returns:
            Concise, conversational summary for voice output
        """
        if not self.enabled:
            # Simple truncation fallback
            return text[:max_length] + "..." if len(text) > max_length else text
        
        try:
            logger.info(f"🎙️  Creating voice summary (max {max_length} chars)...")
            
            prompt = f"""
            Create a concise, conversational summary of this text for voice output.
            Maximum length: {max_length} characters.
            Focus on key points. Use natural, spoken language.
            
            Text:
            {text}
            
            Summary:
            """
            
            provider = self.llm.get_provider_for_role("chat")
            summary = await provider.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            # Ensure it fits max length
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            logger.info(f"✅ Voice summary created ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Voice summary error: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text


# Global instance
azure_enhanced_summarizer = AzureEnhancedSummarizer()
