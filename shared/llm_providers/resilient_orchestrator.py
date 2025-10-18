"""
Resilient LLM Orchestrator

Provides automatic fallback and retry logic across multiple LLM providers.
If one provider fails, automatically tries the next one until success or all fail.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Status of LLM provider attempt"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"


class ResilientLLMOrchestrator:
    """
    Orchestrates LLM requests across multiple providers with automatic fallback
    
    Features:
    - Automatic fallback to alternative providers
    - Retry logic with configurable attempts
    - Circuit breaker pattern for failed providers
    - Detailed error tracking and reporting
    """
    
    def __init__(self):
        self.provider_priority = [
            'together',  # Primary
            'azure',     # Fallback 1
            'openai'     # Fallback 2 (if configured)
        ]
        
        # Track provider health
        self.provider_failures = {
            'together': 0,
            'azure': 0,
            'openai': 0
        }
        
        self.max_failures_before_skip = 3
        self.timeout_seconds = 30
    
    async def chat_completion_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_retries: int = 2,
        preferred_provider: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Execute chat completion with automatic fallback
        
        Args:
            messages: Chat messages
            temperature: Sampling temperature
            max_retries: Max retries per provider
            preferred_provider: Preferred provider to try first
            
        Returns:
            Tuple of (response_text, metadata)
        """
        # Reorder providers if preference specified
        providers = self._get_provider_order(preferred_provider)
        
        all_errors = []
        attempts_log = []
        
        logger.info(f"🔄 Starting resilient LLM request with {len(providers)} providers")
        logger.info(f"   Provider order: {' → '.join(providers)}")
        
        for provider_name in providers:
            # Skip if provider has too many recent failures
            if self.provider_failures.get(provider_name, 0) >= self.max_failures_before_skip:
                logger.warning(f"⏭️  Skipping {provider_name} (circuit breaker: {self.provider_failures[provider_name]} failures)")
                attempts_log.append({
                    'provider': provider_name,
                    'status': ProviderStatus.UNAVAILABLE.value,
                    'error': f'Circuit breaker active ({self.provider_failures[provider_name]} failures)'
                })
                continue
            
            # Try this provider with retries
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"🤖 Attempting {provider_name} (attempt {attempt}/{max_retries})")
                    
                    response, metadata = await self._try_provider(
                        provider_name,
                        messages,
                        temperature
                    )
                    
                    # Success! Reset failure count and return
                    self.provider_failures[provider_name] = 0
                    
                    metadata.update({
                        'provider_used': provider_name,
                        'attempt_number': attempt,
                        'total_attempts': len(attempts_log) + 1,
                        'fallback_used': len(attempts_log) > 0
                    })
                    
                    logger.info(
                        f"✅ Success with {provider_name} on attempt {attempt} "
                        f"(total attempts: {len(attempts_log) + 1})"
                    )
                    
                    return response, metadata
                    
                except asyncio.TimeoutError:
                    error_msg = f"Timeout after {self.timeout_seconds}s"
                    logger.warning(f"⏱️  {provider_name} timed out (attempt {attempt})")
                    
                    attempts_log.append({
                        'provider': provider_name,
                        'attempt': attempt,
                        'status': ProviderStatus.TIMEOUT.value,
                        'error': error_msg
                    })
                    
                    all_errors.append(f"{provider_name}: {error_msg}")
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.warning(f"❌ {provider_name} failed (attempt {attempt}): {error_msg[:100]}")
                    
                    attempts_log.append({
                        'provider': provider_name,
                        'attempt': attempt,
                        'status': ProviderStatus.FAILED.value,
                        'error': error_msg
                    })
                    
                    all_errors.append(f"{provider_name}: {error_msg}")
                    
                    # If last attempt for this provider, increment failure count
                    if attempt == max_retries:
                        self.provider_failures[provider_name] += 1
                    
                    # Small delay before retry
                    if attempt < max_retries:
                        await asyncio.sleep(0.5)
        
        # All providers failed
        logger.error(f"❌ All providers failed after {len(attempts_log)} attempts")
        
        raise Exception(
            f"All LLM providers failed. Tried: {', '.join(providers)}. "
            f"Errors: {' | '.join(all_errors[:3])}"
        )
    
    async def _try_provider(
        self,
        provider_name: str,
        messages: List[Dict[str, str]],
        temperature: float
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Try a specific provider with timeout
        
        Args:
            provider_name: Provider to use
            messages: Chat messages
            temperature: Sampling temperature
            
        Returns:
            Tuple of (response, metadata)
        """
        from shared.llm_providers.factory import LLMFactory
        
        # Create provider
        factory = LLMFactory()
        provider = factory.create_provider(provider_name)
        
        # Execute with timeout
        response = await asyncio.wait_for(
            provider.chat_completion(messages, temperature),
            timeout=self.timeout_seconds
        )
        
        metadata = {
            'provider': provider_name,
            'model': getattr(provider, 'model', 'unknown'),
            'temperature': temperature
        }
        
        return response, metadata
    
    def _get_provider_order(self, preferred: Optional[str] = None) -> List[str]:
        """
        Get ordered list of providers to try
        
        Args:
            preferred: Preferred provider to try first
            
        Returns:
            Ordered list of provider names
        """
        providers = self.provider_priority.copy()
        
        if preferred and preferred in providers:
            # Move preferred to front
            providers.remove(preferred)
            providers.insert(0, preferred)
        
        return providers
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        self.provider_failures = {k: 0 for k in self.provider_failures}
        logger.info("🔄 Reset all circuit breakers")
    
    def get_provider_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            'providers': {
                name: {
                    'failures': count,
                    'circuit_breaker_active': count >= self.max_failures_before_skip
                }
                for name, count in self.provider_failures.items()
            },
            'circuit_breaker_threshold': self.max_failures_before_skip
        }


# Global instance
_global_orchestrator = ResilientLLMOrchestrator()


def get_resilient_orchestrator() -> ResilientLLMOrchestrator:
    """Get the global resilient orchestrator instance"""
    return _global_orchestrator
