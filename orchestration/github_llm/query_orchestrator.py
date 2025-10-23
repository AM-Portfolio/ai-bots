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
from orchestration.summary_layer.beautifier import ResponseBeautifier
from shared.clients.wrappers.github_wrapper import GitHubWrapper
from shared.config import settings

logger = logging.getLogger(__name__)


class GitHubLLMOrchestrator:
    """Orchestrates queries across multiple sources using LangGraph-style workflow"""
    
    def __init__(
        self,
        code_intelligence_api_url: str = "http://localhost:8000/api/code-intelligence",
        github_client: Optional[GitHubWrapper] = None,
        beautifier: Optional[ResponseBeautifier] = None,
        collection_name: Optional[str] = None
    ):
        """
        Initialize GitHub-LLM orchestrator
        
        Args:
            code_intelligence_api_url: Base URL for Code Intelligence API
            github_client: GitHub API client
            beautifier: Response beautification service
            collection_name: Vector database collection name (defaults to settings)
        """
        self.code_intel_api_url = code_intelligence_api_url
        self.github_client = github_client
        self.beautifier = beautifier
        self.collection_name = collection_name or settings.vector_db_collection_name
        self.http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("🤖 GitHub-LLM Orchestrator initialized")
        logger.info(f"   🌐 Code Intelligence API: {code_intelligence_api_url}")
        logger.info(f"   📂 Default Collection: {self.collection_name}")
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """
        Process a query using LangGraph-style orchestration with enhanced logging
        
        Args:
            request: Query request
            
        Returns:
            Processed query response
        """
        start_time = time.time()
        logger.info("=" * 80)
        logger.info(f"🚀 GITHUB-LLM ORCHESTRATION START")
        logger.info(f"📝 Query: '{request.query[:100]}...'")
        logger.info(f"🎯 Query Type: {request.query_type.value}")
        logger.info(f"� Repository Filter: {request.repository or 'All repositories'}")
        logger.info(f"🔍 Vector Search: {request.include_vector_search}, GitHub Direct: {request.include_github_direct}")
        logger.info(f"🌐 Code Intel API: {self.code_intel_api_url}")
        logger.info("=" * 80)
        
        # Step 1: Query Planning - determine which sources to use
        plan_start = time.time()
        sources_to_query = self._plan_query(request)
        plan_time = (time.time() - plan_start) * 1000
        logger.info(f"📋 STEP 1: Query Planning ({plan_time:.2f}ms)")
        logger.info(f"   Sources to query: {sources_to_query}")
        
        # Step 2: Parallel Source Querying
        query_start = time.time()
        source_results = await self._query_sources(request, sources_to_query)
        query_time = (time.time() - query_start) * 1000
        logger.info(f"📦 STEP 2: Source Querying ({query_time:.2f}ms)")
        logger.info(f"   Retrieved {len(source_results)} source results")
        for i, result in enumerate(source_results[:3], 1):
            logger.info(f"   Source {i}: {result.source_type} - relevance {result.relevance_score:.2f}")
        
        # Step 3: Result Synthesis - combine and rank results
        synth_start = time.time()
        synthesized = self._synthesize_results(source_results, request)
        synth_time = (time.time() - synth_start) * 1000
        logger.info(f"🔗 STEP 3: Result Synthesis ({synth_time:.2f}ms)")
        logger.info(f"   Synthesized {len(synthesized)} results")
        
        # Step 4: Summary Generation
        summary_start = time.time()
        summary = self._generate_summary(synthesized, request)
        summary_time = (time.time() - summary_start) * 1000
        logger.info(f"📄 STEP 4: Summary Generation ({summary_time:.2f}ms)")
        logger.info(f"   Summary length: {len(summary)} characters")
        logger.info(f"   Summary preview: {summary[:150]}...")
        
        # Step 5: Beautification - format for LLM consumption
        beautify_start = time.time()
        beautified = await self._beautify_response(
            query=request.query,
            sources=synthesized,
            summary=summary,
            query_type=request.query_type
        )
        beautify_time = (time.time() - beautify_start) * 1000
        logger.info(f"✨ STEP 5: Response Beautification ({beautify_time:.2f}ms)")
        logger.info(f"   Beautified length: {len(beautified) if beautified else 0} characters")
        
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
                'total_sources': len(synthesized),
                'timing_breakdown': {
                    'planning_ms': plan_time,
                    'querying_ms': query_time,
                    'synthesis_ms': synth_time,
                    'summary_ms': summary_time,
                    'beautification_ms': beautify_time
                }
            }
        )
        
        logger.info("=" * 80)
        logger.info(f"✅ GITHUB-LLM ORCHESTRATION COMPLETE")
        logger.info(f"⏱️  Total Time: {processing_time:.2f}ms")
        logger.info(f"🎯 Confidence: {confidence:.2%}")
        logger.info(f"📊 Timing Breakdown:")
        logger.info(f"   Planning: {plan_time:.2f}ms")
        logger.info(f"   Querying: {query_time:.2f}ms")
        logger.info(f"   Synthesis: {synth_time:.2f}ms")
        logger.info(f"   Summary: {summary_time:.2f}ms")
        logger.info(f"   Beautification: {beautify_time:.2f}ms")
        logger.info("=" * 80)
        
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
        
        if request.include_vector_search:
            sources.append('code_intelligence')
        
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
        
        # Query Code Intelligence API
        if 'code_intelligence' in sources:
            code_intel_results = await self._query_code_intelligence(request)
            results.extend(code_intel_results)
        
        # Query GitHub API directly
        if 'github_api' in sources and self.github_client:
            github_results = await self._query_github_api(request)
            results.extend(github_results)
        
        return results
    
    async def _query_code_intelligence(self, request: QueryRequest) -> List[SourceResult]:
        """Query using Code Intelligence API"""
        try:
            logger.info(f"🔍 Querying Code Intelligence API: '{request.query[:100]}...'")
            
            # Use default collection name (repository-specific collections not yet implemented)
            collection_name = self.collection_name
            logger.info(f"📂 Using default collection: {collection_name}")
            
            # TODO: Repository-specific collections - need to implement indexing first
            # if request.repository:
            #     collection_name = request.repository.replace("/", "_").replace("-", "_").lower()
            #     logger.info(f"📂 Using repository-specific collection: {collection_name}")
            
            # Prepare API request
            api_payload = {
                "query": request.query,
                "limit": request.max_results,
                "collection_name": collection_name
            }
            
            logger.info(f"🌐 Calling Code Intelligence API: POST {self.code_intel_api_url}/query")
            logger.info(f"   📦 Payload: query='{request.query[:100]}...', limit={request.max_results}, collection={collection_name}")
            
            # Call Code Intelligence API
            response = await self.http_client.post(
                f"{self.code_intel_api_url}/query",
                json=api_payload
            )
            
            logger.info(f"📡 API Response: status_code={response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"❌ Code Intelligence API failed: {response.status_code} - {response.text}")
                return []
            
            api_response = response.json()
            
            if not api_response.get('success'):
                logger.error(f"❌ Code Intelligence query failed: {api_response.get('error')}")
                return []
            
            logger.info(f"✅ Code Intelligence API returned {api_response.get('total_results', 0)} results")
            
            # Convert API results to SourceResult format
            source_results = []
            for result in api_response.get('results', []):
                # Extract metadata from result
                payload = result.get('payload', {})
                
                # Extract repo and file info with fallbacks
                repo_name = payload.get('repo_name') or payload.get('repository') or payload.get('source') or 'local-repo'
                file_path = payload.get('file_path') or payload.get('path') or 'unknown'
                
                source = SourceResult(
                    source_type='code_intelligence',
                    content=payload.get('content', ''),
                    metadata={
                        'doc_id': result.get('id'),
                        'repo': repo_name,  # Use 'repo' key for consistency
                        'file_path': file_path,
                        'language': payload.get('language', 'unknown'),
                        'chunk_index': payload.get('chunk_index', 0)
                    },
                    relevance_score=result.get('score', 0.0)
                )
                source_results.append(source)
            
            logger.info(f"✅ Converted {len(source_results)} API results to SourceResult format")
            return source_results
            
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error calling Code Intelligence API: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"❌ Code Intelligence query failed: {e}", exc_info=True)
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
