"""
GitHub-LLM Query Orchestrator

Uses LangGraph to orchestrate queries across code intelligence and GitHub API,
then formats responses using the summary/beautify layer.
"""

from __future__ import annotations

import logging
import time
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import QueryRequest, QueryResponse, SourceResult, QueryType
from .orchestrator_config import GitHubLLMConfig
from .code_intelligence_client import CodeIntelligenceClient
from shared.clients.wrappers.github_wrapper import GitHubWrapper

logger = logging.getLogger(__name__)


class GitHubLLMOrchestrator:
    """Orchestrates queries across multiple sources using LangGraph-style workflow"""
    
    def __init__(
        self,
        config: Optional[GitHubLLMConfig] = None,
        github_client: Optional[GitHubWrapper] = None,
    ):
        """
        Initialize GitHub-LLM orchestrator
        
        Args:
            config: Configuration object (uses defaults if not provided)
            github_client: GitHub API client
        """
        self.config = config or GitHubLLMConfig.from_settings()
        self.github_client = github_client
        
        # Initialize Code Intelligence client
        self.client = CodeIntelligenceClient(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            max_tokens=self.config.llm_max_tokens,
            code_intel_api_url=self.config.code_intelligence_api_url,
            collection_name=self.config.collection_name
        )
        
        logger.info("🤖 GitHub-LLM Orchestrator initialized")
        logger.info(f"   🌐 API: {self.config.code_intelligence_api_url}")
        logger.info(f"   📂 Collection: {self.config.collection_name}")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("CODE INTELLIGENCE QUERY START")
        logger.info(f"Query: '{request.query[:100]}...'")
        logger.info(f"Type: {request.query_type.value}")
        logger.info("=" * 80)
        
        # Query using client
        raw_results = await self.client.query(
            query=request.query,
            max_results=request.max_results,
            repository=request.repository
        )
        logger.info(f"Retrieved {len(raw_results)} results")
        
        # Convert to SourceResult format
        results = [
            SourceResult(
                source_type='code_intelligence',
                content=r['content'],
                metadata={
                    'repo': r['repo'],
                    'file_path': r['file_path'],
                    'language': r['language']
                },
                relevance_score=r['score']
            )
            for r in raw_results
        ]
        
        # Generate Summary
        summary = self._generate_summary(results, request)
        
        # Beautify Response
        beautified = summary
        if self.config.enable_beautification:
            beautified = await self._beautify_response(
                query=request.query,
                sources=results,
                summary=summary,
                query_type=request.query_type
            )
        
        # Calculate confidence
        confidence = self._calculate_confidence(results)
        processing_time = (time.time() - start_time) * 1000
        
        response = QueryResponse(
            query=request.query,
            query_type=request.query_type,
            sources=results,
            summary=summary,
            beautified_response=beautified,
            confidence_score=confidence,
            processing_time_ms=processing_time,
            metadata={'total_results': len(results)}
        )
        
        logger.info(f"QUERY COMPLETE - Total: {processing_time:.2f}ms | Results: {len(results)}")
        return response
    
    def _generate_summary(
        self,
        results: List[SourceResult],
        request: QueryRequest
    ) -> str:
        """Generate a summary of the results"""
        if not results:
            return "No results found for your query."
        
        summary_parts = [f"Found {len(results)} relevant results:"]
        
        for idx, result in enumerate(results[:3], 1):
            repo = result.metadata.get('repo', 'unknown')
            file_path = result.metadata.get('file_path', 'unknown')
            summary_parts.append(
                f"{idx}. {repo}/{file_path} (relevance: {result.relevance_score:.2f})"
            )
        
        return "\n".join(summary_parts)
    
    async def _beautify_response(
        self,
        query: str,
        sources: List[SourceResult],
        summary: str,
        query_type: QueryType
    ) -> str:
        """Beautify response using the LLM client"""
        # Build context from sources
        context_parts = []
        for idx, source in enumerate(sources[:5], 1):
            repo = source.metadata.get('repo', 'unknown')
            file_path = source.metadata.get('file_path', 'unknown')
            content_preview = source.content[:500] if source.content else ""
            
            context_parts.append(
                f"**Source {idx}** ({repo}/{file_path}):\n```\n{content_preview}\n```\n"
            )
        
        context = "\n".join(context_parts)
        
        try:
            beautified, metadata = await self.client.beautify_response(
                query=query,
                context=context,
                summary=summary,
                query_type=query_type.value
            )
            return beautified
        except Exception as e:
            logger.warning(f"⚠️  Beautification failed: {e}")
            return summary
    
    def _calculate_confidence(self, results: List[SourceResult]) -> float:
        """Calculate overall confidence score"""
        if not results:
            return 0.0
        
        # Average of top results' scores
        top_scores = [r.relevance_score for r in results[:3]]
        return sum(top_scores) / len(top_scores) if top_scores else 0.0

