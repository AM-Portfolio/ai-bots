from together import Together
from typing import List, Dict, Any, Optional
import json
import os
import time

from .base import BaseLLMProvider
from shared.logger import get_logger

logger = get_logger(__name__)


class TogetherAIProvider(BaseLLMProvider):
    """Together AI LLM provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"):
        self.api_key = api_key or os.environ.get("TOGETHER_API_KEY")
        self.model = model
        self.client: Any = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not self.api_key:
            logger.warning("Together AI API key not configured", provider="together", status="not_configured")
            return
        
        try:
            # Set the environment variable (Together client uses env var, not api_key parameter)
            if self.api_key and not os.environ.get("TOGETHER_API_KEY"):
                os.environ["TOGETHER_API_KEY"] = self.api_key
                logger.debug("Set TOGETHER_API_KEY environment variable from config")
            
            # Initialize Together AI client (uses TOGETHER_API_KEY env var)
            self.client = Together()
            logger.info(
                "Together AI client initialized successfully",
                provider="together",
                model=self.model,
                status="ready"
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Together AI client",
                provider="together",
                error=str(e)
            )
            self.client = None
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Optional[str]:
        if not self.client:
            logger.error("Together AI client not initialized", provider="together", status="not_initialized")
            return None
        
        # Extract prompt for logging
        prompt = messages[-1].get("content", "") if messages else ""
        
        # Log request
        logger.log_llm_request(
            provider="Together AI",
            model=self.model,
            prompt=prompt,
            temperature=temperature
        )
        
        start_time = time.time()
        
        try:
            response = self.client.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            
            result = response.choices[0].message.content
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            logger.log_llm_response(
                provider="Together AI",
                response=result,
                duration_ms=duration_ms,
                tokens=getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None
            )
            
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error response
            logger.log_llm_response(
                provider="Together AI",
                response=None,
                duration_ms=duration_ms,
                error=str(e)
            )
            return None
    
    async def analyze_code(
        self,
        code: str,
        context: str,
        task: str = "analyze"
    ) -> Optional[Dict[str, Any]]:
        system_message = """You are an expert software engineer and code analyst. 
        Provide detailed, actionable analysis of code issues and suggest fixes."""
        
        user_message = f"""
Task: {task}

Context: {context}

Code:
```
{code}
```

Provide your analysis in JSON format with the following structure:
{{
    "root_cause": "description of the issue",
    "affected_components": ["component1", "component2"],
    "suggested_fix": "detailed fix description",
    "fixed_code": "the corrected code",
    "explanation": "explanation of the fix",
    "confidence": 0.95
}}
"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3)
        
        if not response:
            return None
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error("Failed to parse Together AI response as JSON")
            return {"raw_response": response}
    
    async def generate_tests(
        self,
        code: str,
        language: str = "python"
    ) -> Optional[str]:
        system_message = f"""You are an expert test engineer. 
        Generate comprehensive unit tests for {language} code."""
        
        user_message = f"""
Generate unit tests for the following code:

```{language}
{code}
```

Provide complete, runnable test code with all necessary imports and test cases.
"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        return await self.chat_completion(messages, temperature=0.5)
    
    async def generate_documentation(
        self,
        content: str,
        doc_type: str = "confluence"
    ) -> Optional[str]:
        system_message = f"""You are a technical writer. 
        Create clear, comprehensive documentation in {doc_type} format."""
        
        user_message = f"""
Create documentation for the following:

{content}

Format the output as markdown suitable for {doc_type}.
"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        return await self.chat_completion(messages, temperature=0.7)
