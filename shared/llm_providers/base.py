from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """Base class for LLM providers with standardized interface"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Optional[str]:
        """Execute chat completion with the LLM"""
        pass
    
    @abstractmethod
    async def analyze_code(
        self,
        code: str,
        context: str,
        task: str = "analyze"
    ) -> Optional[Dict[str, Any]]:
        """Analyze code and provide structured output"""
        pass
    
    @abstractmethod
    async def generate_tests(
        self,
        code: str,
        language: str = "python"
    ) -> Optional[str]:
        """Generate unit tests for given code"""
        pass
    
    @abstractmethod
    async def generate_documentation(
        self,
        content: str,
        doc_type: str = "confluence"
    ) -> Optional[str]:
        """Generate documentation for given content"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is properly configured and available"""
        pass
