"""
Together AI Provider Implementation

Wraps existing Together AI LLM provider to implement cloud-agnostic templates.
"""

from typing import Optional, Dict, Any, List
from ..templates.base import (
    CloudProvider,
    LLMProvider,
    ProviderConfig,
    ProviderCapability,
    LLMResult
)
from shared.llm_providers.together_provider import TogetherAIProvider as LegacyTogetherProvider
from shared.logger import get_logger

logger = get_logger(__name__)


class TogetherProvider(CloudProvider, LLMProvider):
    """
    Together AI Provider
    
    Implements LLM capabilities using Together AI:
    - Chat Completion
    - Embeddings
    """
    
    def __init__(self, config: ProviderConfig, capability: ProviderCapability):
        super().__init__(config)
        self.capability = capability
        
        self.llm_provider = LegacyTogetherProvider(
            api_key=config.api_key,
            model=config.model or "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        )
        
        self._capabilities = [
            ProviderCapability.LLM_CHAT,
            ProviderCapability.LLM_EMBEDDING,
        ]
        
        logger.info(f"🟢 Together AI Provider initialized for {capability.value}")
    
    def is_available(self) -> bool:
        """Check if Together AI is available"""
        return self.llm_provider.is_available()
    
    def get_capabilities(self) -> List[ProviderCapability]:
        """Get supported capabilities"""
        return self._capabilities
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Together AI"""
        return {
            "provider": "together",
            "available": self.is_available(),
            "model": self.config.model,
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> LLMResult:
        """Generate chat completion using Together AI"""
        content = await self.llm_provider.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if not content:
            raise RuntimeError("Together AI returned empty response")
        
        return LLMResult(
            content=content,
            model=self.config.model or "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            usage=None,
            metadata={"provider": "together"}
        )
    
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding using Together AI"""
        return await self.llm_provider.generate_embedding(text, model)
    
    @property
    def model_name(self) -> str:
        """Get current model name"""
        return self.config.model or "meta-llama/Llama-3.3-70B-Instruct-Turbo"
