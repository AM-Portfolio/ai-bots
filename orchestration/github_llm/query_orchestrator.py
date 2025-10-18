"""
GitHub-LLM Query Orchestrator

Uses LangGraph to orchestrate queries across vector DB and GitHub API,
then formats responses using the summary/beautify layer.
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import QueryRequest, QueryResponse, SourceResult, QueryType
from shared.vector_db.services.vector_query_service import VectorQueryService
from shared.clients.wrappers.github_wrapper import GitHubWrapper
from orchestration.summary_layer.beautifier import ResponseBeautifier

logger = logging.getLogger(__name__)


class GitHubLLMOrchestrator:
    """Orchestrates queries across multiple sources using LangGraph-style workflow"""
    
    def __init__(
        self,
        vector_query_service: Optional[VectorQueryService] = None,
        github_client: Optional[GitHubWrapper] = None,
        beautifier: Optional[ResponseBeautifier] = None
    ):
        """
        Initialize GitHub-LLM orchestrator
        
        Args:
            vector_query_service: Vector database query service
            github_client: GitHub API client
            beautifier: Response beautification service
        """
        self.vector_service = vector_query_service
        self.github_client = github_client
        self.beautifier = beautifier
        logger.info("🤖 GitHub-LLM Orchestrator initialized")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a query using LangGraph-style orchestration
        
        Args:
            request: Query request
            
        Returns:
            Processed query response
        """
        start_time = time.time()
        logger.info(f"🔄 Processing query: '{request.query[:50]}...'")
        
        # Step 1: Query Planning - determine which sources to use
        sources_to_query = self._plan_query(request)
        logger.info(f"📋 Query plan: {sources_to_query}")
        
        # Step 2: Parallel Source Querying
        source_results = await self._query_sources(request, sources_to_query)
        logger.info(f"📦 Retrieved {len(source_results)} source results")
        
        # Step 3: Result Synthesis - combine and rank results
        synthesized = self._synthesize_results(source_results, request)
        
        # Step 4: Summary Generation
        summary = self._generate_summary(synthesized, request)
        
        # Step 5: Beautification - format for LLM consumption
        beautified = await self._beautify_response(
            query=request.query,
            sources=synthesized,
            summary=summary,
            query_type=request.query_type
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence(synthesized)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = QueryResponse(
            query=request.query,
            query_type=request.query_type,
            sources=synthesized,
            summary=summary,
            beautified_response=beautified,
            confidence_score=confidence,
            processing_time_ms=processing_time,
            metadata={
                'sources_queried': sources_to_query,
                'total_sources': len(synthesized)
            }
        )
        
        logger.info(f"✅ Query processed in {processing_time:.2f}ms (confidence: {confidence:.2f})")
        return response
    
    def _plan_query(self, request: QueryRequest) -> List[str]:
        """
        Plan which sources to query based on request type
        
        Args:
            request: Query request
            
        Returns:
            List of source identifiers to query
        """
        sources = []
        
        if request.include_vector_search and self.vector_service:
            sources.append('vector_db')
        
        if request.include_github_direct and self.github_client:
            sources.append('github_api')
        
        return sources
    
    async def _query_sources(
        self,
        request: QueryRequest,
        sources: List[str]
    ) -> List[SourceResult]:
        """
        Query all specified sources
        
        Args:
            request: Query request
            sources: List of sources to query
            
        Returns:
            Combined results from all sources
        """
        results = []
        
        # Query Vector DB
        if 'vector_db' in sources and self.vector_service:
            vector_results = await self._query_vector_db(request)
            results.extend(vector_results)
        
        # Query GitHub API directly
        if 'github_api' in sources and self.github_client:
            github_results = await self._query_github_api(request)
            results.extend(github_results)
        
        return results
    
    async def _query_vector_db(self, request: QueryRequest) -> List[SourceResult]:
        """Query vector database"""
        try:
            # Apply filters based on request
            filters = {}
            if request.repository:
                filters['repo_name'] = request.repository
            if request.language:
                filters['language'] = request.language
            
            vector_results = await self.vector_service.semantic_search(
                query=request.query,
                top_k=request.max_results,
                filters=filters if filters else None
            )
            
            # Convert to SourceResult
            source_results = []
            for vr in vector_results:
                source = SourceResult(
                    source_type='vector_db',
                    content=vr.content,
                    metadata={
                        'doc_id': vr.doc_id,
                        'repo': vr.metadata.repo_name,
                        'file_path': vr.metadata.file_path,
                        'language': vr.metadata.language
                    },
                    relevance_score=vr.score
                )
                source_results.append(source)
            
            logger.info(f"🔍 Vector DB returned {len(source_results)} results")
            return source_results
            
        except Exception as e:
            logger.error(f"❌ Vector DB query failed: {e}")
            return []
    
    async def _query_github_api(self, request: QueryRequest) -> List[SourceResult]:
        """Query GitHub API directly"""
        try:
            # TODO: Implement direct GitHub API querying
            # For now, return empty
            logger.info("📡 GitHub API query (not fully implemented)")
            return []
            
        except Exception as e:
            logger.error(f"❌ GitHub API query failed: {e}")
            return []
    
    def _synthesize_results(
        self,
        results: List[SourceResult],
        request: QueryRequest
    ) -> List[SourceResult]:
        """
        Synthesize and rank results from multiple sources
        
        Args:
            results: Raw results from all sources
            request: Original request
            
        Returns:
            Ranked and deduplicated results
        """
        # Sort by relevance score
        sorted_results = sorted(
            results,
            key=lambda x: x.relevance_score,
            reverse=True
        )
        
        # Take top N
        return sorted_results[:request.max_results]
    
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
        """
        Beautify response using the beautifier service
        
        Args:
            query: Original query
            sources: Source results
            summary: Generated summary
            query_type: Type of query
            
        Returns:
            Beautified response
        """
        if not self.beautifier:
            return summary
        
        return await self.beautifier.beautify(
            query=query,
            sources=sources,
            summary=summary,
            query_type=query_type
        )
    
    def _calculate_confidence(self, results: List[SourceResult]) -> float:
        """Calculate overall confidence score"""
        if not results:
            return 0.0
        
        # Average of top results' scores
        top_scores = [r.relevance_score for r in results[:3]]
        return sum(top_scores) / len(top_scores) if top_scores else 0.0
