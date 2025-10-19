"""
Vector Query Service
Provides semantic search capabilities over indexed repositories
"""

import logging
from typing import List, Dict, Any, Optional

from ..base import VectorDBProvider, VectorSearchResult
from ..embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorQueryService:
    """Service for querying vector database"""
    
    def __init__(
        self,
        vector_db: VectorDBProvider,
        embedding_service: EmbeddingService
    ):
        """
        Initialize vector query service
        
        Args:
            vector_db: Vector database provider
            embedding_service: Embedding generation service
        """
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        logger.info("🔍 Vector Query Service initialized")
    
    async def semantic_search(
        self,
        query: str,
        collection: str = "github_repos",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        Perform semantic search over vector database with enhanced logging
        
        Args:
            query: Natural language query
            collection: Collection to search
            top_k: Number of results to return
            filters: Metadata filters
            
        Returns:
            List of search results
        """
        import time
        start_time = time.time()
        
        logger.info("~" * 60)
        logger.info(f"🔍 VECTOR DB SEMANTIC SEARCH START")
        logger.info(f"📝 Query: '{query[:80]}...'")
        logger.info(f"📦 Collection: {collection}")
        logger.info(f"🎯 Top K: {top_k}")
        logger.info(f"🔧 Filters: {filters or 'None'}")
        logger.info("~" * 60)
        
        try:
            # Generate query embedding
            embed_start = time.time()
            logger.info(f"🧮 Generating query embedding...")
            query_embedding = await self.embedding_service.generate_embedding(query)
            embed_time = (time.time() - embed_start) * 1000
            logger.info(f"✅ Embedding generated ({embed_time:.2f}ms)")
            logger.info(f"   Embedding dimension: {len(query_embedding)}")
            
            # Search vector database
            search_start = time.time()
            logger.info(f"🔎 Searching vector database...")
            results = await self.vector_db.search(
                collection=collection,
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filters
            )
            search_time = (time.time() - search_start) * 1000
            
            total_time = (time.time() - start_time) * 1000
            
            logger.info(f"✅ Search completed ({search_time:.2f}ms)")
            logger.info(f"📊 Results: {len(results)} documents found")
            
            # Log top results
            for i, result in enumerate(results[:3], 1):
                repo = getattr(result.metadata, 'repo_name', 'Unknown')
                file_path = getattr(result.metadata, 'file_path', 'Unknown')
                logger.info(f"   Result {i}: {repo}/{file_path} (score: {result.score:.4f})")
            
            logger.info("~" * 60)
            logger.info(f"✅ VECTOR DB SEMANTIC SEARCH COMPLETE")
            logger.info(f"⏱️  Total Time: {total_time:.2f}ms")
            logger.info(f"   Embedding: {embed_time:.2f}ms")
            logger.info(f"   Search: {search_time:.2f}ms")
            logger.info("~" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}", exc_info=True)
            logger.info("~" * 60)
            return []
    
    async def search_by_repository(
        self,
        query: str,
        repo_name: str,
        collection: str = "github_repos",
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """
        Search within a specific repository
        
        Args:
            query: Search query
            repo_name: Repository name (owner/repo)
            collection: Collection to search
            top_k: Number of results
            
        Returns:
            Search results from specific repository
        """
        logger.info(f"📂 Repository-scoped search: {repo_name}")
        filters = {'repo_name': repo_name}
        return await self.semantic_search(
            query=query,
            collection=collection,
            top_k=top_k,
            filters=filters
        )
    
    async def search_by_language(
        self,
        query: str,
        language: str,
        collection: str = "github_repos",
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """
        Search for code in a specific programming language
        
        Args:
            query: Search query
            language: Programming language
            collection: Collection to search
            top_k: Number of results
            
        Returns:
            Search results filtered by language
        """
        filters = {'language': language}
        return await self.semantic_search(
            query=query,
            collection=collection,
            top_k=top_k,
            filters=filters
        )
    
    async def get_similar_documents(
        self,
        doc_id: str,
        collection: str = "github_repos",
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """
        Find documents similar to a given document
        
        Args:
            doc_id: Document ID
            collection: Collection to search
            top_k: Number of results
            
        Returns:
            Similar documents
        """
        # TODO: Implement document-to-document similarity
        logger.warning("⚠️  Document similarity not fully implemented")
        return []
