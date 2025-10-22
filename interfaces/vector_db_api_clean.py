"""
Vector Database API - Core Vector Operations Only

Provides REST API for essential vector database operations:
- Vector search (semantic search)
- Collection management
- Health checks
- Embedding testing
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.embedding_service import EmbeddingService
from shared.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vector-db", tags=["vector-db"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VectorSearchRequest(BaseModel):
    """Semantic vector search request"""
    query: str
    collection: str = "code_intelligence"
    top_k: int = 10
    filters: Optional[Dict[str, Any]] = None
    min_score: Optional[float] = None


class VectorSearchResponse(BaseModel):
    """Vector search results"""
    success: bool
    results: List[Dict[str, Any]]
    query: str
    total_results: int
    collection: str


class CollectionInfo(BaseModel):
    """Collection information"""
    name: str
    vectors_count: int
    indexed_vectors_count: Optional[int] = None
    points_count: Optional[int] = None
    config: Optional[Dict[str, Any]] = None


class VectorDBStatus(BaseModel):
    """Vector DB system status"""
    provider: str
    initialized: bool
    collections: List[CollectionInfo]
    embedding_service: Optional[Dict[str, Any]] = None


class EmbeddingTestRequest(BaseModel):
    """Test embedding generation"""
    texts: List[str]
    model: Optional[str] = None


class EmbeddingTestResponse(BaseModel):
    """Embedding test results"""
    success: bool
    embeddings_count: int
    dimension: int
    provider: str
    model: str


# ============================================================================
# GLOBAL STATE
# ============================================================================

vector_db = None
embedding_service = None


async def initialize_vector_db():
    """Initialize vector database and embedding service"""
    global vector_db, embedding_service
    
    try:
        logger.info("🔧 Initializing Vector DB system...")
        
        # Create vector DB provider
        provider_type = settings.vector_db_provider
        logger.info(f"   Creating {provider_type.capitalize()} vector DB provider...")
        
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
        
        # Fallback to in-memory if needed
        if not init_success and settings.vector_db_fallback_enabled and provider_type != "in-memory":
            logger.warning(f"   ⚠️  {provider_type.capitalize()} failed, falling back to in-memory...")
            vector_db = VectorDBFactory.create(provider_type="in-memory")
            if vector_db:
                init_success = await vector_db.initialize()
        
        if not init_success:
            raise Exception("Vector DB initialization failed")
        
        logger.info("   ✅ Vector DB initialized")
        
        # Initialize embedding service
        logger.info("   Creating embedding service...")
        embedding_service = EmbeddingService(provider="auto")
        logger.info("   ✅ Embedding service initialized")
        
        logger.info("✅ Vector DB system ready")
        
    except Exception as e:
        logger.error(f"❌ Vector DB initialization failed: {e}")
        raise


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@router.get("/status", response_model=VectorDBStatus)
async def get_status():
    """
    Get vector database status and available collections.
    
    Returns:
        - Provider type (qdrant, in-memory)
        - Initialization status
        - List of collections with metadata
        - Embedding service info
    """
    await initialize_vector_db()
    
    try:
        # Get collections
        collections_data = []
        collections = await vector_db.list_collections()
        
        for collection in collections:
            if isinstance(collection, dict):
                collections_data.append(CollectionInfo(
                    name=collection.get("name", "unknown"),
                    vectors_count=collection.get("vectors_count", 0),
                    indexed_vectors_count=collection.get("indexed_vectors_count"),
                    points_count=collection.get("points_count"),
                    config=collection.get("config")
                ))
            else:
                # Handle collection name string
                collections_data.append(CollectionInfo(
                    name=str(collection),
                    vectors_count=0
                ))
        
        # Get embedding service info
        embedding_info = None
        if embedding_service:
            embedding_info = {
                "provider": embedding_service.provider_name,
                "model": embedding_service.embedding_model,
                "dimension": embedding_service.dimension,
                "api_available": embedding_service.api_available
            }
        
        return VectorDBStatus(
            provider=settings.vector_db_provider,
            initialized=True,
            collections=collections_data,
            embedding_service=embedding_info
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        - healthy: bool
        - provider: str
        - collections_count: int
    """
    try:
        await initialize_vector_db()
        
        collections = await vector_db.list_collections()
        
        return {
            "healthy": True,
            "provider": settings.vector_db_provider,
            "collections_count": len(collections)
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


# ============================================================================
# VECTOR SEARCH ENDPOINTS
# ============================================================================

@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    """
    Perform semantic vector search.
    
    Args:
        query: Natural language search query
        collection: Collection to search in
        top_k: Number of results to return
        filters: Optional metadata filters
        min_score: Minimum similarity score threshold
        
    Returns:
        List of matching documents with scores and metadata
    """
    await initialize_vector_db()
    
    try:
        # Generate query embedding
        embeddings = await embedding_service.embed_texts([request.query])
        query_embedding = embeddings[0]
        
        # Search vector DB
        results = await vector_db.search(
            collection_name=request.collection,
            query_vector=query_embedding,
            limit=request.top_k,
            filter_conditions=request.filters
        )
        
        # Filter by minimum score if specified
        if request.min_score:
            results = [r for r in results if r.get("score", 0) >= request.min_score]
        
        return VectorSearchResponse(
            success=True,
            results=results,
            query=request.query,
            total_results=len(results),
            collection=request.collection
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COLLECTION MANAGEMENT
# ============================================================================

@router.get("/collections")
async def list_collections():
    """
    List all available vector collections.
    
    Returns:
        List of collection names and metadata
    """
    await initialize_vector_db()
    
    try:
        collections = await vector_db.list_collections()
        
        collections_info = []
        for collection in collections:
            if isinstance(collection, dict):
                collections_info.append(collection)
            else:
                collections_info.append({"name": str(collection)})
        
        return {
            "success": True,
            "collections": collections_info,
            "count": len(collections_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections/{collection_name}")
async def get_collection_info(collection_name: str):
    """
    Get detailed information about a specific collection.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection metadata and statistics
    """
    await initialize_vector_db()
    
    try:
        collections = await vector_db.list_collections()
        
        for collection in collections:
            if isinstance(collection, dict):
                if collection.get("name") == collection_name:
                    return {
                        "success": True,
                        "collection": collection
                    }
            elif str(collection) == collection_name:
                return {
                    "success": True,
                    "collection": {"name": collection_name}
                }
        
        raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EMBEDDING TEST ENDPOINTS
# ============================================================================

@router.post("/embedding/test", response_model=EmbeddingTestResponse)
async def test_embedding(request: EmbeddingTestRequest):
    """
    Test embedding generation without storing vectors.
    
    Args:
        texts: List of texts to embed
        model: Optional model override
        
    Returns:
        Embedding generation results and metadata
    """
    await initialize_vector_db()
    
    try:
        # Generate embeddings
        embeddings = await embedding_service.embed_texts(request.texts)
        
        return EmbeddingTestResponse(
            success=True,
            embeddings_count=len(embeddings),
            dimension=len(embeddings[0]) if embeddings else 0,
            provider=embedding_service.provider_name,
            model=embedding_service.embedding_model
        )
        
    except Exception as e:
        logger.error(f"Embedding test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embedding/health")
async def embedding_health():
    """
    Check embedding service health.
    
    Returns:
        - available: bool
        - provider: str
        - model: str
        - dimension: int
    """
    await initialize_vector_db()
    
    try:
        # Test with a simple embedding
        test_embeddings = await embedding_service.embed_texts(["test"])
        
        return {
            "available": True,
            "provider": embedding_service.provider_name,
            "model": embedding_service.embedding_model,
            "dimension": embedding_service.dimension,
            "api_available": embedding_service.api_available
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }
