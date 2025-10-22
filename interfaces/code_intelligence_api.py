"""
Code Intelligence API for Enhanced Embedding and Querying

Integrates the code intelligence pipeline with the main application's
vector database system, enabling rich technical summaries to be embedded
and queried alongside code.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import sys
from pathlib import Path

# Add code-intelligence to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code-intelligence"))

from rate_limiter import RateLimitController, QuotaType
from repo_state import RepoState
from parsers import parser_registry
from change_planner import ChangePlanner
from enhanced_summarizer import EnhancedCodeSummarizer
from vector_store import VectorStore, EmbeddingPoint
from embed_repo import EmbeddingOrchestrator

from shared.logger import get_logger
from shared.azure_services.azure_ai_manager import azure_ai_manager
from shared.llm_providers.github_llm_provider import (
    GitHubLLMProvider,
    RepoAnalysisRequest,
    QueryType
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api/repo-code-intelligence", tags=["repo-code-intelligence"])


class EmbedRepoRequest(BaseModel):
    github_repository: str  # Required: GitHub repository (owner/repo)
    repo_path: str = "."  # Local path for code-intelligence processing
    max_files: Optional[int] = None
    force_reindex: bool = False
    collection_name: str = "code_intelligence"
    query: Optional[str] = None  # Optional: Filter files by query
    language: Optional[str] = None  # Optional: Filter by language


class EmbedRepoResponse(BaseModel):
    success: bool
    stats: Dict[str, Any]
    message: str


class QueryCodeRequest(BaseModel):
    query: str
    limit: int = 10
    collection_name: str = "code_intelligence"
    filters: Optional[Dict[str, Any]] = None
    embedding_type: Optional[str] = "both"  # "code", "summary", or "both"


class QueryCodeResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]]
    query: str
    total_results: int


class CodeIntelligenceOrchestrator:
    """
    Thin API orchestrator - delegates to code-intelligence orchestrator.
    """
    
    def __init__(self):
        self.code_intel_orchestrator = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the orchestrator"""
        if self._initialized:
            return
        
        try:
            logger.info("🚀 Initializing Code Intelligence API Orchestrator...")
            
            # Import and initialize main orchestrator from code-intelligence
            from orchestrator import CodeIntelligenceOrchestrator as MainOrchestrator
            
            self.code_intel_orchestrator = MainOrchestrator(repo_path=".")
            
            self._initialized = True
            logger.info("✅ Code Intelligence API Orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
    
    async def embed_repository(
        self,
        github_repository: str,
        repo_path: str = ".",
        max_files: Optional[int] = None,
        force_reindex: bool = False,
        query: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Embed repository - delegates to main orchestrator.
        
        Args:
            github_repository: GitHub repository (owner/repo)
            repo_path: Local path for processing
            max_files: Maximum files to process
            force_reindex: Force re-embedding of all files
            query: Optional query to filter relevant files
            language: Optional language filter
            
        Returns:
            Statistics about the embedding process
        """
        await self.initialize()
        
        logger.info(f"📖 API: Embed repository request for: {github_repository}")
        
        # Delegate to main CodeIntelligenceOrchestrator which handles GitHub LLM + embedding
        stats = await self.code_intel_orchestrator.embed_repository(
            collection_name="code_intelligence",
            max_files=max_files,
            force_reindex=force_reindex,
            github_repository=github_repository,
            query=query,
            language=language
        )
        
        return stats
    
    async def query_code(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query code - delegates to EmbeddingOrchestrator's vector store.
        
        Args:
            query: Natural language query
            limit: Maximum results
            filters: Metadata filters
            
        Returns:
            List of matching code chunks with summaries
        """
        await self.initialize()
        
        logger.info(f"🔍 API: Query code request: '{query}'")
        
        # Delegate to VectorStore search (via embedding orchestrator)
        # Note: Direct search on vector store, no special query logic needed
        from vector_store import VectorStore
        from shared.vector_db.embedding_service import EmbeddingService
        
        # Generate query embedding
        embedding_service = EmbeddingService(provider="auto")
        query_embedding = await embedding_service.generate_embeddings_batch([query])
        
        # Search vector store
        vector_store = VectorStore(
            collection_name="code_intelligence",
            qdrant_path="./qdrant_data"
        )
        
        results = vector_store.search(
            query_embedding=query_embedding[0],
            limit=limit,
            filter_dict=filters
        )
        
        logger.info(f"✅ Found {len(results)} results")
        
        return results
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.code_intel_orchestrator:
            # Cleanup handled by code-intelligence orchestrator
            pass


# Global orchestrator instance
orchestrator = CodeIntelligenceOrchestrator()


@router.post("/embed", response_model=EmbedRepoResponse)
@router.post("/embed", response_model=EmbedRepoResponse)
async def embed_repository(request: EmbedRepoRequest):
    """
    Embed a repository with enhanced summaries.
    
    Endpoint: POST /api/repo-code-intelligence/embed
    
    This endpoint:
    1. Uses GitHub LLM to analyze repository structure
    2. Identifies relevant files based on query/filters
    3. Discovers and prioritizes code files locally
    4. Generates rich technical summaries
    5. Embeds code + summaries together
    6. Stores in vector database
    
    Workflow:
    - GitHub repository analysis → Local file discovery → Code intelligence embedding
    """
    try:
        logger.info(f"📥 Embed request for GitHub repository: {request.github_repository}")
        if request.query:
            logger.info(f"   Query filter: {request.query}")
        if request.language:
            logger.info(f"   Language filter: {request.language}")
        
        stats = await orchestrator.embed_repository(
            github_repository=request.github_repository,
            repo_path=request.repo_path,
            max_files=request.max_files,
            force_reindex=request.force_reindex,
            query=request.query,
            language=request.language
        )
        
        if not stats.get("success", True):
            raise HTTPException(
                status_code=500,
                detail=stats.get("error", "Embedding failed")
            )
        
        return EmbedRepoResponse(
            success=True,
            stats=stats,
            message=f"Successfully embedded {stats.get('chunks_embedded', 0)} code chunks from {request.github_repository}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryCodeResponse)
async def query_code(request: QueryCodeRequest):
    """
    Query code using semantic search with dual embeddings.
    
    Endpoint: POST /api/repo-code-intelligence/query
    
    Embedding Types:
    - "code": Search raw code embeddings (exact code matching)
    - "summary": Search enhanced summary embeddings (conceptual/technical)
    - "both": Search both and merge results (default, best for most queries)
    
    Searches across:
    - Raw code content (exact matching)
    - Enhanced technical summaries (conceptual understanding)
    - Metadata (language, file paths, symbols, etc.)
    """
    try:
        logger.info(f"🔍 Querying code: '{request.query}'")
        logger.info(f"   • Limit: {request.limit}")
        logger.info(f"   • Embedding type: {request.embedding_type}")
        logger.info(f"   • Filters: {request.filters}")
        
        results = await orchestrator.query_code(
            query=request.query,
            limit=request.limit,
            filters=request.filters,
            embedding_type=request.embedding_type
        )
        
        logger.info(f"✅ Found {len(results)} results")
        if results:
            logger.info(f"   • Top result score: {results[0].get('score', 0):.4f}")
            logger.info(f"   • Top result: {results[0].get('metadata', {}).get('file_path', 'N/A')}")
        
        response = QueryCodeResponse(
            success=True,
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
        logger.info(f"📤 Returning response with {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get repository code intelligence system status
    
    Endpoint: GET /api/repo-code-intelligence/status
    """
    try:
        await orchestrator.initialize()
        
        collection_info = orchestrator.vector_store.get_collection_info()
        repo_stats = orchestrator.repo_state.get_stats()
        
        return {
            "status": "ready",
            "vector_db": collection_info,
            "repository": repo_stats,
            "supported_languages": parser_registry.get_supported_languages(),
            "supported_extensions": parser_registry.get_supported_extensions()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Health check endpoint
    
    Endpoint: GET /api/repo-code-intelligence/health
    """
    try:
        await orchestrator.initialize()
        is_healthy = orchestrator.vector_store.health_check()
        
        return {
            "healthy": is_healthy,
            "azure_openai": azure_ai_manager.models.is_available(),
            "vector_db": is_healthy
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }
