"""
Vector Store Interface using Shared VectorDBProvider

Handles bulk upsert, metadata schema, and embedding storage with retry logic.
Now integrated with the shared vector_db system for consistency.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.vector_db.factory import VectorDBFactory
from shared.vector_db.base import VectorDBProvider, DocumentMetadata, VectorSearchResult

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingPoint:
    """A point to be inserted into vector database"""
    chunk_id: str
    embedding: List[float]
    content: str
    summary: str
    metadata: Dict[str, Any]


class VectorStore:
    """
    Vector database interface using shared VectorDBProvider.
    
    Features:
    - Bulk upsert with retry
    - Rich metadata schema
    - Async operations
    - Health verification
    - Integration with shared vector_db system
    """
    
    def __init__(
        self,
        collection_name: str = "code_intelligence",
        embedding_dim: int = 3072,  # text-embedding-3-large
        distance: str = "Cosine",
        qdrant_url: Optional[str] = None,
        qdrant_path: Optional[str] = "./qdrant_data"
    ):
        """
        Initialize vector store using shared VectorDBProvider.
        
        Args:
            collection_name: Collection name
            embedding_dim: Dimension of embeddings
            distance: Distance metric (Cosine, Euclidean, Dot)
            qdrant_url: URL for Qdrant server (if using remote)
            qdrant_path: Path for local Qdrant storage (default: ./qdrant_data)
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.distance = distance
        
        # Create VectorDBProvider using factory
        # Note: For local Qdrant, we use path-based connection (localhost:6333)
        logger.info("🏭 Initializing VectorStore with shared VectorDBProvider...")
        
        # Import settings for Qdrant configuration
        from shared.config import settings
        
        if qdrant_url:
            # Parse URL to extract host and port
            from urllib.parse import urlparse
            parsed = urlparse(qdrant_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6333
            self.provider: VectorDBProvider = VectorDBFactory.create(
                provider_type="qdrant",
                host=host,
                port=port
            )
            logger.info(f"✅ Using remote Qdrant: {host}:{port}")
        else:
            # Use settings for host/port, fallback to localhost:6333
            host = settings.qdrant_host or "localhost"
            port = settings.qdrant_port or 6333
            self.provider = VectorDBFactory.create(
                provider_type="qdrant",
                host=host,
                port=port
            )
            logger.info(f"✅ Using Qdrant at {host}:{port} (data: {qdrant_path})")
        
        if not self.provider:
            raise RuntimeError("Failed to create VectorDBProvider")
        
        # Mark as not initialized - caller must call initialize()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the vector store (must be called after construction)"""
        if self._initialized:
            return
        
        await self.provider.initialize()
        await self.provider.create_collection(
            name=self.collection_name,
            dimension=self.embedding_dim
        )
        self._initialized = True
        logger.info(f"✅ Vector store initialized with collection: {self.collection_name}")
    
    @classmethod
    async def create(
        cls,
        collection_name: str = "code_intelligence",
        embedding_dim: int = 3072,
        distance: str = "Cosine",
        qdrant_url: Optional[str] = None,
        qdrant_path: Optional[str] = "./qdrant_data"
    ) -> "VectorStore":
        """Async factory method to create and initialize VectorStore"""
        instance = cls(
            collection_name=collection_name,
            embedding_dim=embedding_dim,
            distance=distance,
            qdrant_url=qdrant_url,
            qdrant_path=qdrant_path
        )
        await instance.initialize()
        return instance
    
    def _create_metadata(self, point: EmbeddingPoint) -> DocumentMetadata:
        """Convert EmbeddingPoint metadata to DocumentMetadata"""
        return DocumentMetadata(
            doc_id=point.chunk_id,
            source=point.metadata.get('source', 'code_intelligence'),
            repo_name=point.metadata.get('repo_name'),
            file_path=point.metadata.get('file_path'),
            commit_sha=point.metadata.get('commit_sha'),
            content_type=point.metadata.get('chunk_type', 'code'),
            language=point.metadata.get('language'),
            author=point.metadata.get('author'),
            created_at=datetime.fromisoformat(point.metadata['created_at']) if point.metadata.get('created_at') else None,
            updated_at=datetime.fromisoformat(point.metadata['updated_at']) if point.metadata.get('updated_at') else None,
            tags=point.metadata.get('tags', [])
        )
    
    async def upsert_batch(
        self,
        points: List[EmbeddingPoint],
        batch_size: int = 100,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Upsert multiple embeddings in batches.
        
        Args:
            points: List of embedding points to upsert
            batch_size: Number of points per batch
            max_retries: Maximum retry attempts per batch
            
        Returns:
            Dict with success stats
        """
        total_points = len(points)
        successful = 0
        failed = 0
        
        logger.info(f"📤 Upserting {total_points} points in batches of {batch_size}")
        
        # Process in batches
        for i in range(0, total_points, batch_size):
            batch = points[i:i + batch_size]
            
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Convert to format expected by VectorDBProvider
                    documents = []
                    embeddings = []
                    metadatas = []
                    
                    for point in batch:
                        # Combine content and summary into document text
                        doc_text = f"{point.content}\n\nSummary: {point.summary}"
                        documents.append(doc_text)
                        embeddings.append(point.embedding)
                        
                        # Create DocumentMetadata with additional fields in payload
                        metadata = self._create_metadata(point)
                        metadatas.append(metadata)
                    
                    # Use shared provider's add_documents
                    success = await self.provider.add_documents(
                        collection=self.collection_name,
                        documents=documents,
                        embeddings=embeddings,
                        metadatas=metadatas
                    )
                    
                    if success:
                        successful += len(batch)
                        logger.debug(f"   ✅ Batch {i//batch_size + 1}: {len(batch)} points")
                        break
                    else:
                        raise Exception("add_documents returned False")
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"   ❌ Failed batch after {max_retries} retries: {e}")
                        failed += len(batch)
                    else:
                        logger.warning(f"   ⚠️  Retry {retry_count}/{max_retries} for batch {i//batch_size + 1}")
                        await asyncio.sleep(1 * retry_count)  # Exponential backoff
        
        result = {
            "total": total_points,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_points * 100 if total_points > 0 else 0
        }
        
        logger.info(
            f"✅ Upsert complete: {successful}/{total_points} points "
            f"({result['success_rate']:.1f}% success rate)"
        )
        
        return result
    
    async def upsert_single(
        self,
        chunk_id: str,
        embedding: List[float],
        content: str,
        summary: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Upsert a single embedding"""
        point = EmbeddingPoint(
            chunk_id=chunk_id,
            embedding=embedding,
            content=content,
            summary=summary,
            metadata=metadata
        )
        
        result = await self.upsert_batch([point])
        return result["successful"] > 0
    
    async def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar code chunks.
        
        Args:
            query_embedding: Query vector
            limit: Maximum results to return
            score_threshold: Minimum similarity score
            filter_dict: Metadata filters (supports glob patterns for file_path_pattern)
            
        Returns:
            List of search results with scores
        """
        try:
            import fnmatch
            
            logger.info(f"🔍 Vector search with filter_dict: {filter_dict}")
            
            # Build filter for VectorDBProvider
            provider_filter = {}
            file_path_pattern = None
            
            if filter_dict:
                for key, value in filter_dict.items():
                    if key == "file_path_pattern":
                        # Handle glob pattern separately (post-filter)
                        file_path_pattern = value
                        logger.info(f"   • Will post-filter by file_path_pattern: {value}")
                    elif key == "chunk_type":
                        # Map chunk_type to content_type for DocumentMetadata
                        provider_filter["content_type"] = value
                        logger.info(f"   • Added content_type filter: {value}")
                    elif key in ["language", "source", "repo_name"]:
                        provider_filter[key] = value
                        logger.info(f"   • Added {key} filter: {value}")
                    # Note: embedding_type is not in DocumentMetadata, will be ignored
            
            logger.info(f"   • Searching with provider_filter: {provider_filter}")
            
            # Search with higher limit if we need to post-filter by path pattern
            search_limit = limit * 5 if file_path_pattern else limit
            
            # Use shared provider's search
            results: List[VectorSearchResult] = await self.provider.search(
                collection=self.collection_name,
                query_embedding=query_embedding,
                top_k=search_limit,
                filter_metadata=provider_filter if provider_filter else None
            )
            
            logger.info(f"   • Provider returned {len(results)} results")
            
            # Convert VectorSearchResult to dict format and apply filters
            filtered_results = []
            for result in results:
                # Apply score threshold
                if score_threshold and result.score < score_threshold:
                    continue
                
                # Apply file path pattern filter
                file_path = result.metadata.file_path or ""
                if file_path_pattern:
                    if not fnmatch.fnmatch(file_path.lower(), file_path_pattern.lower()):
                        logger.debug(f"   • Skipped (pattern mismatch): {file_path}")
                        continue
                    else:
                        logger.debug(f"   • Matched pattern: {file_path}")
                
                # Parse content and summary from combined document
                content = result.content
                summary = ""
                if "\n\nSummary: " in content:
                    content, summary = content.split("\n\nSummary: ", 1)
                
                filtered_results.append({
                    "chunk_id": result.doc_id,
                    "content": content,
                    "summary": summary,
                    "score": result.score,
                    "metadata": {
                        "file_path": result.metadata.file_path,
                        "language": result.metadata.language,
                        "chunk_type": result.metadata.content_type,
                        "repo_name": result.metadata.repo_name,
                        "source": result.metadata.source,
                        "commit_sha": result.metadata.commit_sha,
                        "author": result.metadata.author,
                        "tags": result.metadata.tags
                    }
                })
                
                # Stop when we have enough results
                if len(filtered_results) >= limit:
                    break
            
            logger.info(f"✅ Returning {len(filtered_results)} filtered results")
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            logger.exception(e)
            return []
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = await self.provider.get_collection_stats(self.collection_name)
            return stats
        except Exception as e:
            logger.error(f"❌ Failed to get collection info: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the entire collection (use with caution!)"""
        try:
            logger.warning(f"⚠️  Deleting collection '{self.collection_name}'...")
            
            # Use the underlying Qdrant client to delete collection
            if hasattr(self.provider, 'client') and self.provider.client:
                self.provider.client.delete_collection(collection_name=self.collection_name)
                logger.info(f"✅ Collection '{self.collection_name}' deleted successfully")
                return True
            else:
                logger.error(f"❌ Cannot delete collection: provider client not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete collection '{self.collection_name}': {e}")
            return False
    
    def health_check(self) -> bool:
        """Check if vector database is healthy"""
        try:
            health = asyncio.run(self.provider.health_check())
            return health
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False

