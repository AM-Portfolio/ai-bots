"""LLM wrapper for intelligent service interactions"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from shared.llm_providers.factory import get_llm_client
from shared.logger import get_logger

logger = get_logger(__name__)


class LLMServiceContext(BaseModel):
    """Context for LLM service interactions"""
    service_name: str
    action: str
    input_data: Dict[str, Any]
    service_capabilities: List[str] = []
    previous_results: Optional[Dict[str, Any]] = None


class ServiceLLMWrapper:
    """Wraps service calls with LLM intelligence"""
    
    def __init__(self):
        self.llm = get_llm_client()
    
    async def enhance_query(self, context: LLMServiceContext) -> Dict[str, Any]:
        """Use LLM to enhance service query parameters"""
        try:
            prompt = f"""Analyze this {context.service_name} service request and suggest optimizations:

Action: {context.action}
Input: {context.input_data}
Capabilities: {context.service_capabilities}

Provide enhanced parameters in JSON format."""

            result = await self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return {"enhanced": True, "suggestion": result}
        except Exception as e:
            logger.error(f"LLM query enhancement failed: {e}")
            return {"enhanced": False, "original": context.input_data}
    
    async def interpret_response(
        self, 
        context: LLMServiceContext, 
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to interpret and summarize service response"""
        try:
            prompt = f"""Interpret this {context.service_name} response:

Action: {context.action}
Response: {response}

Provide a concise summary and key insights."""

            interpretation = await self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            return {
                "raw_response": response,
                "interpretation": interpretation,
                "success": True
            }
        except Exception as e:
            logger.error(f"LLM response interpretation failed: {e}")
            return {"raw_response": response, "interpretation": None, "success": False}
    
    async def suggest_action(
        self, 
        service_name: str, 
        goal: str, 
        capabilities: List[str]
    ) -> str:
        """Use LLM to suggest best action for a given goal"""
        try:
            prompt = f"""Given this goal for {service_name}:
"{goal}"

Available capabilities: {capabilities}

Suggest the best action to take and parameters to use."""

            suggestion = await self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return suggestion
        except Exception as e:
            logger.error(f"LLM action suggestion failed: {e}")
            return "Unable to suggest action"
    
    async def handle_error(
        self, 
        service_name: str, 
        error: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze error and suggest fixes"""
        try:
            prompt = f"""Analyze this {service_name} error:

Error: {error}
Context: {context}

Provide:
1. Root cause analysis
2. Suggested fix
3. Prevention tips"""

            analysis = await self.llm.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return {
                "error": error,
                "analysis": analysis,
                "actionable": True
            }
        except Exception as e:
            logger.error(f"LLM error analysis failed: {e}")
            return {"error": error, "analysis": None, "actionable": False}
