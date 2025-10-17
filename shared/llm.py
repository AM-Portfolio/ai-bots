from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
import logging
import json

from .config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self):
        if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
            logger.warning("Azure OpenAI credentials not configured")
            return
        
        try:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            self.client = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Optional[str]:
        if not self.client:
            logger.error("Azure OpenAI client not initialized")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
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
            logger.error("Failed to parse LLM response as JSON")
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


llm_client = LLMClient()
