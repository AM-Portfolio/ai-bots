"""
Vector Database API Endpoints

Provides REST API for vector database operations:
- Repository indexing
- Semantic search
- Collection management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.embedding_service import EmbeddingService
from shared.vector_db.services.repository_indexer import RepositoryIndexer
from shared.vector_db.services.vector_query_service import VectorQueryService
from orchestration.github_llm.query_orchestrator import GitHubLLMOrchestrator
from orchestration.github_llm.models import QueryRequest, QueryType
from orchestration.summary_layer.beautifier import ResponseBeautifier
from shared.clients.wrappers.github_wrapper import GitHubWrapper
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vector-db", tags=["vector-db"])


# Pydantic models
class IndexRepositoryRequest(BaseModel):
    owner: str
    repo: str
    branch: str = "main"
    collection: str = "github_repos"


class SemanticSearchRequest(BaseModel):
    query: str
    collection: str = "github_repos"
    top_k: int = 5
    repository: Optional[str] = None
    language: Optional[str] = None


class GitHubLLMQueryRequest(BaseModel):
    query: str
    query_type: str = "semantic_search"
    repository: Optional[str] = None
    max_results: int = 5


class VectorDBStatus(BaseModel):
    provider: str
    initialized: bool
    collections: List[Dict[str, Any]]


# Global instances (will be initialized on startup)
vector_db = None
embedding_service = None
query_service = None
github_llm_orchestrator = None
github_client = None


async def initialize_vector_db():
    """Initialize vector database components"""
    global vector_db, embedding_service, query_service, github_llm_orchestrator, github_client
    
    try:
        logger.info("🔧 Initializing Vector DB system...")
        
        # Create vector DB provider from settings
        provider_type = settings.vector_db_provider
        logger.info(f"   Creating {provider_type.capitalize()} vector DB provider...")
        
        # Pass provider-specific config
        provider_kwargs = {}
        if provider_type == "qdrant":
            provider_kwargs = {
                "host": settings.qdrant_host,
                "port": settings.qdrant_port
            }
        
        vector_db = VectorDBFactory.create(provider_type=provider_type, **provider_kwargs)
        if not vector_db:
            raise Exception("Failed to create vector DB provider")
        
        logger.info("   Initializing vector DB...")
        init_success = await vector_db.initialize()
        if not init_success:
            raise Exception("Vector DB initialization returned False")
        
        # Create embedding service
        logger.info("   Creating embedding service...")
        embedding_service = EmbeddingService(provider="together")
        
        # Create collection
        logger.info("   Creating github_repos collection...")
        collection_created = await vector_db.create_collection(
            name="github_repos",
            dimension=embedding_service.get_dimension()
        )
        if not collection_created:
            logger.warning("   Collection 'github_repos' may already exist, continuing...")
        
        # Create query service
        logger.info("   Creating query service...")
        query_service = VectorQueryService(vector_db, embedding_service)
        
        # Create GitHub client
        logger.info("   Creating GitHub client...")
        github_client = GitHubWrapper()
        if github_client.is_configured:
            logger.info(f"   ✅ GitHub client ready (provider: {github_client.provider})")
        else:
            logger.warning("   ⚠️  GitHub client not configured - repository indexing will be limited")
        
        # Create GitHub-LLM orchestrator
        logger.info("   Creating GitHub-LLM orchestrator...")
        beautifier = ResponseBeautifier(llm_provider="together")
        github_llm_orchestrator = GitHubLLMOrchestrator(
            vector_query_service=query_service,
            beautifier=beautifier
        )
        
        logger.info("✅ Vector DB system initialized successfully")
        logger.info(f"   • Provider: {provider_type}")
        logger.info(f"   • Collection: github_repos ({embedding_service.get_dimension()} dimensions)")
        logger.info(f"   • Query service: ready")
        logger.info(f"   • Orchestrator: ready")
        logger.info(f"   • GitHub client: {'configured' if github_client.is_configured else 'not configured'}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Vector DB system: {e}", exc_info=True)
        # Reset globals on failure
        vector_db = None
        embedding_service = None
        query_service = None
        github_llm_orchestrator = None
        return False


@router.get("/status")
async def get_status() -> VectorDBStatus:
    """Get vector DB status"""
    try:
        if not vector_db:
            return VectorDBStatus(
                provider="none",
                initialized=False,
                collections=[]
            )
        
        is_healthy = await vector_db.health_check()
        
        # Get collection stats
        stats = await vector_db.get_collection_stats("github_repos")
        
        return VectorDBStatus(
            provider="in-memory",
            initialized=is_healthy,
            collections=[stats] if stats else []
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples")
async def get_repository_examples():
    """Get example repositories for indexing"""
    return {
        "examples": [
            {
                "owner": "facebook",
                "repo": "react",
                "branch": "main",
                "description": "React - A JavaScript library for building user interfaces",
                "size": "medium"
            },
            {
                "owner": "microsoft",
                "repo": "vscode",
                "branch": "main",
                "description": "Visual Studio Code - Code editing. Redefined.",
                "size": "large"
            },
            {
                "owner": "psf",
                "repo": "requests",
                "branch": "main",
                "description": "Python HTTP library",
                "size": "small"
            },
            {
                "owner": "vercel",
                "repo": "next.js",
                "branch": "canary",
                "description": "The React Framework",
                "size": "large"
            }
        ],
        "tips": [
            "Start with small repositories (< 1000 files) for faster indexing",
            "Indexing large repositories may take several minutes",
            "Use specific branches for consistent results",
            "The system indexes code files (.py, .js, .ts, etc.) and documentation (.md, .rst)"
        ]
    }


@router.post("/index-repository")
async def index_repository(request: IndexRepositoryRequest):
    """Index a GitHub repository into vector database
    
    Example request:
    ```json
    {
        "owner": "facebook",
        "repo": "react",
        "branch": "main",
        "collection": "github_repos"
    }
    ```
    """
    try:
        if not vector_db or not embedding_service:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        # Validate input
        if not request.owner or not request.repo:
            raise HTTPException(
                status_code=400,
                detail="Both 'owner' and 'repo' fields are required. Example: owner='facebook', repo='react'"
            )
        
        # Create indexer with GitHub client
        indexer = RepositoryIndexer(
            vector_db=vector_db,
            embedding_service=embedding_service,
            github_client=github_client
        )
        
        result = await indexer.index_repository(
            owner=request.owner,
            repo=request.repo,
            branch=request.branch,
            collection_name=request.collection
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    """Perform semantic search over indexed repositories"""
    try:
        if not query_service:
            raise HTTPException(status_code=503, detail="Query service not initialized")
        
        filters = {}
        if request.repository:
            filters['repo_name'] = request.repository
        if request.language:
            filters['language'] = request.language
        
        results = await query_service.semantic_search(
            query=request.query,
            collection=request.collection,
            top_k=request.top_k,
            filters=filters if filters else None
        )
        
        # Convert results to dict for JSON response
        return {
            "query": request.query,
            "results": [
                {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "score": r.score,
                    "metadata": {
                        "repo": r.metadata.repo_name,
                        "file_path": r.metadata.file_path,
                        "language": r.metadata.language
                    }
                }
                for r in results
            ],
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def github_llm_query(request: GitHubLLMQueryRequest):
    """
    Intelligent GitHub+Vector DB query using LangGraph orchestration
    Returns beautified, LLM-ready response
    """
    try:
        if not github_llm_orchestrator:
            raise HTTPException(status_code=503, detail="GitHub-LLM not initialized")
        
        # Convert request to QueryRequest
        query_type_map = {
            "semantic_search": QueryType.SEMANTIC_SEARCH,
            "code_search": QueryType.CODE_SEARCH,
            "repo_summary": QueryType.REPO_SUMMARY,
            "file_explanation": QueryType.FILE_EXPLANATION
        }
        
        query_req = QueryRequest(
            query=request.query,
            query_type=query_type_map.get(request.query_type, QueryType.SEMANTIC_SEARCH),
            repository=request.repository,
            max_results=request.max_results
        )
        
        response = await github_llm_orchestrator.process_query(query_req)
        
        return {
            "query": response.query,
            "summary": response.summary,
            "beautified_response": response.beautified_response,
            "confidence": response.confidence_score,
            "processing_time_ms": response.processing_time_ms,
            "sources": [
                {
                    "type": s.source_type,
                    "content": s.content[:200] + "...",  # Truncate for response
                    "score": s.relevance_score,
                    "metadata": s.metadata
                }
                for s in response.sources
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
