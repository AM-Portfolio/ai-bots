"""
Code Summarizer with Caching

Generates concise summaries of code chunks using Azure GPT-4 mini.
Implements caching to avoid re-summarizing unchanged code.
"""

import asyncio
from typing import Optional, Dict
import logging

from parsers.base_parser import CodeChunk
from repo_state import RepoState
from rate_limiter import RateLimitController, QuotaType

logger = logging.getLogger(__name__)


class CodeSummarizer:
    """
    Generates AI-powered summaries for code chunks.
    
    Features:
    - Caching via RepoState
    - Rate-limited API calls
    - Structured prompts optimized for code
    """
    
    def __init__(
        self,
        repo_state: RepoState,
        rate_limiter: RateLimitController,
        azure_client=None
    ):
        """
        Initialize summarizer.
        
        Args:
            repo_state: State manager for caching
            rate_limiter: Rate limit controller
            azure_client: Azure OpenAI client (will auto-detect if None)
        """
        self.repo_state = repo_state
        self.rate_limiter = rate_limiter
        self.azure_client = azure_client
        
        # Initialize Azure client if not provided
        if self.azure_client is None:
            self._init_azure_client()
    
    def _init_azure_client(self):
        """Initialize Azure OpenAI client"""
        try:
            from shared.azure_services.azure_ai_manager import azure_ai_manager
            if azure_ai_manager.models.is_available():
                self.azure_client = azure_ai_manager.models
                logger.info("✅ Using Azure OpenAI for summarization")
            else:
                logger.warning("Azure OpenAI not configured")
        except Exception as e:
            logger.error(f"Failed to initialize Azure client: {e}")
    
    async def summarize_chunk(
        self,
        chunk: CodeChunk,
        use_cache: bool = True
    ) -> str:
        """
        Generate summary for a code chunk.
        
        Args:
            chunk: Code chunk to summarize
            use_cache: Whether to use cached summaries
            
        Returns:
            Summary text
        """
        # Check cache
        if use_cache:
            cached = self.repo_state.get_cached_summary(chunk.chunk_id)
            if cached:
                logger.debug(f"Cache hit for {chunk.chunk_id}")
                return cached
        
        # Generate new summary
        try:
            summary = await self._generate_summary(chunk)
            
            # Update cache
            self.repo_state.update_chunk_state(
                chunk_id=chunk.chunk_id,
                file_path=chunk.metadata.file_path,
                chunk_content=chunk.content,
                chunk_index=int(chunk.chunk_id.split('_')[-1]) if '_' in chunk.chunk_id else 0,
                summary=summary,
                status="summarized"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize {chunk.chunk_id}: {e}")
            return self._fallback_summary(chunk)
    
    async def _generate_summary(self, chunk: CodeChunk) -> str:
        """Generate summary using Azure GPT-4 mini"""
        if not self.azure_client:
            return self._fallback_summary(chunk)
        
        # Build prompt
        prompt = self._build_summary_prompt(chunk)
        
        # Call API with rate limiting
        async def call_api():
            response = await self.azure_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code analysis expert. Summarize code concisely for embedding and retrieval."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="gpt-4o-mini",
                max_tokens=150,
                temperature=0.3
            )
            return response.get("content", "")
        
        summary = await self.rate_limiter.submit(
            QuotaType.SUMMARIZATION,
            call_api,
            priority=3  # Medium priority
        )
        
        return summary.strip() if summary else self._fallback_summary(chunk)
    
    def _build_summary_prompt(self, chunk: CodeChunk) -> str:
        """Build prompt for summarization"""
        meta = chunk.metadata
        
        prompt = f"""Summarize this {meta.language} code in 1-2 sentences.

File: {meta.file_path}
Type: {meta.chunk_type}
{f"Symbol: {meta.symbol_name}" if meta.symbol_name else ""}

Code:
```{meta.language}
{chunk.content[:1000]}  # Limit to first 1000 chars
```

Provide a concise summary focusing on:
1. What the code does
2. Key inputs/outputs or parameters
3. Important logic or algorithms

Summary:"""
        return prompt
    
    def _fallback_summary(self, chunk: CodeChunk) -> str:
        """Generate simple fallback summary without AI"""
        meta = chunk.metadata
        
        if meta.symbol_name:
            return f"{meta.chunk_type} '{meta.symbol_name}' in {Path(meta.file_path).name}"
        else:
            return f"{meta.chunk_type} in {Path(meta.file_path).name} (lines {meta.start_line}-{meta.end_line})"
    
    async def summarize_batch(
        self,
        chunks: list[CodeChunk],
        use_cache: bool = True
    ) -> Dict[str, str]:
        """
        Summarize multiple chunks in parallel.
        
        Args:
            chunks: List of chunks to summarize
            use_cache: Whether to use cached summaries
            
        Returns:
            Dict mapping chunk_id -> summary
        """
        tasks = [
            self.summarize_chunk(chunk, use_cache)
            for chunk in chunks
        ]
        
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        result = {}
        for chunk, summary in zip(chunks, summaries):
            if isinstance(summary, Exception):
                logger.error(f"Failed to summarize {chunk.chunk_id}: {summary}")
                result[chunk.chunk_id] = self._fallback_summary(chunk)
            else:
                result[chunk.chunk_id] = summary
        
        return result


# Fix import
from pathlib import Path
