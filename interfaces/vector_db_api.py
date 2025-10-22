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
    embedding_service: Optional[Dict[str, Any]] = None


# Global instances (will be initialized on startup)
vector_db = None
embedding_service = None
query_service = None
github_llm_orchestrator = None
github_client = None
active_provider_type = None  # Track which provider is actually being used


async def initialize_vector_db():
    """Initialize vector database components with automatic fallback"""
    global vector_db, embedding_service, query_service, github_llm_orchestrator, github_client, active_provider_type
    
    try:
        logger.info("🔧 Initializing Vector DB system...")
        
        # Try primary provider
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
        
        # If initialization fails and fallback is enabled, try in-memory
        if not init_success and settings.vector_db_fallback_enabled and provider_type != "in-memory":
            logger.warning(f"   ⚠️  {provider_type.capitalize()} initialization failed, falling back to in-memory...")
            provider_type = "in-memory"
            logger.info(f"   Creating In-Memory vector DB provider...")
            vector_db = VectorDBFactory.create(provider_type="in-memory")
            if not vector_db:
                raise Exception("Failed to create fallback in-memory provider")
            init_success = await vector_db.initialize()
        
        if not init_success:
            raise Exception("Vector DB initialization returned False")
        
        # Create embedding service - use Together AI for embeddings to match existing vectors
        # Note: Existing vectors in Qdrant were created with Together AI embeddings
        # To use Azure embeddings, you'll need to re-index all documents
        logger.info("   Creating embedding service...")
        embedding_service = EmbeddingService(provider="together")
        logger.info(f"   Using embedding provider: together (matches existing vector data)")
        
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
        
        # Store the active provider type
        active_provider_type = provider_type
        
        logger.info("✅ Vector DB system initialized successfully")
        logger.info(f"   • Provider: {provider_type}")
        if provider_type == "in-memory" and settings.vector_db_provider != "in-memory":
            logger.info(f"   • Note: Fell back from {settings.vector_db_provider} to in-memory")
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
    """Get vector DB status including embedding service health"""
    try:
        if not vector_db:
            return VectorDBStatus(
                provider="none",
                initialized=False,
                collections=[],
                embedding_service=None
            )
        
        is_healthy = await vector_db.health_check()
        
        # Get collection stats
        stats = await vector_db.get_collection_stats("github_repos")
        
        # Get embedding service health
        embedding_health = None
        if embedding_service:
            embedding_health = await embedding_service.health_check()
        
        return VectorDBStatus(
            provider=active_provider_type or "unknown",
            initialized=is_healthy,
            collections=[stats] if stats else [],
            embedding_service=embedding_health
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


@router.post("/test-embedding")
async def test_embedding(request: dict):
    """Test embedding generation with Together AI and fallback
    
    Example request:
    ```json
    {
        "text": "This is a test text for embedding generation",
        "show_details": true
    }
    ```
    """
    try:
        if not embedding_service:
            raise HTTPException(status_code=503, detail="Embedding service not initialized")
        
        text = request.get("text", "Hello, world! This is a test embedding.")
        show_details = request.get("show_details", False)
        
        # Generate embedding
        embedding = await embedding_service.generate_embedding(text)
        
        # Get service info
        model_info = embedding_service.get_model_info()
        
        response = {
            "text": text,
            "embedding_dimension": len(embedding),
            "model_info": model_info,
            "success": True
        }
        
        if show_details:
            # Show first 10 and last 5 values for inspection
            response["embedding_preview"] = {
                "first_10": embedding[:10],
                "last_5": embedding[-5:],
                "sample_stats": {
                    "min": min(embedding),
                    "max": max(embedding),
                    "mean": sum(embedding) / len(embedding)
                }
            }
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Failed to test embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/{owner}/{repo}/documents")
async def list_repository_documents(
    owner: str, 
    repo: str, 
    collection: str = "github_repos",
    limit: int = 1000
):
    """Get all document names from a specific repository
    
    Example: GET /api/vector-db/repository/AM-Portfolio/am-portfolio/documents?collection=github_repos
    """
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        repo_name = f"{owner}/{repo}"
        logger.info(f"📋 Listing documents from repository '{repo_name}' in collection '{collection}'")
        
        # Search for all documents from this repository
        # We'll use a dummy vector and rely on metadata filtering
        dummy_vector = [0.0] * (embedding_service.get_dimension() if embedding_service else 768)
        
        search_results = await vector_db.search(
            collection=collection,
            query_vector=dummy_vector,
            limit=limit,
            filters={"repo_name": repo_name}
        )
        
        if not search_results:
            # Try alternative metadata field names
            search_results = await vector_db.search(
                collection=collection,
                query_vector=dummy_vector,
                limit=limit,
                filters={"repository": repo_name}
            )
        
        if not search_results:
            # Try with owner/repo split
            search_results = await vector_db.search(
                collection=collection,
                query_vector=dummy_vector,
                limit=limit,
                filters={"owner": owner, "repo": repo}
            )
        
        documents = []
        for result in search_results:
            if result.metadata:
                doc_info = {
                    "id": result.metadata.doc_id if hasattr(result.metadata, 'doc_id') else result.id,
                    "file_path": getattr(result.metadata, 'file_path', 'unknown'),
                    "file_type": getattr(result.metadata, 'file_type', 'unknown'),
                    "size": getattr(result.metadata, 'size', 0),
                    "score": result.score if hasattr(result, 'score') else 0.0
                }
                
                # Add any additional metadata fields
                if hasattr(result.metadata, '__dict__'):
                    for key, value in result.metadata.__dict__.items():
                        if key not in ['doc_id', 'file_path', 'file_type', 'size']:
                            doc_info[key] = value
                
                documents.append(doc_info)
        
        logger.info(f"📋 Found {len(documents)} documents in repository '{repo_name}'")
        
        return {
            "repository": repo_name,
            "collection": collection,
            "document_count": len(documents),
            "documents": documents,
            "filters_tried": [
                {"repo_name": repo_name},
                {"repository": repo_name}, 
                {"owner": owner, "repo": repo}
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list repository documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection/{collection_name}")
async def clear_collection(collection_name: str):
    """Clear all documents from a collection
    
    This will delete all documents but keep the collection structure.
    Useful for re-indexing with fresh data.
    """
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector database not initialized")
        
        # Delete all documents from the collection
        success = await vector_db.delete_collection(collection_name)
        
        if success:
            # Recreate the collection with the same structure
            collection_created = await vector_db.create_collection(
                name=collection_name,
                dimension=embedding_service.get_dimension() if embedding_service else 768
            )
            
            if collection_created:
                logger.info(f"✅ Collection '{collection_name}' cleared and recreated")
                return {
                    "message": f"Collection '{collection_name}' cleared successfully",
                    "collection": collection_name,
                    "action": "cleared_and_recreated",
                    "dimension": embedding_service.get_dimension() if embedding_service else 768
                }
            else:
                logger.warning(f"⚠️  Collection '{collection_name}' cleared but recreation failed")
                return {
                    "message": f"Collection '{collection_name}' cleared but recreation failed",
                    "collection": collection_name,
                    "action": "cleared_only"
                }
        else:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found or could not be cleared")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear collection '{collection_name}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def delete_documents(request: dict):
    """Delete documents from vector database - supports both doc IDs and repository deletion
    
    Example requests:
    
    Delete by document IDs:
    ```json
    {
        "collection": "github_repos",
        "doc_ids": ["doc1", "doc2", "doc3"]
    }
    ```
    
    Delete by repository:
    ```json
    {
        "collection": "github_repos",
        "owner": "AM-Portfolio",
        "repo": "am-portfolio"
    }
    ```
    """
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        collection_name = request.get("collection", "github_repos")
        
        # Check if it's repository-based deletion
        owner = request.get("owner")
        repo = request.get("repo")
        doc_ids = request.get("doc_ids", [])
        
        if owner and repo:
            # Repository-based deletion
            repo_name = f"{owner}/{repo}"
            logger.info(f"🗑️  Deleting all documents from repository '{repo_name}' in collection '{collection_name}'")
            
            # First, let's try to find documents with this repository metadata
            # Note: This is a simplified approach - in production you'd use proper filtering
            try:
                # Search for documents from this repository (using a dummy query vector)
                search_results = await vector_db.search(
                    collection=collection_name,
                    query_vector=[0.0] * (embedding_service.get_dimension() if embedding_service else 768),
                    limit=10000,  # Large limit to get all documents
                    filters={"repo_name": repo_name} if hasattr(vector_db, 'search_with_filters') else None
                )
                
                if search_results and hasattr(search_results, 'matches'):
                    doc_ids = [match.id for match in search_results.matches]
                    logger.info(f"📋 Found {len(doc_ids)} documents to delete for repository '{repo_name}'")
                else:
                    # If search doesn't work or no results, we'll still try to delete
                    # by generating expected document IDs based on repository pattern
                    logger.warning(f"⚠️  Could not search for documents, will attempt deletion anyway")
                    
            except Exception as search_error:
                logger.warning(f"⚠️  Search failed: {search_error}, will attempt deletion anyway")
            
            if not doc_ids:
                return {
                    "message": f"No documents found for repository '{repo_name}'",
                    "collection": collection_name,
                    "repository": repo_name,
                    "deleted_count": 0
                }
                
        elif doc_ids:
            # Document ID-based deletion
            logger.info(f"🗑️  Deleting {len(doc_ids)} specific documents from collection '{collection_name}'")
        else:
            raise HTTPException(status_code=400, detail="Either 'owner' and 'repo' OR 'doc_ids' must be provided")
        
        success = await vector_db.delete_documents(
            collection=collection_name,
            doc_ids=doc_ids
        )
        
        if success:
            response = {
                "message": f"Successfully deleted {len(doc_ids)} documents",
                "collection": collection_name,
                "deleted_count": len(doc_ids)
            }
            
            # Add repository info if it was a repository-based deletion
            if owner and repo:
                response["repository"] = f"{owner}/{repo}"
                response["deletion_type"] = "repository_based"
            else:
                response["doc_ids"] = doc_ids
                response["deletion_type"] = "doc_id_based"
                
            return response
        else:
            raise HTTPException(status_code=404, detail="Failed to delete documents")
        
    except Exception as e:
        logger.error(f"❌ Failed to delete documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/repository/{owner}/{repo}")
async def delete_repository_documents(owner: str, repo: str, collection: str = "github_repos"):
    """Delete all documents from a specific repository (simple endpoint)
    
    Example: DELETE /api/vector-db/repository/AM-Portfolio/am-portfolio?collection=github_repos
    """
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        repo_name = f"{owner}/{repo}"
        logger.info(f"🗑️  Deleting all documents from repository '{repo_name}' in collection '{collection}'")
        
        # Use the full path delete function for consistency
        return await delete_repository_documents_full_path(collection, owner, repo)
        
    except Exception as e:
        logger.error(f"❌ Failed to delete repository documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection/{collection_name}/repository/{owner}/{repo}")
async def delete_repository_documents_full_path(collection_name: str, owner: str, repo: str):
    """Delete all documents from a specific repository
    
    Example: DELETE /api/vector-db/collection/github_repos/repository/AM-Portfolio/am-portfolio
    """
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        repo_name = f"{owner}/{repo}"
        logger.info(f"🗑️  Deleting all documents from repository '{repo_name}' in collection '{collection_name}'")
        
        # Search for all documents from this repository first
        # Use proper vector dimension
        dummy_vector = [0.0] * (embedding_service.get_dimension() if embedding_service else 768)
        
        logger.info(f"🔍 Searching for documents with filter: repo_name='{repo_name}'")
        search_results = await vector_db.search(
            collection=collection_name,
            query_vector=dummy_vector,
            limit=10000,  # Large limit to get all
            filters={"repo_name": repo_name}
        )
        
        if not search_results:
            logger.info(f"🔍 No results with repo_name, trying alternative filters...")
            # Try alternative metadata field names
            search_results = await vector_db.search(
                collection=collection_name,
                query_vector=dummy_vector,
                limit=10000,
                filters={"repository": repo_name}
            )
        
        if not search_results:
            # Try with owner/repo split
            logger.info(f"🔍 Trying with split owner/repo filters...")
            search_results = await vector_db.search(
                collection=collection_name,
                query_vector=dummy_vector,
                limit=10000,
                filters={"owner": owner, "repo": repo}
            )
        
        # Also try without any filters to see all documents (for debugging)
        if not search_results:
            logger.info(f"🔍 No documents found with filters, checking total documents in collection...")
            all_results = await vector_db.search(
                collection=collection_name,
                query_vector=dummy_vector,
                limit=50  # Just a sample
            )
            logger.info(f"📊 Total documents in collection: {len(all_results)}")
            if all_results:
                sample_metadata = all_results[0].metadata if all_results[0].metadata else "No metadata"
                logger.info(f"📝 Sample metadata structure: {sample_metadata}")
        
        logger.info(f"🔍 Found {len(search_results)} documents for repository '{repo_name}'")
        
        if not search_results:
            return {
                "message": f"No documents found for repository '{repo_name}'",
                "collection": collection_name,
                "repository": repo_name,
                "deleted_count": 0
            }
        
        # Extract document IDs
        doc_ids = [result.metadata.doc_id for result in search_results if result.metadata and result.metadata.doc_id]
        
        if doc_ids:
            success = await vector_db.delete_documents(
                collection=collection_name,
                doc_ids=doc_ids
            )
            
            if success:
                logger.info(f"✅ Deleted {len(doc_ids)} documents from repository '{repo_name}'")
                return {
                    "message": f"Successfully deleted all documents from repository '{repo_name}'",
                    "collection": collection_name,
                    "repository": repo_name,
                    "deleted_count": len(doc_ids)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to delete repository documents")
        else:
            return {
                "message": f"No documents found for repository '{repo_name}'",
                "collection": collection_name,
                "repository": repo_name,
                "deleted_count": 0
            }
        
    except Exception as e:
        logger.error(f"❌ Failed to delete repository documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
