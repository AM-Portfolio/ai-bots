"""
Vector Store Interface for Qdrant

Handles bulk upsert, metadata schema, and embedding storage with retry logic.
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
import uuid

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False
    logger.warning("Qdrant client not available")


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
    Qdrant vector database interface with bulk operations.
    
    Features:
    - Bulk upsert with retry
    - Rich metadata schema
    - Async operations
    - Health verification
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
        Initialize vector store.
        
        Args:
            collection_name: Qdrant collection name
            embedding_dim: Dimension of embeddings
            distance: Distance metric (Cosine, Euclidean, Dot)
            qdrant_url: URL for Qdrant server (None = local)
            qdrant_path: Path for local Qdrant storage
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self.distance = distance
        
        if not HAS_QDRANT:
            raise ImportError("qdrant-client not installed")
        
        # Initialize client
        if qdrant_url:
            self.client = QdrantClient(url=qdrant_url)
            logger.info(f"Connected to Qdrant at {qdrant_url}")
        else:
            self.client = QdrantClient(path=qdrant_path)
            logger.info(f"Using local Qdrant at {qdrant_path}")
        
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                distance_map = {
                    "Cosine": Distance.COSINE,
                    "Euclidean": Distance.EUCLID,
                    "Dot": Distance.DOT
                }
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=distance_map.get(self.distance, Distance.COSINE)
                    )
                )
                logger.info(f"✅ Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise
    
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
        
        logger.info(f"Upserting {total_points} points in batches of {batch_size}")
        
        # Process in batches
        for i in range(0, total_points, batch_size):
            batch = points[i:i + batch_size]
            
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Convert to Qdrant points
                    qdrant_points = [
                        PointStruct(
                            id=str(uuid.uuid4()),  # Generate unique ID
                            vector=point.embedding,
                            payload={
                                "chunk_id": point.chunk_id,
                                "content": point.content,
                                "summary": point.summary,
                                **point.metadata
                            }
                        )
                        for point in batch
                    ]
                    
                    # Upsert to Qdrant
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=qdrant_points
                    )
                    
                    successful += len(batch)
                    logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} points")
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Failed to upsert batch after {max_retries} retries: {e}")
                        failed += len(batch)
                    else:
                        logger.warning(f"Retry {retry_count}/{max_retries} for batch {i//batch_size + 1}")
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
    
    def search(
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
            filter_dict: Metadata filters
            
        Returns:
            List of search results with scores
        """
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_dict
            )
            
            return [
                {
                    "chunk_id": hit.payload.get("chunk_id"),
                    "content": hit.payload.get("content"),
                    "summary": hit.payload.get("summary"),
                    "score": hit.score,
                    "metadata": {
                        k: v for k, v in hit.payload.items()
                        if k not in ["chunk_id", "content", "summary"]
                    }
                }
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the collection (use with caution!)"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.warning(f"🗑️ Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
