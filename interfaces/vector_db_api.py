"""
Vector Database API Endpoints

Provides REST API for vector database operational tasks:
- Database health and status checks
- Collection statistics and management
- Document listing and deletion (read/admin operations only)

Note: Indexing and embedding operations are handled by the code-intelligence API at /api/code-intelligence/*
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.embedding_service import EmbeddingService
from shared.vector_db.services.vector_query_service import VectorQueryService
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vector-db", tags=["vector-db"])


# Pydantic models
class VectorDBStatus(BaseModel):
    provider: str
    initialized: bool
    collections: List[Dict[str, Any]]
    embedding_service: Optional[Dict[str, Any]] = None


# Global instances (will be initialized on startup)
vector_db = None
embedding_service = None
query_service = None
active_provider_type = None


async def initialize_vector_db():
    """Initialize vector database components with automatic fallback"""
    global vector_db, embedding_service, query_service, active_provider_type
    
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
            logger.info(f"   Qdrant configuration: host={settings.qdrant_host}, port={settings.qdrant_port}")
        
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
        
        # Create embedding service
        logger.info("   Creating embedding service...")
        embedding_service = EmbeddingService(provider="azure")
        logger.info(f"   Using embedding provider: azure (text-embedding-ada-002 for technical content)")
        
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
        
        # Store the active provider type
        active_provider_type = provider_type
        
        logger.info("✅ Vector DB system initialized successfully")
        logger.info(f"   • Provider: {provider_type}")
        if provider_type == "in-memory" and settings.vector_db_provider != "in-memory":
            logger.info(f"   • Note: Fell back from {settings.vector_db_provider} to in-memory")
        logger.info(f"   • Collection: github_repos ({embedding_service.get_dimension()} dimensions)")
        logger.info(f"   • Query service: ready")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Vector DB system: {e}", exc_info=True)
        # Reset globals on failure
        vector_db = None
        embedding_service = None
        query_service = None
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


@router.get("/collections")
async def list_collections():
    """List all collection names present in the vector database"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        logger.info("📋 Fetching all collections from vector database...")
        
        # Get all collections from the provider
        collections = await vector_db.list_collections()
        
        logger.info(f"✅ Found {len(collections)} collections")
        
        return {
            "success": True,
            "provider": active_provider_type or "unknown",
            "collection_count": len(collections),
            "collections": collections
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def check_vector_db_health():
    """Check vector database connection and health"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        is_healthy = await vector_db.health_check()
        
        if not is_healthy:
            logger.warning(f"⚠️  Vector DB health check failed")
            raise HTTPException(
                status_code=503, 
                detail=f"Vector DB is not healthy",
                headers={"X-Health-Status": "unhealthy"}
            )
        
        return {
            "status": "healthy",
            "provider": active_provider_type or "unknown",
            "connected": True,
            "initialized": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to check vector DB health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repository/{owner}/{repo}/documents")
async def list_repository_documents(
    owner: str, 
    repo: str, 
    collection: str = "github_repos",
    limit: int = 1000
):
    """Get all document names from a specific repository"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        repo_name = f"{owner}/{repo}"
        logger.info(f"📋 Listing documents from repository '{repo_name}' in collection '{collection}'")
        
        # Search for all documents from this repository
        dummy_vector = [0.0] * (embedding_service.get_dimension() if embedding_service else 768)
        
        search_results = await vector_db.search(
            collection=collection,
            query_embedding=dummy_vector,
            top_k=limit,
            filter_metadata={"repo_name": repo_name}
        )
        
        if not search_results:
            search_results = await vector_db.search(
                collection=collection,
                query_embedding=dummy_vector,
                top_k=limit,
                filter_metadata={"repository": repo_name}
            )
        
        if not search_results:
            search_results = await vector_db.search(
                collection=collection,
                query_embedding=dummy_vector,
                top_k=limit,
                filter_metadata={"owner": owner, "repo": repo}
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
                documents.append(doc_info)
        
        logger.info(f"📋 Found {len(documents)} documents in repository '{repo_name}'")
        
        return {
            "repository": repo_name,
            "collection": collection,
            "document_count": len(documents),
            "documents": documents
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list repository documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collection/{collection_name}")
async def clear_collection(collection_name: str):
    """Clear all documents from a collection"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector database not initialized")
        
        success = await vector_db.delete_collection(collection_name)
        
        if success:
            collection_created = await vector_db.create_collection(
                name=collection_name,
                dimension=embedding_service.get_dimension() if embedding_service else 768
            )
            
            if collection_created:
                logger.info(f"✅ Collection '{collection_name}' cleared and recreated")
                return {
                    "message": f"Collection '{collection_name}' cleared successfully",
                    "collection": collection_name,
                    "action": "cleared_and_recreated"
                }
            else:
                return {
                    "message": f"Collection '{collection_name}' cleared but recreation failed",
                    "collection": collection_name,
                    "action": "cleared_only"
                }
        else:
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/repository/{owner}/{repo}")
async def delete_repository_documents(owner: str, repo: str, collection: str = "github_repos"):
    """Delete all documents from a specific repository"""
    try:
        if not vector_db:
            raise HTTPException(status_code=503, detail="Vector DB not initialized")
        
        repo_name = f"{owner}/{repo}"
        logger.info(f"🗑️  Deleting all documents from repository '{repo_name}'")
        
        # Search for all documents from this repository
        dummy_vector = [0.0] * (embedding_service.get_dimension() if embedding_service else 768)
        
        search_results = await vector_db.search(
            collection=collection,
            query_embedding=dummy_vector,
            top_k=10000,
            filter_metadata={"repo_name": repo_name}
        )
        
        if not search_results:
            search_results = await vector_db.search(
                collection=collection,
                query_embedding=dummy_vector,
                top_k=10000,
                filter_metadata={"repository": repo_name}
            )
        
        if not search_results:
            search_results = await vector_db.search(
                collection=collection,
                query_embedding=dummy_vector,
                top_k=10000,
                filter_metadata={"owner": owner, "repo": repo}
            )
        
        if not search_results:
            return {
                "message": f"No documents found for repository '{repo_name}'",
                "collection": collection,
                "repository": repo_name,
                "deleted_count": 0
            }
        
        doc_ids = [result.metadata.doc_id for result in search_results if result.metadata and result.metadata.doc_id]
        
        if doc_ids:
            success = await vector_db.delete_documents(
                collection=collection,
                doc_ids=doc_ids
            )
            
            if success:
                logger.info(f"✅ Deleted {len(doc_ids)} documents from repository '{repo_name}'")
                return {
                    "message": f"Successfully deleted all documents from repository '{repo_name}'",
                    "collection": collection,
                    "repository": repo_name,
                    "deleted_count": len(doc_ids)
                }
        
        return {
            "message": f"No documents found for repository '{repo_name}'",
            "collection": collection,
            "repository": repo_name,
            "deleted_count": 0
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to delete repository documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
