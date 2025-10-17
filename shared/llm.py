from typing import List, Dict, Any, Optional
import logging

from .config import settings
from .llm_providers import get_llm_client, BaseLLMProvider

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client that supports multiple providers via factory pattern.
    Defaults to Together AI, with Azure OpenAI as fallback.
    """
    
    def __init__(self):
        self.provider: Optional[BaseLLMProvider] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LLM client using factory pattern"""
        try:
            self.provider = get_llm_client(
                provider_type=settings.llm_provider,
                together_api_key=settings.together_api_key,
                together_model=settings.together_model,
                azure_endpoint=settings.azure_openai_endpoint,
                azure_api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_deployment_name,
                azure_api_version=settings.azure_openai_api_version
            )
            
            if self.provider.is_available():
                logger.info(f"LLM client initialized with provider: {settings.llm_provider}")
            else:
                logger.warning(f"LLM provider '{settings.llm_provider}' not available")
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.provider = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Optional[str]:
        """Execute chat completion with the configured LLM provider"""
        if not self.provider:
            logger.error("LLM provider not initialized")
            return None
        
        return await self.provider.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
    
    async def analyze_code(
        self,
        code: str,
        context: str,
        task: str = "analyze"
    ) -> Optional[Dict[str, Any]]:
        """Analyze code using the configured LLM provider"""
        if not self.provider:
            logger.error("LLM provider not initialized")
            return None
        
        return await self.provider.analyze_code(
            code=code,
            context=context,
            task=task
        )
    
    async def generate_tests(
        self,
        code: str,
        language: str = "python"
    ) -> Optional[str]:
        """Generate tests using the configured LLM provider"""
        if not self.provider:
            logger.error("LLM provider not initialized")
            return None
        
        return await self.provider.generate_tests(
            code=code,
            language=language
        )
    
    async def generate_documentation(
        self,
        content: str,
        doc_type: str = "confluence"
    ) -> Optional[str]:
        """Generate documentation using the configured LLM provider"""
        if not self.provider:
            logger.error("LLM provider not initialized")
            return None
        
        return await self.provider.generate_documentation(
            content=content,
            doc_type=doc_type
        )


llm_client = LLMClient()
