"""
Code Intelligence API

FastAPI router for code intelligence operations including:
- Repository embedding (local and GitHub)
- Code querying with semantic search
- Health and status checks
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Add parent directory for shared imports
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import CodeIntelligenceOrchestrator
from storage.vector_store import VectorStore
from shared.vector_db.embedding_service import EmbeddingService
from shared.logger import get_logger
from shared.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/api/code-intelligence", tags=["code-intelligence"])


class EmbedRepoRequest(BaseModel):
    """Request model for repository embedding"""
    # Repository source (at least one required)
    github_repository: Optional[str] = None  # GitHub repository (owner/repo)
    repo: Optional[str] = None  # Local repository path
    
    # Processing options
    max_files: Optional[int] = None  # None = process all files
    force_reindex: bool = False
    collection_name: Optional[str] = None  # Defaults to settings.vector_db_collection_name
    
    # GitHub LLM filters (only used with github_repository)
    query: Optional[str] = None  # Filter files by query
    language: Optional[str] = None  # Filter by language


class EmbedRepoResponse(BaseModel):
    """Response model for repository embedding"""
    success: bool
    stats: Dict[str, Any]
    message: str


class QueryCodeRequest(BaseModel):
    """Request model for code querying"""
    query: str
    limit: int = 10
    collection_name: Optional[str] = None  # Defaults to settings.vector_db_collection_name
    filters: Optional[Dict[str, Any]] = None
    min_score: float = 0.7


class QueryCodeResponse(BaseModel):
    """Response model for code querying"""
    success: bool
    results: List[Dict[str, Any]]
    query: str
    total_results: int


# Global orchestrator instance (lazy initialization)
_orchestrator: Optional[CodeIntelligenceOrchestrator] = None


def get_orchestrator(repo_path: str = ".") -> CodeIntelligenceOrchestrator:
    """Get or create the global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CodeIntelligenceOrchestrator(repo_path=repo_path)
    return _orchestrator


@router.post("/embed", response_model=EmbedRepoResponse)
async def embed_repository(request: EmbedRepoRequest):
    """
    Embed a repository with enhanced summaries.
    
    Endpoint: POST /api/code-intelligence/embed
    
    Request Body:
    - repo: Local repository path (e.g., "./my-project") OR
    - github_repository: GitHub repo (e.g., "owner/repo")
    - max_files: Maximum files to process (default: None = all files)
    - force_reindex: Force re-embedding (default: false)
    - collection_name: Vector DB collection (default: "code_intelligence")
    - query: Filter files by query (GitHub repos only)
    - language: Filter by language (GitHub repos only)
    
    This endpoint:
    1. Analyzes repository structure (GitHub LLM for GitHub repos)
    2. Discovers and prioritizes code files
    3. Generates rich technical summaries
    4. Embeds code + summaries together
    5. Stores in vector database
    
    Examples:
    - Local repo: {"repo": "./my-project", "max_files": 50}
    - GitHub repo: {"github_repository": "octocat/Hello-World"}
    - All files: {"repo": "."} (max_files defaults to None)
    """
    try:
        # Validate input
        if not request.repo and not request.github_repository:
            raise HTTPException(
                status_code=400,
                detail="Either 'repo' or 'github_repository' must be provided"
            )
        
        # Log request details
        if request.github_repository:
            logger.info(f"📥 Embed request for GitHub repository: {request.github_repository}")
            if request.query:
                logger.info(f"   Query filter: {request.query}")
            if request.language:
                logger.info(f"   Language filter: {request.language}")
        else:
            logger.info(f"📥 Embed request for local repository: {request.repo}")
        
        files_msg = f"max {request.max_files} files" if request.max_files else "all files"
        logger.info(f"   Processing: {files_msg}")
        
        # Get orchestrator (set repo path if local)
        orchestrator = get_orchestrator(repo_path=request.repo or ".")
        
        # Embed repository
        stats = await orchestrator.embed_repository(
            collection_name=request.collection_name,
            max_files=request.max_files,
            force_reindex=request.force_reindex,
            github_repository=request.github_repository,
            query=request.query,
            language=request.language
        )
        
        if not stats.get("success", True):
            raise HTTPException(
                status_code=500,
                detail=stats.get("error", "Embedding failed")
            )
        
        repo_name = request.github_repository or request.repo
        return EmbedRepoResponse(
            success=True,
            stats=stats,
            message=f"Successfully embedded {stats.get('chunks_embedded', 0)} code chunks from {repo_name}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryCodeResponse)
async def query_code(request: QueryCodeRequest):
    """
    Query code using semantic search.
    
    Endpoint: POST /api/code-intelligence/query
    
    Searches across:
    - Raw code content
    - Enhanced technical summaries
    - Metadata (language, file paths, symbols, etc.)
    """
    try:
        logger.info(f"🔍 Querying code: '{request.query}'")
        logger.info(f"   • Limit: {request.limit}")
        logger.info(f"   • Collection: {request.collection_name}")
        if request.filters:
            logger.info(f"   • Filters: {request.filters}")
        
        orchestrator = get_orchestrator()
        
        # Note: orchestrator.query() only accepts query_text, collection_name, and limit
        # min_score and filters are not yet supported
        response = await orchestrator.query(
            query_text=request.query,
            collection_name=request.collection_name,
            limit=request.limit
        )
        
        # Extract results from orchestrator response
        results = response.get("results", [])
        
        logger.info(f"✅ Found {len(results)} results")
        if results:
            logger.info(f"   • Top result score: {results[0].get('score', 0):.4f}")
            logger.info(f"   • Top result: {results[0].get('metadata', {}).get('file_path', 'N/A')}")
        
        return QueryCodeResponse(
            success=True,
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get code intelligence system status
    
    Endpoint: GET /api/code-intelligence/status
    """
    try:
        orchestrator = get_orchestrator()
        
        # Get basic status
        stats = await orchestrator.get_stats()
        
        # Lazy import parser_registry
        try:
            from parsers import parser_registry
            supported_languages = parser_registry.get_supported_languages()
            supported_extensions = parser_registry.get_supported_extensions()
        except (ImportError, Exception) as e:
            logger.warning(f"Could not load parser registry: {e}")
            supported_languages = []
            supported_extensions = []
        
        return {
            "status": "ready",
            "stats": stats,
            "supported_languages": supported_languages,
            "supported_extensions": supported_extensions
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Health check endpoint
    
    Endpoint: GET /api/code-intelligence/health
    """
    try:
        orchestrator = get_orchestrator()
        health = await orchestrator.health_check()
        
        return {
            "healthy": health.get("all_healthy", False),
            "details": health
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


@router.delete("/cleanup")
async def cleanup(
    collection_name: Optional[str] = None,  # Defaults to settings
    confirm: bool = False
):
    """
    Cleanup/delete collection data
    
    Endpoint: DELETE /api/code-intelligence/cleanup?collection_name=xxx&confirm=true
    """
    try:
        # Use collection name from settings if not provided
        if collection_name is None:
            collection_name = settings.vector_db_collection_name
        
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Must set confirm=true to delete data"
            )
        
        logger.info(f"🧹 Cleanup request for collection: {collection_name}")
        
        orchestrator = get_orchestrator()
        result = await orchestrator.cleanup(
            collection_name=collection_name,
            confirm=True
        )
        
        return {
            "success": result.get("status") == "success",
            "message": result.get("message", "Cleanup complete"),
            "vectors_deleted": result.get("vectors_deleted", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
