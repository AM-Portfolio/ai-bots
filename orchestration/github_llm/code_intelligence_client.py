"""
Unified LLM Client for Code Intelligence

Single client to handle all LLM interactions with automatic fallback support.
Used across code intelligence features including GitHub queries, semantic search, and response beautification.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple
from shared.llm_providers.resilient_orchestrator import get_resilient_orchestrator

logger = logging.getLogger(__name__)


class CodeIntelligenceClient:
    """Unified LLM client for code intelligence with automatic provider fallback"""
    
    def __init__(
        self,
        provider: str = "azure",
        model: str = "gpt-4.1-mini",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        code_intel_api_url: str = "http://localhost:8001",
        collection_name: str = "code_intelligence"
    ):
        """
        Initialize LLM client
        
        Args:
            provider: Preferred provider (azure, together, openai)
            model: Model/deployment name
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            code_intel_api_url: Code Intelligence API endpoint
            collection_name: Vector DB collection name
        """
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.code_intel_api_url = code_intel_api_url
        self.collection_name = collection_name
        self._orchestrator = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"🤖 Code Intelligence Client initialized")
        logger.info(f"   Preferred Provider: {provider}")
        logger.info(f"   Model: {model}")
        logger.info(f"   API: {code_intel_api_url}")
        logger.info(f"   Collection: {collection_name}")
    
    def _get_orchestrator(self):
        """Get or create resilient orchestrator (lazy initialization)"""
        if self._orchestrator is None:
            self._orchestrator = get_resilient_orchestrator()
        return self._orchestrator
    
    async def query(
        self,
        query: str,
        max_results: int = 5,
        repository: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Code Intelligence API and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results
            repository: Optional repository filter
            
        Returns:
            List of search results with metadata
        """
        try:
            logger.info(f"🔍 Querying Code Intelligence: '{query[:100]}...'")
            
            # Prepare API request
            api_payload = {
                "query": query,
                "limit": max_results,
                "collection_name": self.collection_name
            }
            
            # Call Code Intelligence API
            response = await self.http_client.post(
                f"{self.code_intel_api_url}/query",
                json=api_payload
            )
            
            if response.status_code != 200:
                logger.error(f"❌ API failed: {response.status_code}")
                return []
            
            api_response = response.json()
            
            if not api_response.get('success'):
                logger.error(f"❌ Query failed: {api_response.get('error')}")
                return []
            
            results = []
            for result in api_response.get('results', []):
                payload = result.get('payload', {})
                results.append({
                    'content': result.get('content', ''),
                    'repo': payload.get('repo_name') or payload.get('source', 'local-repo'),
                    'file_path': payload.get('file_path') or payload.get('path', 'unknown'),
                    'language': payload.get('language', 'unknown'),
                    'score': result.get('score', 0.0),
                    'metadata': payload
                })
            
            logger.info(f"✅ Retrieved {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []
    
    async def beautify_response(
        self,
        query: str,
        context: str,
        summary: str,
        query_type: str = "semantic_search"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Beautify response using LLM
        
        Args:
            query: Original user query
            context: Retrieved context from sources
            summary: Generated summary
            query_type: Type of query
            
        Returns:
            Tuple of (beautified_response, metadata)
        """
        prompt = self._build_beautification_prompt(query, context, summary, query_type)
        
        logger.info(f"🎨 Beautifying response with {self.provider}")
        logger.info(f"   Prompt length: {len(prompt)} characters")
        
        try:
            orchestrator = self._get_orchestrator()
            
            response, metadata = await orchestrator.chat_completion_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                preferred_provider=self.provider,
                model=self.model
            )
            
            if not response:
                raise ValueError("LLM returned empty response")
            
            logger.info(f"✅ Beautification successful with {metadata.get('provider_used', 'unknown')}")
            logger.info(f"   Response length: {len(response)} characters")
            
            return response, metadata
            
        except Exception as e:
            logger.error(f"❌ Beautification failed: {e}")
            # Return simple formatted fallback
            fallback = self._format_fallback(query, summary)
            return fallback, {"provider_used": "fallback", "error": str(e)}
    
    def _build_beautification_prompt(
        self,
        query: str,
        context: str,
        summary: str,
        query_type: str
    ) -> str:
        """Build prompt for beautification"""
        return f"""You are a helpful code assistant. Format this search result into a clear, readable response.

Original Query: {query}
Query Type: {query_type}

Context Retrieved:
{context}

Summary:
{summary}

Please provide a well-formatted, helpful response that:
1. Directly answers the user's query
2. Highlights the most relevant code snippets
3. Explains key concepts clearly
4. Uses proper markdown formatting
5. Includes file paths and references where relevant

Response:"""
    
    def _format_fallback(self, query: str, summary: str) -> str:
        """Format fallback response when LLM fails"""
        return f"""# Query Results

**Query:** {query}

**Summary:**
{summary}

---
*Note: This is a simplified response due to LLM unavailability*
"""
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
