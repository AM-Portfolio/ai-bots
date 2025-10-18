"""
Response Beautifier

Cleans and crafts beautiful, well-structured messages for LLM consumption.
"""

import logging
import time
from typing import List, Dict, Any
from orchestration.github_llm.models import SourceResult, QueryType
from shared.llm_providers.factory import LLMFactory

logger = logging.getLogger(__name__)


class ResponseBeautifier:
    """Beautifies responses for LLM consumption"""
    
    def __init__(self, llm_provider: str = "together"):
        """
        Initialize response beautifier
        
        Args:
            llm_provider: LLM provider to use for beautification
        """
        self.provider_name = llm_provider
        logger.info(f"✨ Response Beautifier initialized with provider: {llm_provider}")
    
    async def beautify(
        self,
        query: str,
        sources: List[SourceResult],
        summary: str,
        query_type: QueryType
    ) -> str:
        """
        Beautify response using LLM with enhanced logging
        
        Args:
            query: Original query
            sources: Source results
            summary: Generated summary
            query_type: Type of query
            
        Returns:
            Beautified, LLM-friendly response
        """
        logger.info("-" * 60)
        logger.info(f"✨ RESPONSE BEAUTIFIER START")
        logger.info(f"📝 Query: '{query[:80]}...'")
        logger.info(f"🎯 Query Type: {query_type.value}")
        logger.info(f"📊 Sources: {len(sources)}")
        logger.info(f"📄 Summary Length: {len(summary)} characters")
        logger.info("-" * 60)
        
        try:
            # Build context from sources
            context_start = time.time()
            context = self._build_context(sources, query_type)
            context_time = (time.time() - context_start) * 1000
            logger.info(f"🔗 Context built from {len(sources)} sources ({context_time:.2f}ms)")
            logger.info(f"   Context length: {len(context)} characters")
            
            # Create beautification prompt
            prompt_start = time.time()
            prompt = self._create_beautification_prompt(
                query=query,
                summary=summary,
                context=context,
                query_type=query_type
            )
            prompt_time = (time.time() - prompt_start) * 1000
            logger.info(f"📝 Beautification prompt created ({prompt_time:.2f}ms)")
            logger.info(f"   Prompt length: {len(prompt)} characters")
            
            # Use LLM to beautify
            llm_start = time.time()
            logger.info(f"🤖 Calling {self.provider_name.upper()} LLM for beautification...")
            provider = LLMFactory.create(self.provider_name)
            beautified = await provider.generate(
                prompt=prompt,
                temperature=0.3  # Lower temperature for more focused output
            )
            llm_time = (time.time() - llm_start) * 1000
            
            logger.info(f"✅ LLM beautification completed ({llm_time:.2f}ms)")
            logger.info(f"   Response length: {len(beautified)} characters")
            logger.info(f"   Response preview: {beautified[:200]}...")
            logger.info("-" * 60)
            logger.info(f"✅ RESPONSE BEAUTIFIER COMPLETE")
            logger.info(f"⏱️  Total Time: {context_time + prompt_time + llm_time:.2f}ms")
            logger.info("-" * 60)
            
            return beautified
            
        except Exception as e:
            logger.error(f"❌ Beautification failed: {e}", exc_info=True)
            logger.info("🔄 Using fallback formatting...")
            # Fallback to basic formatting
            fallback = self._fallback_formatting(query, summary, sources)
            logger.info(f"✅ Fallback formatting complete ({len(fallback)} characters)")
            logger.info("-" * 60)
            return fallback
    
    def _build_context(
        self,
        sources: List[SourceResult],
        query_type: QueryType
    ) -> str:
        """Build context from source results"""
        if not sources:
            return "No source context available."
        
        context_parts = []
        
        for idx, source in enumerate(sources, 1):
            repo = source.metadata.get('repo', 'Unknown')
            file_path = source.metadata.get('file_path', 'Unknown')
            
            context_parts.append(
                f"Source {idx} ({source.source_type}):\n"
                f"Repository: {repo}\n"
                f"File: {file_path}\n"
                f"Relevance: {source.relevance_score:.2f}\n"
                f"Content:\n{source.content[:500]}...\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _create_beautification_prompt(
        self,
        query: str,
        summary: str,
        context: str,
        query_type: QueryType
    ) -> str:
        """Create prompt for LLM beautification"""
        prompt = f"""You are a technical documentation expert. Your task is to create a clear, 
well-structured response to a developer's question.

User Query: {query}
Query Type: {query_type.value}

Raw Summary:
{summary}

Source Context:
{context}

Instructions:
1. Create a clear, professional response that directly answers the user's query
2. Use proper formatting (markdown headings, code blocks, lists)
3. Reference specific files and locations when relevant
4. Highlight key insights and important details
5. Keep the response concise but comprehensive
6. Use technical language appropriate for developers

Please provide a well-formatted, beautiful response:"""
        
        return prompt
    
    def _fallback_formatting(
        self,
        query: str,
        summary: str,
        sources: List[SourceResult]
    ) -> str:
        """Fallback formatting when LLM is unavailable"""
        formatted = f"""# Query: {query}

## Summary
{summary}

## Details
"""
        
        for idx, source in enumerate(sources[:3], 1):
            repo = source.metadata.get('repo', 'Unknown')
            file_path = source.metadata.get('file_path', 'Unknown')
            
            formatted += f"""
### Result {idx}
- **Repository**: {repo}
- **File**: {file_path}
- **Relevance**: {source.relevance_score:.2f}
- **Source**: {source.source_type}

```
{source.content[:300]}...
```
"""
        
        return formatted
